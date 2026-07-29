from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = (
    REPO_ROOT
    / "docs"
    / "decisions"
    / "0001-commercial-sustainability-and-licensing-boundary.md"
)


def test_public_core_license_remains_apache_2() -> None:
    pyproject = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
    notice_text = (REPO_ROOT / "NOTICE").read_text(encoding="utf-8")

    assert pyproject["project"]["license"] == "Apache-2.0"
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
    assert "Licensed under the Apache License, Version 2.0" in notice_text


def test_commercial_boundary_decision_is_accepted_and_linked() -> None:
    decision = DECISION_PATH.read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    ownership = (REPO_ROOT / "docs" / "ownership-and-use.md").read_text(
        encoding="utf-8"
    )
    funding = (REPO_ROOT / "docs" / "funding-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "Status: Accepted" in decision
    assert "The Public Core Remains Apache-2.0" in decision
    assert "Research-Only Relicensing Of The Public Core Is Rejected" in decision
    assert "Hosted-Service Terms Do Not Change Code Rights" in decision
    assert "Commercial components must be separately named" in decision
    assert "This decision authorizes no version bump" in decision
    assert "v0.12.0" in decision
    assert DECISION_PATH.name in readme
    assert DECISION_PATH.name in ownership
    assert DECISION_PATH.name in funding


def test_contribution_and_release_policies_enforce_boundary() -> None:
    contributing = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    release_policy = (REPO_ROOT / "RELEASE.md").read_text(encoding="utf-8")

    assert "Contribution Licensing" in contributing
    assert "distributed under Apache-2.0" in contributing
    assert "Do not submit code, data, model files" in contributing
    assert "Licensing And Commercial Boundary" in release_policy
    assert (
        "Public release wheels and source distributions remain Apache-2.0"
        in release_policy
    )
    assert "governed `v0.12.0` preparation" in release_policy
    assert "no provider credentials" in release_policy
    assert "QPU execution" in release_policy


def test_security_policy_names_current_supported_release() -> None:
    security = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    pyproject = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    version = pyproject["project"]["version"].split(".")
    supported_line = f"v{version[0]}.{version[1]}.x"

    assert f"supported public release line is `{supported_line}`" in security
    assert f"backported to `{supported_line}`" in security


def test_relative_markdown_links_resolve() -> None:
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
    missing: list[str] = []
    repo_root = REPO_ROOT.resolve()

    for markdown_path in REPO_ROOT.rglob("*.md"):
        relative_path = markdown_path.relative_to(REPO_ROOT)
        if any(part.startswith(".") for part in relative_path.parts):
            continue
        text = markdown_path.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            href = match.group(1).strip("<>")
            parsed = urlsplit(href)
            if parsed.scheme or href.startswith(("#", "mailto:")) or not parsed.path:
                continue
            decoded_path = unquote(parsed.path)
            if decoded_path.startswith("/"):
                target = (repo_root / decoded_path.lstrip("/")).resolve()
            else:
                target = (markdown_path.parent / decoded_path).resolve()
            try:
                target.relative_to(repo_root)
            except ValueError:
                line = text.count("\n", 0, match.start()) + 1
                missing.append(
                    f"{relative_path}:{line} -> {href} (escapes repository)"
                )
                continue
            if not target.exists():
                line = text.count("\n", 0, match.start()) + 1
                missing.append(f"{relative_path}:{line} -> {href}")

    assert not missing, "Broken relative Markdown links:\n" + "\n".join(missing)


def test_dependency_review_blocks_moderate_or_higher_findings() -> None:
    workflow_path = (
        REPO_ROOT / ".github" / "workflows" / "dependency-review.yml"
    )
    workflow = yaml.load(
        workflow_path.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    review_steps = workflow["jobs"]["dependency-review"]["steps"]
    review_step = next(
        step
        for step in review_steps
        if str(step.get("uses", "")).startswith(
            "actions/dependency-review-action@"
        )
    )

    assert "pull_request" in workflow["on"]
    assert workflow["permissions"] == {"contents": "read"}
    assert re.fullmatch(
        r"actions/dependency-review-action@v[1-9]\d*",
        review_step["uses"],
    )
    assert review_step["with"]["fail-on-severity"] == "moderate"


def test_v012_release_notes_preserve_quantum_and_license_boundaries() -> None:
    release_notes = (REPO_ROOT / "docs" / "release-v0.12.0.md").read_text(
        encoding="utf-8"
    )

    for required in {
        "no provider integration or provider submission",
        "no provider credentials",
        "no remote quantum API calls",
        "no QPU execution",
        "zero authorized spend",
        "peer-reviewed scientific validation",
        "Apache-2.0",
        "Development Status :: 4 - Beta",
    }:
        assert required in release_notes

    assert "research-only" in release_notes
    assert "noncommercial" in release_notes
