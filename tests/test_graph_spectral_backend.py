import json
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from fastapi import HTTPException

from qs_dmss.app import execute_run, replay_run
from qs_dmss.cockpit.api import CockpitService, LaunchRunRequest
from qs_dmss.cockpit.artifacts import CockpitArtifactService
from qs_dmss.core.fractal_graph import build_sierpinski_gasket
from qs_dmss.core.fractal_spectral import FractalGraphSpectralSolver
from qs_dmss.core.fractal_validation import build_multilevel_spectral_report
from qs_dmss.core.graph_policy import graph_resource_estimate
from qs_dmss.core.graph_spectrum import sanitize_spectrum, tail_cluster_start
from qs_dmss.core.solver_registry import build_solver
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.io.config import config_digest, load_config, parse_config
from qs_dmss.io.graph_config import FractalGraphConfig

ROOT = Path(__file__).resolve().parents[1]


def graph_config(level=2, boundary="dirichlet"):
    raw = load_config(ROOT / "configs/sierpinski_graph_spectral.yaml").to_dict()
    raw["engine"].pop("grid_shape")
    raw["engine"]["num_steps"] = 4
    raw["engine"]["log_every"] = 1
    raw["fractal_graph"].update(level=level, boundary_condition=boundary, validation_levels=[])
    return parse_config(raw)


@pytest.mark.parametrize("level", [0, 1, 2, 3, 4, 5])
def test_graph_operator_structure(level):
    graph = build_sierpinski_gasket(level, boundary_condition="neumann")
    assert graph.vertex_count == (3**(level + 1) + 3) // 2
    assert graph.full_edges.shape == (3**(level + 1), 2)
    assert graph.mass_weights.sum() == pytest.approx(1.0)
    assert np.all(graph.mass_weights > 0)
    np.testing.assert_array_equal(graph.stiffness, graph.stiffness.T)
    np.testing.assert_allclose(graph.stiffness @ np.ones(graph.vertex_count), 0, atol=1e-12)
    if level:
        bounded = build_sierpinski_gasket(level)
        assert bounded.vertex_count == graph.vertex_count - 3
        np.testing.assert_allclose(bounded.stiffness, graph.stiffness[np.ix_(bounded.active_vertex_ids, bounded.active_vertex_ids)])


def test_known_dirichlet_spectrum_and_eigenmode_phase():
    config = graph_config(1)
    config = replace(config, engine=replace(config.engine, g_int=0),
                     fractal_graph=replace(config.fractal_graph, quadrant_potential=(0, 0, 0, 0)))
    solver = build_solver(config)
    np.testing.assert_allclose(solver.eigenvalues, [15, 37.5, 37.5], atol=1e-12)
    psi = solver.eigenvectors[:, 0] / solver.sqrt_mass
    expected = psi * np.exp(-1j * config.engine.time_step * 15 / (2 * config.engine.mass))
    np.testing.assert_allclose(solver.step(psi), expected, atol=1e-13)
    assert solver.compute_norm(psi) == pytest.approx(1.0)
    assert solver.compute_energy(psi) == pytest.approx(15 / (2 * config.engine.mass))


def test_tail_is_invariant_under_degenerate_basis_rotation():
    solver = build_solver(graph_config(1, "neumann"))
    assert solver.tail_start == 3  # nominal index 4 crosses the double eigenvalue 45
    psi = solver.eigenvectors[:, 3].astype(complex) / solver.sqrt_mass
    before = solver.compute_spectral_tail_fraction(psi)
    theta = 0.731
    rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    solver.eigenvectors[:, 3:5] = solver.eigenvectors[:, 3:5] @ rotation
    assert solver.compute_spectral_tail_fraction(psi) == pytest.approx(before, abs=1e-13)
    solver.eigenvectors[:, [3, 4]] = solver.eigenvectors[:, [4, 3]]
    assert solver.compute_spectral_tail_fraction(psi) == pytest.approx(before, abs=1e-13)
    assert before == pytest.approx(1.0)
    assert tail_cluster_start(solver.eigenvalues, 1.0)[0] == len(solver.eigenvalues)


def test_nonlinear_refinement_against_independent_rk4():
    solver = build_solver(graph_config())
    initial = solver.initialize_wavefunction()
    operator = solver.graph.stiffness / solver.graph.mass_weights[:, None] / (2 * solver.engine.mass)

    def rhs(psi):
        return -1j * (operator @ psi + (solver.potential + solver.gamma * np.abs(psi)**2) * psi)

    reference = initial.copy()
    total_time = 0.04
    dt = total_time / 2048
    for _ in range(2048):
        k1 = rhs(reference)
        k2 = rhs(reference + dt * k1 / 2)
        k3 = rhs(reference + dt * k2 / 2)
        k4 = rhs(reference + dt * k3)
        reference += dt / 6 * (k1 + 2*k2 + 2*k3 + k4)
    errors = []
    for count in (4, 8, 16):
        psi = initial.copy()
        for _ in range(count):
            psi = solver._step_with_dt(psi, total_time / count)
        errors.append(np.sqrt(np.sum(solver.mass_weights * np.abs(psi - reference)**2)))
        assert solver.compute_norm(psi) == pytest.approx(solver.compute_norm(initial), rel=1e-12)
    assert 3.5 < errors[0] / errors[1] < 4.5
    assert 3.5 < errors[1] / errors[2] < 4.5
    assert solver._time_reversal_error(initial) < 1e-12


def test_multilevel_nullspace_is_not_a_percentage_error():
    report = build_multilevel_spectral_report((1, 2, 3), boundary_condition="neumann", physical_scale=1)
    assert all(row["nullity"] == 1 for row in report["spectra"])
    assert all(row["nullspace_absolute_residual"] < 1e-10 for row in report["spectra"])
    assert report["successive_level_changes"][0]["compared_eigenvalues"] == 5
    assert report == build_multilevel_spectral_report((3, 2, 1), boundary_condition="neumann", physical_scale=1)
    with pytest.raises(ValueError, match="negative"):
        sanitize_spectrum(np.array([-1.0, 1.0]))
    with pytest.raises(ValueError, match="finite"):
        sanitize_spectrum(np.array([np.nan]))


@pytest.mark.parametrize("level", [-1, True, 2.0, 6, 10, 1_000_000])
def test_oversized_or_invalid_graph_rejected_before_allocation(level, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid level reached graph allocation")
    monkeypatch.setattr("qs_dmss.core.fractal_graph._sierpinski_cells", forbidden)
    with pytest.raises(ValueError):
        build_sierpinski_gasket(level)
    with pytest.raises(ValueError):
        FractalGraphConfig(level=level)
    with pytest.raises(ValueError):
        build_multilevel_spectral_report((1, level), boundary_condition="neumann", physical_scale=1)


@pytest.mark.parametrize("field,value", [
    ("device", "gpu"), ("family", "unknown"), ("boundary_condition", "periodic"),
    ("tail_fraction", 0), ("tail_fraction", True), ("tail_fraction", float("nan")),
    ("artifact_eigenmodes", 1000000), ("validation_eigenvalues", True),
    ("quadrant_gamma", [1, 1, 1, float("inf")]),
    ("quadrant_potential", [1, 2]), ("validation_levels", [1, 1]),
    ("validation_levels", [0]), ("validation_levels", [3]),
    ("validation_levels", [True]), ("ignored_option", 2),
])
def test_invalid_graph_options(field, value):
    raw = graph_config().to_dict()
    raw["fractal_graph"][field] = value
    with pytest.raises(ValueError):
        parse_config(raw)


@pytest.mark.parametrize("shape", [[12.0, 1, 1], [12, True, 1], [12, 1], [13, 1, 1]])
def test_explicit_graph_shape_is_strict(shape):
    raw = graph_config().to_dict()
    raw["engine"]["grid_shape"] = shape
    with pytest.raises(ValueError, match="grid_shape"):
        parse_config(raw)


def test_work_limit_applies_to_parser_and_direct_solver():
    config = graph_config(5)
    raw = config.to_dict()
    raw["engine"]["num_steps"] = 10000
    with pytest.raises(ValueError, match="work budget"):
        parse_config(raw)
    with pytest.raises(ValueError, match="work budget"):
        FractalGraphSpectralSolver(replace(config.engine, num_steps=10000), config.initial,
                                   config.run.seed, config.fractal_graph)
    assert graph_resource_estimate(5, "neumann")["estimated_peak_bytes"] < 64 * 1024**2


def test_graph_evidence_roundtrip_and_domain_guards(tmp_path):
    config = graph_config()
    config = replace(config, initial=replace(config.initial, random_phase=True),
                     fractal_graph=replace(config.fractal_graph, validation_levels=(1, 2)))
    assert config_digest(config) == config_digest(parse_config(config.to_dict()))
    run = execute_run(config, tmp_path / "config.yaml", tmp_path / "runs")
    assert verify_run_path(run.run_dir).success
    assert verify_run_path(run.bundle_path).success
    replay = replay_run(run.run_dir, tmp_path / "replays")
    assert verify_run_path(replay.bundle_path).success
    with np.load(run.run_dir / "artifacts" / "graph_operator.npz", allow_pickle=False) as arrays:
        assert arrays["fractal_stiffness"].shape == (12, 12)
        assert arrays["fractal_mass_weights"].shape == (12,)
        assert arrays["fractal_eigenvalues"].shape == (12,)
        active = arrays["fractal_active_vertex_ids"]
        np.testing.assert_array_equal(arrays["fractal_lattice_coordinates"],
                                      arrays["fractal_full_lattice_coordinates"][active])
        np.testing.assert_array_equal(arrays["fractal_coordinates"],
                                      arrays["fractal_full_coordinates"][active])
        assert arrays["fractal_eigenmodes"].shape[1] <= config.fractal_graph.artifact_eigenmodes
    density = np.load(run.run_dir / "artifacts" / "final_density.npy")
    assert density.shape == (12,)
    np.testing.assert_allclose(density, np.load(replay.run_dir / "artifacts" / "final_density.npy"))
    metrics = json.loads((run.run_dir / "metrics.json").read_text())
    assert metrics["energy_diagnostic_convention"] == "graph_mass_stiffness_v1"
    assert metrics["diagnostics"]["domain"]["kind"] == "finite_graph"
    report = (run.run_dir / "report.html").read_text(encoding="utf-8")
    assert "not a rectangular" in report
    assert "not exact full nonlinear evolution" in report
    artifacts = CockpitArtifactService(tmp_path / "runs", tmp_path / "experiments")
    for profile in ("review", "state"):
        with zipfile.ZipFile(artifacts.run_bundle_profile_path(run.run_id, profile)) as bundle:
            assert "artifacts/graph_operator.npz" in bundle.namelist()
    from qs_dmss.quantum_sidecar import _validate_profile
    from qs_dmss.showcase import _write_showcase_artifacts
    with pytest.raises(ValueError, match="numpy_fractal_ssfm"):
        _validate_profile(config)
    with pytest.raises(ValueError, match="finite-graph"):
        _write_showcase_artifacts(tmp_path / "showcase", run.run_dir, config)


def test_graph_does_not_silently_replace_rectangular_sections():
    raw = graph_config().to_dict()
    raw["geometry"] = {}
    with pytest.raises(ValueError, match="rectangular"):
        parse_config(raw)
    old = load_config(ROOT / "configs" / "demo.yaml").to_dict()
    old["fractal_graph"] = {}
    with pytest.raises(ValueError, match="requires"):
        parse_config(old)


def test_hosted_graph_is_not_listed_or_admitted(tmp_path):
    service = CockpitService.create(ROOT, output_root=tmp_path, hosted_demo=True)
    assert "sierpinski_graph_spectral.yaml" not in {item["name"] for item in service.list_configs()}
    with pytest.raises(HTTPException) as exc:
        service._assert_hosted_config_envelope(graph_config().to_dict())
    assert exc.value.status_code == 403
    assert "local-only" in exc.value.detail


@pytest.mark.parametrize("scale", [0, float("nan"), float("inf"), 1e-300, 1e7])
def test_scale_is_validated_at_every_entry_point(scale):
    with pytest.raises(ValueError):
        build_sierpinski_gasket(1, physical_scale=scale)
    raw = graph_config().to_dict()
    raw["engine"]["box_size"] = scale
    with pytest.raises(ValueError):
        parse_config(raw)


def test_cpu_only_local_cockpit_acceptance(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "cupy", None)
    service = CockpitService.create(ROOT, output_root=tmp_path / "runs", hosted_demo=False)
    config = graph_config()
    config = replace(config, initial=replace(config.initial, kind="uniform"))
    detail = service.launch_run(LaunchRunRequest(config=config.to_dict(), source_name="graph.yaml"))
    assert detail["metrics"]["diagnostics"]["device"] == "cpu"
    assert detail["metrics"]["diagnostics"]["domain"]["state_shape"] == [12]
    assert "sierpinski_graph_spectral.yaml" in {item["name"] for item in service.list_configs()}
    run_id = detail["run_record"]["run_id"]
    replay = service.replay_run(run_id)
    assert replay["metrics"]["diagnostics"]["device"] == "cpu"
    hosted = CockpitService.create(ROOT, output_root=tmp_path / "runs", hosted_demo=True)
    with pytest.raises(HTTPException, match="local-only"):
        hosted.replay_run(run_id)


def test_run_schemas_and_graph_contract():
    from jsonschema import Draft202012Validator

    schema = json.loads((ROOT / "schemas/run_config.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for path in (ROOT / "configs").glob("*.yaml"):
        validator.validate(load_config(path).to_dict())
    for level in range(6):
        raw = graph_config(level, "neumann").to_dict()
        validator.validate(raw)
        raw["engine"].pop("grid_shape")
        validator.validate(raw)
    raw = graph_config().to_dict()
    for key, value in (("device", "gpu"), ("level", 6), ("validation_levels", [3])):
        invalid = json.loads(json.dumps(raw))
        invalid["fractal_graph"][key] = value
        assert not validator.is_valid(invalid)
    raw["engine"]["grid_shape"] = [12, True, 1]
    assert not validator.is_valid(raw)
    raw = graph_config(5).to_dict()
    raw["engine"]["num_steps"] = 10000
    assert not validator.is_valid(raw)
