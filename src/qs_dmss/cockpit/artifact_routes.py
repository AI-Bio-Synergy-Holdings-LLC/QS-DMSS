"""Run-artifact delivery routes with application-owned service and response guards."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse

from qs_dmss.paths import safe_filename


class _RunArtifactService(Protocol):
    def bundle_path(self, run_id: str) -> Path: ...

    def run_bundle_profile_path(self, run_id: str, profile: str) -> Path: ...

    def report_path(self, run_id: str) -> Path: ...


def register_run_artifact_routes(
    app: FastAPI,
    service_dependency: Callable[..., _RunArtifactService],
    guarded_file_response: Callable[..., FileResponse],
) -> None:
    """Register delivery only; session selection and download/CSP policy stay injected."""

    @app.get("/api/runs/{run_id}/bundle")
    def bundle_download(
        run_id: str,
        active_service: _RunArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        bundle_path = active_service.bundle_path(run_id)
        return guarded_file_response(
            active_service,
            bundle_path,
            media_type="application/zip",
            filename=f"{safe_filename(run_id, default='run')}-evidence-bundle.zip",
        )

    @app.get("/api/runs/{run_id}/review-bundle")
    def review_bundle_download(
        run_id: str,
        active_service: _RunArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        bundle_path = active_service.run_bundle_profile_path(run_id, "review")
        return guarded_file_response(
            active_service,
            bundle_path,
            media_type="application/zip",
            filename=f"{safe_filename(run_id, default='run')}-review-bundle.zip",
        )

    @app.get("/api/runs/{run_id}/state-bundle")
    def state_bundle_download(
        run_id: str,
        active_service: _RunArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        bundle_path = active_service.run_bundle_profile_path(run_id, "state")
        return guarded_file_response(
            active_service,
            bundle_path,
            media_type="application/zip",
            filename=f"{safe_filename(run_id, default='run')}-state-bundle.zip",
        )

    @app.get("/api/runs/{run_id}/report")
    def run_report(
        run_id: str,
        active_service: _RunArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        report_path = active_service.report_path(run_id)
        return guarded_file_response(
            active_service,
            report_path,
            media_type="text/html",
        )
