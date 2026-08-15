from __future__ import annotations

import hashlib
import json
import warnings
import zipfile
from pathlib import Path

from qs_dmss.cli import main
from qs_dmss.evidence.review_package import (
    ENVIRONMENT_SCHEMA,
    MANIFEST_NAME,
    MANIFEST_SCHEMA,
    RECEIPT_SCHEMA,
    RELEASE_TAG,
    RELEASE_VERSION,
    SOURCE_COMMIT,
    WHEEL_FILENAME,
    WHEEL_SHA256,
    verify_review_evidence_package,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _entry(root: Path, path: str, role: str, media_type: str) -> dict[str, object]:
    payload = (root / path).read_bytes()
    return {
        "path": path,
        "role": role,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "media_type": media_type,
    }


def _refresh_entry(root: Path, manifest: dict[str, object], path: str) -> None:
    entries = manifest["files"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, dict)
        if entry["path"] == path:
            payload = (root / path).read_bytes()
            entry["sha256"] = hashlib.sha256(payload).hexdigest()
            entry["size_bytes"] = len(payload)
            return
    raise AssertionError(f"Missing manifest entry for {path}")


def _package(root: Path) -> dict[str, object]:
    root.mkdir(parents=True)
    (root / "review.md").write_text("# Technical review\n\nIndependent review feedback.\n", encoding="utf-8")
    _write_json(root / "validation.json", {"schema_version": 1, "success": True})
    (root / "validation.md").write_text("# Validation output\n\nMaintainer harness: PASS.\n", encoding="utf-8")
    _write_json(
        root / "environment.json",
        {
            "schema_version": ENVIRONMENT_SCHEMA,
            "release_version": RELEASE_VERSION,
            "wheel_sha256": WHEEL_SHA256,
            "python_version": "3.12.13",
            "numpy_version": "2.5.1",
            "platform": "review-platform",
        },
    )
    command = "qs-dmss validation fractal-ssfm --output-root fractal-ssfm-validation"
    _write_json(
        root / "receipts" / "validation.json",
        {
            "schema_version": RECEIPT_SCHEMA,
            "command_id": "fractal-validation",
            "command": command,
            "exit_code": 0,
            "executed_at": "2026-08-13T12:00:00Z",
            "environment_path": "environment.json",
        },
    )
    files = [
        _entry(root, "review.md", "technical_review", "text/markdown"),
        _entry(root, "validation.json", "validation_json", "application/json"),
        _entry(root, "validation.md", "validation_markdown", "text/markdown"),
        _entry(root, "environment.json", "environment", "application/json"),
        _entry(root, "receipts/validation.json", "command_receipt", "application/json"),
    ]
    manifest: dict[str, object] = {
        "schema_version": MANIFEST_SCHEMA,
        "subject": {
            "component": "numpy_fractal_ssfm",
            "release_version": RELEASE_VERSION,
            "release_tag": RELEASE_TAG,
            "source_commit": SOURCE_COMMIT,
            "wheel": {"filename": WHEEL_FILENAME, "sha256": WHEEL_SHA256},
        },
        "gate": {
            "issues": [105, 183],
            "scientific_validation_status": "NOT_ESTABLISHED",
            "claim_boundary": "Software-validation evidence only; this package does not establish independent scientific or physical-model validation.",
        },
        "reviewer": {
            "name": "Independent Reviewer",
            "affiliation": "Independent research reviewer",
            "contact_or_profile": "https://example.test/reviewer",
            "independent_from_maintainer": True,
            "independence_statement": "I am independent from the QS-DMSS maintainer and its development work.",
            "accountability_statement": "I accept human accountability for the technical observations in review.md.",
            "ai_assistance_disclosure": "AI assistance was not used to form the technical conclusions in this fixture.",
        },
        "commands": [
            {"id": "fractal-validation", "command": command, "receipt_path": "receipts/validation.json"}
        ],
        "files": files,
    }
    _write_json(root / MANIFEST_NAME, manifest)
    return manifest


def _codes(result: object) -> set[str]:
    return {finding.code for finding in result.findings}


def test_review_evidence_directory_and_zip_are_deterministic(tmp_path: Path) -> None:
    package = tmp_path / "package"
    _package(package)

    directory_result = verify_review_evidence_package(package)
    assert directory_result.success
    assert directory_result.checked_files == 5
    assert directory_result.as_dict()["scientific_validation_status"] == "NOT_ESTABLISHED"

    archive = tmp_path / "package.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in reversed(sorted(package.rglob("*"))):
            if path.is_file():
                output.write(path, path.relative_to(package).as_posix())
    archive_result = verify_review_evidence_package(archive)
    assert archive_result == directory_result


def test_review_evidence_rejects_missing_unlisted_and_tampered_files(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    _package(missing)
    (missing / "review.md").unlink()
    assert "LISTED_FILE_MISSING" in _codes(verify_review_evidence_package(missing))

    unlisted = tmp_path / "unlisted"
    _package(unlisted)
    (unlisted / "extra.txt").write_text("not declared", encoding="utf-8")
    assert "UNLISTED_FILE" in _codes(verify_review_evidence_package(unlisted))

    tampered = tmp_path / "tampered"
    _package(tampered)
    (tampered / "review.md").write_text("# Technical review\n\nTampered review feedback.\n", encoding="utf-8")
    assert "HASH_MISMATCH" in _codes(verify_review_evidence_package(tampered))


def test_review_evidence_rejects_duplicate_and_unsafe_paths(tmp_path: Path) -> None:
    package = tmp_path / "package"
    manifest = _package(package)
    manifest["files"].append(dict(manifest["files"][0]))
    _write_json(package / MANIFEST_NAME, manifest)
    assert "DUPLICATE_PATH" in _codes(verify_review_evidence_package(package))

    archive = tmp_path / "unsafe.zip"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(archive, "w") as output:
            for path in sorted(package.rglob("*")):
                if path.is_file():
                    output.write(path, path.relative_to(package).as_posix())
            output.writestr("../escape.txt", "unsafe")
            output.writestr("review.md", "duplicate")
    codes = _codes(verify_review_evidence_package(archive))
    assert {"UNSAFE_PATH", "DUPLICATE_PATH"}.issubset(codes)


def test_review_evidence_rejects_provenance_receipt_and_claim_drift(tmp_path: Path) -> None:
    package = tmp_path / "package"
    manifest = _package(package)
    manifest["subject"]["release_version"] = "0.13.3"
    manifest["gate"]["scientific_validation_status"] = "VALIDATED"
    manifest["files"][0]["media_type"] = "application/octet-stream"
    _write_json(package / MANIFEST_NAME, manifest)
    receipt_path = package / "receipts" / "validation.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["command"] = "different command"
    _write_json(receipt_path, receipt)

    codes = _codes(verify_review_evidence_package(package))
    assert "PROVENANCE_MISMATCH" in codes
    assert "HASH_MISMATCH" in codes
    assert "MEDIA_TYPE_MISMATCH" in codes


def test_review_evidence_rejects_ambiguous_and_nonstandard_json(tmp_path: Path) -> None:
    duplicate_manifest = tmp_path / "duplicate-manifest"
    _package(duplicate_manifest)
    manifest_path = duplicate_manifest / MANIFEST_NAME
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_path.write_text(
        '{"schema_version":"ambiguous",' + manifest_text.lstrip()[1:],
        encoding="utf-8",
    )
    assert "INVALID_JSON" in _codes(verify_review_evidence_package(duplicate_manifest))

    cases = {
        "duplicate-environment": (
            "environment.json",
            '{"platform":"ambiguous","schema_version":"qs-dmss-review-environment/v1",'
            '"release_version":"0.13.2",'
            f'"wheel_sha256":"{WHEEL_SHA256}",'
            '"python_version":"3.12.13","numpy_version":"2.5.1",'
            '"platform":"review-platform"}',
        ),
        "duplicate-receipt": (
            "receipts/validation.json",
            '{"exit_code":1,"schema_version":"qs-dmss-command-receipt/v1",'
            '"command_id":"fractal-validation",'
            '"command":"qs-dmss validation fractal-ssfm --output-root fractal-ssfm-validation",'
            '"exit_code":0,"executed_at":"2026-08-13T12:00:00Z",'
            '"environment_path":"environment.json"}',
        ),
        "non-finite-validation": (
            "validation.json",
            '{"schema_version":1,"success":true,"estimated_order":NaN}',
        ),
        "positive-infinity-validation": (
            "validation.json",
            '{"schema_version":1,"success":true,"estimated_order":Infinity}',
        ),
        "negative-infinity-validation": (
            "validation.json",
            '{"schema_version":1,"success":true,"estimated_order":-Infinity}',
        ),
    }
    for name, (relative_path, payload) in cases.items():
        package = tmp_path / name
        manifest = _package(package)
        (package / relative_path).write_text(payload, encoding="utf-8")
        _refresh_entry(package, manifest, relative_path)
        _write_json(package / MANIFEST_NAME, manifest)
        assert "INVALID_JSON" in _codes(verify_review_evidence_package(package))


def test_review_evidence_cli_returns_machine_readable_result(tmp_path: Path, capsys: object) -> None:
    package = tmp_path / "package"
    _package(package)
    assert main(["validation", "review-evidence", str(package), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is True
    assert payload["gate_issues"] == [105, 183]
