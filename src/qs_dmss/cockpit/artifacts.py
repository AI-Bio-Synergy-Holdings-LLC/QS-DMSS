from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from qs_dmss.paths import contained_path, safe_filename

RUN_BUNDLE_PROFILES: dict[str, dict[str, Any]] = {
    "review": {
        "title": "Scientific review bundle",
        "claim_boundary": (
            "Human-readable configuration, diagnostics, report, environment, and "
            "integrity records. This package supports review of numerical evidence; "
            "it is not physical validation."
        ),
        "files": (
            "config.yaml",
            "energy.csv",
            "environment.lock.json",
            "metrics.json",
            "run.json",
            "report.html",
            "manifest.sha256.json",
        ),
    },
    "state": {
        "title": "Reproducibility state bundle",
        "claim_boundary": (
            "Configuration, final numerical state, run metadata, metrics, and "
            "integrity manifest for controlled replay and downstream inspection."
        ),
        "files": (
            "config.yaml",
            "metrics.json",
            "run.json",
            "manifest.sha256.json",
            "artifacts/final_density.npy",
            "artifacts/final_state.npz",
        ),
    },
}


@dataclass(frozen=True)
class CockpitArtifactService:
    """Resolve and package run and experiment artifacts within declared roots."""

    output_root: Path
    experiments_root: Path

    def list_run_dirs(self) -> list[Path]:
        if not self.output_root.exists():
            return []
        run_dirs = [
            path
            for path in self.output_root.iterdir()
            if path.is_dir() and (path / "run.json").exists()
        ]
        return sorted(run_dirs, key=lambda path: path.stat().st_mtime, reverse=True)

    def list_experiment_dirs(self) -> list[Path]:
        if not self.experiments_root.exists():
            return []
        experiment_dirs = [
            path
            for path in self.experiments_root.iterdir()
            if path.is_dir() and (path / "experiment.json").exists()
        ]
        return sorted(
            experiment_dirs,
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def get_run_dir(self, run_id: str) -> Path:
        run_dir = (self.output_root / run_id).resolve()
        if run_dir.parent != self.output_root.resolve():
            raise HTTPException(status_code=404, detail="Run not found")
        if not run_dir.exists() or not (run_dir / "run.json").exists():
            raise HTTPException(status_code=404, detail="Run not found")
        return run_dir

    def get_experiment_dir(self, experiment_id: str) -> Path:
        experiment_dir = (self.experiments_root / experiment_id).resolve()
        if experiment_dir.parent != self.experiments_root.resolve():
            raise HTTPException(status_code=404, detail="Experiment not found")
        if not experiment_dir.exists() or not (
            experiment_dir / "experiment.json"
        ).exists():
            raise HTTPException(status_code=404, detail="Experiment not found")
        return experiment_dir

    def bundle_path(self, run_id: str) -> Path:
        run_dir = self.get_run_dir(run_id)
        bundle_path = run_dir / "evidence_bundle.zip"
        if not bundle_path.exists():
            raise HTTPException(status_code=404, detail="Evidence bundle not found")
        return bundle_path

    def run_bundle_profile_path(self, run_id: str, profile_name: str) -> Path:
        profile = RUN_BUNDLE_PROFILES.get(profile_name)
        if profile is None:
            raise HTTPException(
                status_code=404,
                detail="Evidence bundle profile not found",
            )
        run_dir = self.get_run_dir(run_id)
        safe_run_id = safe_filename(run_id, default="run")
        bundle_root = contained_path(self.output_root, "_derived_bundles")
        bundle_root.mkdir(parents=True, exist_ok=True)
        bundle_path = contained_path(
            bundle_root,
            f"{safe_run_id}-{safe_filename(profile_name, default='profile')}-bundle.zip",
        )
        if bundle_path.exists():
            return bundle_path

        included_files: list[str] = []
        missing_files: list[str] = []
        for relative_name in profile["files"]:
            candidate = contained_path(run_dir, relative_name)
            if candidate.exists() and candidate.is_file():
                included_files.append(relative_name)
            else:
                missing_files.append(relative_name)

        profile_record = {
            "schema_version": "1.0",
            "profile": profile_name,
            "title": profile["title"],
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "claim_boundary": profile["claim_boundary"],
            "included_files": included_files,
            "missing_optional_files": missing_files,
        }
        with zipfile.ZipFile(
            bundle_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            archive.writestr(
                "bundle-profile.json",
                json.dumps(profile_record, indent=2, sort_keys=True) + "\n",
            )
            for relative_name in included_files:
                archive.write(
                    contained_path(run_dir, relative_name),
                    arcname=relative_name,
                )
        return bundle_path

    def report_path(self, run_id: str) -> Path:
        run_dir = self.get_run_dir(run_id)
        report_path = run_dir / "report.html"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Run report not found")
        return report_path

    def experiment_bundle_path(self, experiment_id: str) -> Path:
        experiment_dir = self.get_experiment_dir(experiment_id)
        bundle_path = experiment_dir / "evidence_bundle.zip"
        if not bundle_path.exists():
            raise HTTPException(status_code=404, detail="Experiment bundle not found")
        return bundle_path

    def experiment_report_path(self, experiment_id: str) -> Path:
        experiment_dir = self.get_experiment_dir(experiment_id)
        report_path = experiment_dir / "report.html"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Experiment report not found")
        return report_path

    def experiment_workbook_path(self, experiment_id: str) -> Path:
        experiment_dir = self.get_experiment_dir(experiment_id)
        workbook_path = experiment_dir / "workbook.html"
        if not workbook_path.exists():
            raise HTTPException(status_code=404, detail="Experiment workbook not found")
        return workbook_path
