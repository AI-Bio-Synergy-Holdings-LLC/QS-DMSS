"""Experiment-artifact delivery with application-owned service and response guards."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse

from qs_dmss.paths import safe_filename


class _ExperimentArtifactService(Protocol):
    def experiment_bundle_path(self, experiment_id: str) -> Path:
        pass

    def experiment_report_path(self, experiment_id: str) -> Path:
        pass

    def experiment_workbook_path(self, experiment_id: str) -> Path:
        pass


def register_experiment_artifact_routes(
    app: FastAPI,
    service_dependency: Callable[..., _ExperimentArtifactService],
    guarded_file_response: Callable[..., FileResponse],
) -> None:
    """Preserve delivery contracts; session selection and download/CSP policy stay injected."""

    @app.get("/api/experiments/{experiment_id}/bundle")
    def experiment_bundle_download(
        experiment_id: str,
        active_service: _ExperimentArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        bundle_path = active_service.experiment_bundle_path(experiment_id)
        return guarded_file_response(
            active_service,
            bundle_path,
            media_type="application/zip",
            filename=(
                f"{safe_filename(experiment_id, default='experiment')}"
                "-comparison-bundle.zip"
            ),
        )

    @app.get("/api/experiments/{experiment_id}/report")
    def experiment_report(
        experiment_id: str,
        active_service: _ExperimentArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        report_path = active_service.experiment_report_path(experiment_id)
        return guarded_file_response(
            active_service,
            report_path,
            media_type="text/html",
        )

    @app.get("/api/experiments/{experiment_id}/workbook")
    def experiment_workbook(
        experiment_id: str,
        active_service: _ExperimentArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        workbook_path = active_service.experiment_workbook_path(experiment_id)
        return guarded_file_response(
            active_service,
            workbook_path,
            media_type="text/html",
        )

    @app.get("/api/experiments/{experiment_id}/workbook/download")
    def experiment_workbook_download(
        experiment_id: str,
        active_service: _ExperimentArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        workbook_path = active_service.experiment_workbook_path(experiment_id)
        return guarded_file_response(
            active_service,
            workbook_path,
            media_type="text/html",
            filename=(
                f"{safe_filename(experiment_id, default='experiment')}"
                "-research-workbook.html"
            ),
        )
