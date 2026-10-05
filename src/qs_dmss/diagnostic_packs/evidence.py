"""Immutable explicit-directory exports and bounded, extraction-free integrity checks."""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

from qs_dmss.diagnostic_packs.admission import (
    AdmittedPack,
    PackError,
    decode_json,
    read_regular_snapshot,
    sha256,
)
from qs_dmss.diagnostic_packs.models import MAX_BUNDLE_BYTES

FILES = {"pack/manifest.json", "pack/cases.json", "result.json", "summary.md"}
ARCHIVE_FILES = FILES | {"manifest.sha256.json"}


def json_bytes(value) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


def _markdown(report: dict) -> bytes:
    lines = [
        "# FFT analytic-reference diagnostic result",
        "",
        f"Numerical outcome: {report['numerical_outcome']}",
        "Scientific assessment: NOT_ESTABLISHED; human disposition: PENDING.",
        "",
        "| Case | Analytic energy | Measured energy | Absolute error | Pass |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in report["case_results"]:
        lines.append(
            f"| {row['case']['case_id']} | {row['analytic_energy']:.12g} | "
            f"{row['measured_energy']} | {row['absolute_energy_error']} | {row['passed']} |"
        )
    lines.extend(["", "## Scope and limitations", ""])
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    lines.extend(
        [
            "",
            "Exact cases, tolerances, environment, implementation and input hashes are in result.json.",
        ]
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def export_result(
    pack: AdmittedPack,
    report: dict,
    output: str | Path,
    *,
    source_commit: str | None = None,
    candidate_wheel_sha256: str | None = None,
) -> dict:
    for name, value, pattern in (
        ("source commit", source_commit, r"[0-9a-f]{40}"),
        ("wheel hash", candidate_wheel_sha256, r"[0-9a-f]{64}"),
    ):
        if value is not None and re.fullmatch(pattern, value) is None:
            raise PackError(
                f"Declared {name} must be a full lowercase hexadecimal identity."
            )
    report = {
        **report,
        "declared_artifact_identity": {
            "source_commit": source_commit,
            "candidate_wheel_sha256": candidate_wheel_sha256,
            "verification_scope": "caller_declared_not_independently_verified",
        },
    }
    files = {
        "pack/manifest.json": pack.manifest_bytes,
        "pack/cases.json": pack.cases_bytes,
        "result.json": json_bytes(report),
        "summary.md": _markdown(report),
    }
    files["manifest.sha256.json"] = json_bytes(
        {
            "schema_version": "qs-dmss-diagnostic-pack-integrity/v1",
            "files": {
                name: {"sha256": sha256(data), "size_bytes": len(data)}
                for name, data in sorted(files.items())
            },
        }
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(
                zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), data
            )
    bundle = buffer.getvalue()
    if len(bundle) > MAX_BUNDLE_BYTES:
        raise PackError("Result bundle exceeds the core export ceiling.")
    target = Path(output)
    # No overwrite, including an existing empty directory. Failed writes leave
    # their partial output for diagnosis; do not remove user-owned paths.
    try:
        try:
            target.parent.resolve(strict=True)
        except RuntimeError as exc:
            # Older supported CPython reports resolution loops as RuntimeError.
            # Normalize only this path boundary, not arbitrary write failures.
            raise PackError("Output parent cannot be resolved safely.") from exc
        target.mkdir(exist_ok=False)
        (target / "pack").mkdir()
        for name, data in files.items():
            with (target / name).open("xb") as stream:
                stream.write(data)
        bundle_path = target / "diagnostic-pack-evidence.zip"
        with bundle_path.open("xb") as stream:
            stream.write(bundle)
    except OSError as exc:
        raise PackError(
            "Output must be a new writable directory under an existing parent; partial output is retained."
        ) from exc
    return {
        "output": str(target),
        "bundle": str(bundle_path),
        "bundle_sha256": sha256(bundle),
        "all_cases_pass": report["all_cases_pass"],
        "numerical_outcome": report["numerical_outcome"],
        "scientific_validation_status": "NOT_ESTABLISHED",
    }


def verify_bundle(path: str | Path) -> dict:
    try:
        data = read_regular_snapshot(Path(path), byte_limit=MAX_BUNDLE_BYTES)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if (
                len(entries) != len(ARCHIVE_FILES)
                or {e.filename for e in entries} != ARCHIVE_FILES
            ):
                raise PackError("Evidence bundle has unexpected or duplicate entries.")
            if any(
                e.compress_type != zipfile.ZIP_STORED or e.flag_bits & 1
                for e in entries
            ):
                raise PackError(
                    "Only unencrypted, stored diagnostic evidence is supported."
                )
            if sum(e.file_size for e in entries) > MAX_BUNDLE_BYTES:
                raise PackError("Evidence content exceeds the core byte ceiling.")
            files = {entry.filename: archive.read(entry) for entry in entries}
        manifest = decode_json(files["manifest.sha256.json"])
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {"schema_version", "files"}
            or manifest["schema_version"] != "qs-dmss-diagnostic-pack-integrity/v1"
            or not isinstance(manifest["files"], dict)
            or set(manifest["files"]) != FILES
        ):
            raise PackError("Evidence integrity manifest is invalid.")
        for name in FILES:
            entry = manifest["files"][name]
            if (
                not isinstance(entry, dict)
                or set(entry) != {"sha256", "size_bytes"}
                or type(entry["size_bytes"]) is not int
                or entry["size_bytes"] != len(files[name])
                or entry["sha256"] != sha256(files[name])
            ):
                raise PackError(
                    "Evidence content does not match its integrity manifest."
                )
        return {
            "success": True,
            "checked_files": len(FILES),
            "bundle_sha256": sha256(data),
            "integrity_scope": "content_hashes_only_not_rerun_or_authorship",
            "scientific_validation_status": "NOT_ESTABLISHED",
        }
    except (OSError, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
        raise PackError("Evidence bundle cannot be read safely.") from exc
