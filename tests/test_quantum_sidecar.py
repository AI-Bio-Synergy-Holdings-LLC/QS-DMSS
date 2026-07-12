from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from qs_dmss.cli import main
from qs_dmss.quantum_sidecar import (
    QUANTUM_SIDECAR_BUNDLE,
    QUANTUM_SIDECAR_JSON_REPORT,
    QUANTUM_SIDECAR_MANIFEST,
    QUANTUM_SIDECAR_MARKDOWN_REPORT,
    validate_fractal_quantum_sidecar,
    verify_quantum_sidecar_directory,
)


QUANTUM_STACK_AVAILABLE = (
    importlib.util.find_spec("qiskit") is not None
    and importlib.util.find_spec("qiskit_aer") is not None
)


@pytest.mark.skipif(not QUANTUM_STACK_AVAILABLE, reason="optional quantum stack not installed")
def test_fractal_quantum_sidecar_writes_verifiable_evidence(tmp_path: Path) -> None:
    output_root = tmp_path / "quantum-sidecar-validation"

    report = validate_fractal_quantum_sidecar(
        output_root=output_root,
        shots=1024,
        seed=7,
    )

    assert report["success"] is True
    assert report["submission_policy"] == {
        "submitted": False,
        "qpu_used": False,
        "credentials_required": False,
        "provider": None,
    }
    assert report["profile"]["grid_shape"] == [4, 4, 1]
    assert report["profile"]["geometry_mode"] == "fuzzy_potential"
    assert report["profile"]["g_int"] == 0.0
    assert report["profile"]["dealias_fraction"] is None

    exact = report["metrics"]["exact_statevector"]
    assert exact["state_l2_error"] <= 1e-10
    assert exact["density_mae"] <= 1e-10
    assert exact["norm_error"] <= 1e-10
    assert report["metrics"]["sampling"]["acceptance_role"] == "diagnostic_only"
    assert report["metrics"]["sampling"]["synthetic_noise_model"][
        "physical_calibration"
    ] is False
    assert report["metrics"]["resources"]["qubits"] == 4
    assert report["metrics"]["resources"]["two_qubit_gates"] > 0
    assert report["evidence_verification"]["success"] is True

    expected_files = {
        QUANTUM_SIDECAR_JSON_REPORT,
        QUANTUM_SIDECAR_MARKDOWN_REPORT,
        QUANTUM_SIDECAR_MANIFEST,
        QUANTUM_SIDECAR_BUNDLE,
        "profile.yaml",
        "environment.lock.json",
        "artifacts/fractal-fuzzy-strang.openqasm",
        "artifacts/fractal-fuzzy-strang.qpy",
        "artifacts/fractal-fuzzy-strang.txt",
        "artifacts/measurement-counts.json",
        "artifacts/state-comparison.npz",
    }
    actual_files = {
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    }
    assert expected_files <= actual_files

    persisted = json.loads(
        (output_root / QUANTUM_SIDECAR_JSON_REPORT).read_text(encoding="utf-8")
    )
    assert persisted["success"] is True
    assert "not QPU execution" in persisted["claim_boundary"]
    assert persisted["artifacts"]["openqasm3"].endswith(".openqasm")

    qasm = (output_root / persisted["artifacts"]["openqasm3"]).read_text(
        encoding="utf-8"
    )
    assert qasm.startswith("OPENQASM 3.0;")
    markdown = (output_root / QUANTUM_SIDECAR_MARKDOWN_REPORT).read_text(
        encoding="utf-8"
    )
    assert "Exact Encoding Agreement" in markdown
    assert "synthetic noise run is diagnostic only" in markdown
    assert "No cloud account, QPU, provider credential" in markdown

    with zipfile.ZipFile(output_root / QUANTUM_SIDECAR_BUNDLE) as bundle:
        names = set(bundle.namelist())
    prefix = f"{output_root.name}/"
    assert prefix + QUANTUM_SIDECAR_MANIFEST in names
    assert prefix + "artifacts/fractal-fuzzy-strang.openqasm" in names
    assert prefix + "artifacts/state-comparison.npz" in names


@pytest.mark.skipif(not QUANTUM_STACK_AVAILABLE, reason="optional quantum stack not installed")
def test_quantum_sidecar_manifest_detects_tampering(tmp_path: Path) -> None:
    output_root = tmp_path / "quantum-sidecar-validation"
    report = validate_fractal_quantum_sidecar(
        output_root=output_root,
        shots=128,
        seed=3,
    )
    artifact_path = output_root / report["artifacts"]["circuit_text"]
    artifact_path.write_text("tampered", encoding="utf-8")

    verification = verify_quantum_sidecar_directory(output_root)

    assert verification["success"] is False
    assert any("Hash mismatch" in error for error in verification["errors"])


def test_quantum_sidecar_cli_routes_to_validation(monkeypatch, tmp_path: Path, capsys) -> None:
    from qs_dmss import quantum_sidecar

    seen: dict[str, object] = {}

    def fake_validate_fractal_quantum_sidecar(
        *,
        output_root: str | Path | None,
        shots: int,
        seed: int,
        exact_tolerance: float,
    ) -> dict[str, object]:
        seen.update(
            {
                "output_root": output_root,
                "shots": shots,
                "seed": seed,
                "exact_tolerance": exact_tolerance,
            }
        )
        return {
            "success": True,
            "report_path": str(tmp_path / QUANTUM_SIDECAR_JSON_REPORT),
            "markdown_report_path": str(tmp_path / QUANTUM_SIDECAR_MARKDOWN_REPORT),
            "evidence_bundle_path": str(tmp_path / QUANTUM_SIDECAR_BUNDLE),
        }

    monkeypatch.setattr(
        quantum_sidecar,
        "validate_fractal_quantum_sidecar",
        fake_validate_fractal_quantum_sidecar,
    )

    exit_code = main(
        [
            "quantum",
            "validate-fractal",
            "--output-root",
            str(tmp_path),
            "--shots",
            "512",
            "--seed",
            "11",
            "--exact-tolerance",
            "1e-9",
        ]
    )

    assert exit_code == 0
    assert seen == {
        "output_root": str(tmp_path),
        "shots": 512,
        "seed": 11,
        "exact_tolerance": 1e-9,
    }
    output = capsys.readouterr().out
    assert "quantum-readiness sidecar passed" in output
    assert "no QPU job was submitted" in output


def test_quantum_sidecar_rejects_unbounded_shot_count() -> None:
    with pytest.raises(ValueError, match="between 128 and 100000"):
        validate_fractal_quantum_sidecar(shots=100_001)
