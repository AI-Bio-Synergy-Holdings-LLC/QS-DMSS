"""Bounded local snapshots and strict JSON; no network or archive extraction."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from pathlib import Path

from qs_dmss.external_data.contracts import EvidenceError


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def decode_json(data: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise EvidenceError("Duplicate JSON members are not admitted.")
            result[key] = value
        return result

    def reject(_value):
        raise EvidenceError("Non-finite JSON numbers are not admitted.")

    try:
        value = json.loads(
            data.decode("utf-8"), object_pairs_hook=unique, parse_constant=reject
        )
        stack = [(value, 0)]
        while stack:
            item, depth = stack.pop()
            if depth > 16:
                raise EvidenceError("JSON nesting exceeds the pilot limit.")
            if isinstance(item, dict):
                stack.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                stack.extend((child, depth + 1) for child in item)
            elif isinstance(item, str):
                item.encode("utf-8")
            elif isinstance(item, float) and not math.isfinite(item):
                raise EvidenceError("Non-finite JSON numbers are not admitted.")
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EvidenceError("Evidence JSON is malformed.") from exc


def literal_path(path: Path) -> Path:
    """Reject links/reparse points in every existing component, including parents."""
    if str(path).startswith(("//", "\\\\")) or (
        os.name == "nt" and ":" in str(path)[2:]
    ):
        raise EvidenceError("Only local literal filesystem paths are admitted.")
    absolute = Path(os.path.abspath(path))
    for component in (*reversed(absolute.parents), absolute):
        if not component.exists() and not component.is_symlink():
            continue
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise EvidenceError("Linked or reparse-point paths are not admitted.")
    return absolute


def read_snapshot(path: str | Path, limit: int) -> bytes:
    try:
        target = literal_path(Path(path))
        before = target.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise EvidenceError("Input must be a regular local file.")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        with os.fdopen(os.open(target, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (before.st_dev, before.st_ino) != (
                opened.st_dev,
                opened.st_ino,
            ):
                raise EvidenceError("Input changed during admission.")
            if opened.st_size > limit:
                raise EvidenceError("Input exceeds the pilot byte ceiling.")
            data = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
        current = target.lstat()

        def identity(info):
            # Windows path stat and descriptor stat can use different ctime
            # semantics. Compare ctime only within the same kind of call.
            return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)

        if (
            identity(opened) != identity(after)
            or identity(after) != identity(current)
            or opened.st_ctime_ns != after.st_ctime_ns
            or before.st_ctime_ns != current.st_ctime_ns
            or len(data) != after.st_size
        ):
            raise EvidenceError("Input changed during admission.")
        if len(data) > limit:
            raise EvidenceError("Input exceeds the pilot byte ceiling.")
        return data
    except OSError as exc:
        raise EvidenceError("Local input cannot be read safely.") from exc


def write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
