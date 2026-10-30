"""Remaining export downloads with application-owned lookup and response guards."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse


class _ExportArtifactService(Protocol):
    def ai_draft_bundle_path(self, interaction_id: str) -> Path:
        pass

    def campaign_study_template_path(self, template_id: str) -> Path:
        pass

    def research_object_markdown_path(self, export_id: str) -> tuple[Path, str]:
        pass

    def workspace_path(self, workspace_id: str) -> Path:
        pass


def register_ai_bundle_route(
    app: FastAPI,
    service_dependency: Callable[..., _ExportArtifactService],
    guarded_file_response: Callable[..., FileResponse],
) -> None:
    """Register at the original AI bundle position; do not enable providers."""

    @app.get("/api/ai/drafts/{interaction_id}/bundle")
    def ai_draft_bundle(
        interaction_id: str,
        active_service: _ExportArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        try:
            path = active_service.ai_draft_bundle_path(interaction_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="AI advisory draft not found") from None
        return guarded_file_response(
            active_service,
            path,
            media_type="application/zip",
            filename=f"{interaction_id}-ai-advisory-bundle.zip",
        )


def register_campaign_study_download_route(
    app: FastAPI,
    service_dependency: Callable[..., _ExportArtifactService],
    guarded_file_response: Callable[..., FileResponse],
) -> None:
    """Register delivery without moving template precedence or persistence."""

    @app.get("/api/campaign-studies/{template_id}/download")
    def campaign_study_download(
        template_id: str,
        active_service: _ExportArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        template_path = active_service.campaign_study_template_path(template_id)
        return guarded_file_response(
            active_service,
            template_path,
            media_type="application/json",
            filename=template_path.name,
        )


def register_research_object_download_route(
    app: FastAPI,
    service_dependency: Callable[..., _ExportArtifactService],
    guarded_file_response: Callable[..., FileResponse],
) -> None:
    """Keep metadata-derived naming and Markdown policy with their owners."""

    @app.get("/api/research-objects/{export_id}/download")
    def research_object_download(
        export_id: str,
        active_service: _ExportArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        markdown_path, file_name = active_service.research_object_markdown_path(export_id)
        return guarded_file_response(
            active_service,
            markdown_path,
            media_type="text/markdown",
            filename=file_name,
        )


def register_workspace_download_route(
    app: FastAPI,
    service_dependency: Callable[..., _ExportArtifactService],
    guarded_file_response: Callable[..., FileResponse],
) -> None:
    """Register only the GET download, leaving workspace mutations unchanged."""

    @app.get("/api/workspaces/{workspace_id}/download")
    def workspace_download(
        workspace_id: str,
        active_service: _ExportArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        workspace_path = active_service.workspace_path(workspace_id)
        return guarded_file_response(
            active_service,
            workspace_path,
            media_type="application/json",
            filename=workspace_path.name,
        )
