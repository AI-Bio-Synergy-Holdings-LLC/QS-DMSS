"""Documentation-only contracts for the frozen graph-review handoff."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BRIEF_PATH = ROOT / "docs/sc-graph-001-reviewer-handoff.md"


@pytest.fixture
def brief():
    return BRIEF_PATH.read_text(encoding="utf-8")


@pytest.fixture
def registry():
    return json.loads(
        (ROOT / "research/challenges/registry-v1.json").read_text(encoding="utf-8")
    )


def section(text, heading):
    return text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


def table_rows(text):
    return [
        [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if line.startswith("|") and not line.startswith("| ---")
    ]


def graph_challenge(registry):
    return next(c for c in registry["challenges"] if c["id"] == "SC-GRAPH-001")


def test_handoff_distinguishes_release_candidate_baseline_and_tooling(brief, registry):
    rows = table_rows(section(brief, "Review target and artifact identity"))
    tracks = {row[0]: row[1:] for row in rows[1:]}
    release = (ROOT / "docs/release-v0.14.0.md").read_text(encoding="utf-8")
    release_source = re.search(r"`([0-9a-f]{40})`", release).group(1)
    release_wheel = re.search(
        r"\| `qs_dmss-0\.14\.0-py3-none-any\.whl` \| \d+ \| `([0-9a-f]{64})`",
        release,
    ).group(1)

    assert tracks["Published v0.14.0"][:2] == [release_source, release_wheel]
    assert tracks["Frozen challenge candidate; reports 0.13.2"][:2] == [
        registry["candidate"]["source_commit"],
        registry["candidate"]["wheel_sha256"],
    ]
    assert tracks["Historical published v0.13.2"][:2] == [
        registry["published_baseline"]["source_commit"],
        registry["published_baseline"]["wheel_sha256"],
    ]
    assert tracks["Reviewed pilot tooling and packets"][0] == (
        registry["engineering_review"]["merged_commit"]
    )
    assert len({release_source, registry["candidate"]["source_commit"],
                registry["published_baseline"]["source_commit"]}) == 3
    assert "**new wheel and receipt**" in brief
    assert "Installing `qs-dmss==0.14.0` does not reproduce the frozen candidate." in brief


def test_handoff_reuses_exact_packet_identities_and_result_pointers(brief, registry):
    evidence = section(brief, "Preserved evidence and unchanged statuses")
    graph = graph_challenge(registry)
    for packet in registry["evidence_packets"]:
        assert f"]({packet['url']})" in evidence
        assert f"`{packet['sha256']}`" in evidence
    for result in graph["results"]:
        assert f"`{result['pointer']}`" in evidence
    assert "same 15 graph cases" in evidence
    assert "not a new invocation" in evidence
    assert "same AI-assisted maintainer workflow" in evidence


def test_handoff_bounds_match_unchanged_protocol_and_registry(brief, registry):
    protocol = json.loads(
        (ROOT / "research/falsification/protocol-v1.json").read_text(encoding="utf-8")
    )
    review = section(brief, "Bounded review questions")
    assert f"`{protocol['protocol_id']}`" in review
    assert f"`{registry['candidate']['protocol_canonical_sha256']}`" in review
    for convention in graph_challenge(registry)["diagnostic_conventions"]:
        assert f"`{convention}`" in review
    rows = table_rows(review.split("### Registered bounds and parameters", 1)[1])
    documented = {key: float(value) for key, value in rows[1:]}
    limits = graph_challenge(registry)["acceptance_limits"]
    assert documented == limits
    assert documented == {key: protocol["graph"][key] for key in limits}
    assert protocol["graph"]["levels"] == [0, 1, 2]
    assert protocol["graph"]["lengths"] == [0.75, 1.0, 2.5]
    case_count = sum(
        level != 0 or boundary != "dirichlet"
        for level in protocol["graph"]["levels"]
        for boundary in protocol["graph"]["boundaries"]
        for _ in protocol["graph"]["lengths"]
    )
    assert case_count == graph_challenge(registry)["case_count"] == 15
    assert "grouping parameter, not an error bound" in review
    assert "continuum-convergence claim" in review


def test_handoff_keeps_scientific_and_human_statuses_separate(brief, registry):
    graph = graph_challenge(registry)
    evidence = section(brief, "Preserved evidence and unchanged statuses")
    assert f"`{graph['evidence_outcome']}`" in evidence
    assert f"`{registry['engineering_review']['status']}`" in evidence
    for status in graph["scientific_assessment"].values():
        assert f"`{status}`" in evidence
    assert "pilot #194 only" in evidence
    assert "partial SC-GRAPH-001" in brief
    assert "Hosted AI/graph execution remain disabled." in brief


def test_handoff_does_not_promise_graph_only_or_failure_safe_runner(brief, registry):
    lanes = section(brief, "Choose a review lane before executing anything")
    total = sum(c["case_count"] for c in registry["challenges"])
    assert "**Methodological desk review (`NOT_RUN`).**" in lanes
    assert "**Installed-candidate reproduction.**" in lanes
    assert "**no graph-only switch**" in lanes
    assert f"({total} total)" in lanes
    assert "does not guarantee a complete packet" in lanes
    assert "stdout/stderr capture outside its output directory" in lanes
    assert "not an importer for new reviewer packets" in lanes


def test_handoff_is_discoverable_but_outreach_and_issue_update_remain_drafts(brief):
    for path in (
        "docs/scientific-challenges.md",
        "docs/scientific-challenge-handoff.md",
    ):
        assert f"]({BRIEF_PATH.name})" in (ROOT / path).read_text(encoding="utf-8")
    assert "### Unsent invitation draft" in brief
    assert "## Draft update for #183 (not posted)" in brief
    assert "replace `HANDOFF_URL`" in brief
    assert "Invitations and\npublic updates require separate approval" in brief
    assert "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=scientific_review.yml" in brief
    assert "The form's initial disposition stays `PENDING`." in brief
