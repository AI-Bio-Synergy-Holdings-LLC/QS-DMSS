from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from qs_dmss.paths import bundled_assets_root, contained_path


QUANTUM_SHOWCASE_SCHEMA_VERSION = 1
QUANTUM_SHOWCASE_ID = "fractal-ssfm-compilation-v0.12.0"
QUANTUM_SHOWCASE_FILES = {
    "report": "quantum-compilation-validation.json",
    "summary": "quantum-compilation-validation.html",
    "markdown": "quantum-compilation-validation.md",
    "matrix": "quantum-compilation-matrix.csv",
    "manifest": "manifest.sha256.json",
    "bundle": "quantum-compilation-evidence.zip",
}


def quantum_compilation_showcase_root() -> Path:
    root = bundled_assets_root() / "quantum" / "compilation-showcase"
    if not root.is_dir():
        raise FileNotFoundError(
            f"Bundled quantum compilation showcase not found at {root}"
        )
    return root


def quantum_compilation_showcase_path(artifact_name: str) -> Path:
    filename = QUANTUM_SHOWCASE_FILES.get(artifact_name)
    if filename is None and artifact_name in QUANTUM_SHOWCASE_FILES.values():
        filename = artifact_name
    if filename is None:
        raise ValueError(f"Unknown quantum compilation showcase artifact: {artifact_name}")
    path = contained_path(quantum_compilation_showcase_root(), filename)
    if not path.is_file():
        raise FileNotFoundError(f"Quantum compilation showcase artifact not found: {filename}")
    return path


def quantum_compilation_showcase_artifact_key(artifact_name: str) -> str:
    if artifact_name in QUANTUM_SHOWCASE_FILES:
        return artifact_name
    for key, filename in QUANTUM_SHOWCASE_FILES.items():
        if artifact_name == filename:
            return key
    raise ValueError(f"Unknown quantum compilation showcase artifact: {artifact_name}")


def quantum_compilation_artifact_path(
    root: str | Path,
    artifact_name: str,
) -> Path:
    filename = QUANTUM_SHOWCASE_FILES.get(artifact_name)
    if filename is None and artifact_name in QUANTUM_SHOWCASE_FILES.values():
        filename = artifact_name
    if filename is None:
        raise ValueError(f"Unknown quantum compilation artifact: {artifact_name}")
    path = contained_path(Path(root).resolve(), filename)
    if not path.is_file():
        raise FileNotFoundError(f"Quantum compilation artifact not found: {filename}")
    return path


def _archive_inventory(bundle_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(bundle_path) as archive:
        corrupt_member = archive.testzip()
        names = archive.namelist()
    return {
        "readable": corrupt_member is None,
        "corrupt_member": corrupt_member,
        "file_count": len(names),
        "contains_manifest": any(name.endswith("/manifest.sha256.json") for name in names),
        "contains_json_report": any(
            name.endswith("/quantum-compilation-validation.json") for name in names
        ),
        "contains_html_report": any(
            name.endswith("/quantum-compilation-validation.html") for name in names
        ),
    }


def load_quantum_compilation_directory(
    root: str | Path,
    *,
    showcase_id: str,
    title: str,
    subtitle: str,
    limitations: list[str],
    download_prefix: str,
) -> dict[str, Any]:
    resolved_root = Path(root).resolve()
    report_path = quantum_compilation_artifact_path(resolved_root, "report")
    bundle_path = quantum_compilation_artifact_path(resolved_root, "bundle")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    matrix = report.get("matrix", [])
    exact_rows = [
        row
        for row in matrix
        if row.get("semantics", {}).get("acceptance_class") == "reference_exact"
    ]
    approximate_rows = [
        row
        for row in matrix
        if row.get("semantics", {}).get("acceptance_class")
        == "bounded_approximation"
    ]
    archive = _archive_inventory(bundle_path)
    success_count = sum(bool(row.get("success")) for row in matrix)

    return {
        "schema_version": QUANTUM_SHOWCASE_SCHEMA_VERSION,
        "showcase_id": showcase_id,
        "title": title,
        "subtitle": subtitle,
        "status": "pass" if report.get("success") and archive["readable"] else "review",
        "generated_at": report.get("generated_at"),
        "claim_boundary": report.get("claim_boundary"),
        "execution_policy": report.get("execution_policy", {}),
        "matrix_definition": report.get("matrix_definition", {}),
        "matrix": matrix,
        "recommended_configuration": report.get("recommended_configuration", {}),
        "validation": {
            "rows_passing": success_count,
            "row_count": len(matrix),
            "reference_exact_rows": len(exact_rows),
            "bounded_approximation_rows": len(approximate_rows),
            "all_rows_pass": bool(matrix) and success_count == len(matrix),
            "archive": archive,
        },
        "limitations": limitations,
        "downloads": {
            key: f"{download_prefix}/{key}"
            for key in QUANTUM_SHOWCASE_FILES
        },
        "bundle": {
            "filename": bundle_path.name,
            "size_bytes": bundle_path.stat().st_size,
        },
    }


def load_quantum_compilation_showcase() -> dict[str, Any]:
    return load_quantum_compilation_directory(
        quantum_compilation_showcase_root(),
        showcase_id=QUANTUM_SHOWCASE_ID,
        title="Fractal SSFM Quantum Compilation Validation",
        subtitle="Precomputed simulator-only compilation matrix and resource attribution",
        limitations=[
            "Precomputed from the v0.12.0 local ideal-simulator harness; the hosted app does not transpile circuits.",
            "Generic topology profiles are not named provider devices or calibration snapshots.",
            "The resource counts are not runtime, price, error-rate, or quantum-advantage predictions.",
            "This does not scientifically validate the underlying Fractal SSFM model.",
        ],
        download_prefix="/api/quantum-validation/files",
    )
