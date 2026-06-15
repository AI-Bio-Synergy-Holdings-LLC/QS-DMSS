from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from qs_dmss.app import execute_run_from_path, replay_run
from qs_dmss.core.solver_registry import build_solver
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.io.config import SUPPORTED_DECISION_METRICS, parse_config


def _base_config() -> dict:
    return {
        "run": {"name": "demo", "seed": 1, "output_root": "runs"},
        "engine": {
            "backend": "numpy",
            "grid_shape": [8, 8, 8],
            "box_size": 1.0,
            "mass": 1.0,
            "g_int": 0.05,
            "time_step": 0.02,
            "num_steps": 2,
            "log_every": 1,
        },
        "initial": {"kind": "gaussian", "amplitude": 1.0, "width": 0.2, "random_phase": False},
    }


def test_fractal_backend_config_parses_without_exposing_decision_metrics() -> None:
    raw = _base_config()
    raw["engine"] = {
        **raw["engine"],
        "backend": "numpy_fractal_ssfm",
        "grid_shape": [16, 16, 1],
    }
    raw["geometry"] = {
        "mode": "fuzzy_potential",
        "fractal": "mandelbrot",
        "potential_strength": 10.0,
        "boundary_epsilon": 0.05,
        "mandelbrot_iterations": 16,
        "quadrant_gamma": [1.0, 0.8, 1.2, 0.7],
    }
    raw["spectral"] = {"dealias_fraction": None, "leakage_fraction": 0.8}

    config = parse_config(raw)

    assert config.engine.backend == "numpy_fractal_ssfm"
    assert config.engine.grid_shape == (16, 16, 1)
    assert config.geometry is not None
    assert config.geometry.mode == "fuzzy_potential"
    assert config.geometry.quadrant_gamma == (1.0, 0.8, 1.2, 0.7)
    assert config.spectral is not None
    assert config.spectral.dealias_fraction is None
    assert "spectral_leakage" not in SUPPORTED_DECISION_METRICS
    assert "aliasing_ratio" not in SUPPORTED_DECISION_METRICS


def test_fractal_config_schema_lists_sections_and_backends() -> None:
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "qs_dmss"
        / "assets"
        / "schemas"
        / "run_config.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "geometry" in schema["properties"]
    assert "spectral" in schema["properties"]
    assert schema["properties"]["engine"]["properties"]["backend"]["enum"] == [
        "numpy",
        "numpy_fractal_ssfm",
        "cupy_fractal_ssfm",
    ]


def test_numpy_backend_rejects_fractal_sections_to_prevent_silent_noop() -> None:
    raw = _base_config()
    raw["geometry"] = {"mode": "fuzzy_potential"}

    with pytest.raises(ValueError, match="only supported by fractal SSFM backends"):
        parse_config(raw)


def test_fractal_backend_requires_2d_embedded_grid() -> None:
    raw = _base_config()
    raw["engine"] = {
        **raw["engine"],
        "backend": "numpy_fractal_ssfm",
        "grid_shape": [16, 16, 2],
    }

    with pytest.raises(ValueError, match=r"grid_shape.*\[nx, ny, 1\]"):
        parse_config(raw)


def test_invalid_quadrant_gamma_is_rejected() -> None:
    raw = _base_config()
    raw["engine"] = {
        **raw["engine"],
        "backend": "numpy_fractal_ssfm",
        "grid_shape": [16, 16, 1],
    }
    raw["geometry"] = {"quadrant_gamma": [1.0, 2.0]}

    with pytest.raises(ValueError, match="quadrant_gamma"):
        parse_config(raw)


def test_cupy_backend_fails_cleanly_when_cupy_is_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "cupy", None)
    raw = _base_config()
    raw["engine"] = {
        **raw["engine"],
        "backend": "cupy_fractal_ssfm",
        "grid_shape": [8, 8, 1],
    }
    config = parse_config(raw)

    with pytest.raises(RuntimeError, match="requires CuPy"):
        build_solver(config)


def test_numpy_fractal_backend_creates_verifiable_and_replayable_evidence(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "configs" / "fractal_quadrant_ssfm.yaml"

    first_run = execute_run_from_path(
        config_path=config_path,
        output_root=tmp_path / "runs",
    )
    verification = verify_run_path(first_run.run_dir)
    assert verification.success, verification.errors
    bundle_verification = verify_run_path(first_run.bundle_path)
    assert bundle_verification.success, bundle_verification.errors

    metrics = json.loads((first_run.run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["backend"] == "numpy_fractal_ssfm"
    assert metrics["diagnostics"]["geometry_mode"] == "fuzzy_potential"
    assert metrics["diagnostics"]["conservation_mode"] == "phase_only_fuzzy_potential"
    assert metrics["diagnostics"]["nonconservative_reasons"] == []
    assert "spectral_leakage" in metrics["diagnostics"]
    assert "aliasing_ratio" in metrics["diagnostics"]
    assert "atomic-void" in metrics["diagnostics"]["claim_boundary"]

    run_record = json.loads((first_run.run_dir / "run.json").read_text(encoding="utf-8"))
    assert run_record["backend"] == "numpy_fractal_ssfm"
    assert run_record["execution_job"]["backend"] == "local"
    assert first_run.job_record_path is not None
    assert first_run.job_record_path.exists()

    replayed_run = replay_run(
        run_dir=first_run.run_dir,
        output_root=tmp_path / "replays",
    )
    replay_verification = verify_run_path(replayed_run.run_dir)
    assert replay_verification.success, replay_verification.errors

    first_density = np.load(first_run.run_dir / "artifacts" / "final_density.npy")
    replay_density = np.load(replayed_run.run_dir / "artifacts" / "final_density.npy")
    np.testing.assert_allclose(first_density, replay_density)
