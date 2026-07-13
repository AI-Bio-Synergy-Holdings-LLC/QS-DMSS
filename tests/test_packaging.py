from __future__ import annotations

import json
from importlib import metadata
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

import qs_dmss


def test_version_metadata_is_aligned() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    declared_version = pyproject["project"]["version"]

    assert declared_version == "0.12.0"
    assert qs_dmss.__version__ == declared_version
    assert metadata.version("qs-dmss") == declared_version

    cockpit_favicon = repo_root / "src" / "qs_dmss" / "cockpit" / "static" / "favicon.svg"
    assert cockpit_favicon.exists()


def test_public_discovery_metadata_is_present() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["license"] == "Apache-2.0"
    classifiers = set(project["classifiers"])
    assert "Development Status :: 4 - Beta" in classifiers
    assert "Development Status :: 3 - Alpha" not in classifiers

    keywords = set(project["keywords"])
    for keyword in {
        "dark matter",
        "scientific computing",
        "simulation",
        "reproducibility",
        "schrodinger-poisson",
        "evidence bundles",
        "research software",
    }:
        assert keyword in keywords

    urls = project["urls"]
    for label in {
        "Homepage",
        "QS-DMSS Studio",
        "Repository",
        "Issues",
        "Documentation",
        "Contributing",
        "Review",
        "Reviewer Packet",
        "Reviewer Quickstart",
        "Circulation Funnel",
        "Beta Readiness",
        "Benchmark Validation",
        "Simulation Showcase",
        "JOSS Preflight",
        "PyPI",
        "DOI",
        "Latest Archived Release DOI",
        "Zenodo",
    }:
        assert label in urls

    assert urls["Homepage"] == "https://qs-dmss.studio"
    assert urls["QS-DMSS Studio"] == "https://qs-dmss.studio"
    assert urls["Documentation"] == "https://qs-dmss.studio"
    assert urls["Latest Archived Release DOI"] == "https://doi.org/10.5281/zenodo.21329711"
    assert urls["Zenodo"] == "https://zenodo.org/records/21329711"
    assert urls["Release Notes"].endswith("/docs/release-v0.12.0.md")


def test_codemeta_release_metadata_is_aligned() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    declared_version = pyproject["project"]["version"]
    codemeta = json.loads((repo_root / "codemeta.json").read_text(encoding="utf-8"))

    assert codemeta["softwareVersion"] == declared_version
    assert codemeta["version"] == declared_version
    assert codemeta["citation"] == "https://doi.org/10.5281/zenodo.21329711"
    assert codemeta["url"] == "https://qs-dmss.studio"
    assert codemeta["releaseNotes"].endswith(f"/releases/tag/v{declared_version}")
