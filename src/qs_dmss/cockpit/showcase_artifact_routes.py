"""Showcase delivery with application-owned service and file-response guards."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse


class _ShowcaseArtifactService(Protocol):
    def showcase_markdown_path(self, scenario: str) -> Path:
        pass

    def showcase_json_path(self, scenario: str) -> Path:
        pass

    def showcase_artifact_path(self, scenario: str, artifact_name: str) -> Path:
        pass


def register_showcase_artifact_routes(
    app: FastAPI,
    service_dependency: Callable[..., _ShowcaseArtifactService],
    guarded_file_response: Callable[..., FileResponse],
) -> None:
    """Move delivery only; lookup, normalization, session selection and policy stay injected."""

    @app.get("/api/showcases/{scenario}/report")
    def showcase_markdown_report(
        scenario: str,
        active_service: _ShowcaseArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        report_path = active_service.showcase_markdown_path(scenario)
        return guarded_file_response(
            active_service,
            report_path,
            media_type="text/markdown",
        )

    @app.get("/api/showcases/{scenario}/report.json")
    def showcase_json_report(
        scenario: str,
        active_service: _ShowcaseArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        report_path = active_service.showcase_json_path(scenario)
        return guarded_file_response(
            active_service,
            report_path,
            media_type="application/json",
        )

    @app.get("/api/showcases/{scenario}/artifacts/{artifact_name}")
    def showcase_artifact(
        scenario: str,
        artifact_name: str,
        active_service: _ShowcaseArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        artifact_path = active_service.showcase_artifact_path(scenario, artifact_name)
        media_type = "application/octet-stream"
        if artifact_path.suffix == ".svg":
            media_type = "image/svg+xml"
        elif artifact_path.suffix == ".csv":
            media_type = "text/csv"
        return guarded_file_response(
            active_service,
            artifact_path,
            media_type=media_type,
            filename=artifact_path.name,
        )
