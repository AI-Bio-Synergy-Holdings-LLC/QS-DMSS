from __future__ import annotations

import json
import zipfile
from pathlib import Path

from qs_dmss.cli import main
from qs_dmss.data_registry import (
    DATA_CALIBRATION_BUNDLE,
    DATA_CALIBRATION_JSON_REPORT,
    DATA_CALIBRATION_MARKDOWN_REPORT,
    list_data_sources,
    resolve_data_source,
    run_reference_calibration,
)


def test_packaged_public_data_sources_are_available() -> None:
    sources = list_data_sources()
    source_ids = {source.source_id for source in sources}

    assert source_ids == {
        "desi-dr1",
        "gaia-dr3",
        "planck-legacy",
        "sdss-dr19",
    }

    planck = resolve_data_source("planck-legacy")
    assert planck.payload["name"] == "Planck Legacy Archive"
    assert planck.payload["official_url"] == "https://pla.esac.esa.int/"
    assert "Cosmological parameters" in planck.payload["citation"]


def test_reference_data_calibration_evidence_bundle(tmp_path: Path) -> None:
    output_root = tmp_path / "reference-data-calibration"
    cache_root = tmp_path / "cache"

    report = run_reference_calibration(
        output_root=output_root,
        cache_root=cache_root,
    )

    assert report["success"] is True
    assert report["metrics"]["source_count"] == 4
    assert Path(report["report_path"]) == output_root / DATA_CALIBRATION_JSON_REPORT
    assert Path(report["markdown_report_path"]) == output_root / DATA_CALIBRATION_MARKDOWN_REPORT
    assert Path(report["evidence_bundle_path"]) == output_root / DATA_CALIBRATION_BUNDLE

    saved_report = json.loads(
        (output_root / DATA_CALIBRATION_JSON_REPORT).read_text(encoding="utf-8")
    )
    assert saved_report["success"] is True
    for source in saved_report["sources"]:
        assert source["official_url"].startswith("https://")
        assert source["access_date"]
        assert source["citation"]

    for entry in saved_report["cache_entries"]:
        assert entry["sha256"]
        assert Path(entry["path"]).is_file()

    markdown = (output_root / DATA_CALIBRATION_MARKDOWN_REPORT).read_text(
        encoding="utf-8"
    )
    assert "not a fine-tuned scientific model" in markdown
    assert "not peer-reviewed scientific validation" in markdown

    with zipfile.ZipFile(output_root / DATA_CALIBRATION_BUNDLE) as bundle:
        names = set(bundle.namelist())

    assert "evidence-manifest.json" in names
    assert DATA_CALIBRATION_JSON_REPORT in names
    assert DATA_CALIBRATION_MARKDOWN_REPORT in names
    assert "calibration-config.json" in names
    assert "cached-sources/planck-legacy.source-manifest.json" in names
    assert "calibration-inputs/workflow-smoke-reference.json" in names


def test_reference_data_calibration_source_subset(tmp_path: Path) -> None:
    report = run_reference_calibration(
        output_root=tmp_path / "calibration-subset",
        cache_root=tmp_path / "cache",
        source_ids=["gaia-dr3"],
    )

    assert report["success"] is True
    assert report["metrics"]["source_count"] == 1
    assert report["sources"][0]["id"] == "gaia-dr3"


def test_cli_data_sources_and_calibration(tmp_path: Path, capsys) -> None:
    list_exit_code = main(["data", "sources", "list"])
    assert list_exit_code == 0
    list_output = capsys.readouterr().out
    assert "planck-legacy" in list_output
    assert "gaia-dr3" in list_output

    inspect_exit_code = main(["data", "sources", "inspect", "desi-dr1"])
    assert inspect_exit_code == 0
    inspect_output = capsys.readouterr().out
    assert "DESI Data Release 1" in inspect_output
    assert "Official URL: https://data.desi.lbl.gov/doc/releases/dr1/" in inspect_output
    assert "Citation:" in inspect_output

    run_exit_code = main(
        [
            "data",
            "calibration",
            "run",
            "--output-root",
            str(tmp_path / "cli-reference-data-calibration"),
            "--cache-root",
            str(tmp_path / "cli-cache"),
        ]
    )
    assert run_exit_code == 0
    run_output = capsys.readouterr().out
    assert "Reference-data calibration passed." in run_output
    assert "Evidence bundle:" in run_output
    assert "Cache root:" in run_output
