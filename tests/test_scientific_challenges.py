"""Frozen evidence identity, claim-boundary and human-intake contracts."""

import ast
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "research/challenges/registry-v1.json"


@pytest.fixture
def validator():
    spec = importlib.util.spec_from_file_location("validate_registry", ROOT / "research/challenges/validate_registry.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_corresponds_to_original_evidence(validator, registry):
    assert validator.validate_registry(registry) == {
        "registry_integrity": "CONSISTENT", "challenges": 3, "candidate_cases": 89,
        "cross_tool_comparisons": 89, "scientific_validation_status": "NOT_ESTABLISHED",
        "independent_review": "PENDING",
    }
    assert registry["candidate"]["source_commit"] != registry["engineering_review"]["merged_commit"]
    assert registry["candidate"]["source_commit"] != registry["published_baseline"]["source_commit"]


@pytest.mark.parametrize("mutation", [
    "source", "wheel", "release_conflation", "missing_limit", "loosened_limit", "convention", "duplicate_id",
    "case_count", "duplicate_packet", "duplicate_result", "pointer", "outcome", "unpinned_url", "packet_hash",
    "approval", "independence", "disposition", "validated_badge", "unknown_field", "engineering_head",
])
def test_registry_drift_cannot_pass(validator, registry, mutation):
    challenge = registry["challenges"][0]
    if mutation == "source":
        challenge["source_commit"] = registry["engineering_review"]["merged_commit"]
    elif mutation == "wheel":
        registry["candidate"]["wheel_sha256"] = "0" * 64
    elif mutation == "release_conflation":
        registry["candidate"]["published_release"] = True
    elif mutation == "missing_limit":
        challenge["acceptance_limits"].pop("norm_error_max")
    elif mutation == "loosened_limit":
        challenge["acceptance_limits"]["scaled_energy_error_max"] = 1
    elif mutation == "convention":
        challenge["diagnostic_conventions"] = ["fft_cell_measure_v1"]
    elif mutation == "duplicate_id":
        registry["challenges"][1] = copy.deepcopy(challenge)
    elif mutation == "case_count":
        challenge["results"][0]["case_count"] = 73
    elif mutation == "duplicate_packet":
        registry["evidence_packets"][1] = copy.deepcopy(registry["evidence_packets"][0])
    elif mutation == "duplicate_result":
        challenge["results"][1] = copy.deepcopy(challenge["results"][0])
    elif mutation == "pointer":
        challenge["results"][0]["pointer"] = "results.json#/exercises/graph"
    elif mutation == "outcome":
        challenge["results"][0]["outcome"] = "INCONCLUSIVE"
    elif mutation == "unpinned_url":
        packet = registry["evidence_packets"][0]
        packet["url"] = packet["url"].replace(registry["engineering_review"]["merged_commit"], "main")
    elif mutation == "packet_hash":
        registry["evidence_packets"][0]["sha256"] = "0" * 64
    elif mutation == "approval":
        challenge["scientific_assessment"]["status"] = "VALIDATED"
    elif mutation == "independence":
        challenge["scientific_assessment"]["independent_review"] = "APPROVED"
    elif mutation == "disposition":
        challenge["scientific_assessment"]["human_disposition"] = "ACCEPTED"
    elif mutation == "validated_badge":
        challenge["evidence_outcome"] = "VALIDATED"
    elif mutation == "unknown_field":
        registry["validated"] = True
    else:
        registry["engineering_review"]["reviewed_head"] = "0" * 40
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_registry(registry)


@pytest.mark.parametrize("value", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'])
def test_ambiguous_or_nonfinite_json_is_rejected(validator, value):
    with pytest.raises(ValueError):
        validator.read_json(value)


@pytest.mark.parametrize("relative", ["../outside", "C:/private", "//server/share", "docs\\file", "/tmp/file"])
def test_paths_cannot_escape_repository(validator, relative):
    with pytest.raises(ValueError):
        validator.checked_path(ROOT, relative)


def test_tampered_archive_is_rejected_before_parsing(validator, registry, tmp_path):
    packet = registry["evidence_packets"][0]
    destination = tmp_path / packet["path"]
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"not a zip and not the recorded packet")
    with pytest.raises(ValueError, match="hash mismatch"):
        validator.read_packet(tmp_path, packet)


@pytest.mark.parametrize("changed_status", ["FAIL", "INCONCLUSIVE"])
def test_changed_evidence_cannot_keep_success_label(validator, registry, monkeypatch, changed_status):
    original = validator.read_packet

    def changed(root, packet):
        documents = original(root, packet)
        if packet["id"] == "pilot-v1":
            documents["results.json"]["exercises"]["fft"][0]["status"] = changed_status
        return documents

    monkeypatch.setattr(validator, "read_packet", changed)
    with pytest.raises(ValueError, match="outcome differs"):
        validator.validate_registry(registry)


def test_outcome_aggregation_never_promotes_missing_or_failed_data(validator):
    assert validator.aggregate(["FAIL", "INCONCLUSIVE"]) == "FAIL"
    assert validator.aggregate(["NOT_FALSIFIED_WITHIN_SCOPE", "INCONCLUSIVE"]) == "INCONCLUSIVE"
    for values in ([], ["VALIDATED"], [None]):
        with pytest.raises(ValueError):
            validator.aggregate(values)


def test_validator_is_data_only_and_schema_references_are_local():
    tree = ast.parse((ROOT / "research/challenges/validate_registry.py").read_text(encoding="utf-8"))
    allowed = {"__future__", "argparse", "hashlib", "json", "math", "zipfile", "pathlib", "jsonschema"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name in allowed for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module in allowed
    schema = (ROOT / "schemas/scientific-challenge-registry-v1.schema.json").read_text(encoding="utf-8")
    assert all(value.startswith("#/") for value in re.findall(r'"\$ref":\s*"([^"]+)"', schema))


def test_scientific_intake_matches_registry_and_requires_accountability(registry):
    form = yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE/scientific_review.yml").read_text(encoding="utf-8"))
    fields = {field["id"]: field for field in form["body"] if "id" in field}
    assert len(fields) == len([field for field in form["body"] if "id" in field])
    required = {"challenge-id", "focus", "candidate-identity", "reproduction-commands", "environment",
                "numerical-outcome", "counterexample", "evidence", "reviewer-independence", "ai-assistance",
                "suggested-change", "human-disposition"}
    assert required <= set(fields)
    assert all(fields[name]["validations"]["required"] is True for name in required)
    options = fields["challenge-id"]["attributes"]["options"]
    assert [option.split(" — ")[0] for option in options[:3]] == [c["id"] for c in registry["challenges"]]
    assert "default" not in fields["challenge-id"]["attributes"]
    assert fields["human-disposition"]["attributes"]["value"] == "PENDING — awaiting named human triage under issue #183."
    assert fields["numerical-outcome"]["attributes"]["options"][0].startswith("NOT_RUN")
    for field in form["body"]:
        assert field["type"] in {"markdown", "textarea", "dropdown", "checkboxes"}
        if "id" in field:
            assert re.fullmatch(r"[a-zA-Z0-9_-]+", field["id"])
        if field["type"] == "dropdown":
            values = field["attributes"]["options"]
            assert all(isinstance(value, str) for value in values)
            assert len(values) == len(set(values))
    texts = json.dumps(form)
    assert "#183" in texts and "Closed #105 is historical" in texts
    assert "private contact" in texts and "NOT_RUN" in texts


def test_current_review_navigation_and_historical_boundary():
    opt_in = (ROOT / ".github/ISSUE_TEMPLATE/reviewer_opt_in.yml").read_text(encoding="utf-8")
    assert "#183" in opt_in and "#105" not in opt_in
    for path in ("README.md", "CONTRIBUTING.md", "docs/reviewer-packet.md", "docs/circulation-funnel.md"):
        assert "scientific-challenges.md" in (ROOT / path).read_text(encoding="utf-8")
    current = (ROOT / "docs/conceptual-reference-map.md").read_text(encoding="utf-8")
    assert "scientific review issue #183" in current
    historical = json.loads((ROOT / "docs/review-evidence/fractal-ssfm-v0.13.2.json").read_text(encoding="utf-8"))
    assert historical["review_gate"].endswith("/105")  # Do not rewrite the archived packet.


def test_cli_reports_integrity_not_scientific_approval(validator, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["validate_registry.py", "--registry", str(REGISTRY_PATH)])
    validator.main()
    report = json.loads(capsys.readouterr().out)
    assert report["registry_integrity"] == "CONSISTENT"
    assert report["independent_review"] == "PENDING"
    assert report["scientific_validation_status"] == "NOT_ESTABLISHED"
