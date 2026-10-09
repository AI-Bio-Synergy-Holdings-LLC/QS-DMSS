"""Keep new build identity separate from published and scientific evidence."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def structured_data(path: Path) -> dict:
    match = re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        path.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert match
    return json.loads(match.group(1))


def test_published_build_keeps_project_and_version_archive_identities_separate() -> None:
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    assert citation["version"] == "0.14.0"
    assert citation["doi"] == "10.5281/zenodo.20074924"
    cockpit = ROOT / "src/qs_dmss/cockpit/static"
    app = structured_data(cockpit / "index.html")
    assert app["softwareVersion"] == "0.14.0"
    assert app["citation"] == "https://doi.org/10.5281/zenodo.20074924"
    js = (cockpit / "app.js").read_text(encoding="utf-8")
    assert 'packageVersion: "0.14.0"' in js
    assert 'archivedReleaseTag: "v0.14.0"' in js
    assert "citationMetadata.archivedReleaseTag" in js
    metadata = json.loads((ROOT / "codemeta.json").read_text(encoding="utf-8"))
    assert "https://doi.org/10.5281/zenodo.23250727" in metadata["sameAs"]
    assert any(item["value"] == "10.5281/zenodo.23250727" for item in citation["identifiers"])
    assert "https://doi.org/10.5281/zenodo.21366910" not in metadata.get("sameAs", [])


@pytest.mark.parametrize(
    "path",
    ["codemeta.json", "src/qs_dmss/cockpit/static/index.html"],
)
def test_published_metadata_pins_download_targets_to_verified_release(path: str) -> None:
    metadata_path = ROOT / path
    metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.suffix == ".json"
        else structured_data(metadata_path)
    )
    assert metadata["softwareVersion"] == "0.14.0"
    assert metadata["codeRepository"].endswith("/QS-DMSS")
    assert urlsplit(metadata["downloadUrl"]) == urlsplit(
        "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.14.0"
    )
    assert urlsplit(metadata["installUrl"]) == urlsplit("https://pypi.org/project/qs-dmss/0.14.0/")
    assert {urlsplit(url).hostname for url in metadata.get("sameAs", [])} <= {
        "github.com",
        "doi.org",
    }


def test_export_requires_source_and_hash_identity_instead_of_version_equivalence() -> None:
    js = (ROOT / "src/qs_dmss/cockpit/static/app.js").read_text(encoding="utf-8")
    assert "pypiUrl" not in js
    assert "pypi.org/project/qs-dmss" not in js
    assert "compare source commit and artifact hashes" in js
    assert "archive is historical" not in js
    assert 'release.archived_release_doi || "10.5281/zenodo.23250727"' in js


def test_release_notes_use_the_registered_diagnostic_convention() -> None:
    schema = json.loads(
        (ROOT / "schemas/diagnostic-pack-v1.schema.json").read_text(encoding="utf-8")
    )
    convention = schema["properties"]["required_diagnostic_conventions"]["prefixItems"][0]["const"]
    notes = (ROOT / "docs/release-v0.14.0.md").read_text(encoding="utf-8")
    assert f"`{convention}`" in notes
    assert "FFT_cell_measure_v2" not in notes


def test_portal_identifies_published_artifacts_without_scientific_promotion() -> None:
    index = (ROOT / "site/index.html").read_text(encoding="utf-8")
    graph = structured_data(ROOT / "site/index.html")["@graph"]
    source = next(item for item in graph if item["@type"] == "SoftwareSourceCode")
    application = next(item for item in graph if item["@type"] == "SoftwareApplication")
    assert source["version"] == "0.14.0"
    assert "graph model remains experimental and local-only" in source["description"].lower()
    assert application["softwareVersion"] == "0.14.0"
    assert urlsplit(application["installUrl"]) == urlsplit(
        "https://pypi.org/project/qs-dmss/0.14.0/"
    )
    assert "published on GitHub and PyPI" in index
    assert "Independent scientific review #183 remains open" in index
    assert "Hosted AI and graph execution remain disabled" in index
    assert urlsplit(application["downloadUrl"]) == urlsplit(
        "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.14.0"
    )
    assert "frozen, commit-pinned candidate results" in index
    assert "not a rerun of the published v0.14.0 package" in index


def test_manual_published_install_defaults_target_the_verified_release() -> None:
    workflow = yaml.load(
        (ROOT / ".github/workflows/fresh-install-smoke.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    assert inputs["package_version"]["default"] == "0.14.0"
    assert inputs["release_tag"]["default"] == "v0.14.0"


@pytest.mark.parametrize(
    ("source", "version", "expected"),
    [
        ("candidate-wheel", "0.13.2", True),
        ("candidate-wheel", "0.14.0", True),
        ("pypi", "0.13.2", False),
        ("release-wheel", "0.13.2", False),
        ("pypi", "0.14.0", True),
        ("release-wheel", "0.14.0", True),
    ],
)
def test_published_new_artifacts_exercise_admitted_pilots(source, version, expected) -> None:
    spec = importlib.util.spec_from_file_location(
        "fresh_install_smoke", ROOT / ".github/scripts/fresh_install_smoke.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._includes_admitted_pilots(source, version) is expected


@pytest.mark.parametrize(
    "path",
    [
        "zenodo-citation.md",
        "ownership-and-use.md",
        "post-v0.3-active-roadmap.md",
        "outreach-contact-avenues.md",
        "funding-roadmap.md",
        "ascl-joss-readiness.md",
        "joss-preflight.md",
        "circulation-funnel.md",
        "simulation-showcase.md",
    ],
)
def test_current_release_guidance_matches_verified_publication(path: str) -> None:
    text = (ROOT / "docs" / path).read_text(encoding="utf-8")
    assert "`v0.14.0`" in text
    assert "10.5281/zenodo.23250727" in text
    assert not re.search(
        r"(?im)^(?:- )?(?:Current|Latest|The current|PyPI package is)"
        r"[^\n]*(?:v?0\.13\.2|21366910)",
        text,
    )


@pytest.mark.parametrize(
    "path",
    [
        "diagnostic-packs.md",
        "recommendation-robustness.md",
        "experimental-graph-spectral-backend.md",
        "scientific-challenge-handoff.md",
    ],
)
def test_admitted_feature_guides_no_longer_describe_release_as_unpublished(path: str) -> None:
    overview = "\n".join((ROOT / "docs" / path).read_text(encoding="utf-8").splitlines()[:20])
    assert "published `v0.14.0`" in overview
    assert "not published" not in overview
    assert "under release" not in overview
    assert "#183" in overview


def test_showcase_install_guidance_targets_current_release_artifact() -> None:
    text = (ROOT / "docs/simulation-showcase.md").read_text(encoding="utf-8")
    assert "/releases/download/v0.14.0/qs_dmss-0.14.0-py3-none-any.whl" in text
    assert "/releases/download/v0.13.2/" not in text


def test_documentation_refresh_preserves_historical_and_experimental_boundaries() -> None:
    baseline = json.loads(
        (ROOT / "docs/review-evidence/fractal-ssfm-v0.13.2.json").read_text(encoding="utf-8")
    )["release"]
    assert baseline["version"] == "0.13.2"
    assert baseline["source_commit"] == "7a063eb91af6c50e483c2d062bf6cee0daf709e4"
    assert baseline["wheel_sha256"] == (
        "6f22876fa625681aa72b96d99e14de92cfd5cfae870fc53d9d41673ebf82416f"
    )
    spine = (ROOT / "docs/fractal-quadrant-ssfm-validation-spine.md").read_text(encoding="utf-8")
    assert "historical `v0.13.2` scientific-review baseline" in re.sub(r"\s+", " ", spine)
    assert "fractal-ssfm-independent-review-v0.13.2.md" in spine
    graph = (ROOT / "docs/experimental-graph-spectral-backend.md").read_text(encoding="utf-8")
    assert "experimental, CPU-only and local-only" in re.sub(r"\s+", " ", graph)
    assert "#183 remains open" in graph
    assert "The public demo cannot execute this backend" in graph
    assert "qs-dmss run $graphConfig" in graph
    assert "files('qs_dmss.assets').joinpath('configs/sierpinski_graph_spectral.yaml')" in graph
