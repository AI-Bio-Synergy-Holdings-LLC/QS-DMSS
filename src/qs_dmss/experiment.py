from __future__ import annotations

import copy
import html
import json
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any

from qs_dmss.decision import apply_decision_profile
from qs_dmss.evidence.bundle import (
    create_bundle_zip_for_directory,
    write_experiment_report,
    write_manifest_for_directory,
)


@dataclass(frozen=True)
class SweepParameter:
    path: str
    label: str
    description: str
    value_type: str
    minimum: int | float | None = None
    step: int | float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "label": self.label,
            "description": self.description,
            "value_type": self.value_type,
            "minimum": self.minimum,
            "step": self.step,
        }


@dataclass(frozen=True)
class ExperimentOutputs:
    experiment_id: str
    experiment_dir: Path
    bundle_path: Path


SWEEP_PARAMETERS: tuple[SweepParameter, ...] = (
    SweepParameter(
        path="engine.g_int",
        label="Interaction",
        description="Sweep the nonlinear interaction term to compare stability and density response.",
        value_type="float",
        step=0.01,
    ),
    SweepParameter(
        path="engine.time_step",
        label="Time Step",
        description="Sweep the solver time step to study drift and runtime tradeoffs.",
        value_type="float",
        minimum=0.0001,
        step=0.001,
    ),
    SweepParameter(
        path="engine.num_steps",
        label="Steps",
        description="Sweep total solver steps to compare terminal state behavior across longer evolutions.",
        value_type="int",
        minimum=1,
        step=1,
    ),
    SweepParameter(
        path="initial.amplitude",
        label="Amplitude",
        description="Sweep initial density amplitude to compare mass concentration and drift.",
        value_type="float",
        minimum=0.0001,
        step=0.1,
    ),
    SweepParameter(
        path="initial.width",
        label="Width",
        description="Sweep Gaussian width to compare compact versus diffuse initial conditions.",
        value_type="float",
        minimum=0.0001,
        step=0.01,
    ),
    SweepParameter(
        path="run.seed",
        label="Seed",
        description="Sweep random seeds to compare deterministic replay behavior across initial phases.",
        value_type="int",
        minimum=0,
        step=1,
    ),
)

_SWEEP_PARAMETER_INDEX = {parameter.path: parameter for parameter in SWEEP_PARAMETERS}
_CAPTURED_RUN_FILES = {
    "config.yaml": "config",
    "run.json": "run_record",
    "metrics.json": "metrics",
    "report.html": "report",
    "manifest.sha256.json": "manifest",
    "evidence_bundle.zip": "bundle",
}


def list_sweep_parameters() -> list[dict[str, Any]]:
    return [parameter.to_dict() for parameter in SWEEP_PARAMETERS]


def get_sweep_parameter(path: str) -> SweepParameter:
    parameter = _SWEEP_PARAMETER_INDEX.get(path)
    if parameter is None:
        available = ", ".join(item.path for item in SWEEP_PARAMETERS)
        raise ValueError(f"Unsupported sweep parameter '{path}'. Expected one of: {available}")
    return parameter


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_int(value: Any, path: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Sweep value for '{path}' must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"Sweep value for '{path}' must be an integer")
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Sweep value for '{path}' cannot be empty")
        try:
            return int(stripped, 10)
        except ValueError as exc:
            raise ValueError(f"Sweep value for '{path}' must be an integer") from exc
    raise ValueError(f"Sweep value for '{path}' must be an integer")


def _coerce_float(value: Any, path: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"Sweep value for '{path}' must be numeric")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Sweep value for '{path}' cannot be empty")
        try:
            return float(stripped)
        except ValueError as exc:
            raise ValueError(f"Sweep value for '{path}' must be numeric") from exc
    raise ValueError(f"Sweep value for '{path}' must be numeric")


def coerce_parameter_values(
    path: str,
    values: list[Any],
    *,
    minimum_count: int = 2,
) -> list[int | float]:
    parameter = get_sweep_parameter(path)
    if not values:
        raise ValueError("Parameter values cannot be empty")
    if len(values) < minimum_count:
        qualifier = "value" if minimum_count == 1 else "values"
        raise ValueError(f"Parameter '{path}' requires at least {minimum_count} {qualifier}")

    coerced: list[int | float] = []
    for raw_value in values:
        if parameter.value_type == "int":
            value = _coerce_int(raw_value, path)
        else:
            value = _coerce_float(raw_value, path)
        if parameter.minimum is not None and value < parameter.minimum:
            raise ValueError(f"Sweep value for '{path}' must be >= {parameter.minimum}")
        coerced.append(value)
    return coerced


def coerce_sweep_values(path: str, values: list[Any]) -> list[int | float]:
    return coerce_parameter_values(path, values, minimum_count=2)


def format_parameter_value(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    return f"{value:g}"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-").lower()
    return slug or "value"


def apply_parameter_values(
    config: dict[str, Any],
    assignments: list[tuple[str, int | float]],
) -> dict[str, Any]:
    updated = copy.deepcopy(config)
    suffix_parts: list[str] = []
    for parameter_path, value in assignments:
        keys = parameter_path.split(".")
        target: dict[str, Any] = updated
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value

        parameter_slug = keys[-1].replace("_", "-")
        value_slug = _slugify(format_parameter_value(value))
        suffix_parts.append(f"{parameter_slug}-{value_slug}")

    base_name = str(updated["run"]["name"]).strip() or "experiment"
    updated["run"]["name"] = f"{base_name}-{'-'.join(suffix_parts)}"
    return updated


def apply_sweep_value(
    config: dict[str, Any],
    parameter_path: str,
    value: int | float,
) -> dict[str, Any]:
    return apply_parameter_values(config, [(parameter_path, value)])


def create_experiment_id(kind: str = "sweep") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{_slugify(kind)}-{timestamp}-{uuid.uuid4().hex[:8]}"


def _variant_label(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "baseline"
    return " | ".join(
        f"{entry['label']}={entry['value_label']}"
        for entry in entries
    )


def build_experiment_context(
    experiment_id: str,
    label: str,
    parameter: SweepParameter,
    value: int | float,
    ordinal: int,
    total_runs: int,
) -> dict[str, Any]:
    value_label = format_parameter_value(value)
    variant = [
        {
            "path": parameter.path,
            "label": parameter.label,
            "value": value,
            "value_label": value_label,
        }
    ]
    return {
        "id": experiment_id,
        "kind": "sweep",
        "label": label,
        "strategy": "list",
        "dimensions": [
            {
                "path": parameter.path,
                "label": parameter.label,
            }
        ],
        "dimension_count": 1,
        "parameter_path": parameter.path,
        "parameter_label": parameter.label,
        "parameter_value": value,
        "parameter_value_label": value_label,
        "variant": variant,
        "variant_label": value_label,
        "ordinal": ordinal,
        "total_runs": total_runs,
    }


def build_campaign_plan(
    config: dict[str, Any],
    *,
    experiment_id: str | None = None,
) -> dict[str, Any]:
    campaign = config.get("campaign")
    if not isinstance(campaign, dict):
        raise ValueError("Selected config does not define a decision campaign")

    strategy = str(campaign.get("strategy", "grid")).strip() or "grid"
    if strategy != "grid":
        raise ValueError(f"Unsupported campaign strategy '{strategy}'")

    dimensions_data = campaign.get("dimensions")
    if not isinstance(dimensions_data, list) or not dimensions_data:
        raise ValueError("Campaign must define at least one search dimension")

    dimensions: list[dict[str, Any]] = []
    for raw_dimension in dimensions_data:
        if not isinstance(raw_dimension, dict):
            raise ValueError("Campaign dimensions must be mappings")
        path = str(raw_dimension.get("path") or "").strip()
        parameter = get_sweep_parameter(path)
        raw_values = raw_dimension.get("values")
        if not isinstance(raw_values, list):
            raise ValueError(f"Campaign dimension '{path}' must include a value list")
        values = coerce_parameter_values(path, raw_values, minimum_count=1)
        dimensions.append(
            {
                "path": parameter.path,
                "label": parameter.label,
                "description": parameter.description,
                "value_type": parameter.value_type,
                "values": values,
            }
        )

    planned_run_count = 1
    for dimension in dimensions:
        planned_run_count *= len(dimension["values"])
    if planned_run_count < 2:
        raise ValueError("Campaign requires at least two planned runs")

    max_runs = int(campaign.get("max_runs", planned_run_count))
    if planned_run_count > max_runs:
        raise ValueError(
            f"Campaign expands to {planned_run_count} runs, which exceeds campaign.max_runs={max_runs}"
        )

    label = str(campaign.get("label") or f"{config['run']['name']} decision campaign").strip()
    resolved_id = experiment_id or create_experiment_id("campaign")
    variants: list[dict[str, Any]] = []

    for ordinal, value_tuple in enumerate(
        product(*(dimension["values"] for dimension in dimensions)),
        start=1,
    ):
        variant = [
            {
                "path": dimension["path"],
                "label": dimension["label"],
                "value": value,
                "value_label": format_parameter_value(value),
            }
            for dimension, value in zip(dimensions, value_tuple)
        ]
        variants.append(
            {
                "ordinal": ordinal,
                "variant": variant,
                "variant_label": _variant_label(variant),
                "config": apply_parameter_values(
                    config,
                    [(entry["path"], entry["value"]) for entry in variant],
                ),
            }
        )

    return {
        "id": resolved_id,
        "kind": "campaign",
        "label": label,
        "strategy": strategy,
        "dimension_count": len(dimensions),
        "planned_run_count": planned_run_count,
        "dimensions": [
            {
                "path": dimension["path"],
                "label": dimension["label"],
                "description": dimension["description"],
                "value_type": dimension["value_type"],
                "values": dimension["values"],
            }
            for dimension in dimensions
        ],
        "variants": variants,
    }


def build_campaign_context(
    experiment_id: str,
    label: str,
    strategy: str,
    dimensions: list[dict[str, Any]],
    variant: list[dict[str, Any]],
    ordinal: int,
    total_runs: int,
) -> dict[str, Any]:
    variant_label = _variant_label(variant)
    context = {
        "id": experiment_id,
        "kind": "campaign",
        "label": label,
        "strategy": strategy,
        "dimensions": [
            {
                "path": dimension["path"],
                "label": dimension["label"],
            }
            for dimension in dimensions
        ],
        "dimension_count": len(dimensions),
        "variant": variant,
        "variant_label": variant_label,
        "ordinal": ordinal,
        "total_runs": total_runs,
    }

    if len(variant) == 1:
        entry = variant[0]
        context.update(
            {
                "parameter_path": entry["path"],
                "parameter_label": entry["label"],
                "parameter_value": entry["value"],
                "parameter_value_label": entry["value_label"],
            }
        )
    else:
        context.update(
            {
                "parameter_path": None,
                "parameter_label": "Campaign Variant",
                "parameter_value": None,
                "parameter_value_label": variant_label,
            }
        )

    return context


def _metric_range(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    min_row = min(rows, key=lambda row: row[key])
    max_row = max(rows, key=lambda row: row[key])
    return {
        "min": min_row[key],
        "min_run_id": min_row["run_id"],
        "max": max_row[key],
        "max_run_id": max_row["run_id"],
        "span": round(max_row[key] - min_row[key], 12),
    }


def _comparison_execution_job(detail: dict[str, Any]) -> dict[str, Any] | None:
    execution_job = detail.get("execution_job")
    if isinstance(execution_job, dict):
        summary = execution_job.get("summary")
        if isinstance(summary, dict):
            return summary

    summary_job = (detail.get("summary") or {}).get("execution_job")
    if isinstance(summary_job, dict):
        return summary_job
    return None


def build_run_comparison(run_details: list[dict[str, Any]]) -> dict[str, Any]:
    if len(run_details) < 2:
        raise ValueError("At least two runs are required for comparison")

    baseline = run_details[0]
    baseline_metrics = baseline["metrics"]
    rows: list[dict[str, Any]] = []

    for detail in run_details:
        run_record = detail["run_record"]
        metrics = detail["metrics"]
        experiment = run_record.get("experiment") or {}
        rows.append(
            {
                "run_id": run_record["run_id"],
                "name": run_record["name"],
                "config_name": run_record["source_config_name"],
                "seed": run_record["seed"],
                "finished_at": run_record["finished_at"],
                "elapsed_seconds": run_record["elapsed_seconds"],
                "parameter_path": experiment.get("parameter_path"),
                "parameter_label": experiment.get("parameter_label"),
                "parameter_value": experiment.get("parameter_value"),
                "parameter_value_label": experiment.get("parameter_value_label"),
                "variant": experiment.get("variant"),
                "variant_label": experiment.get("variant_label"),
                "dimension_count": experiment.get("dimension_count"),
                "energy_drift": metrics["energy_drift"],
                "norm_drift": metrics["norm_drift"],
                "max_density": metrics["max_density"],
                "bundle_size_label": detail["evidence"]["bundle_size_label"],
                "verification_success": detail["verification"]["success"],
                "execution_job": _comparison_execution_job(detail),
                "delta_from_baseline": {
                    "energy_drift": round(
                        metrics["energy_drift"] - baseline_metrics["energy_drift"],
                        12,
                    ),
                    "norm_drift": round(
                        metrics["norm_drift"] - baseline_metrics["norm_drift"],
                        12,
                    ),
                    "max_density": round(
                        metrics["max_density"] - baseline_metrics["max_density"],
                        12,
                    ),
                    "elapsed_seconds": round(
                        run_record["elapsed_seconds"] - baseline["run_record"]["elapsed_seconds"],
                        12,
                    ),
                },
            }
        )

    shared_experiment = None
    experiment_contexts = [
        detail["run_record"].get("experiment")
        for detail in run_details
        if detail["run_record"].get("experiment")
    ]
    unique_ids = {
        experiment.get("id")
        for experiment in experiment_contexts
        if experiment and experiment.get("id")
    }
    labels = {
        experiment.get("label")
        for experiment in experiment_contexts
        if experiment and experiment.get("label")
    }
    kinds = {
        experiment.get("kind")
        for experiment in experiment_contexts
        if experiment and experiment.get("kind")
    }
    dimension_signatures = {
        json.dumps(experiment.get("dimensions") or [], sort_keys=True)
        for experiment in experiment_contexts
    }
    if (
        len(experiment_contexts) == len(run_details)
        and len(unique_ids) == 1
        and len(labels) == 1
        and len(kinds) == 1
        and len(dimension_signatures) == 1
    ):
        template = experiment_contexts[0] or {}
        shared_experiment = {
            "id": next(iter(unique_ids)),
            "label": next(iter(labels)),
            "kind": next(iter(kinds)),
            "strategy": template.get("strategy"),
            "dimension_count": template.get("dimension_count"),
            "dimensions": template.get("dimensions") or [],
            "parameter_path": template.get("parameter_path"),
            "parameter_label": template.get("parameter_label"),
        }

    comparison = {
        "baseline_run_id": baseline["summary"]["run_id"],
        "shared_experiment": shared_experiment,
        "rows": rows,
        "ranges": {
            "energy_drift": _metric_range(rows, "energy_drift"),
            "norm_drift": _metric_range(rows, "norm_drift"),
            "max_density": _metric_range(rows, "max_density"),
            "elapsed_seconds": _metric_range(rows, "elapsed_seconds"),
        },
        "highlights": {
            "lowest_abs_energy_drift_run_id": min(rows, key=lambda row: abs(row["energy_drift"]))["run_id"],
            "lowest_abs_norm_drift_run_id": min(rows, key=lambda row: abs(row["norm_drift"]))["run_id"],
            "highest_max_density_run_id": max(rows, key=lambda row: row["max_density"])["run_id"],
        },
    }
    comparison["decision"] = apply_decision_profile(comparison, run_details)
    return comparison


def _default_experiment_label(
    kind: str,
    comparison: dict[str, Any],
    run_details: list[dict[str, Any]],
) -> str:
    shared = comparison.get("shared_experiment")
    if kind == "sweep" and shared and shared.get("label"):
        return str(shared["label"])
    if shared and shared.get("label"):
        return f"{shared['label']} comparison"
    return f"{len(run_details)}-run comparison"


def _copy_run_capture(
    run_dir: Path,
    destination_dir: Path,
    experiment_dir: Path,
) -> dict[str, str]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}
    for filename, key in _CAPTURED_RUN_FILES.items():
        source = run_dir / filename
        if not source.exists():
            continue
        target = destination_dir / filename
        shutil.copy2(source, target)
        copied[key] = target.relative_to(experiment_dir).as_posix()
    return copied


def _shared_context_from_campaign_plan(campaign_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": campaign_plan["id"],
        "label": campaign_plan["label"],
        "kind": "campaign",
        "strategy": campaign_plan["strategy"],
        "dimension_count": campaign_plan["dimension_count"],
        "dimensions": [
            {
                "path": dimension["path"],
                "label": dimension["label"],
            }
            for dimension in campaign_plan["dimensions"]
        ],
        "parameter_path": None,
        "parameter_label": "Campaign Variant",
    }


def _failure_rows(run_details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for detail in run_details:
        run_record = detail["run_record"]
        metrics = detail["metrics"]
        experiment = run_record.get("experiment") or {}
        rows.append(
            {
                "run_id": run_record["run_id"],
                "name": run_record["name"],
                "config_name": run_record["source_config_name"],
                "seed": run_record["seed"],
                "finished_at": run_record["finished_at"],
                "elapsed_seconds": run_record["elapsed_seconds"],
                "parameter_path": experiment.get("parameter_path"),
                "parameter_label": experiment.get("parameter_label"),
                "parameter_value": experiment.get("parameter_value"),
                "parameter_value_label": experiment.get("parameter_value_label"),
                "variant": experiment.get("variant"),
                "variant_label": experiment.get("variant_label"),
                "dimension_count": experiment.get("dimension_count"),
                "energy_drift": metrics["energy_drift"],
                "norm_drift": metrics["norm_drift"],
                "max_density": metrics["max_density"],
                "bundle_size_label": detail["evidence"]["bundle_size_label"],
                "verification_success": detail["verification"]["success"],
                "execution_job": _comparison_execution_job(detail),
            }
        )
    return rows


def _write_failed_campaign_report(
    experiment_dir: Path,
    experiment_record: dict[str, Any],
    comparison: dict[str, Any],
) -> None:
    failure = experiment_record["failure"]
    shared = experiment_record["shared_experiment"]
    dimension_rows = "".join(
        f"<li>{html.escape(str(dimension['label']))} (<code>{html.escape(str(dimension['path']))}</code>)</li>"
        for dimension in shared.get("dimensions", [])
    )
    run_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['run_id'])}</td>"
        f"<td>{html.escape(str(row.get('variant_label') or '-'))}</td>"
        f"<td>{row['energy_drift']}</td>"
        f"<td>{row['norm_drift']}</td>"
        f"<td>{row['max_density']}</td>"
        f"<td>{row['elapsed_seconds']}</td>"
        "</tr>"
        for row in comparison["rows"]
    )
    if not run_rows:
        run_rows = "<tr><td colspan=\"6\">No variants completed before failure.</td></tr>"

    html_body = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>QS-DMSS Failed Campaign Report</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 32px; color: #111827; }}
      h1, h2 {{ margin-bottom: 0.4rem; }}
      table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
      th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
      th {{ background: #f3f4f6; }}
      code {{ background: #f3f4f6; padding: 2px 4px; }}
    </style>
  </head>
  <body>
    <h1>QS-DMSS Failed Campaign Report</h1>
    <p><strong>Experiment ID:</strong> <code>{html.escape(experiment_record['experiment_id'])}</code></p>
    <p><strong>Label:</strong> {html.escape(experiment_record['label'])}</p>
    <p><strong>Status:</strong> {html.escape(experiment_record['status'])}</p>
    <p><strong>Error:</strong> {html.escape(failure['message'])}</p>
    <h2>Campaign Context</h2>
    <ul>
      <li>Strategy: {html.escape(str(shared.get('strategy', '-')))}</li>
      <li>Completed runs: {failure['completed_run_count']} of {failure['planned_run_count']}</li>
    </ul>
    <h3>Dimensions</h3>
    <ul>
      {dimension_rows}
    </ul>
    <h2>Completed Variants</h2>
    <table>
      <thead>
        <tr>
          <th>Run ID</th>
          <th>Variant</th>
          <th>Energy Drift</th>
          <th>Norm Drift</th>
          <th>Max Density</th>
          <th>Elapsed Seconds</th>
        </tr>
      </thead>
      <tbody>
        {run_rows}
      </tbody>
    </table>
  </body>
</html>
"""
    (experiment_dir / "report.html").write_text(html_body, encoding="utf-8")


def persist_failed_campaign_artifact(
    *,
    campaign_plan: dict[str, Any],
    run_dirs: list[Path],
    run_details: list[dict[str, Any]],
    experiments_root: Path,
    error: BaseException,
    execution_job: dict[str, Any] | None = None,
) -> ExperimentOutputs:
    if len(run_dirs) != len(run_details):
        raise ValueError("Run directory count must match run detail count")

    experiments_root = Path(experiments_root).resolve()
    experiments_root.mkdir(parents=True, exist_ok=True)
    experiment_dir = experiments_root / campaign_plan["id"]
    try:
        experiment_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"Experiment artifact already exists: {campaign_plan['id']}") from exc

    rows = _failure_rows(run_details)
    rows_by_run_id = {row["run_id"]: row for row in rows}
    run_entries: list[dict[str, Any]] = []
    for run_dir, detail in zip(run_dirs, run_details):
        run_id = detail["summary"]["run_id"]
        row = rows_by_run_id[run_id]
        artifact_paths = _copy_run_capture(
            run_dir=run_dir,
            destination_dir=experiment_dir / "runs" / run_id,
            experiment_dir=experiment_dir,
        )
        run_entries.append({**row, "artifacts": artifact_paths})

    failure = {
        "message": str(error) or error.__class__.__name__,
        "error_type": error.__class__.__name__,
        "completed_run_count": len(run_entries),
        "planned_run_count": campaign_plan["planned_run_count"],
    }
    decision = {
        "available": False,
        "status": "failed",
        "reason": "Campaign execution failed before every planned variant completed.",
    }
    comparison = {
        "schema_version": 1,
        "status": "failed",
        "failure": failure,
        "baseline_run_id": rows[0]["run_id"] if rows else None,
        "shared_experiment": _shared_context_from_campaign_plan(campaign_plan),
        "rows": rows,
        "ranges": {},
        "highlights": {},
        "decision": decision,
    }
    (experiment_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2),
        encoding="utf-8",
    )

    experiment_record = {
        "schema_version": 1,
        "status": "failed",
        "experiment_id": campaign_plan["id"],
        "label": campaign_plan["label"],
        "kind": "campaign",
        "created_at": _utc_now(),
        "baseline_run_id": comparison["baseline_run_id"],
        "run_count": len(run_entries),
        "planned_run_count": campaign_plan["planned_run_count"],
        "run_ids": [entry["run_id"] for entry in run_entries],
        "shared_experiment": comparison["shared_experiment"],
        "ranges": comparison["ranges"],
        "highlights": comparison["highlights"],
        "decision": decision,
        "failure": failure,
        "runs": run_entries,
        "execution_job": execution_job,
        "artifacts": {
            "experiment": "experiment.json",
            "comparison": "comparison.json",
            "report": "report.html",
            "manifest": "manifest.sha256.json",
            "bundle": "evidence_bundle.zip",
        },
    }
    (experiment_dir / "experiment.json").write_text(
        json.dumps(experiment_record, indent=2),
        encoding="utf-8",
    )

    _write_failed_campaign_report(
        experiment_dir=experiment_dir,
        experiment_record=experiment_record,
        comparison=comparison,
    )
    write_manifest_for_directory(experiment_dir)
    bundle_path = create_bundle_zip_for_directory(experiment_dir)
    return ExperimentOutputs(
        experiment_id=campaign_plan["id"],
        experiment_dir=experiment_dir,
        bundle_path=bundle_path,
    )


def persist_experiment_artifact(
    run_dirs: list[Path],
    run_details: list[dict[str, Any]],
    experiments_root: Path,
    *,
    label: str | None = None,
    experiment_id: str | None = None,
    kind: str = "comparison",
    execution_job: dict[str, Any] | None = None,
) -> ExperimentOutputs:
    if len(run_dirs) < 2:
        raise ValueError("At least two runs are required to persist an experiment")
    if len(run_dirs) != len(run_details):
        raise ValueError("Run directory count must match run detail count")

    comparison = build_run_comparison(run_details)
    resolved_id = experiment_id or create_experiment_id(kind)
    resolved_label = label or _default_experiment_label(kind, comparison, run_details)

    experiments_root = Path(experiments_root).resolve()
    experiments_root.mkdir(parents=True, exist_ok=True)
    experiment_dir = experiments_root / resolved_id
    try:
        experiment_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"Experiment artifact already exists: {resolved_id}") from exc

    rows_by_run_id = {row["run_id"]: row for row in comparison["rows"]}
    run_entries: list[dict[str, Any]] = []
    for run_dir, detail in zip(run_dirs, run_details):
        run_id = detail["summary"]["run_id"]
        row = rows_by_run_id[run_id]
        artifact_paths = _copy_run_capture(
            run_dir=run_dir,
            destination_dir=experiment_dir / "runs" / run_id,
            experiment_dir=experiment_dir,
        )
        run_entries.append(
            {
                **row,
                "artifacts": artifact_paths,
            }
        )

    comparison_path = experiment_dir / "comparison.json"
    comparison_path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")

    experiment_record = {
        "schema_version": 1,
        "experiment_id": resolved_id,
        "label": resolved_label,
        "kind": kind,
        "created_at": _utc_now(),
        "baseline_run_id": comparison["baseline_run_id"],
        "run_count": len(run_entries),
        "run_ids": [entry["run_id"] for entry in run_entries],
        "shared_experiment": comparison.get("shared_experiment"),
        "ranges": comparison["ranges"],
        "highlights": comparison["highlights"],
        "decision": comparison.get("decision"),
        "runs": run_entries,
        "execution_job": execution_job,
        "artifacts": {
            "experiment": "experiment.json",
            "comparison": "comparison.json",
            "report": "report.html",
            "manifest": "manifest.sha256.json",
            "bundle": "evidence_bundle.zip",
        },
    }
    experiment_record_path = experiment_dir / "experiment.json"
    experiment_record_path.write_text(json.dumps(experiment_record, indent=2), encoding="utf-8")

    write_experiment_report(
        experiment_dir=experiment_dir,
        experiment_record=experiment_record,
        comparison=comparison,
    )
    write_manifest_for_directory(experiment_dir)
    bundle_path = create_bundle_zip_for_directory(experiment_dir)

    return ExperimentOutputs(
        experiment_id=resolved_id,
        experiment_dir=experiment_dir,
        bundle_path=bundle_path,
    )
