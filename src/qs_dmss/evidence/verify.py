from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from qs_dmss.io.config import config_digest_for_file


@dataclass(frozen=True)
class VerificationResult:
    success: bool
    checked_files: int
    errors: list[str]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _locate_run_root(base_path: Path) -> Path | None:
    if (base_path / "manifest.sha256.json").exists():
        return base_path

    candidates = [path for path in base_path.iterdir() if path.is_dir()]
    for candidate in candidates:
        if (candidate / "manifest.sha256.json").exists():
            return candidate
    return None


def _verify_run_directory(run_dir: Path) -> VerificationResult:
    errors: list[str] = []
    manifest_path = run_dir / "manifest.sha256.json"
    run_record_path = run_dir / "run.json"
    config_path = run_dir / "config.yaml"

    if not manifest_path.exists():
        return VerificationResult(False, 0, [f"Missing manifest: {manifest_path}"])
    if not run_record_path.exists():
        return VerificationResult(False, 0, [f"Missing run record: {run_record_path}"])
    if not config_path.exists():
        return VerificationResult(False, 0, [f"Missing config: {config_path}"])

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_record = json.loads(run_record_path.read_text(encoding="utf-8"))

    checked_files = 0
    for entry in manifest.get("files", []):
        file_path = run_dir / entry["path"]
        if not file_path.exists():
            errors.append(f"Missing file listed in manifest: {entry['path']}")
            continue
        actual_hash = _file_sha256(file_path)
        if actual_hash != entry["sha256"]:
            errors.append(f"Hash mismatch for {entry['path']}")
        actual_size = file_path.stat().st_size
        if actual_size != entry["size_bytes"]:
            errors.append(f"Size mismatch for {entry['path']}")
        checked_files += 1

    expected_digest = config_digest_for_file(config_path)
    actual_digest = run_record.get("config_digest")
    if expected_digest != actual_digest:
        errors.append("Config digest mismatch between config.yaml and run.json")

    return VerificationResult(
        success=not errors,
        checked_files=checked_files,
        errors=errors,
    )


def verify_run_path(path: str | Path) -> VerificationResult:
    resolved_path = Path(path).resolve()
    if resolved_path.is_dir():
        run_root = _locate_run_root(resolved_path)
        if run_root is None:
            return VerificationResult(False, 0, [f"No run root found under {resolved_path}"])
        return _verify_run_directory(run_root)

    if resolved_path.is_file() and resolved_path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as temp_dir:
            extraction_root = Path(temp_dir)
            with zipfile.ZipFile(resolved_path, "r") as archive:
                archive.extractall(extraction_root)

            run_root = _locate_run_root(extraction_root)
            if run_root is None:
                return VerificationResult(
                    False,
                    0,
                    [f"No run root found in archive {resolved_path}"],
                )
            return _verify_run_directory(run_root)

    return VerificationResult(False, 0, [f"Unsupported verification target: {resolved_path}"])
