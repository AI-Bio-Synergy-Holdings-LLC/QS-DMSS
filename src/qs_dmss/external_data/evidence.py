"""Failure-retaining local workflow and bounded extraction-free bundle verification."""

from __future__ import annotations

import io
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from qs_dmss import __version__
from qs_dmss.external_data.admission import admit_csv
from qs_dmss.external_data.analysis import analyze
from qs_dmss.external_data.contracts import (
    MAX_BUNDLE_BYTES,
    MAX_INPUT_BYTES,
    MAX_RECEIPT_BYTES,
    MAX_RECORD_BYTES,
    MAX_RETAINED_BYTES,
    METHOD,
    SCHEMA,
    AnalysisProfile,
    EvidenceError,
    validate_hash,
)
from qs_dmss.external_data.reporting import render_report
from qs_dmss.external_data.storage import (
    decode_json,
    json_bytes,
    literal_path,
    read_snapshot,
    sha256,
    write_new,
)

FILES = {
    "input.csv",
    "analysis.json",
    "profile.json",
    "source.json",
    "report.html",
    "receipt.json",
}
ARCHIVE_FILES = FILES | {"manifest.sha256.json"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _receipt(target: Path, document: dict, *, initial=False) -> bytes:
    data = json_bytes(document)
    if len(data) > MAX_RECEIPT_BYTES:
        raise EvidenceError("Receipt exceeds the reserved byte ceiling.")
    if initial:
        write_new(target / "receipt.json", data)
    else:
        # The only mutable record while a workflow is active. Never modify it
        # after completion; immutable exports require a new directory to rerun.
        temporary = target / "receipt.pending.json"
        write_new(temporary, data)
        temporary.replace(target / "receipt.json")
    return data


def _implementation() -> dict:
    # Installed/editable package locations may have trusted interpreter aliases
    # (e.g. a Windows Documents junction). Resolve our own code, never caller input.
    root = Path(__file__).resolve().parent
    return {
        name: sha256(read_snapshot(root / name, MAX_RECORD_BYTES))
        for name in (
            "contracts.py",
            "storage.py",
            "admission.py",
            "analysis.py",
            "reporting.py",
            "evidence.py",
            "cli.py",
        )
    }


def run_analysis(
    input_path: str | Path,
    output: str | Path,
    *,
    kind: str,
    profile: AnalysisProfile,
    expected_sha256: str | None = None,
    source_commit: str | None = None,
    candidate_wheel_sha256: str | None = None,
) -> dict:
    # Validate bounded caller metadata before reserving any output.
    validate_hash(source_commit, 40, "Declared source commit")
    validate_hash(candidate_wheel_sha256, 64, "Declared wheel hash")
    validate_hash(expected_sha256, 64, "Expected input hash")
    if not isinstance(kind, str) or kind not in {"synthetic", "cms-record-5203"}:
        raise EvidenceError("Input kind must be synthetic or cms-record-5203.")
    try:
        target = literal_path(Path(output))
        if not target.parent.is_dir():
            raise EvidenceError("Output parent must already exist.")
        target.mkdir(exist_ok=False)
    except OSError as exc:
        raise EvidenceError(
            "Output must be a new writable directory; no existing directory is overwritten."
        ) from exc
    receipt = {
        "schema_version": SCHEMA,
        "state": "STARTED",
        "stage": "snapshot",
        "started_utc": _now(),
        "scientific_validation_status": "NOT_ESTABLISHED",
        "human_disposition": "PENDING",
        "requested_profile": profile.document(),
        "input_kind": kind,
        "expected_sha256": expected_sha256,
        "declared_artifact_identity": {
            "source_commit": source_commit,
            "candidate_wheel_sha256": candidate_wheel_sha256,
            "scope": "caller_declared_not_independently_verified",
        },
        "resource_policy": {
            "max_input_bytes": MAX_INPUT_BYTES,
            "max_rows": 25000,
            "max_bins": 100,
            "max_noninput_record_bytes": MAX_RECORD_BYTES,
            "max_receipt_bytes": MAX_RECEIPT_BYTES,
            "max_bundle_bytes": MAX_BUNDLE_BYTES,
            "max_retained_bytes": MAX_RETAINED_BYTES,
            "scope": "Admission and output bounds; not an OS wall-clock or RSS sandbox.",
        },
    }
    try:
        _receipt(target, receipt, initial=True)
        raw = read_snapshot(input_path, MAX_INPUT_BYTES)
        write_new(target / "input.csv", raw)
        receipt["input_sha256"] = sha256(raw)
        receipt["stage"] = "admission"
        admitted = admit_csv(raw, kind, expected_sha256)
        receipt["stage"] = "analysis"
        result = analyze(admitted, profile)
        receipt["stage"] = "export"
        files = {
            "input.csv": raw,
            "analysis.json": json_bytes(result),
            "profile.json": json_bytes(profile.document()),
            "source.json": json_bytes(admitted.source),
            "report.html": render_report(result, profile.document(), admitted.source),
        }
        receipt.update(
            {
                "state": "COMPLETED",
                "stage": "export",
                "completed_utc": _now(),
                "environment": {
                    "python": sys.version.split()[0],
                    "numpy": np.__version__,
                    "qs_dmss": __version__,
                    "platform": platform.system(),
                },
                "implementation_sha256": _implementation(),
                "workflow_outcome": result["workflow_outcome"],
            }
        )
        files["receipt.json"] = json_bytes(receipt)
        if (
            len(files["receipt.json"]) > MAX_RECEIPT_BYTES
            or sum(len(data) for name, data in files.items() if name != "input.csv")
            > MAX_RECORD_BYTES
        ):
            raise EvidenceError("Generated records exceed the reserved byte ceiling.")
        files["manifest.sha256.json"] = json_bytes(
            {
                "schema_version": SCHEMA + "-integrity",
                "files": {
                    name: {"sha256": sha256(data), "size_bytes": len(data)}
                    for name, data in sorted(files.items())
                },
            }
        )
        if (
            sum(len(data) for name, data in files.items() if name != "input.csv")
            > MAX_RECORD_BYTES
        ):
            raise EvidenceError(
                "Records and manifest exceed their combined byte ceiling."
            )
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, data in sorted(files.items()):
                archive.writestr(
                    zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), data
                )
        bundle = buffer.getvalue()
        if (
            len(bundle) > MAX_BUNDLE_BYTES
            or sum(map(len, files.values())) + len(bundle) > MAX_RETAINED_BYTES
        ):
            raise EvidenceError(
                "Evidence export exceeds the pilot delivery or retention ceiling."
            )
        for name, data in files.items():
            if name not in {"receipt.json", "input.csv"}:
                write_new(target / name, data)
        _receipt(target, receipt)
        write_new(target / "dimuon-evidence.zip", bundle)
        return {
            "success": True,
            "output": str(target),
            "bundle": str(target / "dimuon-evidence.zip"),
            "bundle_sha256": sha256(bundle),
            "selected_events": result["selected_events"],
            "workflow_outcome": result["workflow_outcome"],
            "scientific_validation_status": "NOT_ESTABLISHED",
        }
    except BaseException as exc:
        # Preserve bounded input snapshot/partial writes, including refusals and
        # interruption. Do not retain arbitrary exception text or unbounded logs.
        receipt.pop("completed_utc", None)
        reason = (
            str(exc)
            if isinstance(exc, EvidenceError)
            else "Storage, interruption or internal failure; no arbitrary exception text retained."
        )
        receipt.update(
            {
                "state": "FAILED",
                "failed_utc": _now(),
                "failure": "interrupted"
                if isinstance(exc, (KeyboardInterrupt, SystemExit))
                else "workflow_failed",
                "failure_reason": reason,
            }
        )
        try:
            _receipt(target, receipt)
        except (OSError, EvidenceError):
            pass  # STARTED/partial receipt remains if storage itself failed.
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise EvidenceError(
            f"{reason} Bounded input/partial records are retained in the new output directory."
        ) from exc


def verify_bundle(path: str | Path, *, recompute=False) -> dict:
    try:
        raw = read_snapshot(path, MAX_BUNDLE_BYTES)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            if (
                len(entries) != len(ARCHIVE_FILES)
                or {entry.filename for entry in entries} != ARCHIVE_FILES
            ):
                raise EvidenceError(
                    "Evidence archive has unexpected or duplicate entries."
                )
            if any(
                entry.compress_type != zipfile.ZIP_STORED
                or entry.flag_bits & 1
                or entry.file_size != entry.compress_size
                for entry in entries
            ):
                raise EvidenceError(
                    "Only unencrypted, stored evidence members are admitted."
                )
            if any(
                entry.file_size
                > (
                    MAX_INPUT_BYTES
                    if entry.filename == "input.csv"
                    else MAX_RECORD_BYTES
                )
                for entry in entries
            ):
                raise EvidenceError("Evidence member exceeds its byte ceiling.")
            if (
                sum(
                    entry.file_size
                    for entry in entries
                    if entry.filename != "input.csv"
                )
                > MAX_RECORD_BYTES
            ):
                raise EvidenceError(
                    "Evidence records exceed their combined byte ceiling."
                )
            files = {entry.filename: archive.read(entry) for entry in entries}
        manifest = decode_json(files["manifest.sha256.json"])
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {"schema_version", "files"}
            or manifest["schema_version"] != SCHEMA + "-integrity"
            or not isinstance(manifest["files"], dict)
            or set(manifest["files"]) != FILES
        ):
            raise EvidenceError("Evidence integrity manifest is invalid.")
        for name in FILES:
            item = manifest["files"][name]
            if (
                not isinstance(item, dict)
                or set(item) != {"sha256", "size_bytes"}
                or type(item["size_bytes"]) is not int
                or item["size_bytes"] != len(files[name])
                or item["sha256"] != sha256(files[name])
            ):
                raise EvidenceError("Evidence member does not match its manifest.")
        if len(files["receipt.json"]) > MAX_RECEIPT_BYTES:
            raise EvidenceError("Evidence receipt exceeds its ceiling.")
        result = decode_json(files["analysis.json"])
        profile = decode_json(files["profile.json"])
        source = decode_json(files["source.json"])
        receipt = decode_json(files["receipt.json"])
        if any(
            not isinstance(item, dict) for item in (result, profile, source, receipt)
        ):
            raise EvidenceError("Evidence records must be JSON objects.")
        if (
            result.get("schema_version") != SCHEMA
            or result.get("method") != METHOD
            or result.get("scientific_validation_status") != "NOT_ESTABLISHED"
            or result.get("human_disposition") != "PENDING"
            or result.get("independent_scientific_review") != "PENDING"
            or result.get("ai_advice", False) is not None
            or receipt.get("state") != "COMPLETED"
            or receipt.get("schema_version") != SCHEMA
            or receipt.get("scientific_validation_status") != "NOT_ESTABLISHED"
            or receipt.get("human_disposition") != "PENDING"
        ):
            raise EvidenceError("Evidence records violate the pilot status contract.")
        try:
            chosen = AnalysisProfile(
                **{
                    key: profile[key]
                    for key in ("bins", "mass_min", "mass_max", "pt_min")
                }
            )
        except (KeyError, TypeError) as exc:
            raise EvidenceError("Evidence profile is invalid.") from exc
        if (
            profile != chosen.document()
            or receipt.get("requested_profile") != profile
            or receipt.get("input_kind") != source.get("input_kind")
            or receipt.get("expected_sha256") != source.get("expected_sha256")
            or source.get("input_sha256") != sha256(files["input.csv"])
            or receipt.get("input_sha256") != source["input_sha256"]
        ):
            raise EvidenceError("Evidence profile or source identity is inconsistent.")
        if recompute:
            admitted = admit_csv(
                files["input.csv"],
                source.get("input_kind"),
                source.get("expected_sha256"),
            )
            if source != admitted.source or analyze(admitted, chosen) != result:
                raise EvidenceError(
                    "Recomputation differs from the retained analysis or source record."
                )
        return {
            "success": True,
            "checked_files": len(FILES),
            "bundle_sha256": sha256(raw),
            "integrity_scope": "content_hashes_and_closed_profile_not_authorship_or_scientific_validation",
            "recomputation": "MATCHED_CURRENT_IMPLEMENTATION"
            if recompute
            else "NOT_RUN",
            "scientific_validation_status": "NOT_ESTABLISHED",
        }
    except (
        OSError,
        zipfile.BadZipFile,
        RuntimeError,
        EOFError,
        NotImplementedError,
    ) as exc:
        raise EvidenceError("Evidence archive cannot be read safely.") from exc
