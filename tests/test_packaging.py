from __future__ import annotations

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

    assert qs_dmss.__version__ == declared_version
    assert metadata.version("qs-dmss") == declared_version


def test_public_discovery_metadata_is_present() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

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
        "Repository",
        "Issues",
        "Documentation",
        "Contributing",
        "Review",
        "Reviewer Quickstart",
        "Circulation Funnel",
        "PyPI",
        "DOI",
        "Latest Archived Release DOI",
        "Zenodo",
    }:
        assert label in urls
