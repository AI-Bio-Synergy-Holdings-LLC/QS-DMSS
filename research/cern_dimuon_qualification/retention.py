"""Closed 26 MiB ledger; fixed failure/log slots are reserved before controls."""

import hashlib
import os
import stat
from pathlib import Path

from .contract import (
    BUCKETS,
    LOG_BYTES,
    SCIENTIFIC,
    SLOT_BYTES,
    TOTAL_BYTES,
    WORKERS,
    Hold,
    json_bytes,
)


def literal(path):
    path = Path(path)
    if ".." in path.parts or str(path).startswith(("//", "\\\\")):
        raise Hold("Only literal local paths without parent traversal are admitted.")
    if os.name == "nt" and ":" in str(path)[2:]:
        raise Hold("Alternate filesystem streams are not admitted.")
    absolute = Path(os.path.abspath(path))
    for entry in (*reversed(absolute.parents), absolute):
        try:
            info = entry.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise Hold("Linked or reparse-point paths are not admitted.")
    return absolute


def read_regular(path, ceiling):
    path = literal(path)
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_size > ceiling
        or before.st_nlink != 1
    ):
        raise Hold("Identity read exceeds its regular-file/byte policy.")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode):
            raise Hold("Identity source is no longer a regular file.")
        data = stream.read(ceiling + 1)
        after = os.fstat(stream.fileno())
    current = path.lstat()
    identities = [
        (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        for s in (before, opened, after, current)
    ]
    if len(data) > ceiling or len(set(identities)) != 1 or len(data) != before.st_size:
        raise Hold("Identity source changed during its bounded read.")
    return data


def digest(path, ceiling):
    return hashlib.sha256(read_regular(path, ceiling)).hexdigest()


def audit_existing(root):
    """Inspect a retained failed root without reopening it for writes/retry."""
    view = object.__new__(Store)
    view.root = literal(root)
    if not view.root.is_dir():
        raise Hold("Retained root is unavailable for read-only accounting.")
    return view.audit()


class Store:
    def __init__(self, root, *, workers=WORKERS):
        if workers not in (WORKERS, ("windows", "linux", "comparison", "control")):
            raise Hold("Only fixed four-worker receipt layouts are admitted.")
        self.root = literal(root)
        if not self.root.parent.is_dir():
            raise Hold("Qualification output parent must already exist.")
        try:
            self.root.mkdir(exist_ok=False)
        except FileExistsError as exc:
            raise Hold(
                "Qualification output must be new; no overwrite or retry."
            ) from exc
        for bucket in BUCKETS:
            (self.root / bucket).mkdir(parents=True, exist_ok=True)
        # Each receipt has immutable STARTED and separately reserved final slots.
        # 5 * 16 KiB + 4 * 24 KiB + 16 KiB emergency = exactly 192 KiB.
        for worker in ("supervisor", *workers):
            self.write(
                "records/logs",
                worker + "-started.json",
                self._slot({"state": "STARTED", "worker": worker}),
            )
            self.write(
                "records/logs",
                worker + "-final.json",
                self._slot({"state": "NOT_EXECUTED", "worker": worker}),
            )
        for worker in workers:
            self.write("records/logs", worker + ".log", bytes(LOG_BYTES))
        self.write("records/logs", "emergency.bin", bytes(16 * 1024))
        self.audit()

    @staticmethod
    def _slot(value):
        payload = json_bytes(
            {**value, "qualification_outcome": "NOT_EXECUTED", **SCIENTIFIC}
        )
        if len(payload) > SLOT_BYTES:
            raise Hold("Receipt exceeds its reserved slot.")
        return payload.ljust(SLOT_BYTES, b" ")

    def audit(self):
        for attempt in range(2):
            try:
                return self._audit_once()
            except FileNotFoundError as exc:
                if attempt:
                    raise Hold(
                        "Retention entries kept disappearing; complete accounting unavailable."
                    ) from exc

    def _audit_once(self):
        def refuse_enumeration(error):
            raise Hold(
                "Directory enumeration failed; complete byte accounting is unavailable."
            ) from error

        totals = dict.fromkeys(BUCKETS, 0)
        entries = {}
        for directory, directories, files in os.walk(
            self.root, followlinks=False, onerror=refuse_enumeration
        ):
            for name in directories:
                literal(Path(directory) / name)
            for name in files:
                path = literal(Path(directory) / name)
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise Hold("Nonregular or hard-linked retention entry refused.")
                relative = path.relative_to(self.root).as_posix()
                bucket = next(
                    (key for key in BUCKETS if relative.startswith(key + "/")), None
                )
                if bucket is None:
                    raise Hold("Unallocated retained entry refused.")
                totals[bucket] += info.st_size
                entries[relative] = info.st_size
        if (
            any(totals[key] > limit for key, limit in BUCKETS.items())
            or sum(totals.values()) > TOTAL_BYTES
        ):
            raise Hold(
                "Retained bytes exceed the approved allocation; preserve and stop."
            )
        return {
            "bucket_bytes": totals,
            "total_bytes": sum(totals.values()),
            "files": entries,
        }

    def write(self, bucket, relative, data):
        if bucket not in BUCKETS:
            raise Hold("Unknown retention bucket.")
        relative = Path(relative)
        if relative.anchor or relative.drive or ".." in relative.parts:
            raise Hold("Invalid retained relative path.")
        current = self.audit()
        if (
            current["bucket_bytes"][bucket] + len(data) > BUCKETS[bucket]
            or current["total_bytes"] + len(data) > TOTAL_BYTES
        ):
            raise Hold("Write exceeds its reserved allocation.")
        target = literal(self.root / bucket / relative)
        try:
            target.relative_to(self.root / bucket)
        except ValueError as exc:
            raise Hold("Retained path escaped its allocation.") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return target

    def finish(self, worker, value):
        path = literal(self.root / "records/logs" / (worker + "-final.json"))
        if path.stat().st_size != SLOT_BYTES:
            raise Hold("Reserved receipt slot changed.")
        # Never replace STARTED. A torn final write still leaves its start receipt.
        with path.open("r+b") as stream:
            stream.write(self._slot({"worker": worker, **value}))
            stream.flush()
            os.fsync(stream.fileno())

    def inventory(self):
        ledger = self.audit()
        entries = {
            name: {"bytes": size, "sha256": digest(self.root / name, size)}
            for name, size in sorted(ledger["files"].items())
        }
        document = {
            "files": entries,
            "inventory_self_hashed": False,
            "inventory_bytes": 0,
            "total_retained_bytes": ledger["total_bytes"],
            "scope": "Includes all padding, partial, staging and transport files under this root; excludes identified interpreter/dependency caches",
        }
        for _ in range(16):
            data = json_bytes(document)
            if document["inventory_bytes"] == len(data):
                break
            document["inventory_bytes"] = len(data)
            document["total_retained_bytes"] = ledger["total_bytes"] + len(data)
        else:
            raise Hold("Integrity ledger size did not converge.")
        self.write("records/integrity", "inventory.json", data)
        final = self.audit()
        if final["total_bytes"] != document["total_retained_bytes"]:
            raise Hold("Final ledger does not cover every retained byte.")
        return {
            "sha256": hashlib.sha256(data).hexdigest(),
            "total_bytes": final["total_bytes"],
        }
