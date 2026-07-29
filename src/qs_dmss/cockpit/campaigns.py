from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable

from fastapi import HTTPException

from qs_dmss.io.config import (
    SUPPORTED_DECISION_METRICS,
    SUPPORTED_OBJECTIVE_GOALS,
    parse_config,
)
from qs_dmss.paths import contained_path, safe_filename

CampaignCallable = Callable[..., Any]
CampaignClock = Callable[[], datetime]


@dataclass(frozen=True)
class CampaignLaunchSpec:
    config: dict[str, Any]
    source_name: str = "campaign.yaml"
    study_template_id: str | None = None


@dataclass(frozen=True)
class CockpitCampaignService:
    """Own Campaign Studio persistence and execution behind stable contracts."""

    output_root: Path
    experiments_root: Path
    packaged_studies_root: Path
    hosted_demo_enabled: bool
    hosted_template_id: str
    list_configs: CampaignCallable
    safe_source_name: Callable[[str], str]
    temp_source_path: Callable[[Path, str], Path]
    start_parent_job: CampaignCallable
    job_reference: CampaignCallable
    complete_experiment_job: CampaignCallable
    fail_parent_job: CampaignCallable
    build_run_detail: CampaignCallable
    build_experiment_detail: CampaignCallable
    execute_variant: CampaignCallable
    plan_campaign: CampaignCallable
    build_campaign_context: CampaignCallable
    compare_runs: CampaignCallable
    persist_experiment: CampaignCallable
    persist_failed_campaign: CampaignCallable
    assert_hosted_config_envelope: CampaignCallable
    now: CampaignClock

    def campaign_studio_preview(self) -> dict:
        configs = self.list_configs()
        default_config = configs[0] if configs else None
        if default_config is None:
            return {
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

        config = default_config["config"]
        try:
            campaign_plan = self.plan_campaign(config)
        except ValueError:
            return {
                "available": False,
                "title": "Campaign Studio",
                "source_config_name": default_config["name"],
                "summary": (
                    "The default config is not a launchable campaign study yet."
                ),
                "current_boundary": (
                    "This config can launch a run, but it does not define an "
                    "automated campaign."
                ),
                "next_capabilities": [
                    "Add a campaign section",
                    "Attach objective constraints",
                    "Save a comparison research object",
                ],
            }

        objective = config.get("objective") or {}
        constraints = {
            "require_verification": True,
            **(config.get("constraints") or {}),
        }
        ranking = config.get("ranking") or {}
        return {
            "available": True,
            "title": "Campaign Studio",
            "source_config_name": default_config["name"],
            "label": campaign_plan["label"],
            "strategy": campaign_plan["strategy"],
            "max_runs": config.get("campaign", {}).get(
                "max_runs",
                campaign_plan["planned_run_count"],
            ),
            "planned_run_count": campaign_plan["planned_run_count"],
            "dimension_count": campaign_plan["dimension_count"],
            "dimensions": campaign_plan["dimensions"],
            "objective": {
                "name": objective.get("name", "No objective"),
                "summary": objective.get(
                    "summary",
                    "No objective summary provided.",
                ),
                "primary_metric": objective.get("primary_metric"),
                "goal": objective.get("goal"),
                "target_value": objective.get("target_value"),
                "supported_metrics": list(SUPPORTED_DECISION_METRICS),
                "supported_goals": list(SUPPORTED_OBJECTIVE_GOALS),
            },
            "constraint_values": constraints,
            "constraints": [
                {"name": key, "value": value}
                for key, value in constraints.items()
            ],
            "ranking": {
                "primary_metric_weight": ranking.get(
                    "primary_metric_weight"
                ),
                "weights": ranking.get("weights", {}),
            },
            "readiness_badges": [
                {"label": "Grid plan", "status": "ready"},
                {"label": "Objective scoring", "status": "ready"},
                {"label": "Evidence bundle", "status": "ready"},
                {"label": "Grid editor", "status": "ready"},
                {"label": "Objective editor", "status": "ready"},
                {"label": "Study templates", "status": "ready"},
            ],
            "summary": (
                "A packaged decision campaign can already expand a template into a "
                "multi-run search matrix, score every run, save reusable study "
                "templates, and export a comparison bundle."
            ),
            "current_boundary": (
                "Campaign Studio now edits, saves, reopens, imports, and exports "
                "reusable campaign study templates with the scoring contract "
                "attached."
            ),
            "next_capabilities": [
                "Richer template library metadata",
                "Template-to-publication export provenance",
                "Team-shared study template registries",
            ],
            "launch_endpoint": "/api/campaigns",
        }

    def list_campaign_study_templates(self) -> list[dict]:
        local_records: list[dict] = [
            self._read_json(path)
            for path in self._list_campaign_study_template_paths()
        ]
        local_records_by_id = {
            record["template_id"]: record
            for record in local_records
            if record.get("template_id")
        }
        packaged_ids: set[str] = set()
        summaries: list[dict] = []

        for packaged_path in self._list_packaged_campaign_study_template_paths():
            packaged_record = self._read_json(packaged_path)
            template_id = packaged_record.get("template_id")
            if not template_id:
                continue
            packaged_ids.add(template_id)
            summaries.append(
                self._build_campaign_study_summary(
                    local_records_by_id.get(template_id, packaged_record),
                )
            )

        for record in local_records:
            template_id = record.get("template_id")
            if template_id and template_id not in packaged_ids:
                summaries.append(self._build_campaign_study_summary(record))

        return summaries

    def get_campaign_study_template(self, template_id: str) -> dict:
        path = self._get_campaign_study_template_path(template_id)
        return self._build_campaign_study_detail(path)

    def campaign_study_template_path(self, template_id: str) -> Path:
        return self._get_campaign_study_template_path(template_id)

    def save_campaign_study_template(
        self,
        template: dict[str, Any],
    ) -> dict:
        if self.hosted_demo_enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo keeps study templates packaged and temporary. "
                    "Install QS-DMSS locally to save custom study templates."
                ),
            )
        try:
            record = self._normalize_campaign_study_template(template)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        path = contained_path(
            self._campaign_studies_root(create=True),
            f"{record['template_id']}.json",
        )
        path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return self._build_campaign_study_detail(path)

    def import_campaign_study_template(
        self,
        source_template: dict[str, Any],
    ) -> dict:
        if self.hosted_demo_enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo does not accept uploaded study templates. "
                    "Install QS-DMSS locally to import portable campaign designs."
                ),
            )
        template = dict(source_template)
        imported_from = template.get("template_id")
        if imported_from:
            template["imported_from_template_id"] = str(imported_from)
        return self.save_campaign_study_template(template)

    def launch_campaign(self, payload: CampaignLaunchSpec) -> dict:
        try:
            base_config = parse_config(payload.config).to_dict()
            campaign_plan = self.plan_campaign(base_config)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        self._assert_hosted_packaged_campaign(
            payload,
            base_config,
            campaign_plan,
        )

        study_template_path = None
        study_template_record = None
        if payload.study_template_id:
            study_template_path = (
                self._ensure_local_campaign_study_template_path(
                    payload.study_template_id,
                )
            )
            study_template_record = self._read_json(study_template_path)

        run_dirs: list[Path] = []
        summaries: list[dict] = []
        details: list[dict] = []
        parent_handle = self.start_parent_job(
            config=base_config,
            source_name=payload.source_name,
            experiment={
                "id": campaign_plan["id"],
                "kind": "campaign",
                "label": campaign_plan["label"],
                "strategy": campaign_plan["strategy"],
                "planned_run_count": campaign_plan["planned_run_count"],
            },
            labels=("experiment", "campaign", "multi-run"),
            metadata={
                "dimension_count": campaign_plan["dimension_count"],
                "planned_run_count": campaign_plan["planned_run_count"],
                "study_template_id": payload.study_template_id,
            },
            message="Local campaign job started.",
        )
        try:
            with TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                for variant in campaign_plan["variants"]:
                    temp_config_dir = (
                        temp_root / f"run-{variant['ordinal']:02d}"
                    )
                    temp_config_dir.mkdir(parents=True, exist_ok=True)
                    temp_path = self.temp_source_path(
                        temp_config_dir,
                        payload.source_name,
                    )
                    outputs = self.execute_variant(
                        config=parse_config(variant["config"]),
                        source_config_path=temp_path,
                        output_root=self.output_root,
                        experiment=self.build_campaign_context(
                            experiment_id=campaign_plan["id"],
                            label=campaign_plan["label"],
                            strategy=campaign_plan["strategy"],
                            dimensions=campaign_plan["dimensions"],
                            variant=variant["variant"],
                            ordinal=variant["ordinal"],
                            total_runs=campaign_plan["planned_run_count"],
                        ),
                    )
                    run_dirs.append(outputs.run_dir)
                    detail = self.build_run_detail(outputs.run_dir)
                    details.append(detail)
                    summaries.append(detail["summary"])
        except Exception as exc:
            try:
                failure_outputs = self.persist_failed_campaign(
                    campaign_plan=campaign_plan,
                    run_dirs=run_dirs,
                    run_details=details,
                    experiments_root=self.experiments_root,
                    error=exc,
                    execution_job=self.job_reference(parent_handle),
                )
                self.complete_experiment_job(
                    parent_handle,
                    experiment_id=failure_outputs.experiment_id,
                    experiment_dir=failure_outputs.experiment_dir,
                    bundle_path=failure_outputs.bundle_path,
                    run_details=details,
                    state="failed",
                    message=(
                        "Campaign job failed; partial artifact was saved."
                    ),
                    error=exc,
                )
                failure_detail = self.build_experiment_detail(
                    failure_outputs.experiment_dir
                )
            except Exception as persist_exc:
                self.fail_parent_job(parent_handle, persist_exc)
                raise HTTPException(
                    status_code=500,
                    detail={
                        "message": (
                            "Campaign failed, and the failed campaign artifact "
                            "could not be saved."
                        ),
                        "error": str(exc),
                        "artifact_error": str(persist_exc),
                        "completed_run_ids": [
                            summary["run_id"] for summary in summaries
                        ],
                    },
                ) from persist_exc
            raise HTTPException(
                status_code=500,
                detail={
                    "message": (
                        "Campaign failed; a failed campaign artifact was saved."
                    ),
                    "error": str(exc),
                    "experiment_id": failure_detail["summary"][
                        "experiment_id"
                    ],
                    "run_ids": failure_detail["summary"]["run_ids"],
                    "bundle": failure_detail["urls"]["bundle"],
                    "report": failure_detail["urls"]["report"],
                },
            ) from exc

        try:
            comparison = self.compare_runs(details)
            artifact_outputs = self.persist_experiment(
                run_dirs=run_dirs,
                run_details=details,
                experiments_root=self.experiments_root,
                label=campaign_plan["label"],
                experiment_id=campaign_plan["id"],
                kind="campaign",
                execution_job=self.job_reference(parent_handle),
            )
            self.complete_experiment_job(
                parent_handle,
                experiment_id=artifact_outputs.experiment_id,
                experiment_dir=artifact_outputs.experiment_dir,
                bundle_path=artifact_outputs.bundle_path,
                run_details=details,
                message="Campaign job completed.",
            )
        except Exception as exc:
            self.fail_parent_job(parent_handle, exc)
            raise
        artifact = self.build_experiment_detail(
            artifact_outputs.experiment_dir
        )
        campaign_summary = {
            "id": campaign_plan["id"],
            "label": campaign_plan["label"],
            "strategy": campaign_plan["strategy"],
            "dimension_count": campaign_plan["dimension_count"],
            "planned_run_count": campaign_plan["planned_run_count"],
            "dimensions": campaign_plan["dimensions"],
            "run_ids": [summary["run_id"] for summary in summaries],
            "recommended_run_id": (comparison.get("decision") or {}).get(
                "recommended_run_id"
            ),
        }
        study_template = None
        if study_template_path is not None:
            study_template = self._record_campaign_study_last_run(
                study_template_path,
                campaign_summary=campaign_summary,
                comparison=comparison,
                artifact=artifact,
                run_count=len(summaries),
            )

        return {
            "campaign": campaign_summary,
            "runs": summaries,
            "comparison": comparison,
            "guide": self._build_campaign_study_guide(
                study_template_record,
                comparison,
            ),
            "artifact": artifact,
            "execution_job": artifact["execution_job"],
            "study_template": study_template,
        }

    def _assert_hosted_packaged_campaign(
        self,
        payload: CampaignLaunchSpec,
        base_config: dict[str, Any],
        campaign_plan: dict[str, Any],
    ) -> None:
        if not self.hosted_demo_enabled:
            return
        if payload.study_template_id != self.hosted_template_id:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo only runs the packaged Self-Interaction Sweep "
                    "template. Install QS-DMSS locally to edit or launch custom "
                    "campaigns."
                ),
            )
        packaged_template = self._read_json(
            self._get_campaign_study_template_path(
                self.hosted_template_id,
            ),
        )
        packaged_config = parse_config(
            packaged_template.get("config")
        ).to_dict()
        if base_config != packaged_config:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo does not run edited Campaign Studio payloads. "
                    "Use the packaged Self-Interaction Sweep or install QS-DMSS "
                    "locally."
                ),
            )
        self.assert_hosted_config_envelope(
            base_config,
            planned_run_count=campaign_plan["planned_run_count"],
        )

    def _campaign_studies_root(self, *, create: bool = False) -> Path:
        studies_root = self.experiments_root / "campaign-studies"
        if create:
            studies_root.mkdir(parents=True, exist_ok=True)
        return studies_root

    def _list_campaign_study_template_paths(self) -> list[Path]:
        studies_root = self._campaign_studies_root()
        if not studies_root.exists():
            return []
        return sorted(
            [
                path
                for path in studies_root.glob("*.json")
                if path.is_file()
            ],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def _list_packaged_campaign_study_template_paths(self) -> list[Path]:
        if not self.packaged_studies_root.exists():
            return []
        return sorted(
            [
                path
                for path in self.packaged_studies_root.glob("*.json")
                if path.is_file()
            ],
            key=lambda path: path.name,
        )

    def _get_campaign_study_template_path(
        self,
        template_id: str,
    ) -> Path:
        template_name = safe_filename(
            template_id,
            default="campaign-study",
            suffixes=(".json",),
        )
        local_path = contained_path(
            self._campaign_studies_root(),
            template_name,
        )
        if local_path.exists() and local_path.is_file():
            return local_path

        packaged_path = contained_path(
            self.packaged_studies_root,
            template_name,
        )
        if packaged_path.exists() and packaged_path.is_file():
            return packaged_path

        raise HTTPException(
            status_code=404,
            detail="Campaign study template not found",
        )

    def _ensure_local_campaign_study_template_path(
        self,
        template_id: str,
    ) -> Path:
        template_name = safe_filename(
            template_id,
            default="campaign-study",
            suffixes=(".json",),
        )
        studies_root = self._campaign_studies_root(create=True)
        local_path = contained_path(studies_root, template_name)
        if local_path.exists() and local_path.is_file():
            return local_path

        source_path = self._get_campaign_study_template_path(template_id)
        record = self._read_json(source_path)
        now = self._utc_now_z()
        record.setdefault("created_at", now)
        record["updated_at"] = now
        if record.get("packaged"):
            record["installed_from_packaged_template"] = True
        local_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return local_path

    def _campaign_study_template_id(self, label: str) -> str:
        timestamp = self.now().strftime("%Y%m%dT%H%M%SZ")
        stem = safe_filename(
            label.lower().replace(" ", "-"),
            default="campaign-study",
        )
        base_id = f"{stem}-{timestamp}"
        template_id = base_id
        index = 2
        studies_root = self._campaign_studies_root(create=True)
        while contained_path(
            studies_root,
            f"{template_id}.json",
        ).exists():
            template_id = f"{base_id}-{index}"
            index += 1
        return template_id

    def _normalize_campaign_study_template(
        self,
        template: dict[str, Any],
    ) -> dict:
        if not isinstance(template, dict):
            raise ValueError("Campaign study template must be an object")
        raw_config = template.get("config")
        if not isinstance(raw_config, dict):
            raise ValueError(
                "Campaign study template requires a config object"
            )

        config = parse_config(raw_config).to_dict()
        campaign_plan = self.plan_campaign(config)
        objective = config.get("objective") or {}
        constraints = {
            "require_verification": True,
            **(config.get("constraints") or {}),
        }
        ranking = config.get("ranking") or {}
        label = str(
            template.get("label")
            or campaign_plan["label"]
            or "Campaign Studio study template"
        ).strip()
        if not label:
            label = "Campaign Studio study template"
        description = str(
            template.get("description")
            or objective.get("summary")
            or "Reusable Campaign Studio study template."
        ).strip()
        source_config_name = self.safe_source_name(
            str(
                template.get("source_config_name")
                or "campaign-study.yaml"
            )
        )
        now = self._utc_now_z()
        campaign = {
            "label": campaign_plan["label"],
            "strategy": campaign_plan["strategy"],
            "max_runs": config.get("campaign", {}).get(
                "max_runs",
                campaign_plan["planned_run_count"],
            ),
            "planned_run_count": campaign_plan["planned_run_count"],
            "dimension_count": campaign_plan["dimension_count"],
            "dimensions": campaign_plan["dimensions"],
        }
        scoring_contract = {
            "objective": objective,
            "constraints": constraints,
            "ranking": {
                "primary_metric_weight": ranking.get(
                    "primary_metric_weight"
                ),
                "weights": ranking.get("weights", {}),
            },
            "planned_run_count": campaign_plan["planned_run_count"],
            "max_runs": campaign["max_runs"],
        }

        record: dict[str, Any] = {
            "schema_version": 1,
            "template_id": self._campaign_study_template_id(label),
            "label": label,
            "description": description,
            "created_at": now,
            "updated_at": now,
            "source_config_name": source_config_name,
            "campaign": campaign,
            "objective": objective,
            "constraints": constraints,
            "ranking": scoring_contract["ranking"],
            "scoring_contract": scoring_contract,
            "config": config,
        }
        for key in (
            "purpose",
            "expected_runtime",
            "metrics",
            "limitations",
            "non_claims",
            "interpretation",
        ):
            if key in template:
                record[key] = template[key]
        if template.get("packaged"):
            record["packaged"] = True
        if template.get("imported_from_template_id"):
            record["imported_from_template_id"] = str(
                template["imported_from_template_id"]
            )
        if template.get("imported_from_workspace_id"):
            record["imported_from_workspace_id"] = str(
                template["imported_from_workspace_id"]
            )
        return record

    def _record_campaign_study_last_run(
        self,
        path: Path,
        *,
        campaign_summary: dict,
        comparison: dict,
        artifact: dict,
        run_count: int,
    ) -> dict:
        record = self._read_json(path)
        decision = comparison.get("decision") or {}
        now = self._utc_now_z()
        last_run = {
            "ran_at": now,
            "status": "completed",
            "campaign_id": campaign_summary["id"],
            "campaign_label": campaign_summary["label"],
            "strategy": campaign_summary["strategy"],
            "planned_run_count": campaign_summary["planned_run_count"],
            "run_count": run_count,
            "run_ids": campaign_summary["run_ids"],
            "recommended_run_id": campaign_summary.get(
                "recommended_run_id"
            ),
            "decision_status": decision.get("status"),
            "recommended_score": decision.get("recommended_score"),
            "reason": decision.get("reason"),
            "experiment_id": artifact["summary"]["experiment_id"],
            "experiment_report_url": artifact["urls"]["report"],
            "experiment_bundle_url": artifact["urls"]["bundle"],
        }
        record["last_run"] = last_run
        record["updated_at"] = now
        path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return self._build_campaign_study_detail(path)

    def _campaign_study_urls(self, template_id: str) -> dict:
        return {
            "detail": f"/api/campaign-studies/{template_id}",
            "download": (
                f"/api/campaign-studies/{template_id}/download"
            ),
        }

    def _build_campaign_study_summary(self, record: dict) -> dict:
        template_id = record["template_id"]
        campaign = record.get("campaign") or {}
        objective = record.get("objective") or {}
        packaged = bool(record.get("packaged"))
        return {
            "template_id": template_id,
            "label": record.get("label", template_id),
            "description": record.get("description", ""),
            "purpose": record.get("purpose"),
            "expected_runtime": record.get("expected_runtime"),
            "metrics": record.get("metrics") or [],
            "limitations": record.get("limitations") or [],
            "non_claims": record.get("non_claims") or [],
            "interpretation": record.get("interpretation") or {},
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "source_config_name": record.get("source_config_name"),
            "campaign_label": campaign.get("label"),
            "strategy": campaign.get("strategy"),
            "planned_run_count": campaign.get("planned_run_count"),
            "dimension_count": campaign.get("dimension_count"),
            "objective_name": objective.get("name"),
            "primary_metric": objective.get("primary_metric"),
            "goal": objective.get("goal"),
            "packaged": packaged,
            "origin": "packaged" if packaged else "local",
            "imported": bool(record.get("imported_from_template_id")),
            "imported_from_template_id": record.get(
                "imported_from_template_id"
            ),
            "exportable": True,
            "last_run": record.get("last_run"),
            "urls": self._campaign_study_urls(template_id),
        }

    def _build_campaign_study_detail(self, path: Path) -> dict:
        record = self._read_json(path)
        return {
            "summary": self._build_campaign_study_summary(record),
            "template": record,
            "urls": self._campaign_study_urls(record["template_id"]),
        }

    def _build_campaign_study_guide(
        self,
        record: dict | None,
        comparison: dict[str, Any],
    ) -> dict[str, Any]:
        interpretation = (record or {}).get("interpretation") or {}
        label = (record or {}).get("label") or "Campaign Studio study"
        rows = comparison.get("rows") or []
        ranges = comparison.get("ranges") or {}
        decision = comparison.get("decision") or {}
        shared = comparison.get("shared_experiment") or {}
        dimensions = shared.get("dimensions") or []
        changed_paths = ", ".join(
            str(dimension.get("path") or dimension.get("label"))
            for dimension in dimensions
        )
        if not changed_paths:
            changed_paths = "the configured campaign parameters"

        what_changed = list(interpretation.get("what_changed") or [])
        if rows:
            energy_span = ranges.get("energy_drift", {}).get("span")
            norm_span = ranges.get("norm_drift", {}).get("span")
            density_span = ranges.get("max_density", {}).get("span")
            if energy_span is not None:
                what_changed.append(
                    "Energy drift span across completed variants: "
                    f"{energy_span:.3e}."
                )
            if norm_span is not None:
                what_changed.append(
                    "Norm drift span across completed variants: "
                    f"{norm_span:.3e}."
                )
            if density_span is not None:
                what_changed.append(
                    "Max-density span across completed variants: "
                    f"{density_span:.3e}."
                )
        if decision.get("recommended_run_id"):
            what_changed.append(
                "The scoring contract recommends "
                f"{decision['recommended_run_id']} because: "
                f"{decision.get('reason', 'no rationale recorded')}"
            )
        if not what_changed:
            what_changed.append(
                f"The campaign varies {changed_paths} and compares the "
                "resulting evidence rows."
            )

        return {
            "title": f"{label} guided interpretation",
            "plain_language_summary": interpretation.get(
                "summary",
                (
                    f"QS-DMSS ran a Campaign Studio study varying "
                    f"{changed_paths}. Read the result as a reproducible "
                    "parameter-study workflow, not a scientific verdict."
                ),
            ),
            "what_changed": what_changed,
            "metric_meanings": list(
                interpretation.get("metric_meanings")
                or [
                    (
                        "Energy and norm drift are stability-oriented "
                        "diagnostics."
                    ),
                    (
                        "Max density is an output response to compare across "
                        "variants."
                    ),
                    (
                        "Elapsed seconds keeps reviewer-facing runtime "
                        "visible."
                    ),
                    (
                        "The recommendation is a scoring-contract result, "
                        "not peer-reviewed validation."
                    ),
                ]
            ),
            "what_this_does_not_claim": list(
                interpretation.get("what_this_does_not_claim")
                or (record or {}).get("non_claims")
                or [
                    (
                        "It does not prove that one parameter value is "
                        "scientifically correct."
                    ),
                    (
                        "It does not replace external validation or peer "
                        "review."
                    ),
                ]
            ),
            "review_prompt": interpretation.get(
                "review_prompt",
                (
                    "A useful review comment can focus on whether the "
                    "campaign evidence makes parameter behavior "
                    "understandable."
                ),
            ),
        }

    def _utc_now_z(self) -> str:
        return (
            self.now()
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))
