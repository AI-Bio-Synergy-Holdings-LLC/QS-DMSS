from __future__ import annotations

import copy
import json
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


def coerce_sweep_values(path: str, values: list[Any]) -> list[int | float]:
    parameter = get_sweep_parameter(path)
    if not values:
        raise ValueError("Sweep values cannot be empty")
    if len(values) < 2:
        raise ValueError("Sweep requires at least two values")

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


def format_parameter_value(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    return f"{value:g}"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-").lower()
    return slug or "value"


def apply_sweep_value(
    config: dict[str, Any],
    parameter_path: str,
    value: int | float,
) -> dict[str, Any]:
    updated = copy.deepcopy(config)
    keys = parameter_path.split(".")
    target: dict[str, Any] = updated
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value

    parameter_slug = keys[-1].replace("_", "-")
    value_slug = _slugify(format_parameter_value(value))
    base_name = str(updated["run"]["name"]).strip() or "experiment"
    updated["run"]["name"] = f"{base_name}-{parameter_slug}-{value_slug}"
    return updated


def create_experiment_id(kind: str = "sweep") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{_slugify(kind)}-{timestamp}-{uuid.uuid4().hex[:8]}"


def build_experiment_context(
    experiment_id: str,
    label: str,
    parameter: SweepParameter,
    value: int | float,
    ordinal: int,
    total_runs: int,
) -> dict[str, Any]:
    return {
        "id": experiment_id,
        "kind": "sweep",
        "label": label,
        "parameter_path": parameter.path,
        "parameter_label": parameter.label,
        "parameter_value": value,
        "parameter_value_label": format_parameter_value(value),
        "ordinal": ordinal,
        "total_runs": total_runs,
    }


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
                "energy_drift": metrics["energy_drift"],
                "norm_drift": metrics["norm_drift"],
                "max_density": metrics["max_density"],
                "bundle_size_label": detail["evidence"]["bundle_size_label"],
                "verification_success": detail["verification"]["success"],
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

    experiment_ids = {
        row["run_id"]: detail["run_record"].get("experiment", {}).get("id")
        for row, detail in zip(rows, run_details)
    }
    labels = {
        detail["run_record"].get("experiment", {}).get("label")
        for detail in run_details
        if detail["run_record"].get("experiment")
    }
    parameter_paths = {
        detail["run_record"].get("experiment", {}).get("parameter_path")
        for detail in run_details
        if detail["run_record"].get("experiment")
    }
    parameter_labels = {
        detail["run_record"].get("experiment", {}).get("parameter_label")
        for detail in run_details
        if detail["run_record"].get("experiment")
    }

    shared_experiment = None
    unique_ids = {value for value in experiment_ids.values() if value}
    if len(unique_ids) == 1 and len(labels) == 1 and len(parameter_paths) == 1 and len(parameter_labels) == 1:
        shared_experiment = {
            "id": next(iter(unique_ids)),
            "label": next(iter(labels)),
            "parameter_path": next(iter(parameter_paths)),
            "parameter_label": next(iter(parameter_labels)),
        }

    return {
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


def persist_experiment_artifact(
    run_dirs: list[Path],
    run_details: list[dict[str, Any]],
    experiments_root: Path,
    *,
    label: str | None = None,
    experiment_id: str | None = None,
    kind: str = "comparison",
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
        "runs": run_entries,
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
