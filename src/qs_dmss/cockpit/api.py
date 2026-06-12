from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from qs_dmss.app import execute_run, replay_run as replay_existing_run
from qs_dmss.decision import evaluate_run_decision
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.experiment import (
    apply_parameter_values,
    apply_sweep_value,
    build_campaign_context,
    build_campaign_plan,
    build_experiment_context,
    build_run_comparison,
    coerce_sweep_values,
    create_experiment_id,
    format_parameter_value,
    get_sweep_parameter,
    list_sweep_parameters,
    persist_failed_campaign_artifact,
    persist_experiment_artifact,
)
from qs_dmss.io.config import (
    SUPPORTED_DECISION_METRICS,
    SUPPORTED_OBJECTIVE_GOALS,
    load_config,
    parse_config,
)
from qs_dmss.paths import (
    contained_path,
    configs_root,
    discover_repo_root,
    experiments_root,
    runs_root,
    safe_filename,
)
from qs_dmss.showcase import (
    DEFAULT_SHOWCASE_NAME,
    SHOWCASE_JSON_REPORT,
    SHOWCASE_MARKDOWN_REPORT,
    list_showcase_scenarios,
    resolve_showcase_scenario,
    run_simulation_showcase,
    showcase_scenario_metadata,
)


GENERIC_COCKPIT_ERROR_DETAIL = "Cockpit request failed; check server logs for details."


class LaunchRunRequest(BaseModel):
    config: dict
    source_name: str = "cockpit.yaml"


class CompareRunsRequest(BaseModel):
    run_ids: list[str]


class CreateExperimentRequest(BaseModel):
    run_ids: list[str]
    label: str | None = None


class SweepRequest(BaseModel):
    config: dict
    parameter_path: str
    values: list[int | float | str]
    source_name: str = "sweep.yaml"
    experiment_name: str | None = None


class LaunchCampaignRequest(BaseModel):
    config: dict
    source_name: str = "campaign.yaml"
    study_template_id: str | None = None


class CampaignStudyTemplateRequest(BaseModel):
    template: dict[str, Any]


@dataclass(frozen=True)
class CockpitService:
    repo_root: Path
    output_root: Path
    experiments_root: Path
    config_root: Path
    static_root: Path

    @classmethod
    def create(
        cls,
        repo_root: str | Path | None = None,
        output_root: str | Path | None = None,
    ) -> "CockpitService":
        resolved_repo_root = discover_repo_root(Path(repo_root) if repo_root else Path.cwd())
        resolved_output_root = (
            Path(output_root).resolve() if output_root else runs_root(resolved_repo_root)
        )
        resolved_experiments_root = experiments_root(
            resolved_repo_root,
            resolved_output_root,
        )
        resolved_output_root.mkdir(parents=True, exist_ok=True)
        resolved_experiments_root.mkdir(parents=True, exist_ok=True)
        return cls(
            repo_root=resolved_repo_root,
            output_root=resolved_output_root,
            experiments_root=resolved_experiments_root,
            config_root=configs_root(resolved_repo_root),
            static_root=Path(__file__).resolve().parent / "static",
        )

    def list_configs(self) -> list[dict]:
        items: list[dict] = []
        for path in sorted(self.config_root.glob("*.y*ml")):
            config = load_config(path)
            try:
                relative_path = path.relative_to(self.repo_root).as_posix()
            except ValueError:
                relative_path = f"configs/{path.name}"
            items.append(
                {
                    "label": path.stem.replace("_", " "),
                    "name": path.name,
                    "path": relative_path,
                    "config": config.to_dict(),
                }
            )
        return items

    def list_runs(self) -> list[dict]:
        return [self._build_run_summary(run_dir) for run_dir in self._list_run_dirs()]

    def list_experiments(self) -> list[dict]:
        return [
            self._build_experiment_summary(experiment_dir)
            for experiment_dir in self._list_experiment_dirs()
        ]

    def list_sweep_parameters(self) -> list[dict]:
        return list_sweep_parameters()

    def list_showcases(self) -> list[dict]:
        return [self._build_showcase_summary(name) for name in list_showcase_scenarios()]

    def campaign_studio_preview(self) -> dict:
        configs = self.list_configs()
        default_config = configs[0] if configs else None
        if default_config is None:
            return {
                "available": False,
                "title": "Campaign Studio",
                "summary": "No packaged config is available for a campaign preview.",
                "current_boundary": "Add a config with objective and campaign sections to enable Campaign Studio.",
                "next_capabilities": [
                    "Scenario-linked campaign templates",
                    "Editable parameter-grid studies",
                    "Decision-profile editing",
                ],
            }

        config = default_config["config"]
        try:
            campaign_plan = build_campaign_plan(config)
        except ValueError as exc:
            return {
                "available": False,
                "title": "Campaign Studio",
                "source_config_name": default_config["name"],
                "summary": str(exc),
                "current_boundary": "This config can launch a run, but it does not define an automated campaign.",
                "next_capabilities": [
                    "Add a campaign section",
                    "Attach objective constraints",
                    "Save a comparison research object",
                ],
            }

        objective = config.get("objective") or {}
        constraints = {"require_verification": True, **(config.get("constraints") or {})}
        ranking = config.get("ranking") or {}
        return {
            "available": True,
            "title": "Campaign Studio",
            "source_config_name": default_config["name"],
            "label": campaign_plan["label"],
            "strategy": campaign_plan["strategy"],
            "max_runs": config.get("campaign", {}).get("max_runs", campaign_plan["planned_run_count"]),
            "planned_run_count": campaign_plan["planned_run_count"],
            "dimension_count": campaign_plan["dimension_count"],
            "dimensions": campaign_plan["dimensions"],
            "objective": {
                "name": objective.get("name", "No objective"),
                "summary": objective.get("summary", "No objective summary provided."),
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
                "primary_metric_weight": ranking.get("primary_metric_weight"),
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
                "multi-run search matrix, score every run, save reusable study templates, "
                "and export a comparison bundle."
            ),
            "current_boundary": (
                "Campaign Studio now edits, saves, reopens, imports, and exports reusable "
                "campaign study templates with the scoring contract attached."
            ),
            "next_capabilities": [
                "Richer template library metadata",
                "Template-to-publication export provenance",
                "Team-shared study template registries",
            ],
            "launch_endpoint": "/api/campaigns",
        }

    def list_campaign_study_templates(self) -> list[dict]:
        return [
            self._build_campaign_study_summary(self._read_json(path))
            for path in self._list_campaign_study_template_paths()
        ]

    def get_campaign_study_template(self, template_id: str) -> dict:
        path = self._get_campaign_study_template_path(template_id)
        return self._build_campaign_study_detail(path)

    def campaign_study_template_path(self, template_id: str) -> Path:
        return self._get_campaign_study_template_path(template_id)

    def save_campaign_study_template(self, payload: CampaignStudyTemplateRequest) -> dict:
        try:
            record = self._normalize_campaign_study_template(payload.template)
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

    def import_campaign_study_template(self, payload: CampaignStudyTemplateRequest) -> dict:
        template = dict(payload.template)
        imported_from = template.get("template_id")
        if imported_from:
            template["imported_from_template_id"] = str(imported_from)
        return self.save_campaign_study_template(
            CampaignStudyTemplateRequest(template=template),
        )

    def get_run_detail(self, run_id: str) -> dict:
        run_dir = self._get_run_dir(run_id)
        return self._build_run_detail(run_dir)

    def get_experiment_detail(self, experiment_id: str) -> dict:
        experiment_dir = self._get_experiment_dir(experiment_id)
        return self._build_experiment_detail(experiment_dir)

    def launch_run(self, payload: LaunchRunRequest) -> dict:
        config = parse_config(payload.config)
        with TemporaryDirectory() as temp_dir:
            temp_path = self._temp_source_path(Path(temp_dir), payload.source_name)
            outputs = execute_run(
                config=config,
                source_config_path=temp_path,
                output_root=self.output_root,
            )
        return self._build_run_detail(outputs.run_dir)

    def verify_run(self, run_id: str) -> dict:
        run_dir = self._get_run_dir(run_id)
        verification = verify_run_path(run_dir)
        return {
            "run_id": run_id,
            "success": verification.success,
            "checked_files": verification.checked_files,
            "errors": verification.errors,
        }

    def replay_run(self, run_id: str) -> dict:
        run_dir = self._get_run_dir(run_id)
        outputs = replay_existing_run(run_dir, output_root=self.output_root)
        return self._build_run_detail(outputs.run_dir)

    def launch_showcase(self, scenario: str = DEFAULT_SHOWCASE_NAME) -> dict:
        selected = self._resolve_showcase_scenario(scenario)
        showcase_root = self._showcase_output_root(selected.name, create=True)
        report = run_simulation_showcase(
            output_root=showcase_root,
            scenario=selected.name,
            runs_output_root=self.output_root,
            replay_output_root=self.output_root,
        )
        run_detail = self._build_run_detail(Path(report["run"]["run_dir"]))
        replay_detail = None
        if report.get("replay"):
            replay_detail = self._build_run_detail(Path(report["replay"]["run_dir"]))

        return {
            "scenario": self._build_showcase_summary(selected.name),
            "report": report,
            "run": run_detail,
            "replay_run": replay_detail,
            "artifact_links": self._build_showcase_artifact_links(selected.name, report),
            "urls": {
                "markdown_report": f"/api/showcases/{selected.name}/report",
                "json_report": f"/api/showcases/{selected.name}/report.json",
            },
        }

    def launch_showcase_comparison(self, scenario: str = DEFAULT_SHOWCASE_NAME) -> dict:
        selected = self._resolve_showcase_scenario(scenario)
        base_config = load_config(selected.config_path).to_dict()
        dimensions = self._guided_comparison_dimensions()
        variants = self._guided_comparison_variants(base_config)
        experiment_id = create_experiment_id("guided-comparison")
        experiment_label = f"{selected.name.replace('-', ' ').title()} guided comparison"

        run_dirs: list[Path] = []
        summaries: list[dict] = []
        details: list[dict] = []
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for ordinal, variant in enumerate(variants, start=1):
                variant_config = self._guided_comparison_config(
                    base_config,
                    variant["values"],
                )
                temp_config_dir = temp_root / f"variant-{ordinal:02d}"
                temp_config_dir.mkdir(parents=True, exist_ok=True)
                temp_path = self._temp_source_path(
                    temp_config_dir,
                    f"{selected.name}-{variant['slug']}.yaml",
                )
                outputs = execute_run(
                    config=parse_config(variant_config),
                    source_config_path=temp_path,
                    output_root=self.output_root,
                    experiment=self._guided_comparison_context(
                        experiment_id=experiment_id,
                        label=experiment_label,
                        dimensions=dimensions,
                        variant=variant,
                        ordinal=ordinal,
                        total_runs=len(variants),
                    ),
                )
                run_dirs.append(outputs.run_dir)
                detail = self._build_run_detail(outputs.run_dir)
                details.append(detail)
                summaries.append(detail["summary"])

        artifact_outputs = persist_experiment_artifact(
            run_dirs=run_dirs,
            run_details=details,
            experiments_root=self.experiments_root,
            label=experiment_label,
            experiment_id=experiment_id,
            kind="guided-comparison",
        )
        artifact_detail = self._build_experiment_detail(artifact_outputs.experiment_dir)

        return {
            "scenario": self._build_showcase_summary(selected.name),
            "comparison": artifact_detail["comparison"],
            "guide": self._build_guided_comparison_guide(artifact_detail["comparison"]),
            "runs": summaries,
            "artifact": artifact_detail,
            "urls": artifact_detail["urls"],
        }

    def compare_runs(self, payload: CompareRunsRequest) -> dict:
        run_ids = [run_id for run_id in payload.run_ids if run_id]
        if len(run_ids) < 2:
            raise HTTPException(status_code=400, detail="Select at least two runs to compare")

        try:
            details = [self._build_run_detail(self._get_run_dir(run_id)) for run_id in run_ids]
            return build_run_comparison(details)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def create_experiment(self, payload: CreateExperimentRequest) -> dict:
        run_ids = [run_id for run_id in payload.run_ids if run_id]
        if len(run_ids) < 2:
            raise HTTPException(status_code=400, detail="Select at least two runs to save an experiment")

        try:
            run_dirs = [self._get_run_dir(run_id) for run_id in run_ids]
            details = [self._build_run_detail(run_dir) for run_dir in run_dirs]
            outputs = persist_experiment_artifact(
                run_dirs=run_dirs,
                run_details=details,
                experiments_root=self.experiments_root,
                label=payload.label,
                kind="comparison",
            )
            return self._build_experiment_detail(outputs.experiment_dir)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def launch_sweep(self, payload: SweepRequest) -> dict:
        try:
            base_config = parse_config(payload.config).to_dict()
            parameter = get_sweep_parameter(payload.parameter_path)
            values = coerce_sweep_values(parameter.path, payload.values)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        experiment_id = create_experiment_id("sweep")
        experiment_label = payload.experiment_name or f"{base_config['run']['name']} {parameter.label} sweep"

        run_dirs: list[Path] = []
        summaries: list[dict] = []
        details: list[dict] = []
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for index, value in enumerate(values, start=1):
                varied_config = apply_sweep_value(base_config, parameter.path, value)
                temp_config_dir = temp_root / f"run-{index:02d}"
                temp_config_dir.mkdir(parents=True, exist_ok=True)
                temp_path = self._temp_source_path(temp_config_dir, payload.source_name)
                outputs = execute_run(
                    config=parse_config(varied_config),
                    source_config_path=temp_path,
                    output_root=self.output_root,
                    experiment=build_experiment_context(
                        experiment_id=experiment_id,
                        label=experiment_label,
                        parameter=parameter,
                        value=value,
                        ordinal=index,
                        total_runs=len(values),
                    ),
                )
                run_dirs.append(outputs.run_dir)
                detail = self._build_run_detail(outputs.run_dir)
                details.append(detail)
                summaries.append(detail["summary"])

        comparison = build_run_comparison(details)
        artifact_outputs = persist_experiment_artifact(
            run_dirs=run_dirs,
            run_details=details,
            experiments_root=self.experiments_root,
            label=experiment_label,
            experiment_id=experiment_id,
            kind="sweep",
        )

        return {
            "experiment": {
                "id": experiment_id,
                "label": experiment_label,
                "parameter_path": parameter.path,
                "parameter_label": parameter.label,
                "values": values,
                "run_ids": [summary["run_id"] for summary in summaries],
            },
            "runs": summaries,
            "comparison": comparison,
            "artifact": self._build_experiment_detail(artifact_outputs.experiment_dir),
        }

    def launch_campaign(self, payload: LaunchCampaignRequest) -> dict:
        try:
            base_config = parse_config(payload.config).to_dict()
            campaign_plan = build_campaign_plan(base_config)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        study_template_path = None
        if payload.study_template_id:
            study_template_path = self._get_campaign_study_template_path(
                payload.study_template_id,
            )

        run_dirs: list[Path] = []
        summaries: list[dict] = []
        details: list[dict] = []
        try:
            with TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                for variant in campaign_plan["variants"]:
                    temp_config_dir = temp_root / f"run-{variant['ordinal']:02d}"
                    temp_config_dir.mkdir(parents=True, exist_ok=True)
                    temp_path = self._temp_source_path(temp_config_dir, payload.source_name)
                    outputs = execute_run(
                        config=parse_config(variant["config"]),
                        source_config_path=temp_path,
                        output_root=self.output_root,
                        experiment=build_campaign_context(
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
                    detail = self._build_run_detail(outputs.run_dir)
                    details.append(detail)
                    summaries.append(detail["summary"])
        except Exception as exc:
            try:
                failure_outputs = persist_failed_campaign_artifact(
                    campaign_plan=campaign_plan,
                    run_dirs=run_dirs,
                    run_details=details,
                    experiments_root=self.experiments_root,
                    error=exc,
                )
                failure_detail = self._build_experiment_detail(failure_outputs.experiment_dir)
            except Exception as persist_exc:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "message": "Campaign failed, and the failed campaign artifact could not be saved.",
                        "error": str(exc),
                        "artifact_error": str(persist_exc),
                        "completed_run_ids": [summary["run_id"] for summary in summaries],
                    },
                ) from persist_exc
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Campaign failed; a failed campaign artifact was saved.",
                    "error": str(exc),
                    "experiment_id": failure_detail["summary"]["experiment_id"],
                    "run_ids": failure_detail["summary"]["run_ids"],
                    "bundle": failure_detail["urls"]["bundle"],
                    "report": failure_detail["urls"]["report"],
                },
            ) from exc

        comparison = build_run_comparison(details)
        artifact_outputs = persist_experiment_artifact(
            run_dirs=run_dirs,
            run_details=details,
            experiments_root=self.experiments_root,
            label=campaign_plan["label"],
            experiment_id=campaign_plan["id"],
            kind="campaign",
        )
        artifact = self._build_experiment_detail(artifact_outputs.experiment_dir)
        campaign_summary = {
            "id": campaign_plan["id"],
            "label": campaign_plan["label"],
            "strategy": campaign_plan["strategy"],
            "dimension_count": campaign_plan["dimension_count"],
            "planned_run_count": campaign_plan["planned_run_count"],
            "dimensions": campaign_plan["dimensions"],
            "run_ids": [summary["run_id"] for summary in summaries],
            "recommended_run_id": (comparison.get("decision") or {}).get("recommended_run_id"),
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
            "artifact": artifact,
            "study_template": study_template,
        }

    def bundle_path(self, run_id: str) -> Path:
        run_dir = self._get_run_dir(run_id)
        bundle_path = run_dir / "evidence_bundle.zip"
        if not bundle_path.exists():
            raise HTTPException(status_code=404, detail="Evidence bundle not found")
        return bundle_path

    def report_path(self, run_id: str) -> Path:
        run_dir = self._get_run_dir(run_id)
        report_path = run_dir / "report.html"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Run report not found")
        return report_path

    def experiment_bundle_path(self, experiment_id: str) -> Path:
        experiment_dir = self._get_experiment_dir(experiment_id)
        bundle_path = experiment_dir / "evidence_bundle.zip"
        if not bundle_path.exists():
            raise HTTPException(status_code=404, detail="Experiment bundle not found")
        return bundle_path

    def experiment_report_path(self, experiment_id: str) -> Path:
        experiment_dir = self._get_experiment_dir(experiment_id)
        report_path = experiment_dir / "report.html"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Experiment report not found")
        return report_path

    def showcase_markdown_path(self, scenario: str) -> Path:
        report_path = self._showcase_output_root(
            self._resolve_showcase_scenario(scenario).name
        ) / SHOWCASE_MARKDOWN_REPORT
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Showcase report not found")
        return report_path

    def showcase_json_path(self, scenario: str) -> Path:
        report_path = self._showcase_output_root(
            self._resolve_showcase_scenario(scenario).name
        ) / SHOWCASE_JSON_REPORT
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Showcase JSON report not found")
        return report_path

    def showcase_artifact_path(self, scenario: str, artifact_name: str) -> Path:
        scenario_name = self._resolve_showcase_scenario(scenario).name
        artifact_root = self._showcase_output_root(scenario_name) / "artifacts"
        artifact_path = contained_path(
            artifact_root,
            safe_filename(artifact_name, default="artifact"),
        )
        if not artifact_path.exists() or not artifact_path.is_file():
            raise HTTPException(status_code=404, detail="Showcase artifact not found")
        return artifact_path

    def index_path(self) -> Path:
        return self.static_root / "index.html"

    def _list_run_dirs(self) -> list[Path]:
        if not self.output_root.exists():
            return []
        run_dirs = [
            path
            for path in self.output_root.iterdir()
            if path.is_dir() and (path / "run.json").exists()
        ]
        return sorted(run_dirs, key=lambda path: path.stat().st_mtime, reverse=True)

    def _list_experiment_dirs(self) -> list[Path]:
        if not self.experiments_root.exists():
            return []
        experiment_dirs = [
            path
            for path in self.experiments_root.iterdir()
            if path.is_dir() and (path / "experiment.json").exists()
        ]
        return sorted(experiment_dirs, key=lambda path: path.stat().st_mtime, reverse=True)

    def _safe_source_name(self, source_name: str) -> str:
        return safe_filename(
            source_name,
            default="cockpit.yaml",
            suffixes=(".yaml", ".yml"),
        )

    def _temp_source_path(self, temp_dir: Path, source_name: str) -> Path:
        return contained_path(temp_dir, self._safe_source_name(source_name))

    def _get_run_dir(self, run_id: str) -> Path:
        run_dir = (self.output_root / run_id).resolve()
        if run_dir.parent != self.output_root.resolve():
            raise HTTPException(status_code=404, detail="Run not found")
        if not run_dir.exists() or not (run_dir / "run.json").exists():
            raise HTTPException(status_code=404, detail="Run not found")
        return run_dir

    def _get_experiment_dir(self, experiment_id: str) -> Path:
        experiment_dir = (self.experiments_root / experiment_id).resolve()
        if experiment_dir.parent != self.experiments_root.resolve():
            raise HTTPException(status_code=404, detail="Experiment not found")
        if not experiment_dir.exists() or not (experiment_dir / "experiment.json").exists():
            raise HTTPException(status_code=404, detail="Experiment not found")
        return experiment_dir

    def _resolve_showcase_scenario(self, scenario: str):
        try:
            return resolve_showcase_scenario(scenario)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail="Showcase scenario not found") from exc

    def _showcase_output_root(self, scenario: str, *, create: bool = False) -> Path:
        showcases_root = self.output_root.resolve().parent / "showcases"
        output_root = contained_path(
            showcases_root,
            safe_filename(scenario, default=DEFAULT_SHOWCASE_NAME),
        )
        if create:
            output_root.mkdir(parents=True, exist_ok=True)
        return output_root

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

    def _get_campaign_study_template_path(self, template_id: str) -> Path:
        template_name = safe_filename(
            template_id,
            default="campaign-study",
            suffixes=(".json",),
        )
        path = contained_path(self._campaign_studies_root(), template_name)
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail="Campaign study template not found")
        return path

    def _campaign_study_template_id(self, label: str) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stem = safe_filename(
            label.lower().replace(" ", "-"),
            default="campaign-study",
        )
        base_id = f"{stem}-{timestamp}"
        template_id = base_id
        index = 2
        studies_root = self._campaign_studies_root(create=True)
        while contained_path(studies_root, f"{template_id}.json").exists():
            template_id = f"{base_id}-{index}"
            index += 1
        return template_id

    def _normalize_campaign_study_template(self, template: dict[str, Any]) -> dict:
        if not isinstance(template, dict):
            raise ValueError("Campaign study template must be an object")
        raw_config = template.get("config")
        if not isinstance(raw_config, dict):
            raise ValueError("Campaign study template requires a config object")

        config = parse_config(raw_config).to_dict()
        campaign_plan = build_campaign_plan(config)
        objective = config.get("objective") or {}
        constraints = {"require_verification": True, **(config.get("constraints") or {})}
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
        source_config_name = self._safe_source_name(
            str(template.get("source_config_name") or "campaign-study.yaml")
        )
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
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
                "primary_metric_weight": ranking.get("primary_metric_weight"),
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
        if template.get("imported_from_template_id"):
            record["imported_from_template_id"] = str(template["imported_from_template_id"])
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
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        last_run = {
            "ran_at": now,
            "status": "completed",
            "campaign_id": campaign_summary["id"],
            "campaign_label": campaign_summary["label"],
            "strategy": campaign_summary["strategy"],
            "planned_run_count": campaign_summary["planned_run_count"],
            "run_count": run_count,
            "run_ids": campaign_summary["run_ids"],
            "recommended_run_id": campaign_summary.get("recommended_run_id"),
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
            "download": f"/api/campaign-studies/{template_id}/download",
        }

    def _build_campaign_study_summary(self, record: dict) -> dict:
        template_id = record["template_id"]
        campaign = record.get("campaign") or {}
        objective = record.get("objective") or {}
        return {
            "template_id": template_id,
            "label": record.get("label", template_id),
            "description": record.get("description", ""),
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
            "imported": bool(record.get("imported_from_template_id")),
            "imported_from_template_id": record.get("imported_from_template_id"),
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

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _format_grid_label(self, grid_shape: list[int] | tuple[int, int, int]) -> str:
        return " x ".join(str(value) for value in grid_shape)

    def _format_bytes(self, byte_count: int) -> str:
        units = ["B", "KB", "MB", "GB"]
        value = float(byte_count)
        unit_index = 0
        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1
        precision = 0 if unit_index == 0 else 2
        return f"{value:.{precision}f} {units[unit_index]}"

    def _evidence_categories(self, manifest: dict) -> list[dict]:
        buckets = {
            "State Snapshots": 0,
            "Diagnostics": 0,
            "Invariants": 0,
            "Metadata": 0,
        }
        for entry in manifest.get("files", []):
            path = entry["path"]
            if path.startswith("artifacts/"):
                buckets["State Snapshots"] += 1
            elif path in {"metrics.json", "energy.csv", "report.html"}:
                buckets["Diagnostics"] += 1
            elif path in {"environment.lock.json"}:
                buckets["Invariants"] += 1
            else:
                buckets["Metadata"] += 1

        tones = {
            "State Snapshots": "teal",
            "Diagnostics": "copper",
            "Invariants": "olive",
            "Metadata": "stone",
        }
        return [
            {"label": label, "count": count, "tone": tones[label]}
            for label, count in buckets.items()
            if count > 0
        ]

    def _build_showcase_summary(self, scenario: str) -> dict:
        selected = self._resolve_showcase_scenario(scenario)
        config = load_config(selected.config_path)
        metadata = showcase_scenario_metadata(selected.name)
        guided_variants = self._guided_comparison_variants(config.to_dict())
        return {
            "name": selected.name,
            "label": metadata["title"],
            "config_name": selected.config_path.name,
            "run_name": config.run.name,
            "grid_label": self._format_grid_label(config.engine.grid_shape),
            "steps": config.engine.num_steps,
            "description": (
                "Packaged canonical simulation scenario that produces a run, "
                "verified evidence bundle, replay check, CSV/SVG artifacts, "
                "and a human-readable showcase report."
            ),
            "claim_boundary": (
                "Workflow demonstration only; not peer-reviewed scientific validation."
            ),
            "purpose": metadata["purpose"],
            "expected_runtime": metadata["expected_runtime"],
            "output_artifacts": metadata["output_artifacts"],
            "limitations": metadata["limitations"],
            "readiness_badges": metadata["readiness_badges"],
            "next_actions": metadata["next_actions"],
            "guided_comparison": {
                "label": "Packaged variant comparison",
                "strategy": "packaged-variants",
                "planned_run_count": len(guided_variants),
                "dimensions": self._guided_comparison_dimensions(),
                "variants": [
                    {
                        "slug": variant["slug"],
                        "label": variant["label"],
                        "description": variant["description"],
                    }
                    for variant in guided_variants
                ],
                "purpose": (
                    "Compare curated variants with a shared seed so the cockpit can explain "
                    "evidence deltas without requiring manual YAML edits."
                ),
            },
        }

    def _build_showcase_artifact_links(self, scenario: str, report: dict) -> list[dict]:
        links = []
        for key, value in report.get("artifacts", {}).items():
            artifact_name = Path(value).name
            kind = Path(artifact_name).suffix.lstrip(".") or "file"
            links.append(
                {
                    "key": key,
                    "label": key.replace("_", " ").title(),
                    "name": artifact_name,
                    "kind": kind,
                    "previewable": kind in {"csv", "svg"},
                    "url": f"/api/showcases/{scenario}/artifacts/{artifact_name}",
                }
            )
        return links

    def _guided_comparison_dimensions(self) -> list[dict[str, str]]:
        return [
            {
                "path": "initial.width",
                "label": "Initial packet width",
            },
            {
                "path": "engine.g_int",
                "label": "Interaction strength",
            },
        ]

    def _guided_comparison_variants(self, base_config: dict[str, Any]) -> list[dict[str, Any]]:
        base_width = float(base_config["initial"]["width"])
        base_interaction = float(base_config["engine"]["g_int"])
        wider_width = round(base_width * 1.27, 6)
        stronger_interaction = round(base_interaction * 1.5, 6)
        return [
            {
                "slug": "baseline",
                "label": "Baseline",
                "description": "The packaged canonical showcase settings.",
                "values": {
                    "initial.width": base_width,
                    "engine.g_int": base_interaction,
                },
            },
            {
                "slug": "wider-packet",
                "label": "Wider packet",
                "description": "A wider initial density packet with the same interaction strength.",
                "values": {
                    "initial.width": wider_width,
                    "engine.g_int": base_interaction,
                },
            },
            {
                "slug": "stronger-interaction",
                "label": "Stronger interaction",
                "description": "The baseline packet with a stronger self-interaction setting.",
                "values": {
                    "initial.width": base_width,
                    "engine.g_int": stronger_interaction,
                },
            },
        ]

    def _guided_comparison_config(
        self,
        base_config: dict[str, Any],
        values: dict[str, int | float],
    ) -> dict[str, Any]:
        return apply_parameter_values(
            base_config,
            [(path, value) for path, value in values.items()],
        )

    def _guided_comparison_context(
        self,
        *,
        experiment_id: str,
        label: str,
        dimensions: list[dict[str, str]],
        variant: dict[str, Any],
        ordinal: int,
        total_runs: int,
    ) -> dict[str, Any]:
        entries = [
            {
                "path": dimension["path"],
                "label": dimension["label"],
                "value": variant["values"][dimension["path"]],
                "value_label": format_parameter_value(variant["values"][dimension["path"]]),
            }
            for dimension in dimensions
        ]
        return {
            "id": experiment_id,
            "kind": "guided-comparison",
            "label": label,
            "strategy": "packaged-variants",
            "dimensions": dimensions,
            "dimension_count": len(dimensions),
            "parameter_path": None,
            "parameter_label": "Guided Variant",
            "parameter_value": None,
            "parameter_value_label": variant["label"],
            "variant": entries,
            "variant_label": variant["label"],
            "variant_note": variant["description"],
            "ordinal": ordinal,
            "total_runs": total_runs,
        }

    def _build_guided_comparison_guide(self, comparison: dict[str, Any]) -> dict[str, Any]:
        rows = comparison["rows"]
        highlights = comparison["highlights"]
        ranges = comparison["ranges"]
        decision = comparison.get("decision") or {}
        recommended_run_id = decision.get("recommended_run_id")
        recommended_row = next(
            (row for row in rows if row["run_id"] == recommended_run_id),
            None,
        )
        recommended_label = (
            recommended_row.get("variant_label") or recommended_row.get("parameter_value_label")
            if recommended_row
            else None
        )
        recommendation_sentence = (
            f"The current objective profile recommends the {recommended_label} variant "
            f"({recommended_run_id})."
            if recommended_run_id and recommended_label
            else "No objective-driven recommendation is available, so compare the evidence rows manually."
        )
        return {
            "title": "How the guided variants differ",
            "plain_language_summary": (
                "QS-DMSS ran the canonical showcase as a small guided comparison: the baseline, "
                "a wider initial density packet, and a stronger interaction variant. The variants "
                "use the same deterministic seed so the cockpit can focus attention on evidence "
                "differences rather than random setup changes."
            ),
            "what_changed": [
                f"Baseline run: {rows[0]['run_id']}. Each other row reports deltas against that baseline.",
                f"Energy drift span across variants: {ranges['energy_drift']['span']:.3e}.",
                f"Norm drift span across variants: {ranges['norm_drift']['span']:.3e}.",
                f"Max-density span across variants: {ranges['max_density']['span']:.3e}.",
                recommendation_sentence,
            ],
            "what_to_inspect": [
                f"Lowest absolute energy drift: {highlights['lowest_abs_energy_drift_run_id']}.",
                f"Lowest absolute norm drift: {highlights['lowest_abs_norm_drift_run_id']}.",
                f"Highest max density: {highlights['highest_max_density_run_id']}.",
                "Open the experiment report to inspect the comparison table, copied run evidence, and bundle manifest.",
            ],
            "what_this_does_not_claim": [
                "It does not prove one variant is scientifically correct or physically validated.",
                "It does not replace peer review, calibration, or domain-specific benchmark validation.",
                "It demonstrates the QS-DMSS workflow for comparing reproducible research objects.",
            ],
            "review_prompt": (
                "A useful review comment can focus on whether the comparison makes variant behavior "
                "understandable, whether the evidence deltas are enough, or which diagnostic should be added next."
            ),
        }

    def _build_run_summary(self, run_dir: Path) -> dict:
        run_record = self._read_json(run_dir / "run.json")
        metrics = self._read_json(run_dir / "metrics.json")
        config = load_config(run_dir / "config.yaml")
        experiment = run_record.get("experiment")
        bundle_path = run_dir / "evidence_bundle.zip"
        return {
            "run_id": run_record["run_id"],
            "name": run_record["name"],
            "config_name": run_record["source_config_name"],
            "seed": run_record["seed"],
            "grid_label": self._format_grid_label(config.engine.grid_shape),
            "steps": config.engine.num_steps,
            "status": run_record["status"],
            "finished_at": run_record["finished_at"],
            "elapsed_seconds": run_record["elapsed_seconds"],
            "config_digest": run_record["config_digest"],
            "energy_drift": metrics["energy_drift"],
            "norm_drift": metrics["norm_drift"],
            "bundle_size_bytes": bundle_path.stat().st_size,
            "bundle_size_label": self._format_bytes(bundle_path.stat().st_size),
            "experiment": experiment,
        }

    def _build_run_detail(self, run_dir: Path) -> dict:
        run_record = self._read_json(run_dir / "run.json")
        metrics = self._read_json(run_dir / "metrics.json")
        manifest = self._read_json(run_dir / "manifest.sha256.json")
        config = load_config(run_dir / "config.yaml")
        verification = verify_run_path(run_dir)
        bundle_path = run_dir / "evidence_bundle.zip"
        decision = evaluate_run_decision(
            config,
            metrics,
            verification_success=verification.success,
        )

        return {
            "summary": self._build_run_summary(run_dir),
            "config": config.to_dict(),
            "run_record": run_record,
            "metrics": metrics,
            "latest_snapshot": metrics["history"][-1],
            "decision": decision,
            "verification": {
                "success": verification.success,
                "checked_files": verification.checked_files,
                "errors": verification.errors,
            },
            "evidence": {
                "file_count": len(manifest.get("files", [])),
                "bundle_size_bytes": bundle_path.stat().st_size,
                "bundle_size_label": self._format_bytes(bundle_path.stat().st_size),
                "categories": self._evidence_categories(manifest),
                "artifact_paths": [entry["path"] for entry in manifest.get("files", [])],
            },
            "urls": {
                "bundle": f"/api/runs/{run_record['run_id']}/bundle",
                "report": f"/api/runs/{run_record['run_id']}/report",
            },
        }

    def _build_experiment_summary(self, experiment_dir: Path) -> dict:
        experiment_record = self._read_json(experiment_dir / "experiment.json")
        bundle_path = experiment_dir / "evidence_bundle.zip"
        return {
            "experiment_id": experiment_record["experiment_id"],
            "label": experiment_record["label"],
            "kind": experiment_record["kind"],
            "status": experiment_record.get("status", "completed"),
            "created_at": experiment_record["created_at"],
            "baseline_run_id": experiment_record["baseline_run_id"],
            "run_count": experiment_record["run_count"],
            "planned_run_count": experiment_record.get("planned_run_count"),
            "run_ids": experiment_record["run_ids"],
            "shared_experiment": experiment_record.get("shared_experiment"),
            "decision_available": bool((experiment_record.get("decision") or {}).get("available")),
            "decision_status": (experiment_record.get("decision") or {}).get("status"),
            "recommended_run_id": (experiment_record.get("decision") or {}).get("recommended_run_id"),
            "bundle_size_bytes": bundle_path.stat().st_size,
            "bundle_size_label": self._format_bytes(bundle_path.stat().st_size),
        }

    def _build_experiment_detail(self, experiment_dir: Path) -> dict:
        experiment_record = self._read_json(experiment_dir / "experiment.json")
        comparison = self._read_json(experiment_dir / "comparison.json")
        manifest = self._read_json(experiment_dir / "manifest.sha256.json")
        return {
            "summary": self._build_experiment_summary(experiment_dir),
            "experiment_record": experiment_record,
            "comparison": comparison,
            "decision": comparison.get("decision"),
            "evidence": {
                "file_count": len(manifest.get("files", [])),
                "artifact_paths": [entry["path"] for entry in manifest.get("files", [])],
            },
            "urls": {
                "bundle": f"/api/experiments/{experiment_record['experiment_id']}/bundle",
                "report": f"/api/experiments/{experiment_record['experiment_id']}/report",
            },
        }


def create_app(
    repo_root: str | Path | None = None,
    output_root: str | Path | None = None,
) -> FastAPI:
    service = CockpitService.create(repo_root=repo_root, output_root=output_root)

    app = FastAPI(
        title="QS-DMSS Cockpit",
        summary="Local-first API and browser cockpit for deterministic runs and evidence bundles.",
    )
    app.mount("/static", StaticFiles(directory=service.static_root), name="static")

    @app.get("/")
    def root() -> FileResponse:
        return FileResponse(service.index_path(), media_type="text/html")

    @app.get("/api/health")
    def health() -> dict:
        return {
            "status": "ok",
            "repo_root": str(service.repo_root),
            "output_root": str(service.output_root),
            "experiments_root": str(service.experiments_root),
        }

    @app.get("/api/configs")
    def configs() -> dict:
        items = service.list_configs()
        return {
            "items": items,
            "default_name": items[0]["name"] if items else None,
        }

    @app.get("/api/sweeps/parameters")
    def sweep_parameters() -> dict:
        return {"items": service.list_sweep_parameters()}

    @app.get("/api/showcases")
    def showcases() -> dict:
        try:
            items = service.list_showcases()
            campaign_studio = service.campaign_studio_preview()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=GENERIC_COCKPIT_ERROR_DETAIL,
            ) from None
        return {
            "items": items,
            "default_name": DEFAULT_SHOWCASE_NAME,
            "campaign_studio": campaign_studio,
        }

    @app.post("/api/showcases/{scenario}/run")
    def launch_showcase(scenario: str) -> dict:
        return service.launch_showcase(scenario)

    @app.post("/api/showcases/{scenario}/compare")
    def launch_showcase_comparison(scenario: str) -> dict:
        return service.launch_showcase_comparison(scenario)

    @app.get("/api/showcases/{scenario}/report")
    def showcase_markdown_report(scenario: str) -> FileResponse:
        report_path = service.showcase_markdown_path(scenario)
        return FileResponse(report_path, media_type="text/markdown")

    @app.get("/api/showcases/{scenario}/report.json")
    def showcase_json_report(scenario: str) -> FileResponse:
        report_path = service.showcase_json_path(scenario)
        return FileResponse(report_path, media_type="application/json")

    @app.get("/api/showcases/{scenario}/artifacts/{artifact_name}")
    def showcase_artifact(scenario: str, artifact_name: str) -> FileResponse:
        artifact_path = service.showcase_artifact_path(scenario, artifact_name)
        media_type = "application/octet-stream"
        if artifact_path.suffix == ".svg":
            media_type = "image/svg+xml"
        elif artifact_path.suffix == ".csv":
            media_type = "text/csv"
        return FileResponse(artifact_path, media_type=media_type, filename=artifact_path.name)

    @app.get("/api/runs")
    def runs() -> dict:
        return {"items": service.list_runs()}

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str) -> dict:
        return service.get_run_detail(run_id)

    @app.post("/api/runs")
    def launch_run(payload: LaunchRunRequest) -> dict:
        return service.launch_run(payload)

    @app.post("/api/compare")
    def compare_runs(payload: CompareRunsRequest) -> dict:
        return service.compare_runs(payload)

    @app.post("/api/experiments")
    def create_experiment(payload: CreateExperimentRequest) -> dict:
        return service.create_experiment(payload)

    @app.get("/api/experiments")
    def experiments() -> dict:
        return {"items": service.list_experiments()}

    @app.get("/api/experiments/{experiment_id}")
    def experiment_detail(experiment_id: str) -> dict:
        return service.get_experiment_detail(experiment_id)

    @app.get("/api/campaign-studies")
    def campaign_studies() -> dict:
        return {"items": service.list_campaign_study_templates()}

    @app.post("/api/campaign-studies")
    def save_campaign_study(payload: CampaignStudyTemplateRequest) -> dict:
        return service.save_campaign_study_template(payload)

    @app.post("/api/campaign-studies/import")
    def import_campaign_study(payload: CampaignStudyTemplateRequest) -> dict:
        return service.import_campaign_study_template(payload)

    @app.get("/api/campaign-studies/{template_id}")
    def campaign_study_detail(template_id: str) -> dict:
        return service.get_campaign_study_template(template_id)

    @app.get("/api/campaign-studies/{template_id}/download")
    def campaign_study_download(template_id: str) -> FileResponse:
        template_path = service.campaign_study_template_path(template_id)
        return FileResponse(
            template_path,
            media_type="application/json",
            filename=template_path.name,
        )

    @app.post("/api/sweeps")
    def launch_sweep(payload: SweepRequest) -> dict:
        return service.launch_sweep(payload)

    @app.post("/api/campaigns")
    def launch_campaign(payload: LaunchCampaignRequest) -> dict:
        return service.launch_campaign(payload)

    @app.post("/api/runs/{run_id}/verify")
    def verify_run(run_id: str) -> dict:
        return service.verify_run(run_id)

    @app.post("/api/runs/{run_id}/replay")
    def replay_run(run_id: str) -> dict:
        return service.replay_run(run_id)

    @app.get("/api/runs/{run_id}/bundle")
    def bundle_download(run_id: str) -> FileResponse:
        bundle_path = service.bundle_path(run_id)
        return FileResponse(
            bundle_path,
            media_type="application/zip",
            filename=bundle_path.name,
        )

    @app.get("/api/runs/{run_id}/report")
    def run_report(run_id: str) -> FileResponse:
        report_path = service.report_path(run_id)
        return FileResponse(report_path, media_type="text/html")

    @app.get("/api/experiments/{experiment_id}/bundle")
    def experiment_bundle_download(experiment_id: str) -> FileResponse:
        bundle_path = service.experiment_bundle_path(experiment_id)
        return FileResponse(
            bundle_path,
            media_type="application/zip",
            filename=bundle_path.name,
        )

    @app.get("/api/experiments/{experiment_id}/report")
    def experiment_report(experiment_id: str) -> FileResponse:
        report_path = service.experiment_report_path(experiment_id)
        return FileResponse(report_path, media_type="text/html")

    return app
