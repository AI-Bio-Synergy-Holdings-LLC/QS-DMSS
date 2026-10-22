"""Locked native ledger tests only; no CERN reader or pilot entry point."""

import json
import sys
from pathlib import Path

from ..contract import Hold
from ..readiness import WHEEL_NAME, check_sources, environment_receipt
from ..retention import read_regular
from ..runtime import admit_environment, sha


def main():
    target, root, wheels, repository, expected = sys.argv[1:]
    if target not in ("windows", "linux"):
        raise Hold("Fixed native target required.")
    root, wheels, repository = map(Path, (root, wheels, repository))
    source = root / "records/source"
    raw = read_regular(source / "ledger-index.json", 294912)
    if sha(raw) != expected:
        raise Hold("Qualification source index drifted.")
    index = json.loads(raw)

    def check():
        base = check_sources(root, index["base_index_sha256"])
        for name, entry in index["files"].items():
            if sha(read_regular(source / name, entry["bytes"])) != entry["sha256"]:
                raise Hold("Qualification source drifted.")
        return admit_environment(
            target,
            root / "wheel" / WHEEL_NAME,
            wheels,
            repository,
            cache_dir=Path(sys.pycache_prefix),
            candidate_identity=base["candidate_identity"],
        )

    before = check()
    environment_receipt(root, target, "before", before)
    import pytest

    code = pytest.main(
        [
            "-q",
            "-ra",
            "-p",
            "no:cacheprovider",
            "-o",
            "pythonpath=.",
            "--basetemp",
            str(root / target / "fixtures"),
            "--junitxml",
            str(root / target / "tests.xml"),
            "tests/test_cern_v2.py",
        ]
    )
    after = check()
    environment_receipt(root, target, "after", after)
    if before != after:
        raise Hold("Native environment changed during ledger tests.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
