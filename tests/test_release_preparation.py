"""Keep new build identity separate from published and scientific evidence."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

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


def test_prepared_build_does_not_claim_a_new_public_archive() -> None:
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    assert citation["version"] == "0.14.0"
    assert citation["doi"] == "10.5281/zenodo.20074924"
    cockpit = ROOT / "src/qs_dmss/cockpit/static"
    app = structured_data(cockpit / "index.html")
    assert app["softwareVersion"] == "0.14.0"
    assert app["citation"] == "https://doi.org/10.5281/zenodo.20074924"
    js = (cockpit / "app.js").read_text(encoding="utf-8")
    assert 'packageVersion: "0.14.0"' in js
    assert 'archivedReleaseTag: "v0.13.2"' in js
    assert "citationMetadata.archivedReleaseTag" in js
    metadata = json.loads((ROOT / "codemeta.json").read_text(encoding="utf-8"))
    assert "https://doi.org/10.5281/zenodo.21366910" not in metadata.get("sameAs", [])


@pytest.mark.parametrize(
    "path",
    ["codemeta.json", "src/qs_dmss/cockpit/static/index.html"],
)
def test_candidate_metadata_does_not_advertise_a_published_download(path: str) -> None:
    metadata_path = ROOT / path
    metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.suffix == ".json"
        else structured_data(metadata_path)
    )
    assert metadata["softwareVersion"] == "0.14.0"
    assert metadata["codeRepository"].endswith("/QS-DMSS")
    assert "downloadUrl" not in metadata
    assert "installUrl" not in metadata
    assert not any("pypi.org" in url for url in metadata.get("sameAs", []))


def test_candidate_export_does_not_link_to_a_different_published_package() -> None:
    js = (ROOT / "src/qs_dmss/cockpit/static/app.js").read_text(encoding="utf-8")
    assert "pypiUrl" not in js
    assert "pypi.org/project/qs-dmss" not in js
    assert "publication, not an install source for this build" in js


def test_release_notes_use_the_registered_diagnostic_convention() -> None:
    schema = json.loads(
        (ROOT / "schemas/diagnostic-pack-v1.schema.json").read_text(encoding="utf-8")
    )
    convention = schema["properties"]["required_diagnostic_conventions"]["prefixItems"][0]["const"]
    notes = (ROOT / "docs/release-v0.14.0.md").read_text(encoding="utf-8")
    assert f"`{convention}`" in notes
    assert "FFT_cell_measure_v2" not in notes


def test_portal_distinguishes_development_source_from_published_package() -> None:
    index = (ROOT / "site/index.html").read_text(encoding="utf-8")
    graph = structured_data(ROOT / "site/index.html")["@graph"]
    source = next(item for item in graph if item["@type"] == "SoftwareSourceCode")
    application = next(item for item in graph if item["@type"] == "SoftwareApplication")
    assert source["version"] == "0.14.0"
    assert "under release qualification" in source["description"]
    assert application["softwareVersion"] == "0.13.2"
    assert application["installUrl"].endswith("/qs-dmss/0.13.2/")
    assert "under release qualification, not yet published" in index
    assert "Independent scientific review #183 remains open" in index
    assert "Hosted AI and graph execution remain disabled" in index
    assert "releases/tag/v0.14.0" not in index
    assert "pypi.org/project/qs-dmss/0.14.0/" not in index


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
