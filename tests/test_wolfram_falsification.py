"""Replay retained cross-tool data without requiring a Wolfram license in CI."""

import ast
import copy
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/falsification"
PACKET = ROOT / "docs/review-evidence/wolfram-falsification-v1.zip"


@pytest.fixture
def comparator():
    spec = importlib.util.spec_from_file_location("compare_wolfram", HERE / "compare_wolfram.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def evidence(comparator):
    candidate, protocol, arrays = comparator.load_candidate(ROOT / "docs/review-evidence/falsification-pilot-v1.zip")
    with zipfile.ZipFile(PACKET) as archive:
        receipt = json.loads(archive.read("reference.json"))
    return receipt, candidate, protocol, arrays


def test_wolfram_packet_integrity_and_replay(comparator, evidence):
    with zipfile.ZipFile(PACKET) as archive:
        manifest = json.loads(archive.read("manifest.sha256.json"))
        assert len(archive.namelist()) == len(set(archive.namelist()))
        assert set(archive.namelist()) == set(manifest) | {"manifest.sha256.json"}
        assert all(comparator.sha(archive.read(name)) == digest for name, digest in manifest.items())
        receipt = json.loads(archive.read("reference.json"))
        stored = json.loads(archive.read("results.json"))
        for field, name in (("protocol_file_sha256", "protocol-v1.json"),
                            ("plan_file_sha256", "wolfram-plan-v1.json"),
                            ("reference_file_sha256", "wolfram_reference.wl")):
            assert receipt[field] == comparator.sha(archive.read(name))
        for name in ("compare_wolfram.py", "wolfram_reference.wl"):
            assert archive.read(name).decode().replace("\r\n", "\n") == (HERE / name).read_text(encoding="utf-8")
        assert "Invalid syntax" in archive.read("prior-attempt-01.log").decode("utf-8-sig")
    actual = comparator.compare(*evidence)
    assert actual["status"] == comparator.SUCCESS
    assert {name: len(rows) for name, rows in actual["exercises"].items()} == {"fft": 72, "graph": 15, "evolution": 2}
    assert actual["human_disposition"] == {"status": "PENDING", "reviewer": None}
    assert actual["scientific_validation_status"] == "NOT_ESTABLISHED"
    assert actual["status"] == stored["status"]
    # Float64 reductions may vary by platform; the contract is tolerance, not bit identity.
    for rows in actual["exercises"].values():
        assert all(row["status"] == comparator.SUCCESS for row in rows)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "malformed", "nonfinite", "tool_failure", "wrong_source"])
def test_incomplete_wolfram_evidence_is_inconclusive(comparator, evidence, mutation):
    receipt, candidate, protocol, arrays = evidence
    if mutation == "missing":
        receipt["exercises"]["fft"].pop()
    elif mutation == "duplicate":
        receipt["exercises"]["graph"][1] = copy.deepcopy(receipt["exercises"]["graph"][0])
    elif mutation == "malformed":
        receipt["exercises"]["evolution"][0]["reference"]["real"] = [0]
    elif mutation == "nonfinite":
        receipt["exercises"]["graph"][0]["spectrum"][0] = float("nan")
    elif mutation == "tool_failure":
        receipt["status"] = "INCONCLUSIVE"
    else:
        receipt["source_commit"] = "unrelated"
    assert comparator.compare(receipt, candidate, protocol, arrays)["status"] == "INCONCLUSIVE"


@pytest.mark.parametrize("exercise", ["fft", "graph", "evolution"])
def test_finite_counterexamples_fail(comparator, evidence, exercise):
    receipt, candidate, protocol, arrays = evidence
    if exercise == "fft":
        receipt["exercises"]["fft"][0]["energy"] *= 2
    elif exercise == "graph":
        receipt["exercises"]["graph"][0]["stiffness"][0][0] *= 2
    else:
        receipt["exercises"]["evolution"][0]["linear"]["real"][0] += 0.1
    result = comparator.compare(receipt, candidate, protocol, arrays)
    assert result["status"] == "FAIL"
    assert result["exercises"][exercise][0]["status"] == "FAIL"


def test_precision_disagreement_and_unresolved_refinement(comparator, evidence):
    receipt, candidate, protocol, arrays = evidence
    receipt["exercises"]["evolution"][0]["internal_precision_refinement_error"] = 1e-7
    result = comparator.compare(receipt, candidate, protocol, arrays)
    assert result["status"] == "INCONCLUSIVE"
    assert not result["exercises"]["evolution"][0]["refinement_resolved"]


def test_incomplete_cluster_is_not_accepted(comparator, evidence):
    receipt, candidate, protocol, arrays = evidence
    receipt["exercises"]["graph"][0]["groups"] = [[0], [1], [2]]
    assert comparator.compare(receipt, candidate, protocol, arrays)["status"] == "INCONCLUSIVE"


def test_overflow_counterexample_is_retained(comparator, evidence):
    receipt, candidate, protocol, arrays = evidence
    receipt["exercises"]["graph"][0]["stiffness"][0][0] = 1e308
    with np.errstate(over="ignore", invalid="ignore"):
        result = comparator.compare(receipt, candidate, protocol, arrays)
    assert result["status"] == "FAIL"
    serialized = json.dumps(comparator.json_record(result), allow_nan=False)
    assert '"nonfinite"' in serialized


def test_comparison_has_no_production_or_reference_execution():
    tree = ast.parse((HERE / "compare_wolfram.py").read_text(encoding="utf-8"))
    allowed = {"argparse", "hashlib", "io", "json", "platform", "sys", "zipfile", "datetime", "pathlib", "numpy"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module in allowed
        elif isinstance(node, ast.Import):
            assert all(alias.name in allowed for alias in node.names)
    wolfram = (HERE / "wolfram_reference.wl").read_text(encoding="utf-8")
    assert wolfram.count("Import[") == 2
    assert 'Import[protocolFile, "RawJSON"]' in wolfram
    assert 'Import[planFile, "RawJSON"]' in wolfram
    assert "TimeConstrained[MemoryConstrained[" in wolfram
    assert "536870912" in wolfram


def test_plan_and_candidate_drift_are_rejected(comparator, tmp_path, monkeypatch):
    path = tmp_path / "modified.zip"
    path.write_bytes(b"not the pinned candidate")
    with pytest.raises(ValueError, match="pinned"):
        comparator.load_candidate(path)
    plan = comparator.load_plan()
    plan["working_precisions"] = [20, 30]
    (tmp_path / "wolfram-plan-v1.json").write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.setattr(comparator, "HERE", tmp_path)
    with pytest.raises(ValueError, match="preregistration"):
        comparator.load_plan()


def test_cli_retains_hashes_and_refuses_overwrite(comparator, tmp_path, monkeypatch):
    # Exact executed bytes are used because Git may normalize checkout line endings.
    source = tmp_path / "source"
    source.mkdir()
    with zipfile.ZipFile(PACKET) as archive:
        for name in ("reference.json", "execution.log", "protocol-v1.json", "wolfram-plan-v1.json",
                     "wolfram_reference.wl", "compare_wolfram.py"):
            (source / name).write_bytes(archive.read(name))
    monkeypatch.setattr(comparator, "HERE", source)
    monkeypatch.setattr(sys, "argv", ["compare_wolfram.py", "--candidate-packet",
                                      str(ROOT / "docs/review-evidence/falsification-pilot-v1.zip"),
                                      "--reference", str(source / "reference.json"), "--execution-log",
                                      str(source / "execution.log"), "--output", str(tmp_path / "new-packet")])
    assert comparator.main() == 0
    with zipfile.ZipFile(tmp_path / "new-packet.zip") as archive:
        manifest = json.loads(archive.read("manifest.sha256.json"))
        assert all(hashlib.sha256(archive.read(name)).hexdigest() == value for name, value in manifest.items())
    with pytest.raises(FileExistsError):
        comparator.main()
    path = source / "reference.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt["reference_file_sha256"] = "wrong"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        comparator.main()
