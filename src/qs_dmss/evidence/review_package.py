from __future__ import annotations

import hashlib
import json
import re
import stat
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

MANIFEST_NAME = "review-evidence-manifest.json"
MANIFEST_SCHEMA = "qs-dmss-fractal-ssfm-review-evidence/v1"
RECEIPT_SCHEMA = "qs-dmss-command-receipt/v1"
ENVIRONMENT_SCHEMA = "qs-dmss-review-environment/v1"
RELEASE_VERSION = "0.13.2"
RELEASE_TAG = "v0.13.2"
SOURCE_COMMIT = "7a063eb91af6c50e483c2d062bf6cee0daf709e4"
WHEEL_FILENAME = "qs_dmss-0.13.2-py3-none-any.whl"
WHEEL_SHA256 = "6f22876fa625681aa72b96d99e14de92cfd5cfae870fc53d9d41673ebf82416f"

MAX_FILES = 256
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ROLES = {
    "technical_review",
    "validation_json",
    "validation_markdown",
    "environment",
    "command_receipt",
    "supplemental",
}
_REQUIRED_ROLE_COUNTS = {
    "technical_review": 1,
    "validation_json": 1,
    "validation_markdown": 1,
    "environment": 1,
}
_ROLE_MEDIA_TYPES = {
    "technical_review": "text/markdown",
    "validation_json": "application/json",
    "validation_markdown": "text/markdown",
    "environment": "application/json",
    "command_receipt": "application/json",
}


@dataclass(frozen=True, order=True)
class ReviewEvidenceFinding:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class ReviewEvidenceResult:
    success: bool
    checked_files: int
    findings: tuple[ReviewEvidenceFinding, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "qs-dmss-review-evidence-verification/v1",
            "success": self.success,
            "checked_files": self.checked_files,
            "scientific_validation_status": "NOT_ESTABLISHED",
            "gate_issues": [105, 183],
            "findings": [finding.as_dict() for finding in self.findings],
        }


def _finding(code: str, path: str, message: str) -> ReviewEvidenceFinding:
    return ReviewEvidenceFinding(code=code, path=path, message=message)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate JSON object member {key!r}.")
        value[key] = item
    return value


def _reject_non_finite_json_number(value: str) -> None:
    raise ValueError(f"Non-finite JSON number {value!r} is not allowed.")


def _safe_package_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    if "\\" in value or "\x00" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    if not path.parts or ":" in path.parts[0] or path.as_posix() != value:
        return None
    return value


def _read_directory(root: Path) -> tuple[dict[str, bytes], list[ReviewEvidenceFinding]]:
    files: dict[str, bytes] = {}
    findings: list[ReviewEvidenceFinding] = []
    total_bytes = 0
    casefolded: set[str] = set()

    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            findings.append(_finding("UNSAFE_PATH", relative, "Symbolic links are not allowed."))
            continue
        if not path.is_file():
            continue
        safe_path = _safe_package_path(relative)
        if safe_path is None:
            findings.append(_finding("UNSAFE_PATH", relative, "Package path is not portable and relative."))
            continue
        folded = safe_path.casefold()
        if folded in casefolded:
            findings.append(_finding("DUPLICATE_PATH", safe_path, "Package paths collide case-insensitively."))
            continue
        casefolded.add(folded)
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            findings.append(_finding("FILE_LIMIT_EXCEEDED", safe_path, "File exceeds the 16 MiB limit."))
            continue
        total_bytes += size
        if total_bytes > MAX_TOTAL_BYTES:
            findings.append(_finding("PACKAGE_LIMIT_EXCEEDED", "$", "Package exceeds the 64 MiB limit."))
            break
        files[safe_path] = path.read_bytes()

    if len(files) > MAX_FILES:
        findings.append(_finding("FILE_COUNT_EXCEEDED", "$", "Package exceeds the 256-file limit."))
    return files, findings


def _read_zip(path: Path) -> tuple[dict[str, bytes], list[ReviewEvidenceFinding]]:
    files: dict[str, bytes] = {}
    findings: list[ReviewEvidenceFinding] = []
    seen: set[str] = set()
    casefolded: set[str] = set()
    total_bytes = 0

    try:
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                raw_path = member.filename
                safe_path = _safe_package_path(raw_path.rstrip("/"))
                if safe_path is None:
                    findings.append(_finding("UNSAFE_PATH", raw_path, "Archive path is not portable and relative."))
                    continue
                if member.is_dir():
                    continue
                folded = safe_path.casefold()
                if safe_path in seen or folded in casefolded:
                    findings.append(_finding("DUPLICATE_PATH", safe_path, "Archive contains a duplicate or case-colliding path."))
                    continue
                seen.add(safe_path)
                casefolded.add(folded)
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    findings.append(_finding("UNSAFE_PATH", safe_path, "Archive symbolic links are not allowed."))
                    continue
                if member.flag_bits & 0x1:
                    findings.append(_finding("ENCRYPTED_FILE", safe_path, "Encrypted archive entries are not allowed."))
                    continue
                if member.file_size > MAX_FILE_BYTES:
                    findings.append(_finding("FILE_LIMIT_EXCEEDED", safe_path, "File exceeds the 16 MiB limit."))
                    continue
                total_bytes += member.file_size
                if total_bytes > MAX_TOTAL_BYTES:
                    findings.append(_finding("PACKAGE_LIMIT_EXCEEDED", "$", "Package exceeds the 64 MiB limit."))
                    break
                try:
                    payload = archive.read(member)
                except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                    findings.append(_finding("ARCHIVE_READ_ERROR", safe_path, str(exc)))
                    continue
                if len(payload) != member.file_size:
                    findings.append(_finding("SIZE_MISMATCH", safe_path, "Archive metadata size does not match extracted bytes."))
                    continue
                files[safe_path] = payload
    except (OSError, zipfile.BadZipFile) as exc:
        findings.append(_finding("INVALID_ARCHIVE", "$", str(exc)))

    if len(files) > MAX_FILES:
        findings.append(_finding("FILE_COUNT_EXCEEDED", "$", "Package exceeds the 256-file limit."))
    return files, findings


def _exact_keys(
    value: dict[str, Any],
    required: set[str],
    path: str,
    findings: list[ReviewEvidenceFinding],
) -> None:
    for key in sorted(required - value.keys()):
        findings.append(_finding("REQUIRED_FIELD_MISSING", f"{path}.{key}", "Required field is missing."))
    for key in sorted(value.keys() - required):
        findings.append(_finding("UNKNOWN_FIELD", f"{path}.{key}", "Field is not allowed by the closed manifest contract."))


def _object(value: object, path: str, findings: list[ReviewEvidenceFinding]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        findings.append(_finding("INVALID_TYPE", path, "Expected an object."))
        return None
    return value


def _nonempty_string(
    value: object,
    path: str,
    findings: list[ReviewEvidenceFinding],
    *,
    minimum: int = 1,
) -> str | None:
    if not isinstance(value, str) or value != value.strip() or len(value) < minimum:
        findings.append(_finding("INVALID_VALUE", path, f"Expected a trimmed string of at least {minimum} characters."))
        return None
    return value


def _expect(value: object, expected: object, path: str, findings: list[ReviewEvidenceFinding]) -> None:
    if value != expected:
        findings.append(_finding("PROVENANCE_MISMATCH", path, f"Expected {expected!r}."))


def _json_object(payload: bytes, path: str, findings: list[ReviewEvidenceFinding]) -> dict[str, Any] | None:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_non_finite_json_number,
        )
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        findings.append(_finding("INVALID_JSON", path, str(exc)))
        return None
    return _object(value, path, findings)


def _validate_subject(manifest: dict[str, Any], findings: list[ReviewEvidenceFinding]) -> None:
    subject = _object(manifest.get("subject"), "$.subject", findings)
    if subject is None:
        return
    _exact_keys(subject, {"component", "release_version", "release_tag", "source_commit", "wheel"}, "$.subject", findings)
    _expect(subject.get("component"), "numpy_fractal_ssfm", "$.subject.component", findings)
    _expect(subject.get("release_version"), RELEASE_VERSION, "$.subject.release_version", findings)
    _expect(subject.get("release_tag"), RELEASE_TAG, "$.subject.release_tag", findings)
    _expect(subject.get("source_commit"), SOURCE_COMMIT, "$.subject.source_commit", findings)
    wheel = _object(subject.get("wheel"), "$.subject.wheel", findings)
    if wheel is not None:
        _exact_keys(wheel, {"filename", "sha256"}, "$.subject.wheel", findings)
        _expect(wheel.get("filename"), WHEEL_FILENAME, "$.subject.wheel.filename", findings)
        _expect(wheel.get("sha256"), WHEEL_SHA256, "$.subject.wheel.sha256", findings)


def _validate_gate(manifest: dict[str, Any], findings: list[ReviewEvidenceFinding]) -> None:
    gate = _object(manifest.get("gate"), "$.gate", findings)
    if gate is None:
        return
    _exact_keys(gate, {"issues", "scientific_validation_status", "claim_boundary"}, "$.gate", findings)
    _expect(gate.get("issues"), [105, 183], "$.gate.issues", findings)
    _expect(gate.get("scientific_validation_status"), "NOT_ESTABLISHED", "$.gate.scientific_validation_status", findings)
    _nonempty_string(gate.get("claim_boundary"), "$.gate.claim_boundary", findings, minimum=40)


def _validate_reviewer(manifest: dict[str, Any], findings: list[ReviewEvidenceFinding]) -> None:
    reviewer = _object(manifest.get("reviewer"), "$.reviewer", findings)
    if reviewer is None:
        return
    keys = {
        "name",
        "affiliation",
        "contact_or_profile",
        "independent_from_maintainer",
        "independence_statement",
        "accountability_statement",
        "ai_assistance_disclosure",
    }
    _exact_keys(reviewer, keys, "$.reviewer", findings)
    for key in ("name", "affiliation", "contact_or_profile"):
        _nonempty_string(reviewer.get(key), f"$.reviewer.{key}", findings, minimum=2)
    for key in ("independence_statement", "accountability_statement", "ai_assistance_disclosure"):
        _nonempty_string(reviewer.get(key), f"$.reviewer.{key}", findings, minimum=20)
    if reviewer.get("independent_from_maintainer") is not True:
        findings.append(_finding("INDEPENDENCE_NOT_DECLARED", "$.reviewer.independent_from_maintainer", "Reviewer must explicitly declare independence."))


def _validate_environment(
    files: dict[str, bytes],
    entries_by_role: dict[str, list[dict[str, Any]]],
    findings: list[ReviewEvidenceFinding],
) -> str | None:
    entries = entries_by_role.get("environment", [])
    if len(entries) != 1:
        return None
    path = entries[0]["path"]
    payload = files.get(path)
    if payload is None:
        return path
    environment = _json_object(payload, path, findings)
    if environment is None:
        return path
    keys = {"schema_version", "release_version", "wheel_sha256", "python_version", "numpy_version", "platform"}
    _exact_keys(environment, keys, f"file:{path}", findings)
    _expect(environment.get("schema_version"), ENVIRONMENT_SCHEMA, f"file:{path}.schema_version", findings)
    _expect(environment.get("release_version"), RELEASE_VERSION, f"file:{path}.release_version", findings)
    _expect(environment.get("wheel_sha256"), WHEEL_SHA256, f"file:{path}.wheel_sha256", findings)
    for key in ("python_version", "numpy_version", "platform"):
        _nonempty_string(environment.get(key), f"file:{path}.{key}", findings)
    return path


def _valid_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() is not None


def _validate_commands(
    manifest: dict[str, Any],
    files: dict[str, bytes],
    entries_by_path: dict[str, dict[str, Any]],
    environment_path: str | None,
    findings: list[ReviewEvidenceFinding],
) -> None:
    commands = manifest.get("commands")
    if not isinstance(commands, list) or not commands:
        findings.append(_finding("INVALID_VALUE", "$.commands", "At least one command receipt is required."))
        return
    if len(commands) > 32:
        findings.append(_finding("COMMAND_COUNT_EXCEEDED", "$.commands", "At most 32 command receipts are allowed."))
    seen_ids: set[str] = set()
    seen_receipts: set[str] = set()
    for index, item in enumerate(commands):
        path = f"$.commands[{index}]"
        command = _object(item, path, findings)
        if command is None:
            continue
        _exact_keys(command, {"id", "command", "receipt_path"}, path, findings)
        command_id = _nonempty_string(command.get("id"), f"{path}.id", findings)
        command_text = _nonempty_string(command.get("command"), f"{path}.command", findings, minimum=3)
        receipt_path = _safe_package_path(command.get("receipt_path"))
        if receipt_path is None:
            findings.append(_finding("UNSAFE_PATH", f"{path}.receipt_path", "Receipt path is not portable and relative."))
            continue
        if command_id in seen_ids:
            findings.append(_finding("DUPLICATE_COMMAND", f"{path}.id", "Command ID is duplicated."))
        if receipt_path in seen_receipts:
            findings.append(_finding("DUPLICATE_COMMAND", f"{path}.receipt_path", "Receipt path is used by multiple commands."))
        if command_id is not None:
            seen_ids.add(command_id)
        seen_receipts.add(receipt_path)
        entry = entries_by_path.get(receipt_path)
        if entry is None or entry.get("role") != "command_receipt":
            findings.append(_finding("RECEIPT_NOT_DECLARED", receipt_path, "Command receipt must be listed with role command_receipt."))
            continue
        payload = files.get(receipt_path)
        if payload is None:
            continue
        receipt = _json_object(payload, receipt_path, findings)
        if receipt is None:
            continue
        keys = {"schema_version", "command_id", "command", "exit_code", "executed_at", "environment_path"}
        _exact_keys(receipt, keys, f"file:{receipt_path}", findings)
        _expect(receipt.get("schema_version"), RECEIPT_SCHEMA, f"file:{receipt_path}.schema_version", findings)
        if command_id is not None:
            _expect(receipt.get("command_id"), command_id, f"file:{receipt_path}.command_id", findings)
        if command_text is not None:
            _expect(receipt.get("command"), command_text, f"file:{receipt_path}.command", findings)
        if receipt.get("exit_code") != 0:
            findings.append(_finding("COMMAND_NOT_SUCCESSFUL", f"file:{receipt_path}.exit_code", "Command receipt must record exit code 0."))
        if not _valid_utc_timestamp(receipt.get("executed_at")):
            findings.append(_finding("INVALID_TIMESTAMP", f"file:{receipt_path}.executed_at", "Expected an ISO-8601 UTC timestamp ending in Z."))
        if environment_path is not None:
            _expect(receipt.get("environment_path"), environment_path, f"file:{receipt_path}.environment_path", findings)

    declared_receipts = {
        path for path, entry in entries_by_path.items() if entry.get("role") == "command_receipt"
    }
    for receipt_path in sorted(declared_receipts - seen_receipts):
        findings.append(_finding("ORPHAN_RECEIPT", receipt_path, "Command receipt is not referenced by $.commands."))


def _validate_manifest(files: dict[str, bytes], findings: list[ReviewEvidenceFinding]) -> int:
    manifest_payload = files.get(MANIFEST_NAME)
    if manifest_payload is None:
        findings.append(_finding("MANIFEST_MISSING", MANIFEST_NAME, "Closed evidence manifest is required at package root."))
        return 0
    manifest = _json_object(manifest_payload, MANIFEST_NAME, findings)
    if manifest is None:
        return 0
    top_keys = {"schema_version", "subject", "gate", "reviewer", "commands", "files"}
    _exact_keys(manifest, top_keys, "$", findings)
    _expect(manifest.get("schema_version"), MANIFEST_SCHEMA, "$.schema_version", findings)
    _validate_subject(manifest, findings)
    _validate_gate(manifest, findings)
    _validate_reviewer(manifest, findings)

    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        findings.append(_finding("INVALID_VALUE", "$.files", "Manifest must list evidence files."))
        return 0
    if len(entries) > MAX_FILES:
        findings.append(_finding("FILE_COUNT_EXCEEDED", "$.files", "Manifest exceeds the 256-file limit."))

    entries_by_path: dict[str, dict[str, Any]] = {}
    casefolded: set[str] = set()
    entries_by_role: dict[str, list[dict[str, Any]]] = {}
    checked_files = 0
    for index, item in enumerate(entries):
        entry_path = f"$.files[{index}]"
        entry = _object(item, entry_path, findings)
        if entry is None:
            continue
        _exact_keys(entry, {"path", "role", "sha256", "size_bytes", "media_type"}, entry_path, findings)
        path = _safe_package_path(entry.get("path"))
        if path is None or path == MANIFEST_NAME:
            findings.append(_finding("UNSAFE_PATH", f"{entry_path}.path", "Listed path must be safe and cannot be the manifest itself."))
            continue
        if path in entries_by_path or path.casefold() in casefolded:
            findings.append(_finding("DUPLICATE_PATH", f"{entry_path}.path", "Manifest path is duplicated or case-colliding."))
            continue
        casefolded.add(path.casefold())
        role = entry.get("role")
        if role not in _ROLES:
            findings.append(_finding("INVALID_ROLE", f"{entry_path}.role", "Role is not allowed by the closed manifest contract."))
        else:
            entries_by_role.setdefault(role, []).append(entry)
        digest = entry.get("sha256")
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            findings.append(_finding("INVALID_HASH", f"{entry_path}.sha256", "Expected a lowercase SHA-256 digest."))
        size = entry.get("size_bytes")
        if not isinstance(size, int) or isinstance(size, bool) or not 0 <= size <= MAX_FILE_BYTES:
            findings.append(_finding("INVALID_SIZE", f"{entry_path}.size_bytes", "Expected an integer size between 0 and 16 MiB."))
        media_type = _nonempty_string(entry.get("media_type"), f"{entry_path}.media_type", findings)
        expected_media_type = _ROLE_MEDIA_TYPES.get(role)
        if expected_media_type is not None and media_type != expected_media_type:
            findings.append(_finding("MEDIA_TYPE_MISMATCH", f"{entry_path}.media_type", f"Role {role!r} requires {expected_media_type!r}."))
        entries_by_path[path] = entry

        payload = files.get(path)
        if payload is None:
            findings.append(_finding("LISTED_FILE_MISSING", path, "Manifest-listed file is missing."))
            continue
        checked_files += 1
        if isinstance(digest, str) and _SHA256.fullmatch(digest) and _sha256(payload) != digest:
            findings.append(_finding("HASH_MISMATCH", path, "File SHA-256 does not match the manifest."))
        if isinstance(size, int) and not isinstance(size, bool) and len(payload) != size:
            findings.append(_finding("SIZE_MISMATCH", path, "File size does not match the manifest."))
        if role in {"technical_review", "validation_markdown"}:
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                findings.append(_finding("INVALID_TEXT", path, str(exc)))
            else:
                if not text.strip():
                    findings.append(_finding("INVALID_TEXT", path, "Markdown evidence cannot be empty."))

    actual_paths = set(files) - {MANIFEST_NAME}
    for path in sorted(actual_paths - entries_by_path.keys()):
        findings.append(_finding("UNLISTED_FILE", path, "Closed package contains a file not listed in the manifest."))

    role_counts = Counter(entry.get("role") for entry in entries_by_path.values())
    for role, expected in _REQUIRED_ROLE_COUNTS.items():
        if role_counts[role] != expected:
            findings.append(_finding("ROLE_COUNT_MISMATCH", "$.files", f"Role {role!r} must appear exactly {expected} time(s)."))
    if role_counts["command_receipt"] < 1:
        findings.append(_finding("ROLE_COUNT_MISMATCH", "$.files", "At least one command_receipt file is required."))

    environment_path = _validate_environment(files, entries_by_role, findings)
    for entry in entries_by_role.get("validation_json", []):
        payload = files.get(entry["path"])
        if payload is not None:
            _json_object(payload, entry["path"], findings)
    _validate_commands(manifest, files, entries_by_path, environment_path, findings)
    return checked_files


def verify_review_evidence_package(path: str | Path) -> ReviewEvidenceResult:
    target = Path(path).resolve()
    findings: list[ReviewEvidenceFinding] = []
    if target.is_dir():
        files, read_findings = _read_directory(target)
    elif target.is_file() and target.suffix.lower() == ".zip":
        files, read_findings = _read_zip(target)
    else:
        files = {}
        read_findings = [_finding("UNSUPPORTED_TARGET", "$", "Expected an evidence-package directory or .zip file.")]
    findings.extend(read_findings)
    checked_files = _validate_manifest(files, findings) if files else 0
    ordered = tuple(sorted(set(findings)))
    return ReviewEvidenceResult(success=not ordered, checked_files=checked_files, findings=ordered)
