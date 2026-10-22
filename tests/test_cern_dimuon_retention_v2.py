"""Data-only amendment checks and sizing, not a runtime loader or pilot adapter."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from research.cern_dimuon_qualification.candidate import IDENTITY_MODULES
from research.cern_dimuon_qualification.contract import Hold, checked_protocol
from research.cern_dimuon_qualification.readiness import source_names, source_plan

ROOT = Path(__file__).resolve().parents[1]
BASE = "research/cern_dimuon_qualification/protocol-v1.json"
AMENDMENT = "research/cern_dimuon_qualification/amendments/protocol-v2.json"
GUIDE = "docs/reviews/cern-dimuon-retention-v2-amendment.md"
TEST = "tests/test_cern_dimuon_retention_v2.py"
BASE_RAW = "e826290c17adf15c4c562920842fcd4cc072027f7dcfdb83d457bec92af0fe75"
BASE_CANONICAL = "afb3e2abca46794f71170599865e51d938c5cff50e7c939d3cad3f52e0b91266"
V2_RAW = "305933ea48b9fd39d67c1d9bb226188a7990cbcca636a0dc6177f0462db25912"
V2_CANONICAL = "5198ce0039de27d6ac6a856ae6e44369abc467e0ade566b9e4829552b9383652"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def protocols():
    return tuple(json.loads((ROOT / name).read_bytes()) for name in (BASE, AMENDMENT))


def check_changes(base, amended):
    unchanged = copy.deepcopy(amended)
    assert unchanged.pop("amendment") == {
        "predecessor_revision": 1,
        "predecessor_raw_sha256": BASE_RAW,
        "predecessor_canonical_sha256": BASE_CANONICAL,
        "transfer_bytes": 32768,
        "from": "input",
        "to": "records/source",
        "runtime_selection": "UNCHANGED_BY_THIS_AMENDMENT",
    }
    assert unchanged["revision"] == 2
    unchanged["revision"] = base["revision"]
    assert unchanged["approval_scope"] == (
        "Owner approved the versioned 32 KiB input-to-source transfer within 26 MiB, "
        "amendment preparation and accounting-only preflight. Adapter implementation "
        "and pilot execution require separate authorization; no deployment or release."
    )
    unchanged["approval_scope"] = base["approval_scope"]
    buckets = unchanged["retention"]["buckets"]
    assert buckets["input"] == 4161536 and buckets["records/source"] == 294912
    buckets["input"] += 32768
    buckets["records/source"] -= 32768
    assert unchanged == base


def amendment_source_plan(module_hashes=None):
    """Sizing helper for this data-only review; it never admits an input or starts workers."""
    hashes = module_hashes or {name: "0" * 64 for name in IDENTITY_MODULES.values()}
    files = {name: (ROOT / name).read_bytes() for name in source_names(ROOT)}
    base_index, base_size = source_plan(files, hashes)
    files.update(
        {
            name: (ROOT / name).read_bytes()
            for name in (AMENDMENT, GUIDE, TEST, ".gitattributes")
        }
    )
    index = json.loads(base_index)
    index["files"] = {
        name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in files.items()
    }
    index["allocation_protocol"] = {
        "revision": 2,
        "raw_sha256": V2_RAW,
        "canonical_sha256": V2_CANONICAL,
    }
    index["scope"] = "Accounting-only v2 amendment; no worker or real-data admission"
    raw = canonical(index) + b"\n"
    size = sum(map(len, files.values())) + len(raw) + 4 * 16384
    return files, raw, size, base_size, len(base_index)


def test_protocol_identities_and_only_authorized_changes():
    base, amended = protocols()
    assert sha((ROOT / BASE).read_bytes()) == BASE_RAW
    assert sha(canonical(base)) == BASE_CANONICAL
    assert sha((ROOT / AMENDMENT).read_bytes()) == V2_RAW
    assert sha(canonical(amended)) == V2_CANONICAL
    check_changes(base, amended)


@pytest.mark.parametrize(
    "field",
    [
        "profile",
        "reference",
        "candidate_commit",
        "input",
        "execution",
        "preservation",
        "future_environments",
    ],
)
def test_unapproved_semantic_changes_fail_the_amendment_check(field):
    base, amended = protocols()
    amended[field] = {"changed": True}
    with pytest.raises(AssertionError):
        check_changes(base, amended)


@pytest.mark.parametrize(
    "bucket",
    [
        "wheel",
        "windows",
        "linux",
        "records/comparison",
        "records/logs",
        "records/integrity",
    ],
)
def test_other_buckets_cannot_change(bucket):
    base, amended = protocols()
    amended["retention"]["buckets"][bucket] += 1
    with pytest.raises(AssertionError):
        check_changes(base, amended)


def test_total_and_production_limits_are_not_expanded():
    base, amended = protocols()
    assert sum(base["retention"]["buckets"].values()) == 27262976
    assert sum(amended["retention"]["buckets"].values()) == 27262976
    assert amended["retention"]["total_bytes"] == base["retention"]["total_bytes"]
    assert (
        amended["retention"]["unchanged_production_limits"]
        == base["retention"]["unchanged_production_limits"]
    )
    assert amended["input"]["bytes"] < amended["retention"]["buckets"]["input"]
    assert 2 * amended["input"]["bytes"] > amended["retention"]["buckets"]["input"]


def test_v1_runtime_selection_and_closure_stay_unchanged():
    assert checked_protocol()["retained_bytes_sha256"] == BASE_RAW
    with pytest.raises(Hold, match="approved semantic contract"):
        checked_protocol(ROOT / AMENDMENT)
    names = source_names(ROOT)
    assert len(names) == 19 and AMENDMENT not in names and TEST not in names


def test_v2_accounting_retains_all_sources_and_full_environment_slots():
    files, raw, size, base_size, base_index_bytes = amendment_source_plan()
    assert base_size == 262144 and len(files) == 23
    assert set(source_names(ROOT)) <= set(files)
    assert {AMENDMENT, GUIDE, TEST, ".gitattributes"} <= set(files)
    amendment_files = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "research/cern_dimuon_qualification/amendments").rglob("*")
        if path.suffix in {".py", ".json"}
    }
    assert amendment_files <= set(files)
    assert size == sum(map(len, files.values())) + len(raw) + 65536
    assert size <= 294912
    assert len(files[TEST]) <= 10240
    assert len(files[GUIDE]) + len(files[".gitattributes"]) <= 4096
    assert len(raw) - base_index_bytes <= 2048
    assert 294912 - base_size - len(files[AMENDMENT]) - 24576 == 4497
    attributes = files[".gitattributes"].decode()
    assert TEST + " text eol=lf" in attributes
    assert ".gitattributes text eol=lf" in attributes
    assert "docs/reviews/cern-dimuon-* text eol=lf" in attributes


def test_all_scientific_statuses_and_candidate_pins_remain_frozen():
    base, amended = protocols()
    assert amended["qualification_outcome"] == "NOT_EXECUTED"
    assert amended["preservation"] == base["preservation"]
    assert amended["candidate_commit"] == base["candidate_commit"]
    assert amended["candidate_wheel_sha256"] == base["candidate_wheel_sha256"]
