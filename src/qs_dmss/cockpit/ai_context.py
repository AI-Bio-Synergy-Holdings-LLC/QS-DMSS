"""Bounded, evidence-only context assembly for the cockpit AI sidecar."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException

from qs_dmss.ai import APPROVED_AI_INTENTS, AIIntent, make_ai_artifact

EvidenceResourceBuilder = Callable[[str], dict[str, Any]]
ShowcaseReportPathBuilder = Callable[[str], Path]
JsonReader = Callable[[Path], dict[str, Any]]


def _selected_fields(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {field: value[field] for field in fields if field in value}


@dataclass(frozen=True)
class AIEvidenceContextRequest:
    intent: AIIntent
    scenario_name: str
    run_id: str | None = None
    experiment_id: str | None = None


@dataclass(frozen=True)
class CockpitAIEvidenceContextService:
    """Assemble read-only AI context from characterized evidence contracts."""

    build_showcase_summary: EvidenceResourceBuilder
    get_run_detail: EvidenceResourceBuilder
    get_experiment_detail: EvidenceResourceBuilder
    showcase_json_path: ShowcaseReportPathBuilder
    read_json: JsonReader

    def build(
        self,
        payload: AIEvidenceContextRequest,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if payload.intent in {"summary", "claim"} and not payload.run_id:
            raise HTTPException(
                status_code=400,
                detail="Evidence summary and claim-boundary review require a recorded run.",
            )
        if payload.intent == "comparison" and not payload.experiment_id:
            raise HTTPException(
                status_code=400,
                detail="Comparison critique requires a recorded comparison experiment.",
            )

        scenario = self.build_showcase_summary(payload.scenario_name)
        scenario_data = _selected_fields(
            scenario,
            (
                "name",
                "label",
                "run_name",
                "grid_label",
                "steps",
                "purpose",
                "description",
                "claim_boundary",
                "limitations",
                "next_actions",
                "guided_comparison",
            ),
        )
        artifacts = [
            make_ai_artifact(
                f"scenario-contract/{scenario['name']}",
                "scenario_contract",
                scenario_data,
            )
        ]
        subject: dict[str, Any] = {
            "scenario_name": scenario["name"],
            "run_id": payload.run_id,
            "experiment_id": payload.experiment_id,
        }

        experiment: dict[str, Any] | None = None
        recorded_run_ids: set[str] = set()
        if payload.experiment_id:
            experiment = self.get_experiment_detail(payload.experiment_id)
            experiment_summary = experiment.get("summary") or {}
            execution_job = experiment.get("execution_job") or {}
            job_spec = execution_job.get("spec") or {}
            job_metadata = job_spec.get("metadata") or {}
            recorded_run_ids = {
                str(run_id) for run_id in experiment_summary.get("run_ids") or []
            }
            if experiment_summary.get(
                "kind"
            ) != "guided-comparison" or job_metadata.get("scenario") != scenario.get(
                "name"
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "The selected comparison does not belong to the selected "
                        "packaged scenario."
                    ),
                )
            if payload.run_id and payload.run_id not in recorded_run_ids:
                raise HTTPException(
                    status_code=400,
                    detail="The selected run is not part of the selected comparison.",
                )

        run_detail: dict[str, Any] | None = None
        if payload.run_id:
            run_detail = self.get_run_detail(payload.run_id)
            run_summary = run_detail["summary"]
            if experiment is None and run_summary.get("name") != scenario.get(
                "run_name"
            ):
                raise HTTPException(
                    status_code=400,
                    detail="The selected run does not belong to the selected packaged scenario.",
                )
            safe_summary = _selected_fields(
                run_summary,
                (
                    "run_id",
                    "name",
                    "config_name",
                    "seed",
                    "grid_label",
                    "steps",
                    "status",
                    "finished_at",
                    "elapsed_seconds",
                    "config_digest",
                    "energy_drift",
                    "norm_drift",
                    "bundle_size_bytes",
                    "bundle_sha256",
                ),
            )
            metrics = run_detail.get("metrics") or {}
            history = metrics.get("history") or []
            if len(history) > 16:
                history = [*history[:8], *history[-8:]]
            safe_metrics = _selected_fields(
                metrics,
                (
                    "energy_drift",
                    "norm_drift",
                    "relative_norm_drift",
                    "max_density",
                    "elapsed_seconds",
                ),
            )
            safe_metrics["history_excerpt"] = [
                _selected_fields(
                    snapshot,
                    ("step", "time", "norm", "energy", "max_density"),
                )
                for snapshot in history
                if isinstance(snapshot, dict)
            ]
            artifacts.extend(
                [
                    make_ai_artifact(
                        f"run/{payload.run_id}/summary",
                        "run_summary",
                        safe_summary,
                    ),
                    make_ai_artifact(
                        f"run/{payload.run_id}/metrics",
                        "run_metrics",
                        safe_metrics,
                    ),
                    make_ai_artifact(
                        f"run/{payload.run_id}/verification",
                        "manifest_verification",
                        {
                            **_selected_fields(
                                run_detail.get("verification"),
                                ("success", "checked_files"),
                            ),
                            "evidence": _selected_fields(
                                run_detail.get("evidence"),
                                ("file_count", "bundle_size_bytes", "bundle_sha256"),
                            ),
                        },
                    ),
                ]
            )

            try:
                report = self.read_json(self.showcase_json_path(scenario["name"]))
            except (HTTPException, json.JSONDecodeError, OSError, ValueError):
                report = None
            if report and (report.get("run") or {}).get("run_id") == payload.run_id:
                safe_report = {
                    **_selected_fields(
                        report,
                        (
                            "schema_version",
                            "generated_at",
                            "scenario",
                            "scenario_title",
                            "scenario_narrative",
                            "claim_boundary",
                            "success",
                            "metrics",
                            "interpretation",
                        ),
                    ),
                    "verification": _selected_fields(
                        report.get("verification"),
                        ("success", "checked_files"),
                    ),
                    "replay": _selected_fields(
                        report.get("replay"),
                        (
                            "run_id",
                            "verification_success",
                            "final_density_allclose",
                            "max_abs_density_delta",
                        ),
                    ),
                    "artifact_keys": sorted((report.get("artifacts") or {}).keys()),
                }
                artifacts.append(
                    make_ai_artifact(
                        f"showcase-report/{scenario['name']}/{payload.run_id}",
                        "showcase_report",
                        safe_report,
                    )
                )

        if experiment is not None:
            comparison = experiment.get("comparison") or {}
            safe_rows = []
            for row in comparison.get("rows") or []:
                row_run_id = str(row.get("run_id") or "")
                if not row_run_id:
                    continue
                if row_run_id not in recorded_run_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "The selected comparison contains a run outside its "
                            "recorded experiment lineage."
                        ),
                    )
                safe_rows.append(
                    _selected_fields(
                        row,
                        (
                            "run_id",
                            "name",
                            "seed",
                            "parameter_path",
                            "parameter_label",
                            "parameter_value",
                            "parameter_value_label",
                            "variant",
                            "variant_label",
                            "energy_drift",
                            "norm_drift",
                            "max_density",
                            "elapsed_seconds",
                            "verification_success",
                            "delta_from_baseline",
                        ),
                    )
                )
            if payload.run_id and payload.run_id not in {
                row.get("run_id") for row in safe_rows
            }:
                raise HTTPException(
                    status_code=400,
                    detail="The selected run is not part of the selected comparison.",
                )
            safe_comparison = {
                "experiment": _selected_fields(
                    experiment.get("summary"),
                    (
                        "experiment_id",
                        "label",
                        "kind",
                        "status",
                        "created_at",
                        "baseline_run_id",
                        "run_count",
                        "bundle_sha256",
                    ),
                ),
                "baseline_run_id": comparison.get("baseline_run_id"),
                "shared_experiment": _selected_fields(
                    comparison.get("shared_experiment"),
                    (
                        "id",
                        "label",
                        "kind",
                        "strategy",
                        "dimension_count",
                        "dimensions",
                        "parameter_path",
                        "parameter_label",
                    ),
                ),
                "rows": safe_rows,
                "ranges": _selected_fields(
                    comparison.get("ranges"),
                    ("energy_drift", "norm_drift", "max_density", "elapsed_seconds"),
                ),
                "highlights": _selected_fields(
                    comparison.get("highlights"),
                    (
                        "lowest_abs_energy_drift_run_id",
                        "lowest_abs_norm_drift_run_id",
                        "highest_max_density_run_id",
                    ),
                ),
                "decision": _selected_fields(
                    comparison.get("decision"),
                    (
                        "available",
                        "mode",
                        "status",
                        "reason",
                        "recommended_run_id",
                        "recommended_score",
                        "recommended_status",
                        "primary_metric",
                        "primary_metric_label",
                        "primary_goal",
                        "primary_target_value",
                        "qualified_run_count",
                        "total_run_count",
                        "ranked_run_ids",
                    ),
                ),
            }
            artifacts.append(
                make_ai_artifact(
                    f"comparison/{payload.experiment_id}",
                    "run_comparison",
                    safe_comparison,
                )
            )

        context = {
            "schema_version": 1,
            "intent": payload.intent,
            "intent_label": APPROVED_AI_INTENTS[payload.intent],
            "artifacts": artifacts,
            "policy": {
                "advisory_only": True,
                "human_review_required": True,
                "tools_available": False,
                "run_launch_allowed": False,
                "artifact_mutation_allowed": False,
                "external_sources_allowed": False,
            },
        }
        return context, subject
