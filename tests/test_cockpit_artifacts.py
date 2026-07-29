from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException

from qs_dmss.cockpit.api import CockpitService


@pytest.fixture
def cockpit_service(tmp_path: Path) -> CockpitService:
    return CockpitService.create(
        repo_root=Path(__file__).resolve().parents[1],
        output_root=tmp_path / "runs",
    )


def _write_json(path: Path, payload: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload or {}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_run_and_experiment_lookup_reject_repository_escape(
    cockpit_service: CockpitService,
) -> None:
    run_dir = cockpit_service.output_root / "run-a"
    _write_json(run_dir / "run.json", {"run_id": "run-a"})
    experiment_dir = cockpit_service.experiments_root / "experiment-a"
    _write_json(
        experiment_dir / "experiment.json",
        {"experiment_id": "experiment-a"},
    )

    assert cockpit_service._get_run_dir("run-a") == run_dir.resolve()
    assert cockpit_service._get_experiment_dir("experiment-a") == (
        experiment_dir.resolve()
    )

    escaped_run = cockpit_service.output_root.parent / "escaped-run"
    _write_json(escaped_run / "run.json", {"run_id": "escaped-run"})
    with pytest.raises(HTTPException) as run_error:
        cockpit_service._get_run_dir("../escaped-run")
    assert run_error.value.status_code == 404
    assert run_error.value.detail == "Run not found"

    escaped_experiment = cockpit_service.experiments_root.parent / "escaped-experiment"
    _write_json(
        escaped_experiment / "experiment.json",
        {"experiment_id": "escaped-experiment"},
    )
    with pytest.raises(HTTPException) as experiment_error:
        cockpit_service._get_experiment_dir("../escaped-experiment")
    assert experiment_error.value.status_code == 404
    assert experiment_error.value.detail == "Experiment not found"


def test_artifact_lookup_preserves_not_found_contract(
    cockpit_service: CockpitService,
) -> None:
    run_dir = cockpit_service.output_root / "run-a"
    _write_json(run_dir / "run.json")
    experiment_dir = cockpit_service.experiments_root / "experiment-a"
    _write_json(experiment_dir / "experiment.json")

    cases = (
        (lambda: cockpit_service.bundle_path("run-a"), "Evidence bundle not found"),
        (lambda: cockpit_service.report_path("run-a"), "Run report not found"),
        (
            lambda: cockpit_service.experiment_bundle_path("experiment-a"),
            "Experiment bundle not found",
        ),
        (
            lambda: cockpit_service.experiment_report_path("experiment-a"),
            "Experiment report not found",
        ),
        (
            lambda: cockpit_service.experiment_workbook_path("experiment-a"),
            "Experiment workbook not found",
        ),
        (
            lambda: cockpit_service.run_bundle_profile_path("run-a", "unknown"),
            "Evidence bundle profile not found",
        ),
    )

    for operation, detail in cases:
        with pytest.raises(HTTPException) as error:
            operation()
        assert error.value.status_code == 404
        assert error.value.detail == detail


def test_profile_bundle_records_included_and_missing_files(
    cockpit_service: CockpitService,
) -> None:
    run_dir = cockpit_service.output_root / "run-a"
    _write_json(run_dir / "run.json", {"run_id": "run-a"})
    _write_json(run_dir / "metrics.json", {"relative_norm_change": 0.0})
    _write_json(run_dir / "manifest.sha256.json", {"files": {}})
    (run_dir / "config.yaml").write_text("run:\n  id: run-a\n", encoding="utf-8")

    bundle_path = cockpit_service.run_bundle_profile_path("run-a", "review")

    assert bundle_path == (
        cockpit_service.output_root
        / "_derived_bundles"
        / "run-a-review-bundle.zip"
    )
    assert cockpit_service.run_bundle_profile_path("run-a", "review") == bundle_path
    with zipfile.ZipFile(bundle_path) as archive:
        assert archive.namelist() == [
            "bundle-profile.json",
            "config.yaml",
            "metrics.json",
            "run.json",
            "manifest.sha256.json",
        ]
        profile = json.loads(archive.read("bundle-profile.json"))

    assert profile["schema_version"] == "1.0"
    assert profile["profile"] == "review"
    assert profile["run_id"] == "run-a"
    assert profile["included_files"] == [
        "config.yaml",
        "metrics.json",
        "run.json",
        "manifest.sha256.json",
    ]
    assert profile["missing_optional_files"] == [
        "energy.csv",
        "environment.lock.json",
        "report.html",
    ]
    assert profile["generated_at"].endswith("+00:00")
    assert "not physical validation" in profile["claim_boundary"]


def test_run_and_experiment_directory_listing_is_marker_bounded_and_newest_first(
    cockpit_service: CockpitService,
) -> None:
    old_run = cockpit_service.output_root / "run-old"
    new_run = cockpit_service.output_root / "run-new"
    ignored_run = cockpit_service.output_root / "run-without-marker"
    _write_json(old_run / "run.json")
    _write_json(new_run / "run.json")
    ignored_run.mkdir(parents=True)
    os.utime(old_run, (100, 100))
    os.utime(new_run, (200, 200))

    old_experiment = cockpit_service.experiments_root / "experiment-old"
    new_experiment = cockpit_service.experiments_root / "experiment-new"
    ignored_experiment = cockpit_service.experiments_root / "experiment-without-marker"
    _write_json(old_experiment / "experiment.json")
    _write_json(new_experiment / "experiment.json")
    ignored_experiment.mkdir(parents=True)
    os.utime(old_experiment, (100, 100))
    os.utime(new_experiment, (200, 200))

    assert cockpit_service._list_run_dirs() == [new_run, old_run]
    assert cockpit_service._list_experiment_dirs() == [
        new_experiment,
        old_experiment,
    ]
