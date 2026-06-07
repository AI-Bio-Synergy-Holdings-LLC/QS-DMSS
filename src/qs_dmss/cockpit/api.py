from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from qs_dmss.app import execute_run, replay_run as replay_existing_run
from qs_dmss.decision import evaluate_run_decision
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.experiment import (
    apply_sweep_value,
    build_campaign_context,
    build_campaign_plan,
    build_experiment_context,
    build_run_comparison,
    coerce_sweep_values,
    create_experiment_id,
    get_sweep_parameter,
    list_sweep_parameters,
    persist_failed_campaign_artifact,
    persist_experiment_artifact,
)
from qs_dmss.io.config import load_config, parse_config
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
)


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

        return {
            "campaign": {
                "id": campaign_plan["id"],
                "label": campaign_plan["label"],
                "strategy": campaign_plan["strategy"],
                "dimension_count": campaign_plan["dimension_count"],
                "planned_run_count": campaign_plan["planned_run_count"],
                "dimensions": campaign_plan["dimensions"],
                "run_ids": [summary["run_id"] for summary in summaries],
                "recommended_run_id": (comparison.get("decision") or {}).get("recommended_run_id"),
            },
            "runs": summaries,
            "comparison": comparison,
            "artifact": self._build_experiment_detail(artifact_outputs.experiment_dir),
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
        return {
            "name": selected.name,
            "label": selected.name.replace("-", " ").title(),
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
        }

    def _build_showcase_artifact_links(self, scenario: str, report: dict) -> list[dict]:
        links = []
        for key, value in report.get("artifacts", {}).items():
            artifact_name = Path(value).name
            links.append(
                {
                    "label": key.replace("_", " ").title(),
                    "name": artifact_name,
                    "url": f"/api/showcases/{scenario}/artifacts/{artifact_name}",
                }
            )
        return links

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
        items = service.list_showcases()
        return {
            "items": items,
            "default_name": DEFAULT_SHOWCASE_NAME,
        }

    @app.post("/api/showcases/{scenario}/run")
    def launch_showcase(scenario: str) -> dict:
        return service.launch_showcase(scenario)

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
