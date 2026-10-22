"""Isolated v2 ledger only: no owner-card parser, coordinator or data reader."""

import hashlib
import json
import os
import stat
from pathlib import Path
from types import MappingProxyType

from ..contract import WORKERS, Hold
from ..retention import Store, literal, read_regular

RAW_SHA256 = "305933ea48b9fd39d67c1d9bb226188a7990cbcca636a0dc6177f0462db25912"
CANONICAL_SHA256 = "5198ce0039de27d6ac6a856ae6e44369abc467e0ade566b9e4829552b9383652"


def budget():
    raw = read_regular(Path(__file__).parents[1] / "amendments/protocol-v2.json", 4096)
    if hashlib.sha256(raw).hexdigest() != RAW_SHA256:
        raise Hold("Exact v2 protocol required.")
    plan = json.loads(raw)
    canonical = json.dumps(
        plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    if hashlib.sha256(canonical).hexdigest() != CANONICAL_SHA256:
        raise Hold("Exact v2 semantic contract required.")
    return MappingProxyType(plan["retention"]["buckets"])


class StoreV2(Store):
    """Keep frozen receipt/inventory behavior; bind allocation decisions locally."""

    def __init__(self, root, *, workers=WORKERS):
        self.__budget = budget()
        self.__roles = ("supervisor", *workers)
        super().__init__(root, workers=workers)

    @property
    def budget(self):
        return self.__budget

    @property
    def total(self):
        return sum(self.budget.values())

    def _audit_once(self):
        def refuse(error):
            raise Hold("Complete v2 enumeration unavailable.") from error

        totals = dict.fromkeys(self.budget, 0)
        entries = {}
        for directory, directories, files in os.walk(
            self.root, followlinks=False, onerror=refuse
        ):
            for name in directories:
                literal(Path(directory) / name)
            for name in files:
                path = literal(Path(directory) / name)
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise Hold("Nonregular or hard-linked v2 entry refused.")
                relative = path.relative_to(self.root).as_posix()
                bucket = next(
                    (key for key in self.budget if relative.startswith(key + "/")), None
                )
                if bucket is None:
                    raise Hold("Unallocated v2 entry refused.")
                totals[bucket] += info.st_size
                entries[relative] = info.st_size
        if (
            any(totals[key] > cap for key, cap in self.budget.items())
            or sum(totals.values()) > self.total
        ):
            raise Hold("V2 allocation exceeded; retain and stop.")
        return {
            "bucket_bytes": totals,
            "total_bytes": sum(totals.values()),
            "files": entries,
        }

    def write(self, bucket, relative, data):
        relative = Path(relative)
        if (
            bucket not in self.budget
            or relative.anchor
            or relative.drive
            or ".." in relative.parts
        ):
            raise Hold("Invalid v2 retained path.")
        current = self.audit()
        if (
            current["bucket_bytes"][bucket] + len(data) > self.budget[bucket]
            or current["total_bytes"] + len(data) > self.total
        ):
            raise Hold("V2 write exceeds allocation.")
        target = literal(self.root / bucket / relative)
        if not target.is_relative_to(self.root / bucket):
            raise Hold("V2 path escaped its bucket.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            if stream.write(data) != len(data):
                raise Hold("Partial v2 write; retain and stop.")
            stream.flush()
            os.fsync(stream.fileno())
        return target

    def finish(self, worker, value):
        if worker not in self.__roles:
            raise Hold("Unknown v2 receipt role.")
        read_regular(self.root / "records/logs" / (worker + "-final.json"), 8192)
        super().finish(worker, value)

    @classmethod
    def audit_existing(cls, root):
        view = object.__new__(cls)
        view.__budget = budget()
        view.root = literal(root)
        if not view.root.is_dir():
            raise Hold("Retained v2 root unavailable.")
        return view.audit()
