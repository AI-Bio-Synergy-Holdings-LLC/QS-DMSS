from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException

from qs_dmss.experiment import create_experiment_id
from qs_dmss.paths import contained_path, safe_filename

WorkspaceResourceBuilder = Callable[[str], dict]
CampaignStudyInstaller = Callable[[dict[str, Any]], dict]
WorkspaceIdFactory = Callable[[str], str]


@dataclass(frozen=True)
class WorkspaceExportSpec:
    title: str = "QS-DMSS workspace"
    description: str | None = None
    collaborators: list[dict[str, Any]] = field(default_factory=list)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    experiment_ids: list[str] = field(default_factory=list)
    campaign_study_template_ids: list[str] = field(default_factory=list)
    research_object_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CockpitWorkspaceService:
    """Persist portable research workspaces behind characterized contracts."""

    experiments_root: Path
    hosted_demo_enabled: bool
    build_run_summary: WorkspaceResourceBuilder
    build_experiment_detail: WorkspaceResourceBuilder
    build_campaign_study_detail: WorkspaceResourceBuilder
    build_research_object_detail: WorkspaceResourceBuilder
    install_campaign_study: CampaignStudyInstaller
    workspace_id_factory: WorkspaceIdFactory = create_experiment_id

    def list_workspaces(self) -> list[dict]:
        return [
            self._build_workspace_summary(path) for path in self._list_workspace_paths()
        ]

    def get_workspace(self, workspace_id: str) -> dict:
        return self._build_workspace_detail(self._get_workspace_path(workspace_id))

    def export_workspace(self, payload: WorkspaceExportSpec) -> dict:
        if self.hosted_demo_enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo disables workspace snapshots because public outputs are temporary. "
                    "Use research-object export here, or install QS-DMSS locally for workspace export."
                ),
            )
        try:
            record = self._build_workspace_record(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        workspace_path = (
            self._workspace_dir(
                record["workspace_id"],
                create=True,
            )
            / "workspace.json"
        )
        workspace_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return self._build_workspace_detail(workspace_path)

    def import_workspace(self, workspace: dict[str, Any]) -> dict:
        if self.hosted_demo_enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo does not accept uploaded workspace JSON. "
                    "Install QS-DMSS locally to import collaborator workspaces."
                ),
            )
        try:
            record = self._normalize_imported_workspace(workspace)
            installed_templates = self._install_workspace_campaign_studies(record)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        workspace_path = (
            self._workspace_dir(
                record["workspace_id"],
                create=True,
            )
            / "workspace.json"
        )
        workspace_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        detail = self._build_workspace_detail(workspace_path)
        detail["imported_campaign_studies"] = installed_templates
        return detail

    def workspace_path(self, workspace_id: str) -> Path:
        return self._get_workspace_path(workspace_id)

    def _workspaces_root(self, *, create: bool = False) -> Path:
        workspace_root = self.experiments_root / "workspaces"
        if create:
            workspace_root.mkdir(parents=True, exist_ok=True)
        return workspace_root

    def _workspace_dir(self, workspace_id: str, *, create: bool = False) -> Path:
        workspace_root = self._workspaces_root(create=create)
        workspace_dir = contained_path(
            workspace_root,
            safe_filename(workspace_id, default="workspace"),
        )
        if create:
            workspace_dir.mkdir(parents=True, exist_ok=False)
        if not workspace_dir.exists() or not workspace_dir.is_dir():
            raise HTTPException(status_code=404, detail="Workspace export not found")
        return workspace_dir

    def _get_workspace_path(self, workspace_id: str) -> Path:
        workspace_path = self._workspace_dir(workspace_id) / "workspace.json"
        if not workspace_path.exists() or not workspace_path.is_file():
            raise HTTPException(status_code=404, detail="Workspace export not found")
        return workspace_path

    def _list_workspace_paths(self) -> list[Path]:
        workspace_root = self._workspaces_root()
        if not workspace_root.exists():
            return []
        return sorted(
            [
                path / "workspace.json"
                for path in workspace_root.iterdir()
                if path.is_dir() and (path / "workspace.json").is_file()
            ],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def _build_workspace_record(self, payload: WorkspaceExportSpec) -> dict:
        workspace_id = self.workspace_id_factory("workspace")
        now = datetime.now(timezone.utc).isoformat()
        collaborators = self._normalize_workspace_collaborators(payload.collaborators)
        annotations = self._normalize_workspace_annotations(
            payload.annotations,
            collaborators,
        )
        warnings: list[dict] = []
        resources = {
            "runs": self._collect_workspace_resources(
                "run",
                self._dedupe_text_values(payload.run_ids),
                self._build_workspace_run_resource,
                warnings,
            ),
            "experiments": self._collect_workspace_resources(
                "experiment",
                self._dedupe_text_values(payload.experiment_ids),
                self.build_experiment_detail,
                warnings,
            ),
            "campaign_study_templates": self._collect_workspace_resources(
                "campaign-study",
                self._dedupe_text_values(payload.campaign_study_template_ids),
                self.build_campaign_study_detail,
                warnings,
            ),
            "research_objects": self._collect_workspace_resources(
                "research-object",
                self._dedupe_text_values(payload.research_object_ids),
                self.build_research_object_detail,
                warnings,
            ),
        }
        job_summaries = self._workspace_job_summaries(resources)
        record = {
            "schema_version": 1,
            "workspace_id": workspace_id,
            "title": str(payload.title or "QS-DMSS workspace").strip()
            or "QS-DMSS workspace",
            "description": (
                str(payload.description).strip()
                if payload.description is not None
                else None
            ),
            "created_at": now,
            "updated_at": now,
            "collaborators": collaborators,
            "annotations": annotations,
            "resources": resources,
            "job_summaries": job_summaries,
            "warnings": warnings,
        }
        record["summary"] = self._workspace_resource_counts(
            resources,
            collaborators,
            annotations,
            job_summaries,
            warnings,
        )
        return record

    def _normalize_imported_workspace(
        self,
        workspace: dict[str, Any],
    ) -> dict:
        if not isinstance(workspace, dict):
            raise ValueError("Workspace import requires a workspace object")
        record = json.loads(json.dumps(workspace))
        resources = record.get("resources") or {}
        if not isinstance(resources, dict):
            raise ValueError("Workspace resources must be an object")

        source_workspace_id = str(record.get("workspace_id") or "workspace")
        now = datetime.now(timezone.utc).isoformat()
        collaborators = self._normalize_workspace_collaborators(
            record.get("collaborators") or []
        )
        annotations = self._normalize_workspace_annotations(
            record.get("annotations") or [],
            collaborators,
        )
        job_summaries = self._workspace_job_summaries(resources)
        record["workspace_id"] = self.workspace_id_factory("workspace")
        record["imported_from_workspace_id"] = source_workspace_id
        record["imported_at"] = now
        record["updated_at"] = now
        record["title"] = str(
            record.get("title") or "Imported QS-DMSS workspace"
        ).strip()
        record["description"] = record.get("description")
        record["collaborators"] = collaborators
        record["annotations"] = annotations
        record["resources"] = resources
        record["job_summaries"] = job_summaries
        record["warnings"] = record.get("warnings") or []
        record["summary"] = self._workspace_resource_counts(
            resources,
            collaborators,
            annotations,
            job_summaries,
            record["warnings"],
        )
        return record

    def _install_workspace_campaign_studies(self, record: dict) -> list[dict]:
        installed: list[dict] = []
        resources = record.get("resources") or {}
        templates = resources.get("campaign_study_templates") or []
        if not isinstance(templates, list):
            raise ValueError("Workspace campaign study templates must be a list")

        for item in templates:
            if not isinstance(item, dict):
                continue
            template = item.get("template")
            if not isinstance(template, dict):
                continue
            imported_template = dict(template)
            imported_from_template_id = imported_template.get("template_id")
            if imported_from_template_id:
                imported_template["imported_from_template_id"] = str(
                    imported_from_template_id
                )
            imported_template["imported_from_workspace_id"] = record["workspace_id"]
            imported_template.pop("packaged", None)
            detail = self.install_campaign_study(imported_template)
            installed.append(detail["summary"])
        return installed

    def _build_workspace_run_resource(self, run_id: str) -> dict:
        summary = self.build_run_summary(run_id)
        return {
            "summary": summary,
            "urls": {
                "detail": f"/api/runs/{summary['run_id']}",
                "bundle": f"/api/runs/{summary['run_id']}/bundle",
                "report": f"/api/runs/{summary['run_id']}/report",
            },
        }

    def _collect_workspace_resources(
        self,
        resource_type: str,
        resource_ids: list[str],
        build_resource: WorkspaceResourceBuilder,
        warnings: list[dict],
    ) -> list[dict]:
        resources: list[dict] = []
        for resource_id in resource_ids:
            try:
                resources.append(build_resource(resource_id))
            except HTTPException as exc:
                if exc.status_code != 404:
                    raise
                warnings.append(
                    {
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "message": str(exc.detail),
                    }
                )
        return resources

    def _workspace_urls(self, workspace_id: str) -> dict:
        return {
            "detail": f"/api/workspaces/{workspace_id}",
            "download": f"/api/workspaces/{workspace_id}/download",
        }

    def _build_workspace_summary(self, path: Path) -> dict:
        record = self._read_json(path)
        workspace_id = str(record.get("workspace_id") or path.parent.name)
        resources = record.get("resources") or {}
        collaborators = record.get("collaborators") or []
        annotations = record.get("annotations") or []
        job_summaries = record.get("job_summaries") or []
        warnings = record.get("warnings") or []
        return {
            "workspace_id": workspace_id,
            "title": record.get("title") or workspace_id,
            "description": record.get("description"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "imported_from_workspace_id": record.get("imported_from_workspace_id"),
            **self._workspace_resource_counts(
                resources,
                collaborators,
                annotations,
                job_summaries,
                warnings,
            ),
            "urls": self._workspace_urls(workspace_id),
        }

    def _build_workspace_detail(self, path: Path) -> dict:
        record = self._read_json(path)
        workspace_id = str(record.get("workspace_id") or path.parent.name)
        return {
            "summary": self._build_workspace_summary(path),
            "workspace": record,
            "urls": self._workspace_urls(workspace_id),
        }

    def _workspace_resource_counts(
        self,
        resources: dict,
        collaborators: list[dict],
        annotations: list[dict],
        job_summaries: list[dict],
        warnings: list[dict],
    ) -> dict:
        return {
            "run_count": len(resources.get("runs") or []),
            "experiment_count": len(resources.get("experiments") or []),
            "campaign_study_template_count": len(
                resources.get("campaign_study_templates") or []
            ),
            "research_object_count": len(resources.get("research_objects") or []),
            "collaborator_count": len(collaborators),
            "annotation_count": len(annotations),
            "job_count": len(job_summaries),
            "warning_count": len(warnings),
        }

    def _workspace_job_summaries(self, resources: dict) -> list[dict]:
        job_summaries: dict[str, dict] = {}

        def add(summary: dict | None) -> None:
            if not isinstance(summary, dict) or not summary.get("job_id"):
                return
            job_summaries[str(summary["job_id"])] = summary

        for item in resources.get("runs") or []:
            add(
                ((item.get("summary") or {}).get("execution_job"))
                if isinstance(item, dict)
                else None
            )
        for item in resources.get("experiments") or []:
            if not isinstance(item, dict):
                continue
            add((item.get("summary") or {}).get("execution_job"))
            add((item.get("execution_job") or {}).get("summary"))
        for item in resources.get("research_objects") or []:
            if not isinstance(item, dict):
                continue
            research_object = item.get("research_object") or {}
            if isinstance(research_object, dict):
                add((research_object.get("executionJob") or {}).get("summary"))
                add((research_object.get("execution_job") or {}).get("summary"))
        return list(job_summaries.values())

    def _normalize_workspace_collaborators(
        self,
        collaborators: list[dict[str, Any]],
    ) -> list[dict]:
        if not isinstance(collaborators, list):
            raise ValueError("Workspace collaborators must be a list")
        if not collaborators:
            return [
                {
                    "collaborator_id": "local-user",
                    "display_name": "Local QS-DMSS user",
                    "role": "owner",
                }
            ]

        normalized: list[dict] = []
        for index, raw in enumerate(collaborators, start=1):
            if not isinstance(raw, dict):
                raise ValueError("Workspace collaborator entries must be objects")
            display_name = str(raw.get("display_name") or raw.get("name") or "").strip()
            if not display_name:
                raise ValueError("Workspace collaborator display_name is required")
            collaborator_id = safe_filename(
                str(raw.get("collaborator_id") or raw.get("id") or display_name),
                default=f"collaborator-{index}",
            )
            collaborator = {
                "collaborator_id": collaborator_id,
                "display_name": display_name,
                "role": str(raw.get("role") or "reviewer").strip() or "reviewer",
            }
            for key in ("affiliation", "location_label", "contact", "orcid"):
                value = raw.get(key)
                if value is not None and str(value).strip():
                    collaborator[key] = str(value).strip()
            normalized.append(collaborator)
        return normalized

    def _normalize_workspace_annotations(
        self,
        annotations: list[dict[str, Any]],
        collaborators: list[dict],
    ) -> list[dict]:
        if not isinstance(annotations, list):
            raise ValueError("Workspace annotations must be a list")
        allowed_targets = {
            "workspace",
            "run",
            "experiment",
            "campaign-study",
            "research-object",
            "job",
        }
        collaborator_ids = {
            str(collaborator["collaborator_id"])
            for collaborator in collaborators
            if collaborator.get("collaborator_id")
        }
        now = datetime.now(timezone.utc).isoformat()
        normalized: list[dict] = []
        for index, raw in enumerate(annotations, start=1):
            if not isinstance(raw, dict):
                raise ValueError("Workspace annotation entries must be objects")
            text = str(raw.get("text") or raw.get("body") or "").strip()
            if not text:
                raise ValueError("Workspace annotation text is required")
            target_type = str(raw.get("target_type") or "workspace").strip()
            if target_type not in allowed_targets:
                raise ValueError(
                    f"Unsupported workspace annotation target_type: {target_type}"
                )
            annotation_id = safe_filename(
                str(raw.get("annotation_id") or raw.get("id") or f"annotation-{index}"),
                default=f"annotation-{index}",
            )
            annotation = {
                "annotation_id": annotation_id,
                "target_type": target_type,
                "target_id": str(raw.get("target_id") or "workspace").strip()
                or "workspace",
                "text": text,
                "created_at": str(raw.get("created_at") or now),
                "tags": [
                    str(tag).strip()
                    for tag in (raw.get("tags") or [])
                    if str(tag).strip()
                ],
            }
            author_id = raw.get("author_collaborator_id") or raw.get("author")
            if author_id is not None and str(author_id).strip():
                author = safe_filename(str(author_id), default="collaborator")
                annotation["author_collaborator_id"] = author
                annotation["author_registered"] = author in collaborator_ids
            normalized.append(annotation)
        return normalized

    def _dedupe_text_values(self, values: list[str]) -> list[str]:
        deduped: dict[str, None] = {}
        for value in values:
            text = str(value).strip()
            if text:
                deduped[text] = None
        return list(deduped)

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))
