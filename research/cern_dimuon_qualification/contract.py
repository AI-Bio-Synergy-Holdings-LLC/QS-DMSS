"""Owner-approved comparison and retention contract, separate from production."""

import hashlib
import json
from pathlib import Path

MIB = 1024 * 1024
KIB = 1024
COMMIT = "c158c3ba3f81cadf7d11bdfcab3441c8d99be851"
WHEEL_SHA256 = "6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60"
INPUT_SHA256 = "95bf87f7c14758b445d9cb76bc0111affc1ce70831453dde34f687310685e59f"
PROTOCOL_CANONICAL_SHA256 = (
    "afb3e2abca46794f71170599865e51d938c5cff50e7c939d3cad3f52e0b91266"
)
PROFILE = {"bins": 60, "mass_min": 2.0, "mass_max": 5.0, "pt_min": 0.0}
BUCKETS = {
    "input": 4 * MIB,
    "wheel": MIB,
    "windows": 10 * MIB,
    "linux": 10 * MIB,
    "records/source": 256 * KIB,
    "records/comparison": 512 * KIB,
    "records/logs": 192 * KIB,
    "records/integrity": 64 * KIB,
}
TOTAL_BYTES = 26 * MIB
LOG_BYTES = 24 * KIB
SLOT_BYTES = 8 * KIB
WORKERS = ("normal", "timeout", "overflow", "drift")
SCIENTIFIC = {
    "scientific_validation_status": "NOT_ESTABLISHED",
    "independent_scientific_review": "PENDING",
    "human_disposition": "PENDING",
    "ai_advice": None,
}


class Hold(ValueError):
    """Authored qualification refusal, never raw input or exception text."""


def json_bytes(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def checked_protocol(path=None):
    from .retention import read_regular

    raw = read_regular(
        Path(path) if path else Path(__file__).with_name("protocol-v1.json"), 256 * KIB
    )

    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise Hold("Duplicate protocol fields are not admitted.")
            value[key] = item
        return value

    try:
        plan = json.loads(raw, object_pairs_hook=unique)
        canonical = json.dumps(
            plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Hold("Protocol cannot be read safely.") from exc
    if hashlib.sha256(canonical).hexdigest() != PROTOCOL_CANONICAL_SHA256:
        raise Hold("Protocol differs from the approved semantic contract.")
    if (
        plan["profile"] != PROFILE
        or plan["retention"]["buckets"] != BUCKETS
        or plan["retention"]["total_bytes"] != TOTAL_BYTES
    ):
        raise Hold("Helper constants differ from the approved protocol.")
    return {
        "canonical_sha256": PROTOCOL_CANONICAL_SHA256,
        "retained_bytes_sha256": hashlib.sha256(raw).hexdigest(),
    }
