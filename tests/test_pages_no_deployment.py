"""Inspect Pages policy without dispatching workflows or publishing artifacts."""

from __future__ import annotations

import ast
import copy
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MARKERS = (
    "[skip render]", "[render skip]", "[skip deploy]",
    "[deploy skip]", "[skip cd]", "[cd skip]",
)
EXPECTED_GUARD = (
    "github.event_name == 'workflow_dispatch' || ("
    "github.event_name == 'push' && github.ref == 'refs/heads/main' && "
    "!github.event.deleted && github.event.head_commit.message && "
    + " && ".join(
        f"!contains(github.event.head_commit.message, '{marker}')"
        for marker in MARKERS
    )
    + ")"
)


def workflow(name="pages.yml"):
    return yaml.load(
        (ROOT / ".github/workflows" / name).read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )


def parse_condition(expression):
    # A closed test interpreter, not a general Actions engine or Python eval.
    translated = expression.replace("&&", " and ").replace("||", " or ")
    translated = re.sub(r"!(?!=)", "not ", translated)
    return ast.parse(f"({translated})", mode="eval")


def truthy(value):
    return value is not None and value is not False and value != 0 and value != ""


class Condition(ast.NodeVisitor):
    """Only the bool/string/contains subset pinned below; no code execution."""

    def __init__(self, github):
        self.github = github

    def generic_visit(self, node):
        raise AssertionError(f"Unsupported condition syntax: {type(node).__name__}")

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Name(self, node):
        assert node.id == "github"
        return self.github

    def visit_Constant(self, node):
        assert isinstance(node.value, (str, bool)) or node.value is None
        return node.value

    def visit_Attribute(self, node):
        parent = self.visit(node.value)
        return parent.get(node.attr) if isinstance(parent, dict) else None

    def visit_BoolOp(self, node):
        operation = {ast.And: all, ast.Or: any}[type(node.op)]
        return operation(truthy(self.visit(value)) for value in node.values)

    def visit_UnaryOp(self, node):
        assert isinstance(node.op, ast.Not)
        return not truthy(self.visit(node.operand))

    def visit_Compare(self, node):
        assert len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq)
        left, right = self.visit(node.left), self.visit(node.comparators[0])
        if isinstance(left, str) and isinstance(right, str):
            return left.lower() == right.lower()
        return left == right

    def visit_Call(self, node):
        assert isinstance(node.func, ast.Name) and node.func.id == "contains"
        assert len(node.args) == 2 and not node.keywords
        search, item = (self.visit(arg) for arg in node.args)
        assert isinstance(search, str) and isinstance(item, str)
        return item.lower() in search.lower()


@pytest.fixture
def guard():
    expression = workflow()["jobs"]["deploy"]["if"].strip()
    assert expression.startswith("${{") and expression.endswith("}}")
    return parse_condition(expression[3:-2].strip())


def allowed(guard, *, message="Update portal", event_name="push", ref="refs/heads/main", event=None):
    payload = {"deleted": False, "head_commit": {"message": message}} if event is None else event
    return truthy(Condition({"event_name": event_name, "ref": ref, "event": payload}).visit(guard))


def test_pages_publisher_has_a_job_level_guard(guard):
    # AST equality ignores formatting but preserves exact string/marker bytes.
    assert ast.dump(guard) == ast.dump(parse_condition(EXPECTED_GUARD))
    pages = workflow()
    assert set(pages["jobs"]) == {"deploy"}
    assert pages["on"]["push"] == {
        "branches": ["main"], "paths": ["site/**", ".github/workflows/pages.yml"],
    }
    assert "workflow_dispatch" in pages["on"] and "pull_request" not in pages["on"]
    assert pages["permissions"] == {"contents": "read"}
    job = pages["jobs"]["deploy"]
    assert job["permissions"] == {"contents": "read", "pages": "write", "id-token": "write"}
    assert job["environment"]["name"] == "github-pages"
    uses = [step.get("uses", "").split("@")[0] for step in job["steps"]]
    for action in ("checkout", "configure-pages", "upload-pages-artifact", "deploy-pages"):
        assert uses.count(f"actions/{action}") == 1


@pytest.mark.parametrize("marker", MARKERS)
@pytest.mark.parametrize("placement", ["prefix", "suffix", "body", "mixed-case"])
def test_no_deployment_markers_block_the_entire_publisher(guard, marker, placement):
    messages = {
        "prefix": f"{marker} docs: update portal",
        "suffix": f"chore(release): prepare build {marker}",
        "body": f"Update portal\r\n\r\nOwner-authorized no-deployment merge. {marker}\r\n研究 🧪",
        "mixed-case": f"Update portal {marker.swapcase()}",
    }
    assert not allowed(guard, message=messages[placement])


def test_pr221_merge_message_cannot_publish_pages(guard):
    assert not allowed(
        guard,
        message="chore(release): prepare v0.15.0 engineering beta (#221) [skip render]\n\nOwner reviewed.",
    )


@pytest.mark.parametrize("message", [
    "Update portal", "Mention skip render without brackets", "[skip renderer]",
    "[skip cd-not]", "[skip  render]", "Update portal [skip ci]",
    "Quotes ' and \" and ${{ github.event_name }} are commit text, not expressions",
])
def test_unmarked_main_push_keeps_existing_publication_behavior(guard, message):
    assert allowed(guard, message=message)


@pytest.mark.parametrize("event_name,ref", [
    ("pull_request", "refs/heads/main"), ("pull_request_target", "refs/heads/main"),
    ("schedule", "refs/heads/main"), ("push", "refs/heads/codex/guard"),
    ("push", "refs/tags/v0.15.0"), ("push", None), (None, "refs/heads/main"),
])
def test_other_automatic_events_or_refs_do_not_publish(guard, event_name, ref):
    assert not allowed(guard, event_name=event_name, ref=ref)


@pytest.mark.parametrize("event", [
    {}, {"head_commit": None}, {"head_commit": {}},
    {"head_commit": {"message": None}}, {"head_commit": {"message": ""}},
    {"deleted": True, "head_commit": {"message": "Delete branch"}},
])
def test_missing_commit_messages_and_deleted_refs_fail_closed(guard, event):
    assert not allowed(guard, event=event)


@pytest.mark.parametrize("ref", ["refs/heads/main", "refs/tags/historical-rollback"])
@pytest.mark.parametrize("message", [None, *MARKERS])
def test_explicit_manual_dispatch_retains_rollback_path(guard, ref, message):
    assert allowed(guard, event_name="workflow_dispatch", ref=ref, message=message)
    assert allowed(guard, event_name="workflow_dispatch", ref=ref, event={})


def test_commit_payload_is_not_modified_by_condition_evaluation(guard):
    event = {"deleted": False, "head_commit": {"message": "Update portal [skip render]"}}
    before = copy.deepcopy(event)
    assert not allowed(guard, event=event)
    assert event == before


@pytest.mark.parametrize("expression", ["always()", "github.event_name != 'push'", "github.ref[0]", "__import__('os')"])
def test_closed_interpreter_does_not_silently_accept_other_syntax(expression):
    with pytest.raises(AssertionError):
        Condition({}).visit(parse_condition(expression))


def test_no_deployment_guard_does_not_suppress_engineering_ci():
    ci = workflow("ci.yml")
    assert ci["on"]["push"] == {"branches": ["main"]}
    assert "pull_request" in ci["on"]
    for job in ci["jobs"].values():
        assert not any(marker in job.get("if", "").lower() for marker in MARKERS)
