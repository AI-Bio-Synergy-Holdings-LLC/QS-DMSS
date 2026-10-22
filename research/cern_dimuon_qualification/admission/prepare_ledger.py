"""Prepare a new, bounded ledger-only synthetic qualification corpus."""

import json
import sys
from pathlib import Path

from ..contract import Hold
from ..readiness import STAGES
from ..readiness import prepare as prepare_base
from ..retention import read_regular
from ..runtime import sha
from .ledger import StoreV2

EXTRA = (
    ".gitattributes",
    "research/cern_dimuon_qualification/amendments/protocol-v2.json",
    "docs/reviews/cern-dimuon-retention-v2-amendment.md",
    "tests/test_cern_dimuon_retention_v2.py",
    "tests/test_cern_v2.py",
    *(
        "research/cern_dimuon_qualification/admission/" + name
        for name in ("ledger.py", "prepare_ledger.py", "qualify_ledger.py")
    ),
)


def prepare(output, wheel):
    repository = Path(__file__).resolve().parents[3]
    store = StoreV2(output, workers=STAGES)
    base_sha, base_bytes = prepare_base(store, repository, wheel)
    files = {name: read_regular(repository / name, 294912) for name in EXTRA}
    index = {
        "base_index_sha256": base_sha,
        "files": {
            name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in files.items()
        },
    }
    raw = (json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n").encode()
    reserved = base_bytes + sum(map(len, files.values())) + len(raw) + 1760 + 902
    if reserved > 294912 - 4096:
        raise Hold("Ledger source closure cannot preserve 4 KiB spare.")
    for name, data in files.items():
        store.write("records/source", name, data)
    store.write("records/source", "ledger-index.json", raw)
    print(f"index={sha(raw)} reserved={reserved} spare={294912 - reserved}")


if __name__ == "__main__":
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))
