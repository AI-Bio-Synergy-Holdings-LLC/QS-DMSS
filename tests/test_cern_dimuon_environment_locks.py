"""Data-only environment locks do not admit the numerical pilot."""

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ROOT / "research/cern_dimuon_qualification/environments/v1"


def manifest():
    return json.loads((LOCKS / "manifest.json").read_bytes())


def test_environment_lock_preserves_candidate_and_scientific_contract():
    data = manifest()
    protocol = json.loads((LOCKS.parents[1] / "protocol-v1.json").read_bytes())
    assert data["candidate_wheel_sha256"] == protocol["candidate_wheel_sha256"]
    assert data["candidate_commit"] == protocol["candidate_commit"]
    assert data["python"] == "3.12.15" and data["numpy"] == "2.5.4"
    assert data["criteria_changed"] is False
    assert data["qualification_outcome"] == "NOT_EXECUTED"
    for key in (
        "scientific_validation_status",
        "independent_scientific_review",
        "human_disposition",
        "ai_advice",
    ):
        assert data[key] == protocol["preservation"][key]


@pytest.mark.parametrize("target", ["windows", "linux"])
def test_platform_lock_has_one_exact_hashed_wheel_per_package(target):
    data = manifest()["targets"][target]
    raw = (LOCKS / data["lock_file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == data["lock_sha256"]
    lines = [line for line in raw.decode().splitlines() if not line.startswith("#")]
    expected = [
        f"{row['name']}=={row['version']} --hash=sha256:{row['sha256']}"
        for row in data["packages"]
    ]
    assert lines == expected
    assert len(lines) == len({row["name"] for row in data["packages"]})
    assert all(
        re.fullmatch(r"[\w.-]+==[\w.]+ --hash=sha256:[0-9a-f]{64}", line)
        for line in lines
    )
    assert all(row["filename"].endswith(".whl") for row in data["packages"])


def test_shared_package_versions_match_and_colorama_is_windows_only():
    targets = manifest()["targets"]
    versions = {
        target: {row["name"]: row["version"] for row in value["packages"]}
        for target, value in targets.items()
    }
    assert set(versions["windows"]) - set(versions["linux"]) == {"colorama"}
    assert not set(versions["linux"]) - set(versions["windows"])
    assert all(
        versions["windows"][name] == version
        for name, version in versions["linux"].items()
    )
    assert versions["windows"]["numpy"] == versions["linux"]["numpy"] == "2.5.4"
    assert versions["windows"]["pip"] == versions["linux"]["pip"] == "26.2.2"


def test_numpy_artifacts_are_native_cp312_binaries():
    rows = {
        target: next(row for row in value["packages"] if row["name"] == "numpy")
        for target, value in manifest()["targets"].items()
    }
    assert "cp312-cp312-win_amd64" in rows["windows"]["filename"]
    assert "cp312-cp312-manylinux" in rows["linux"]["filename"]
    assert rows["windows"]["sha256"] != rows["linux"]["sha256"]


def test_runtime_artifacts_are_exactly_pinned():
    targets = manifest()["targets"]
    assert "3.12.15" in targets["windows"]["runtime_sys_version"]
    assert "3.12.15" in targets["linux"]["runtime_sys_version"]
    windows = targets["windows"]["runtime_distribution"]
    assert windows["key"] == "cpython-3.12.15-windows-x86_64-none"
    assert re.fullmatch("[0-9a-f]{64}", windows["sha256"])
    assert re.fullmatch(
        "python@sha256:[0-9a-f]{64}", targets["linux"]["runtime_distribution"]["image"]
    )


def test_hash_identified_qualification_sources_preserve_lf_on_checkout():
    attributes = (ROOT / ".gitattributes").read_text()
    assert "research/cern_dimuon_qualification/** text eol=lf" in attributes
    assert "tests/test_cern_dimuon_qualification.py text eol=lf" in attributes
    assert "tests/test_cern_dimuon_environment_locks.py text eol=lf" in attributes
