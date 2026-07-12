from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from qs_dmss.cli import main
from qs_dmss.quantum_compilation import (
    COMPILATION_BUNDLE,
    COMPILATION_CSV,
    COMPILATION_JSON_REPORT,
    COMPILATION_MANIFEST,
    COMPILATION_MARKDOWN_REPORT,
    validate_fractal_quantum_compilation,
)


QUANTUM_STACK_AVAILABLE = (
    importlib.util.find_spec("qiskit") is not None
    and importlib.util.find_spec("qiskit_aer") is not None
)


@pytest.mark.skipif(not QUANTUM_STACK_AVAILABLE, reason="optional quantum stack not installed")
def test_compilation_harness_validates_matrix_and_attribution(tmp_path: Path) -> None:
    output_root = tmp_path / "quantum-compilation-validation"

    report = validate_fractal_quantum_compilation(
        output_root=output_root,
        shots=128,
        seed=7,
    )

    assert report["success"] is True
    assert report["execution_policy"] == {
        "local_simulation_only": True,
        "submitted": False,
        "provider": None,
        "credentials_read": False,
        "remote_api_called": False,
        "max_authorized_cost_usd": 0.0,
    }
    assert report["matrix_definition"]["row_count"] == 12
    assert report["matrix_definition"]["optimization_levels"] == [0, 1, 2, 3]
    assert len(report["matrix_definition"]["topologies"]) == 3
    assert all(row["success"] for row in report["matrix"])

    exact_rows = [
        row
        for row in report["matrix"]
        if row["semantics"]["acceptance_class"] == "reference_exact"
    ]
    approximate_rows = [
        row
        for row in report["matrix"]
        if row["semantics"]["acceptance_class"] == "bounded_approximation"
    ]
    assert len(exact_rows) == 6
    assert len(approximate_rows) == 6
    assert all(row["semantics"]["unused_qubit_leakage"] <= 1e-10 for row in exact_rows)
    assert all(row["semantics"]["state_l2_error"] <= 1e-6 for row in approximate_rows)

    pareto = [row for row in report["matrix"] if row["pareto_optimal"]]
    assert {
        (
            row["topology_id"],
            row["optimization_level"],
            row["semantics"]["acceptance_class"],
        )
        for row in pareto
    } == {
        ("generic-all-to-all-5q", 1, "reference_exact"),
        ("generic-all-to-all-5q", 3, "bounded_approximation"),
    }

    recommended = report["recommended_configuration"]
    assert recommended["topology_id"] == "generic-all-to-all-5q"
    assert recommended["optimization_level"] == 3
    assert recommended["acceptance_class"] == "bounded_approximation"
    assert recommended["two_qubit_gates"] < 20
    assert recommended["attribution"]["ssfm_evolution"]["two_qubit_gates"] > 0
    assert recommended["attribution"]["measurement"]["two_qubit_gates"] == 0

    linear_level_one = next(
        row
        for row in report["matrix"]
        if row["topology_id"] == "generic-linear-5q"
        and row["optimization_level"] == 1
    )
    assert linear_level_one["routing_overhead"]["cx_above_all_to_all"] > 0
    assert report["evidence_verification"]["success"] is True

    expected_files = {
        COMPILATION_JSON_REPORT,
        COMPILATION_MARKDOWN_REPORT,
        COMPILATION_CSV,
        COMPILATION_MANIFEST,
        COMPILATION_BUNDLE,
        "circuits/generic-linear-5q-opt0.openqasm",
        "circuits/generic-all-to-all-5q-opt3.qpy",
        "baseline-request/qpu-request.json",
        "baseline-request/reference-validation/quantum-sidecar-validation.json",
    }
    actual_files = {
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    }
    assert expected_files <= actual_files

    persisted = json.loads(
        (output_root / COMPILATION_JSON_REPORT).read_text(encoding="utf-8")
    )
    assert persisted["success"] is True
    assert "not physical hardware validation" in persisted["claim_boundary"]
    markdown = (output_root / COMPILATION_MARKDOWN_REPORT).read_text(
        encoding="utf-8"
    )
    assert "Resource Attribution" in markdown
    assert "bounded_approximation" in markdown

    with zipfile.ZipFile(output_root / COMPILATION_BUNDLE) as bundle:
        names = set(bundle.namelist())
    prefix = f"{output_root.name}/"
    assert prefix + COMPILATION_JSON_REPORT in names
    assert prefix + "circuits/generic-all-to-all-5q-opt3.openqasm" in names


def test_compilation_cli_routes_to_harness(monkeypatch, tmp_path: Path, capsys) -> None:
    from qs_dmss import quantum_compilation

    seen: dict[str, object] = {}

    def fake_validate_fractal_quantum_compilation(**kwargs) -> dict[str, object]:
        seen.update(kwargs)
        return {
            "success": True,
            "report_path": str(tmp_path / COMPILATION_JSON_REPORT),
            "markdown_report_path": str(tmp_path / COMPILATION_MARKDOWN_REPORT),
            "matrix_csv_path": str(tmp_path / COMPILATION_CSV),
            "evidence_bundle_path": str(tmp_path / COMPILATION_BUNDLE),
        }

    monkeypatch.setattr(
        quantum_compilation,
        "validate_fractal_quantum_compilation",
        fake_validate_fractal_quantum_compilation,
    )

    exit_code = main(
        [
            "quantum",
            "validate-compilation",
            "--output-root",
            str(tmp_path),
            "--shots",
            "512",
            "--seed",
            "11",
            "--reference-tolerance",
            "1e-11",
            "--compilation-tolerance",
            "2e-6",
        ]
    )

    assert exit_code == 0
    assert seen == {
        "output_root": str(tmp_path),
        "shots": 512,
        "seed": 11,
        "reference_tolerance": 1e-11,
        "compilation_tolerance": 2e-6,
    }
    output = capsys.readouterr().out
    assert "quantum compilation validation passed" in output
    assert "no QPU job was submitted" in output
    assert "maximum authorized cost is $0.00" in output


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"shots": 127}, "between 128 and 100000"),
        ({"seed": -1}, "non-negative integer"),
        ({"reference_tolerance": 0.0}, "reference_tolerance"),
        ({"compilation_tolerance": 0.0}, "compilation_tolerance"),
    ],
)
def test_compilation_harness_rejects_invalid_limits(kwargs, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_fractal_quantum_compilation(**kwargs)


def test_compilation_harness_refuses_nonempty_output_without_optional_stack(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "quantum-compilation-validation"
    output_root.mkdir()
    (output_root / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="must be empty"):
        validate_fractal_quantum_compilation(output_root=output_root, shots=128)

    assert (output_root / "keep.txt").read_text(encoding="utf-8") == "keep"
