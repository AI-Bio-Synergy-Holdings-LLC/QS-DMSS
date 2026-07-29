from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import qs_dmss.cockpit.api as cockpit_api
from qs_dmss.cockpit.api import CockpitService, create_app

REPO_ROOT = Path(__file__).resolve().parents[1]


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 7, 29, 12, 0, 0, tzinfo=tz or timezone.utc)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _campaign_record(
    template_id: str,
    *,
    label: str,
    packaged: bool = False,
    imported_from_template_id: str | None = None,
) -> dict:
    record = {
        "schema_version": 1,
        "template_id": template_id,
        "label": label,
        "description": f"{label} description",
        "created_at": "2026-07-29T10:00:00Z",
        "updated_at": "2026-07-29T10:01:00Z",
        "source_config_name": f"{template_id}.yaml",
        "campaign": {
            "label": f"{label} campaign",
            "strategy": "grid",
            "planned_run_count": 2,
            "dimension_count": 1,
        },
        "objective": {
            "name": f"{label} objective",
            "primary_metric": "energy_drift",
            "goal": "minimize_abs",
        },
        "config": {"run": {"name": template_id}},
    }
    if packaged:
        record["packaged"] = True
    if imported_from_template_id is not None:
        record["imported_from_template_id"] = imported_from_template_id
    return record


def _campaign_summary(record: dict) -> dict:
    template_id = record["template_id"]
    campaign = record["campaign"]
    objective = record["objective"]
    packaged = bool(record.get("packaged"))
    return {
        "template_id": template_id,
        "label": record["label"],
        "description": record["description"],
        "purpose": record.get("purpose"),
        "expected_runtime": record.get("expected_runtime"),
        "metrics": record.get("metrics") or [],
        "limitations": record.get("limitations") or [],
        "non_claims": record.get("non_claims") or [],
        "interpretation": record.get("interpretation") or {},
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
        "source_config_name": record["source_config_name"],
        "campaign_label": campaign["label"],
        "strategy": "grid",
        "planned_run_count": 2,
        "dimension_count": 1,
        "objective_name": objective["name"],
        "primary_metric": objective["primary_metric"],
        "goal": objective["goal"],
        "packaged": packaged,
        "origin": "packaged" if packaged else "local",
        "imported": bool(record.get("imported_from_template_id")),
        "imported_from_template_id": record.get("imported_from_template_id"),
        "exportable": True,
        "last_run": None,
        "urls": {
            "detail": f"/api/campaign-studies/{template_id}",
            "download": f"/api/campaign-studies/{template_id}/download",
        },
    }


def _two_variant_config(client: TestClient, values: list[float]) -> dict:
    template = client.get(
        "/api/campaign-studies/self-interaction-sweep"
    ).json()["template"]
    config = deepcopy(template["config"])
    config["campaign"]["max_runs"] = len(values)
    config["campaign"]["dimensions"] = [
        {"path": "engine.g_int", "values": values}
    ]
    return config


def test_campaign_routes_preserve_precedence_order_payloads_and_errors(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "runs"
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=output_root))
    campaign_root = tmp_path / "experiments" / "campaign-studies"

    packaged_override = _campaign_record(
        "self-interaction-sweep",
        label="Locally reviewed packaged study",
    )
    older_local = _campaign_record("local-older", label="Older local study")
    newer_local = _campaign_record(
        "local-newer",
        label="Newer imported study",
        imported_from_template_id="external-study",
    )
    override_path = campaign_root / "self-interaction-sweep.json"
    older_path = campaign_root / "local-older.json"
    newer_path = campaign_root / "local-newer.json"
    _write_json(override_path, packaged_override)
    _write_json(older_path, older_local)
    _write_json(newer_path, newer_local)
    _write_json(campaign_root / "ignored-without-template-id.json", {"label": "Ignored"})
    os.utime(older_path, (100, 100))
    os.utime(newer_path, (200, 200))
    os.utime(override_path, (300, 300))

    openapi_paths = client.get("/openapi.json").json()["paths"]
    assert set(openapi_paths["/api/campaign-studies"]) == {"get", "post"}
    assert set(openapi_paths["/api/campaign-studies/import"]) == {"post"}
    assert set(openapi_paths["/api/campaign-studies/{template_id}"]) == {"get"}
    assert set(
        openapi_paths["/api/campaign-studies/{template_id}/download"]
    ) == {"get"}
    assert set(openapi_paths["/api/campaigns"]) == {"post"}

    listing = client.get("/api/campaign-studies")
    assert listing.status_code == 200
    assert listing.json() == {
        "items": [
            _campaign_summary(packaged_override),
            _campaign_summary(newer_local),
            _campaign_summary(older_local),
        ]
    }

    detail = client.get("/api/campaign-studies/self-interaction-sweep")
    assert detail.status_code == 200
    assert detail.json() == {
        "summary": _campaign_summary(packaged_override),
        "template": packaged_override,
        "urls": {
            "detail": "/api/campaign-studies/self-interaction-sweep",
            "download": (
                "/api/campaign-studies/self-interaction-sweep/download"
            ),
        },
    }

    download = client.get(
        "/api/campaign-studies/self-interaction-sweep/download"
    )
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/json")
    assert (
        'filename="self-interaction-sweep.json"'
        in download.headers["content-disposition"]
    )
    assert download.json() == packaged_override

    for path in (
        "/api/campaign-studies/missing-template",
        "/api/campaign-studies/missing-template/download",
    ):
        missing = client.get(path)
        assert missing.status_code == 404
        assert missing.json() == {
            "detail": "Campaign study template not found"
        }

    service = CockpitService.create(
        repo_root=REPO_ROOT,
        output_root=tmp_path / "service-runs",
    )
    for template_id in ("missing-template", "../outside-campaigns"):
        with pytest.raises(HTTPException) as error:
            service.campaign_study_template_path(template_id)
        assert error.value.status_code == 404
        assert error.value.detail == "Campaign study template not found"


def test_campaign_save_import_preserve_ids_normalization_and_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(cockpit_api, "datetime", FixedDateTime)
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=tmp_path / "runs"))
    config = _two_variant_config(client, [0.08, 0.02])
    config["objective"] = {
        "name": "Density-first boundary",
        "summary": "Prefer stronger density within the declared constraints.",
        "primary_metric": "max_density",
        "goal": "maximize",
    }
    config["constraints"] = {
        "require_verification": True,
        "max_abs_energy_drift": 0.5,
    }
    config["ranking"] = {
        "primary_metric_weight": 3.0,
        "weights": {
            "energy_drift": 0.0,
            "norm_drift": 0.0,
            "max_density": 1.0,
            "elapsed_seconds": 0.0,
        },
    }
    request_template = {
        "label": "  Density First Study  ",
        "description": "  Portable two-variant review.  ",
        "source_config_name": "../unsafe-name",
        "purpose": "Preserve a bounded comparison design.",
        "metrics": [{"label": "Max density"}],
        "limitations": ["Not a calibrated physical result."],
        "non_claims": ["Not a scientific verdict."],
        "interpretation": {"summary": "Compare the two evidence rows."},
        "config": config,
    }

    first = client.post(
        "/api/campaign-studies",
        json={"template": request_template},
    )
    second = client.post(
        "/api/campaign-studies",
        json={"template": request_template},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    first_detail = first.json()
    second_detail = second.json()
    assert first_detail["summary"]["template_id"] == (
        "density-first-study-20260729T120000Z"
    )
    assert second_detail["summary"]["template_id"] == (
        "density-first-study-20260729T120000Z-2"
    )
    assert first_detail["summary"] == _campaign_summary(
        first_detail["template"]
    )

    saved = first_detail["template"]
    assert saved["label"] == "Density First Study"
    assert saved["description"] == "Portable two-variant review."
    assert saved["created_at"] == "2026-07-29T12:00:00Z"
    assert saved["updated_at"] == "2026-07-29T12:00:00Z"
    assert saved["source_config_name"] == "unsafe-name.yaml"
    assert saved["campaign"]["planned_run_count"] == 2
    assert saved["campaign"]["dimensions"][0]["values"] == [0.08, 0.02]
    assert saved["scoring_contract"]["objective"] == config["objective"]
    assert saved["scoring_contract"]["constraints"] == config["constraints"]
    assert saved["scoring_contract"]["ranking"] == config["ranking"]
    assert saved["purpose"] == request_template["purpose"]
    assert saved["metrics"] == request_template["metrics"]
    assert saved["limitations"] == request_template["limitations"]
    assert saved["non_claims"] == request_template["non_claims"]
    assert saved["interpretation"] == request_template["interpretation"]

    imported = client.post(
        "/api/campaign-studies/import",
        json={"template": saved},
    )
    assert imported.status_code == 200
    imported_detail = imported.json()
    assert imported_detail["summary"]["template_id"] == (
        "density-first-study-20260729T120000Z-3"
    )
    assert imported_detail["summary"]["imported"] is True
    assert imported_detail["summary"]["imported_from_template_id"] == (
        first_detail["summary"]["template_id"]
    )
    assert imported_detail["template"]["config"] == saved["config"]


@pytest.mark.parametrize(
    ("template", "detail"),
    (
        (
            {"label": "Missing config"},
            "Campaign study template requires a config object",
        ),
        (
            {
                "label": "Invalid grid",
                "config": {
                    "run": {"name": "invalid", "seed": 7},
                    "engine": {
                        "backend": "numpy",
                        "grid_shape": [4, 4, 4],
                        "box_size": 1.0,
                        "mass": 1.0,
                        "g_int": 0.05,
                        "time_step": 0.02,
                        "num_steps": 2,
                        "log_every": 1,
                    },
                    "initial": {
                        "kind": "gaussian",
                        "amplitude": 0.35,
                        "width": 0.2,
                        "random_phase": True,
                    },
                    "objective": {
                        "name": "Invalid one-run campaign",
                        "primary_metric": "energy_drift",
                        "goal": "minimize_abs",
                    },
                    "campaign": {
                        "label": "Invalid grid",
                        "strategy": "grid",
                        "dimensions": [
                            {"path": "engine.g_int", "values": [0.05]}
                        ],
                    },
                },
            },
            "Campaign requires at least two planned runs",
        ),
    ),
)
def test_campaign_save_preserves_exact_validation_errors(
    tmp_path: Path,
    template: dict,
    detail: str,
) -> None:
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=tmp_path / "runs"))

    response = client.post(
        "/api/campaign-studies",
        json={"template": template},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": detail}


def test_campaign_preview_preserves_empty_catalog_contract(tmp_path: Path) -> None:
    service = CockpitService.create(
        repo_root=REPO_ROOT,
        output_root=tmp_path / "runs",
    )
    empty_config_root = tmp_path / "empty-configs"
    empty_config_root.mkdir()
    service = replace(service, config_root=empty_config_root)

    assert service.campaign_studio_preview() == {
        "available": False,
        "title": "Campaign Studio",
        "summary": "No packaged config is available for a campaign preview.",
        "current_boundary": (
            "Add a config with objective and campaign sections to enable "
            "Campaign Studio."
        ),
        "next_capabilities": [
            "Scenario-linked campaign templates",
            "Editable parameter-grid studies",
            "Decision-profile editing",
        ],
    }


def test_campaign_launch_preserves_variant_and_response_order(
    tmp_path: Path,
) -> None:
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=tmp_path / "runs"))
    config = _two_variant_config(client, [0.08, 0.02])

    response = client.post(
        "/api/campaigns",
        json={"config": config, "source_name": "../ordered-campaign"},
    )

    assert response.status_code == 200
    campaign = response.json()
    assert list(campaign) == [
        "campaign",
        "runs",
        "comparison",
        "guide",
        "artifact",
        "execution_job",
        "study_template",
    ]
    assert [
        run["experiment"]["ordinal"] for run in campaign["runs"]
    ] == [1, 2]
    assert [
        run["experiment"]["parameter_value"] for run in campaign["runs"]
    ] == [0.08, 0.02]
    assert campaign["campaign"]["run_ids"] == [
        run["run_id"] for run in campaign["runs"]
    ]
    assert [
        row["run_id"] for row in campaign["comparison"]["rows"]
    ] == campaign["campaign"]["run_ids"]
    assert campaign["study_template"] is None
    assert campaign["guide"]["what_changed"][0].startswith(
        "Energy drift span across completed variants:"
    )
    assert campaign["execution_job"]["summary"]["state"] == "succeeded"


def test_campaign_launch_preserves_failed_artifact_error_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = TestClient(create_app(repo_root=REPO_ROOT, output_root=tmp_path / "runs"))
    config = _two_variant_config(client, [0.08, 0.02])
    real_execute = cockpit_api.execute_run
    call_count = 0

    def flaky_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("characterized variant failure")
        return real_execute(*args, **kwargs)

    monkeypatch.setattr(cockpit_api, "execute_run", flaky_execute)
    response = client.post(
        "/api/campaigns",
        json={"config": config, "source_name": "failing-campaign.yaml"},
    )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert list(detail) == [
        "message",
        "error",
        "experiment_id",
        "run_ids",
        "bundle",
        "report",
    ]
    assert detail["message"] == (
        "Campaign failed; a failed campaign artifact was saved."
    )
    assert detail["error"] == "characterized variant failure"
    assert len(detail["run_ids"]) == 1
    assert detail["bundle"].endswith("/bundle")
    assert detail["report"].endswith("/report")


def test_hosted_campaign_mutations_preserve_exact_forbidden_errors(
    tmp_path: Path,
) -> None:
    client = TestClient(
        create_app(
            repo_root=REPO_ROOT,
            output_root=tmp_path / "runs",
            hosted_demo=True,
        )
    )
    packaged = client.get(
        "/api/campaign-studies/self-interaction-sweep"
    ).json()["template"]

    saved = client.post(
        "/api/campaign-studies",
        json={"template": packaged},
    )
    assert saved.status_code == 403
    assert saved.json() == {
        "detail": (
            "Hosted demo keeps study templates packaged and temporary. "
            "Install QS-DMSS locally to save custom study templates."
        )
    }

    imported = client.post(
        "/api/campaign-studies/import",
        json={"template": packaged},
    )
    assert imported.status_code == 403
    assert imported.json() == {
        "detail": (
            "Hosted demo does not accept uploaded study templates. "
            "Install QS-DMSS locally to import portable campaign designs."
        )
    }

    custom_campaign = client.post(
        "/api/campaigns",
        json={
            "config": packaged["config"],
            "source_name": packaged["source_config_name"],
        },
    )
    assert custom_campaign.status_code == 403
    assert custom_campaign.json() == {
        "detail": (
            "Hosted demo only runs the packaged Self-Interaction Sweep template. "
            "Install QS-DMSS locally to edit or launch custom campaigns."
        )
    }
