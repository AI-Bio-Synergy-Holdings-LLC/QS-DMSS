from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from qs_dmss.cockpit.api import CockpitService, create_app

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _workspace_record(
    workspace_id: str,
    *,
    title: str,
    imported_from_workspace_id: str | None = None,
) -> dict:
    record = {
        "schema_version": 1,
        "workspace_id": workspace_id,
        "title": title,
        "description": f"{title} description",
        "created_at": "2026-07-29T00:00:00+00:00",
        "updated_at": "2026-07-29T00:01:00+00:00",
        "collaborators": [
            {
                "collaborator_id": "reviewer",
                "display_name": "Research Reviewer",
                "role": "reviewer",
            }
        ],
        "annotations": [
            {
                "annotation_id": "note",
                "target_type": "workspace",
                "target_id": workspace_id,
                "text": "Review this workspace.",
                "created_at": "2026-07-29T00:00:30+00:00",
                "tags": ["review"],
            }
        ],
        "resources": {
            "runs": [{"summary": {"run_id": "run-a"}}],
            "experiments": [],
            "campaign_study_templates": [{"summary": {"template_id": "study-a"}}],
            "research_objects": [],
        },
        "job_summaries": [{"job_id": "job-a"}],
        "warnings": [
            {
                "resource_type": "experiment",
                "resource_id": "missing-experiment",
                "message": "Experiment not found",
            }
        ],
    }
    if imported_from_workspace_id is not None:
        record["imported_from_workspace_id"] = imported_from_workspace_id
    return record


def _workspace_summary(record: dict) -> dict:
    workspace_id = record["workspace_id"]
    return {
        "workspace_id": workspace_id,
        "title": record["title"],
        "description": record["description"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
        "imported_from_workspace_id": record.get("imported_from_workspace_id"),
        "run_count": 1,
        "experiment_count": 0,
        "campaign_study_template_count": 1,
        "research_object_count": 0,
        "collaborator_count": 1,
        "annotation_count": 1,
        "job_count": 1,
        "warning_count": 1,
        "urls": {
            "detail": f"/api/workspaces/{workspace_id}",
            "download": f"/api/workspaces/{workspace_id}/download",
        },
    }


def test_workspace_routes_preserve_listing_detail_download_and_error_contracts(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "runs"
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=output_root))
    workspace_root = tmp_path / "experiments" / "workspaces"

    old_record = _workspace_record("workspace-old", title="Older workspace")
    new_record = _workspace_record(
        "workspace-new",
        title="Newer workspace",
        imported_from_workspace_id="workspace-source",
    )
    old_path = workspace_root / "workspace-old" / "workspace.json"
    new_path = workspace_root / "workspace-new" / "workspace.json"
    _write_json(old_path, old_record)
    _write_json(new_path, new_record)
    (workspace_root / "ignored-without-marker").mkdir()
    _write_json(workspace_root / "ignored.json", {"workspace_id": "ignored"})
    os.utime(old_path, (100, 100))
    os.utime(new_path, (200, 200))

    openapi_paths = client.get("/openapi.json").json()["paths"]
    assert set(openapi_paths["/api/workspaces"]) == {"get"}
    assert set(openapi_paths["/api/workspaces/export"]) == {"post"}
    assert set(openapi_paths["/api/workspaces/import"]) == {"post"}
    assert set(openapi_paths["/api/workspaces/{workspace_id}"]) == {"get"}
    assert set(openapi_paths["/api/workspaces/{workspace_id}/download"]) == {"get"}

    listing = client.get("/api/workspaces")
    assert listing.status_code == 200
    assert listing.json() == {
        "items": [
            _workspace_summary(new_record),
            _workspace_summary(old_record),
        ]
    }

    detail = client.get("/api/workspaces/workspace-new")
    assert detail.status_code == 200
    assert detail.json() == {
        "summary": _workspace_summary(new_record),
        "workspace": new_record,
        "urls": {
            "detail": "/api/workspaces/workspace-new",
            "download": "/api/workspaces/workspace-new/download",
        },
    }

    download = client.get("/api/workspaces/workspace-new/download")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/json")
    assert 'filename="workspace.json"' in download.headers["content-disposition"]
    assert download.json() == new_record

    for path in (
        "/api/workspaces/missing-workspace",
        "/api/workspaces/missing-workspace/download",
    ):
        missing = client.get(path)
        assert missing.status_code == 404
        assert missing.json() == {"detail": "Workspace export not found"}

    service = CockpitService.create(
        repo_root=REPO_ROOT,
        output_root=tmp_path / "service-runs",
    )
    for workspace_id in ("missing-workspace", "../outside-workspaces"):
        with pytest.raises(HTTPException) as error:
            service.workspace_path(workspace_id)
        assert error.value.status_code == 404
        assert error.value.detail == "Workspace export not found"


def test_workspace_export_preserves_normalization_deduplication_and_warning_order(
    tmp_path: Path,
) -> None:
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=tmp_path / "runs"))

    response = client.post(
        "/api/workspaces/export",
        json={
            "title": "  Portable review workspace  ",
            "description": "  Bounded handoff context.  ",
            "collaborators": [
                {
                    "id": "Ada Reviewer",
                    "name": "  Ada Reviewer  ",
                    "role": " lead reviewer ",
                    "affiliation": "  Evidence Lab  ",
                },
                {
                    "display_name": "Ben Analyst",
                    "role": "",
                },
            ],
            "annotations": [
                {
                    "id": "Note 1",
                    "body": "  Inspect the declared boundary.  ",
                    "author": "Ada Reviewer",
                    "tags": [" review ", "", "boundary"],
                },
                {
                    "text": "Inspect the missing run warning.",
                    "target_type": "run",
                    "target_id": "missing-run-b",
                },
            ],
            "run_ids": ["missing-run-b", "missing-run-a", "missing-run-b", " "],
            "experiment_ids": ["missing-experiment", "missing-experiment"],
            "campaign_study_template_ids": ["missing-study", "missing-study"],
            "research_object_ids": ["missing-object", "missing-object"],
        },
    )

    assert response.status_code == 200
    detail = response.json()
    workspace = detail["workspace"]
    summary = detail["summary"]

    assert workspace["title"] == "Portable review workspace"
    assert workspace["description"] == "Bounded handoff context."
    assert workspace["collaborators"] == [
        {
            "collaborator_id": "Ada-Reviewer",
            "display_name": "Ada Reviewer",
            "role": "lead reviewer",
            "affiliation": "Evidence Lab",
        },
        {
            "collaborator_id": "Ben-Analyst",
            "display_name": "Ben Analyst",
            "role": "reviewer",
        },
    ]
    assert workspace["annotations"][0] == {
        "annotation_id": "Note-1",
        "target_type": "workspace",
        "target_id": "workspace",
        "text": "Inspect the declared boundary.",
        "created_at": workspace["annotations"][0]["created_at"],
        "tags": ["review", "boundary"],
        "author_collaborator_id": "Ada-Reviewer",
        "author_registered": True,
    }
    assert [item["annotation_id"] for item in workspace["annotations"]] == [
        "Note-1",
        "annotation-2",
    ]
    assert workspace["resources"] == {
        "runs": [],
        "experiments": [],
        "campaign_study_templates": [],
        "research_objects": [],
    }
    assert workspace["warnings"] == [
        {
            "resource_type": "run",
            "resource_id": "missing-run-b",
            "message": "Run not found",
        },
        {
            "resource_type": "run",
            "resource_id": "missing-run-a",
            "message": "Run not found",
        },
        {
            "resource_type": "experiment",
            "resource_id": "missing-experiment",
            "message": "Experiment not found",
        },
        {
            "resource_type": "campaign-study",
            "resource_id": "missing-study",
            "message": "Campaign study template not found",
        },
        {
            "resource_type": "research-object",
            "resource_id": "missing-object",
            "message": "Research object export not found",
        },
    ]
    assert summary == {
        "workspace_id": workspace["workspace_id"],
        "title": "Portable review workspace",
        "description": "Bounded handoff context.",
        "created_at": workspace["created_at"],
        "updated_at": workspace["updated_at"],
        "imported_from_workspace_id": None,
        "run_count": 0,
        "experiment_count": 0,
        "campaign_study_template_count": 0,
        "research_object_count": 0,
        "collaborator_count": 2,
        "annotation_count": 2,
        "job_count": 0,
        "warning_count": 5,
        "urls": {
            "detail": f"/api/workspaces/{workspace['workspace_id']}",
            "download": f"/api/workspaces/{workspace['workspace_id']}/download",
        },
    }

    download = client.get(detail["urls"]["download"])
    assert download.status_code == 200
    assert download.json() == workspace


def test_workspace_import_preserves_resource_and_job_order(
    tmp_path: Path,
) -> None:
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=tmp_path / "runs"))
    source_workspace = {
        "schema_version": 1,
        "workspace_id": "workspace-source",
        "title": "Imported collaboration",
        "resources": {
            "runs": [
                {
                    "summary": {
                        "run_id": "run-a",
                        "execution_job": {
                            "job_id": "job-a",
                            "source": "run",
                        },
                    }
                }
            ],
            "experiments": [
                {
                    "summary": {
                        "execution_job": {
                            "job_id": "job-b",
                            "source": "experiment-summary",
                        }
                    },
                    "execution_job": {
                        "summary": {
                            "job_id": "job-c",
                            "source": "experiment-detail",
                        }
                    },
                }
            ],
            "campaign_study_templates": [],
            "research_objects": [
                {
                    "research_object": {
                        "executionJob": {
                            "summary": {
                                "job_id": "job-a",
                                "source": "research-object-newer",
                            }
                        },
                        "execution_job": {
                            "summary": {
                                "job_id": "job-d",
                                "source": "research-object-snake-case",
                            }
                        },
                    }
                }
            ],
        },
        "collaborators": [],
        "annotations": [],
        "warnings": [],
    }

    response = client.post(
        "/api/workspaces/import",
        json={"workspace": source_workspace},
    )

    assert response.status_code == 200
    detail = response.json()
    workspace = detail["workspace"]
    assert workspace["workspace_id"] != "workspace-source"
    assert workspace["imported_from_workspace_id"] == "workspace-source"
    assert workspace["title"] == "Imported collaboration"
    assert workspace["collaborators"] == [
        {
            "collaborator_id": "local-user",
            "display_name": "Local QS-DMSS user",
            "role": "owner",
        }
    ]
    assert [job["job_id"] for job in workspace["job_summaries"]] == [
        "job-a",
        "job-b",
        "job-c",
        "job-d",
    ]
    assert workspace["job_summaries"][0]["source"] == "research-object-newer"
    assert detail["summary"]["run_count"] == 1
    assert detail["summary"]["experiment_count"] == 1
    assert detail["summary"]["research_object_count"] == 1
    assert detail["summary"]["job_count"] == 4
    assert detail["imported_campaign_studies"] == []


@pytest.mark.parametrize(
    ("workspace", "detail"),
    (
        (
            {"workspace_id": "source", "resources": ["not", "an", "object"]},
            "Workspace resources must be an object",
        ),
        (
            {
                "workspace_id": "source",
                "resources": {},
                "collaborators": "not-a-list",
            },
            "Workspace collaborators must be a list",
        ),
        (
            {
                "workspace_id": "source",
                "resources": {},
                "annotations": "not-a-list",
            },
            "Workspace annotations must be a list",
        ),
        (
            {
                "workspace_id": "source",
                "resources": {"campaign_study_templates": "not-a-list"},
            },
            "Workspace campaign study templates must be a list",
        ),
        (
            {
                "workspace_id": "source",
                "resources": {},
                "annotations": [
                    {
                        "target_type": "remote-shell",
                        "text": "Unsupported target.",
                    }
                ],
            },
            "Unsupported workspace annotation target_type: remote-shell",
        ),
    ),
)
def test_workspace_import_preserves_exact_validation_errors(
    tmp_path: Path,
    workspace: dict,
    detail: str,
) -> None:
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=tmp_path / "runs"))

    response = client.post(
        "/api/workspaces/import",
        json={"workspace": workspace},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": detail}


def test_hosted_workspace_mutations_preserve_exact_forbidden_errors(
    tmp_path: Path,
) -> None:
    client = TestClient(
        create_app(
            repo_root=REPO_ROOT,
            output_root=tmp_path / "runs",
            hosted_demo=True,
        )
    )

    export = client.post(
        "/api/workspaces/export",
        json={"title": "Hosted workspace"},
    )
    assert export.status_code == 403
    assert export.json() == {
        "detail": (
            "Hosted demo disables workspace snapshots because public outputs are temporary. "
            "Use research-object export here, or install QS-DMSS locally for workspace export."
        )
    }

    imported = client.post(
        "/api/workspaces/import",
        json={"workspace": {"workspace_id": "source"}},
    )
    assert imported.status_code == 403
    assert imported.json() == {
        "detail": (
            "Hosted demo does not accept uploaded workspace JSON. "
            "Install QS-DMSS locally to import collaborator workspaces."
        )
    }
