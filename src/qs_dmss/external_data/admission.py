"""Exact record-5203 CSV format, bounded rows/cells and explicit source identity."""

from __future__ import annotations

import csv
import math
import re
import zlib
from dataclasses import dataclass

import numpy as np

from qs_dmss.external_data.contracts import (
    HEADER,
    MAX_CELL_BYTES,
    MAX_INPUT_BYTES,
    MAX_LINE_BYTES,
    MAX_ROWS,
    SOURCE,
    EvidenceError,
    validate_hash,
)
from qs_dmss.external_data.storage import sha256


@dataclass(frozen=True)
class AdmittedCSV:
    columns: dict[str, np.ndarray]
    row_count: int
    invalid_rows: dict[str, int]
    source: dict


def admit_csv(
    data: bytes, kind: str, expected_sha256: str | None = None
) -> AdmittedCSV:
    if not isinstance(kind, str) or kind not in {"synthetic", "cms-record-5203"}:
        raise EvidenceError("Input kind must be synthetic or cms-record-5203.")
    validate_hash(expected_sha256, 64, "Expected input hash")
    if len(data) > MAX_INPUT_BYTES:
        raise EvidenceError("CSV exceeds the pilot byte ceiling.")
    digest = sha256(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise EvidenceError("Input does not match the expected SHA-256.")
    checksum = f"{zlib.adler32(data) & 0xFFFFFFFF:08x}"
    provider_match = len(data) == SOURCE["size_bytes"] and checksum == SOURCE["adler32"]
    if kind == "cms-record-5203" and not provider_match:
        raise EvidenceError(
            "CMS input does not match the pinned provider size and Adler-32 metadata."
        )
    reference_match = digest == SOURCE["maintainer_observed_sha256"]
    if kind == "cms-record-5203" and not reference_match:
        raise EvidenceError(
            "CMS input does not match the maintainer-observed provider snapshot SHA-256."
        )
    try:
        text = data.decode("ascii")
    except UnicodeError as exc:
        raise EvidenceError(
            "CSV must contain ASCII data in the exact provider format."
        ) from exc
    if any(ord(char) < 32 and char not in "\r\n" for char in text):
        raise EvidenceError("CSV contains unsupported control characters.")
    lines = text.splitlines()
    if not lines or len(lines) > MAX_ROWS + 1:
        raise EvidenceError("CSV must have a header and at most 25000 data rows.")
    if any(len(line) > MAX_LINE_BYTES for line in lines):
        raise EvidenceError("CSV line exceeds the pilot ceiling.")
    try:
        if tuple(next(csv.reader([lines[0]], strict=True))) != HEADER:
            raise EvidenceError(
                "CSV header does not match record-5203 (case and order are significant)."
            )
        columns = {name: [] for name in HEADER if name not in {"Run", "Event"}}
        invalid = {
            "invalid_numeric": 0,
            "nonfinite_or_out_of_range": 0,
            "invalid_category_or_identity": 0,
        }
        count = 0
        for line in lines[1:]:
            # Parse a physical line in isolation: multiline cells are not part
            # of this numeric provider format and may not bypass row bounds.
            row = next(csv.reader([line], strict=True))
            count += 1
            if len(row) != len(HEADER) or any(
                len(cell) > MAX_CELL_BYTES for cell in row
            ):
                raise EvidenceError(
                    "CSV row width or cell length violates the closed format."
                )
            record = dict(zip(HEADER, row))
            try:
                numeric = {
                    name: float(record[name])
                    for name in columns
                    if name not in {"type1", "type2"}
                }
            except ValueError:
                invalid["invalid_numeric"] += 1
                continue
            if any(
                not math.isfinite(value) or abs(value) > 1e6
                for value in numeric.values()
            ):
                invalid["nonfinite_or_out_of_range"] += 1
                continue
            if any(
                re.fullmatch(r"[0-9]{1,19}", record[name]) is None
                or int(record[name]) > 2**63 - 1
                for name in ("Run", "Event")
            ) or any(
                record[f"type{i}"] not in {"G", "T"}
                or numeric[f"Q{i}"] not in {-1, 1}
                or numeric[f"E{i}"] <= 0
                or numeric[f"pt{i}"] < 0
                for i in (1, 2)
            ):
                invalid["invalid_category_or_identity"] += 1
                continue
            for name in columns:
                columns[name].append(
                    record[name] if name in {"type1", "type2"} else numeric[name]
                )
    except csv.Error as exc:
        raise EvidenceError(
            "CSV quoting is malformed or multiline fields are unsupported."
        ) from exc
    if count == 0:
        raise EvidenceError("CSV must contain at least one data row.")
    if kind == "cms-record-5203" and count != SOURCE["events"]:
        raise EvidenceError(
            "CMS input row count does not match the pinned provider metadata."
        )
    return AdmittedCSV(
        {
            name: np.asarray(
                values, dtype="U1" if name.startswith("type") else np.float64
            )
            for name, values in columns.items()
        },
        count,
        invalid,
        {
            "input_kind": kind,
            "observation_label": "SYNTHETIC_NOT_COLLISION_DATA"
            if kind == "synthetic"
            else "CALLER_DECLARED_CMS_EDUCATIONAL_DATA",
            "format_profile": "cms-record-5203-csv-v1",
            "provider_reference": SOURCE,
            "input_sha256": digest,
            "input_size_bytes": len(data),
            "input_adler32": checksum,
            "expected_sha256": expected_sha256,
            "provider_metadata_match": provider_match,
            "maintainer_snapshot_sha256_match": reference_match,
            "identity_scope": "Local snapshot hashed against a maintainer-observed HTTPS retrieval; not cryptographic source authentication or a CERN signature. Input kind is caller-declared.",
        },
    )
