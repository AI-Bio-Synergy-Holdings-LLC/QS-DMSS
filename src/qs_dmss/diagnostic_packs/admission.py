"""Bounded snapshots of two literal JSON files; never extract or import a pack."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from qs_dmss import __version__
from qs_dmss.diagnostic_packs.models import (
    MAX_FILE_BYTES,
    PackCases,
    PackManifest,
    version_tuple,
)


class PackError(ValueError):
    """Authored admission/verification failure, safe for CLI display."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PackError("Duplicate JSON members are not allowed.")
        result[key] = value
    return result


def decode_json(data: bytes) -> Any:
    def reject_constant(_value):
        raise PackError("JSON numbers must be finite.")

    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=reject_constant,
        )
        stack = [(value, 0)]
        while stack:
            item, depth = stack.pop()
            if depth > 16:
                raise PackError("JSON nesting exceeds the pilot limit.")
            if isinstance(item, dict):
                stack.extend(
                    (child, depth + 1) for pair in item.items() for child in pair
                )
            elif isinstance(item, list):
                stack.extend((child, depth + 1) for child in item)
            elif isinstance(item, str):
                item.encode("utf-8")
            elif isinstance(item, float) and not math.isfinite(item):
                raise PackError("JSON numbers must be finite.")
        return value
    except PackError:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise PackError("Pack JSON is malformed or not valid UTF-8 text.") from exc


def analytic_energy(case) -> float:
    return (
        (2 * math.pi / case.box_size) ** 2
        * sum(m * m for m in case.modes)
        / (2 * case.mass)
    )


@dataclass(frozen=True)
class AdmittedPack:
    manifest: PackManifest
    cases: PackCases
    manifest_bytes: bytes
    cases_bytes: bytes

    def summary(self) -> dict[str, Any]:
        return {
            "admitted": True,
            "manifest": self.manifest.model_dump(mode="json"),
            "case_count": len(self.cases.cases),
            "input_sha256": {
                "manifest.json": sha256(self.manifest_bytes),
                "cases.json": sha256(self.cases_bytes),
            },
            "execution_boundary": "core_owned_diagnostic_only",
            "scientific_validation_status": "NOT_ESTABLISHED",
        }


def admit_bytes(
    manifest_bytes: bytes, cases_bytes: bytes, *, core_version=__version__
) -> AdmittedPack:
    if max(len(manifest_bytes), len(cases_bytes)) > MAX_FILE_BYTES:
        raise PackError("Pack file exceeds the core byte ceiling.")
    try:
        manifest = PackManifest.model_validate(decode_json(manifest_bytes))
        cases = PackCases.model_validate(decode_json(cases_bytes))
    except ValidationError as exc:
        # Do not echo untrusted values, paths or executable-looking content.
        raise PackError("Pack does not satisfy the closed pilot schema.") from exc
    versions = manifest.supported_core_versions
    try:
        current = version_tuple(core_version)
    except ValueError as exc:
        raise PackError("Pilot requires stable three-component core metadata.") from exc
    if (
        not version_tuple(versions.min_inclusive)
        <= current
        < version_tuple(versions.max_exclusive)
    ):
        raise PackError("Pack is incompatible with this core version.")
    limits = manifest.resource_limits
    if max(len(manifest_bytes), len(cases_bytes)) > limits.max_file_bytes:
        raise PackError("Pack exceeds its declared byte ceiling.")
    if sha256(cases_bytes) != manifest.content.sha256:
        raise PackError("Pack content hash does not match.")
    cells = [math.prod(case.grid_shape) for case in cases.cases]
    if (
        len(cells) > limits.max_cases
        or max(cells) > limits.max_grid_cells
        or sum(cells) > limits.max_total_grid_cells
    ):
        raise PackError("Pack exceeds its declared numerical resource budget.")
    for case in cases.cases:
        reference = analytic_energy(case)
        reference_tolerance = min(
            1e-12 * (1 + abs(reference)),
            case.absolute_tolerance + case.relative_tolerance * abs(reference),
        )
        if abs(reference - case.expected_energy) > reference_tolerance:
            raise PackError(
                "Declared reference does not match the core-owned analytic formula."
            )
    return AdmittedPack(manifest, cases, manifest_bytes, cases_bytes)


def _bounded_regular_file(path: Path) -> bytes:
    # Check literal children before opening, including Windows reparse points.
    info = path.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or path.is_symlink()
        or getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        raise PackError("Pack children must be literal regular files, not links.")
    with path.open("rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise PackError("Pack child is not a regular file.")
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise PackError("Pack file exceeds the core byte ceiling.")
    return data


def bundled_pack_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "assets"
        / "diagnostic-packs"
        / "fft-plane-wave-v1"
    )


def admit_pack(path: str | Path | None = None) -> AdmittedPack:
    root = Path(path) if path is not None else bundled_pack_path()
    try:
        if root.is_symlink() or not root.is_dir():
            raise PackError(
                "Pack must be a literal directory containing two JSON files."
            )
        info = root.lstat()
        if getattr(info, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
        ):
            raise PackError("Linked pack roots are not admitted.")
        names = set()
        with os.scandir(root) as entries:
            for entry in entries:
                if len(names) == 2:
                    raise PackError(
                        "Pack directory must contain exactly manifest.json and cases.json."
                    )
                names.add(entry.name)
        if names != {"manifest.json", "cases.json"}:
            raise PackError(
                "Pack directory must contain exactly manifest.json and cases.json."
            )
        return admit_bytes(
            _bounded_regular_file(root / "manifest.json"),
            _bounded_regular_file(root / "cases.json"),
        )
    except (OSError, RuntimeError) as exc:
        raise PackError("Pack storage cannot be read safely.") from exc
