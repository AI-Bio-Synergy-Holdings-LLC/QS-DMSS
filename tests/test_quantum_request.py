from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from qs_dmss.cli import main
from qs_dmss.quantum_request import (
    QPU_REQUEST_BUNDLE,
    QPU_REQUEST_JSON,
    QPU_REQUEST_MANIFEST,
    QPU_REQUEST_MARKDOWN,
    prepare_fractal_qpu_request,
)


QUANTUM_STACK_AVAILABLE = (
    importlib.util.find_spec("qiskit") is not None
    and importlib.util.find_spec("qiskit_aer") is not None
)


@pytest.mark.skipif(not QUANTUM_STACK_AVAILABLE, reason="optional quantum stack not installed")
def test_prepare_qpu_request_writes_review_only_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sentinel = "must-not-appear-in-qpu-request"
    monkeypatch.setenv("IBM_QUANTUM_TOKEN", sentinel)
    output_root = tmp_path / "qpu-request"

    report = prepare_fractal_qpu_request(
        output_root=output_root,
        shots=256,
        seed=11,
        optimization_level=1,
    )

    assert report["success"] is True
    assert report["state"] == "draft"
    assert report["submission_policy"] == {
        "submitted": False,
        "never_submit": True,
        "manual_review_required": True,
        "provider": None,
        "remote_api_called": False,
    }
    assert report["credential_policy"]["credentials_read"] is False
    assert report["credential_policy"]["secret_fields_allowed"] is False
    assert report["cost_policy"]["max_authorized_cost_usd"] == 0.0
    assert report["cost_policy"]["estimated_cost_usd"] is None
    assert report["target"]["profile_id"] == "generic-linear-5q"
    assert report["target"]["physical_device"] is False
    assert report["resources"]["logical_measurement_circuit"]["qubits"] == 4
    assert report["resources"]["target_transpiled"]["qubits"] == 5
    assert report["resources"]["target_transpiled"]["two_qubit_gates"] > 0
    assert report["reference_validation"]["success"] is True
    assert report["evidence_verification"]["success"] is True

    expected_files = {
        QPU_REQUEST_JSON,
        QPU_REQUEST_MARKDOWN,
        QPU_REQUEST_MANIFEST,
        QPU_REQUEST_BUNDLE,
        "target-profile.json",
        "environment.lock.json",
        "artifacts/fractal-fuzzy-logical.qpy",
        "artifacts/fractal-fuzzy-target.qpy",
        "artifacts/fractal-fuzzy-target.openqasm",
        "artifacts/fractal-fuzzy-target.txt",
        "reference-validation/quantum-sidecar-validation.json",
        "reference-validation/quantum-sidecar-evidence.zip",
    }
    actual_files = {
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    }
    assert expected_files <= actual_files

    request_text = (output_root / QPU_REQUEST_JSON).read_text(encoding="utf-8")
    assert sentinel not in request_text
    persisted = json.loads(request_text)
    assert persisted["success"] is True
    assert "not a provider connection" in persisted["claim_boundary"]
    qasm = (output_root / "artifacts/fractal-fuzzy-target.openqasm").read_text(
        encoding="utf-8"
    )
    assert qasm.startswith("OPENQASM 3.0;")
    assert "measure" in qasm
    readme = (output_root / QPU_REQUEST_MARKDOWN).read_text(encoding="utf-8")
    assert "review only; never submitted" in readme
    assert "Authorized provider spend: `$0.00`" in readme

    with zipfile.ZipFile(output_root / QPU_REQUEST_BUNDLE) as bundle:
        names = set(bundle.namelist())
    prefix = f"{output_root.name}/"
    assert prefix + QPU_REQUEST_JSON in names
    assert prefix + "artifacts/fractal-fuzzy-target.openqasm" in names
    assert prefix + "reference-validation/quantum-sidecar-validation.json" in names


def test_qpu_request_cli_routes_to_preparation(monkeypatch, tmp_path: Path, capsys) -> None:
    from qs_dmss import quantum_request

    seen: dict[str, object] = {}

    def fake_prepare_fractal_qpu_request(**kwargs) -> dict[str, object]:
        seen.update(kwargs)
        return {
            "success": True,
            "request_path": str(tmp_path / QPU_REQUEST_JSON),
            "review_path": str(tmp_path / QPU_REQUEST_MARKDOWN),
            "evidence_bundle_path": str(tmp_path / QPU_REQUEST_BUNDLE),
        }

    monkeypatch.setattr(
        quantum_request,
        "prepare_fractal_qpu_request",
        fake_prepare_fractal_qpu_request,
    )

    exit_code = main(
        [
            "quantum",
            "prepare-qpu-request",
            "--output-root",
            str(tmp_path),
            "--shots",
            "512",
            "--seed",
            "13",
            "--optimization-level",
            "2",
            "--exact-tolerance",
            "1e-9",
        ]
    )

    assert exit_code == 0
    assert seen == {
        "output_root": str(tmp_path),
        "shots": 512,
        "seed": 13,
        "optimization_level": 2,
        "exact_tolerance": 1e-9,
    }
    output = capsys.readouterr().out
    assert "QPU request preparation passed" in output
    assert "no QPU job was submitted" in output
    assert "maximum authorized cost is $0.00" in output


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"shots": 100_001}, "between 128 and 100000"),
        ({"seed": -1}, "non-negative integer"),
        ({"optimization_level": True}, "one of 0, 1, 2, or 3"),
        ({"optimization_level": 4}, "one of 0, 1, 2, or 3"),
    ],
)
def test_qpu_request_rejects_invalid_limits(kwargs, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        prepare_fractal_qpu_request(**kwargs)


def test_qpu_request_refuses_nonempty_output_directory(tmp_path: Path) -> None:
    output_root = tmp_path / "qpu-request"
    output_root.mkdir()
    (output_root / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="must be empty"):
        prepare_fractal_qpu_request(output_root=output_root, shots=128)

    assert (output_root / "keep.txt").read_text(encoding="utf-8") == "keep"
