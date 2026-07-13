from __future__ import annotations

from pathlib import Path

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
    assert "Before preparing `v0.12.0`" in release_policy


def test_security_policy_names_current_supported_release() -> None:
    security = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert "supported public release line is `v0.11.x`" in security
    assert "supported public release line is `v0.9.x`" not in security
