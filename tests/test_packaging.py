from __future__ import annotations

import json
from importlib import metadata
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

import qs_dmss
from qs_dmss.quantum_showcase import (
    QUANTUM_SHOWCASE_FILES,
    load_quantum_compilation_showcase,
    quantum_compilation_showcase_root,
)


def test_version_metadata_is_aligned() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    declared_version = pyproject["project"]["version"]

    assert declared_version == "0.13.0"
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
        "Latest Archived Zenodo Record",
    }:
        assert label in urls

    assert urls["Homepage"] == "https://qs-dmss.studio"
    assert urls["QS-DMSS Studio"] == "https://qs-dmss.studio"
    assert urls["Documentation"] == "https://qs-dmss.studio"
    assert urls["Latest Archived Release DOI"] == "https://doi.org/10.5281/zenodo.21329711"
    assert urls["Latest Archived Zenodo Record"] == "https://zenodo.org/records/21329711"
    assert urls["Release Notes"].endswith("/docs/release-v0.13.0.md")


def test_codemeta_release_metadata_is_aligned() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    declared_version = pyproject["project"]["version"]
    codemeta = json.loads((repo_root / "codemeta.json").read_text(encoding="utf-8"))

    assert codemeta["softwareVersion"] == declared_version
    assert codemeta["version"] == declared_version
    assert codemeta["citation"] == "https://doi.org/10.5281/zenodo.20074924"
    assert codemeta["url"] == "https://qs-dmss.studio"
    assert codemeta["releaseNotes"].endswith(f"/docs/release-v{declared_version}.md")


def test_quantum_validation_showcase_assets_are_packaged() -> None:
    root = quantum_compilation_showcase_root()

    assert {path.name for path in root.iterdir() if path.is_file()} == set(
        QUANTUM_SHOWCASE_FILES.values()
    )
    payload = load_quantum_compilation_showcase()
    assert payload["status"] == "pass"
    assert payload["validation"]["all_rows_pass"] is True
    assert payload["validation"]["archive"]["contains_json_report"] is True
    assert payload["validation"]["archive"]["contains_html_report"] is True
    assert (root / "quantum-compilation-validation.html").is_file()
