"""Reference independence, falsification controls and evidence identity contracts."""

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "research/falsification"


@pytest.fixture
def pilot(monkeypatch):
    pytest.importorskip("scipy", reason="Install research/falsification/requirements.txt")
    modules = []
    for name in ("reference", "pilot"):
        spec = importlib.util.spec_from_file_location(name, PILOT / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        modules.append(module)
    return modules[-1]


@pytest.fixture
def protocol():
    return json.loads((PILOT / "protocol-v1.json").read_text(encoding="utf-8"))


def test_reference_has_no_production_imports():
    import ast

    tree = ast.parse((PILOT / "reference.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("qs_dmss")
        if isinstance(node, ast.Import):
            assert all(not alias.name.startswith("qs_dmss") for alias in node.names)


def test_retained_evidence_packet_integrity_and_claim_boundary():
    path = ROOT / "docs/review-evidence/falsification-pilot-v1.zip"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4"
    with zipfile.ZipFile(path) as archive:
        hashes = json.loads(archive.read("manifest.sha256.json"))
        assert set(archive.namelist()) == set(hashes) | {"manifest.sha256.json"}
        assert all(hashlib.sha256(archive.read(name)).hexdigest() == sha for name, sha in hashes.items())
        results = json.loads(archive.read("results.json"))
        assert results["source_commit"] == "48d7ab5d10da189caddbcad1dd6622e58d204940"
        assert results["scientific_validation_status"] == "NOT_ESTABLISHED"
        assert results["human_disposition"]["status"] == "PENDING"
        assert results["wolfram"]["status"] == "NOT_EXECUTED"


def test_known_small_graph_reference(pilot):
    ref = pilot.reference.graph(1, "dirichlet", 1.0)
    np.testing.assert_allclose(ref["mass"], [2/9]*3)
    np.testing.assert_allclose(ref["stiffness"], (5/3)*(5*np.eye(3)-np.ones((3, 3))))
    values, modes = pilot.reference.spectrum(ref)
    np.testing.assert_allclose(values, [15, 37.5, 37.5])
    np.testing.assert_allclose(pilot.reference.projector(modes), np.eye(3), atol=1e-14)
    for args in ((3, "neumann", 1.0), (0, "dirichlet", 1.0), (1, "periodic", 1.0), (1, "neumann", 8)):
        with pytest.raises(ValueError):
            pilot.reference.graph(*args)


def test_preregistered_exercises_and_artifacts(pilot, protocol):
    result, arrays = pilot.run_exercises(protocol)
    assert result["status"] == "NOT_FALSIFIED_WITHIN_SCOPE", result
    assert {name: len(rows) for name, rows in result["exercises"].items()} == {"fft": 72, "graph": 15, "evolution": 2}
    assert all(np.all(np.isfinite(array)) for array in arrays.values())
    assert all(row["legacy_omission_rejected"] for row in result["exercises"]["fft"])
    assert all(row["phase_control_rejected"] for row in result["exercises"]["evolution"])


def test_faulty_energy_is_falsified(pilot, protocol, monkeypatch):
    original = pilot.QuantumScalarDarkMatterSolver.compute_energy
    monkeypatch.setattr(pilot.QuantumScalarDarkMatterSolver, "compute_energy",
                        lambda self, psi, potential: 2*original(self, psi, potential))
    rows = pilot.fft_exercise(protocol)
    assert all(row["status"] == "FAIL" for row in rows if row["backend"] == "numpy")


def test_reference_failure_is_inconclusive(pilot, protocol, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("injected reference failure")
    monkeypatch.setattr(pilot.reference, "trajectory", broken)
    result, _ = pilot.run_exercises(protocol)
    assert result["status"] == "INCONCLUSIVE"
    assert "injected reference failure" in result["exercises"]["evolution"][0]["reason"]


def test_unresolved_refinement_is_not_passed(pilot, protocol):
    protocol["evolution"]["resolution_floor"] = 1
    rows = pilot.evolution_exercise(protocol, {})
    assert all(row["status"] == "INCONCLUSIVE" for row in rows)


def test_nonfinite_values_cannot_pass(pilot):
    for value in (float("nan"), float("inf"), -1):
        assert not pilot.bounded(value, 1e-9)


def test_protocol_drift_requires_explicit_revision(pilot, protocol, tmp_path):
    assert pilot.load_protocol(PILOT / "protocol-v1.json") == protocol
    protocol["fft"]["scaled_energy_error_max"] = 1
    path = tmp_path / "altered.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(ValueError, match="preregistration"):
        pilot.load_protocol(path)


def test_rotated_complete_projector_is_invariant(pilot):
    ref = pilot.reference.graph(1, "dirichlet", 1.0)
    _, modes = pilot.reference.spectrum(ref)
    rotation = np.array([[0.6, -0.8], [0.8, 0.6]])
    np.testing.assert_allclose(pilot.reference.projector(modes[:, 1:]),
                               pilot.reference.projector(modes[:, 1:] @ rotation), atol=1e-14)
    assert np.linalg.norm(pilot.reference.projector(modes[:, 1:2]) -
                          pilot.reference.projector((modes[:, 1:] @ rotation)[:, :1])) > 0.1


def test_candidate_identity_and_installed_bytes(pilot, tmp_path, monkeypatch):
    package = tmp_path / "qs_dmss"
    package.mkdir()
    init = package / "__init__.py"
    init.write_text("# candidate\n", encoding="utf-8")
    monkeypatch.setattr(pilot.qs_dmss, "__file__", str(init))
    wheel = tmp_path / "candidate.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("qs_dmss/__init__.py", init.read_bytes())
    receipt = {"source_commit": pilot.SOURCE_COMMIT, "wheel_sha256": pilot.digest(wheel), "source_clean": True}
    assert pilot.verify_candidate(wheel, receipt) == 1
    with pytest.raises(ValueError, match="source pin"):
        pilot.verify_candidate(wheel, {**receipt, "source_commit": "wrong"})
    with pytest.raises(ValueError, match="clean"):
        pilot.verify_candidate(wheel, {**receipt, "source_clean": False})
    extra = package / "unexpected.py"
    extra.write_text("# extra", encoding="utf-8")
    with pytest.raises(ValueError, match="outside"):
        pilot.verify_candidate(wheel, receipt)
    extra.unlink()
    init.write_text("# tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        pilot.verify_candidate(wheel, receipt)


def test_cli_retains_complete_packet_without_overwriting(pilot, tmp_path, monkeypatch):
    wheel = tmp_path / "candidate.whl"
    wheel.write_bytes(b"identity separately tested")
    receipt = tmp_path / "receipt.json"
    receipt.write_text("{}", encoding="utf-8")
    output = tmp_path / "packet"
    monkeypatch.setattr(pilot, "verify_candidate", lambda *args: 1)
    monkeypatch.setattr(sys, "argv", ["pilot.py", "--wheel", str(wheel), "--build-receipt",
                                      str(receipt), "--output", str(output)])
    assert pilot.main() == 0
    results = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert results["human_disposition"] == {"status": "PENDING", "reviewer": None}
    assert results["scientific_validation_status"] == "NOT_ESTABLISHED"
    assert results["wolfram"]["status"] == "NOT_EXECUTED"
    hashes = json.loads((output / "manifest.sha256.json").read_text(encoding="utf-8"))
    assert all(pilot.digest(output / name) == sha for name, sha in hashes.items())
    assert {p.name for p in output.iterdir()} == set(hashes) | {"manifest.sha256.json"}
    with zipfile.ZipFile(tmp_path / "packet.zip") as archive:
        assert set(archive.namelist()) == set(hashes) | {"manifest.sha256.json"}
    with pytest.raises(FileExistsError):
        pilot.main()


def test_nonfinite_counterexample_is_retained_as_failure(pilot, protocol, monkeypatch):
    monkeypatch.setattr(pilot.QuantumScalarDarkMatterSolver, "compute_energy", lambda *args: float("nan"))
    result, _ = pilot.run_exercises(protocol)
    assert result["status"] == "FAIL"
    serialized = json.dumps(pilot.json_record(result), allow_nan=False)
    retained = json.loads(serialized)
    assert retained["exercises"]["fft"][0]["actual_energy"] == {"nonfinite": "nan"}
    assert retained["exercises"]["fft"][0]["status"] == "FAIL"
