from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from qs_dmss.app import RunOutputs, execute_run_from_path
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.io.config import (
    SimulationConfig,
    load_config,
    write_config,
)
from qs_dmss.paths import contained_path, safe_filename

FRACTAL_VALIDATION_REPORT_SCHEMA_VERSION = 1
FRACTAL_VALIDATION_JSON_REPORT = "fractal-ssfm-validation.json"
FRACTAL_VALIDATION_MARKDOWN_REPORT = "fractal-ssfm-validation.md"
DEFAULT_TIME_STEP_FACTORS = (1.0, 0.5, 0.25)
DEFAULT_NORM_TOLERANCE = 1e-9


def _check(name: str, passed: bool, detail: str, **extra: Any) -> dict[str, Any]:
    return {
        "name": name,
        "success": passed,
        "detail": detail,
        **extra,
    }


def _format_value(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return str(value).lower()
    if isinstance(value, (int, float)):
        return f"{float(value):.6g}"
    return str(value)


def _table_cell(value: Any) -> str:
    return _format_value(value).replace("|", "\\|").replace("\n", " ")


def _state_vector(run_dir: Path) -> np.ndarray:
    payload = np.load(run_dir / "artifacts" / "final_state.npz")
    return payload["real"] + 1j * payload["imag"]


def _relative_l2_error(candidate: np.ndarray, reference: np.ndarray) -> float:
    numerator = np.linalg.norm((candidate - reference).ravel())
    denominator = np.linalg.norm(reference.ravel()) + 1e-300
    return float(numerator / denominator)


def _load_metrics(run_dir: Path) -> dict[str, Any]:
    return json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))


def _clone_fractal_config(
    config: SimulationConfig,
    *,
    run_name: str,
    time_step: float | None = None,
    num_steps: int | None = None,
    geometry_mode: str | None = None,
) -> SimulationConfig:
    geometry = config.geometry
    spectral = config.spectral
    if geometry is None or spectral is None:
        raise ValueError("Fractal SSFM validation requires geometry and spectral config sections")

    return replace(
        config,
        run=replace(config.run, name=run_name),
        engine=replace(
            config.engine,
            backend="numpy_fractal_ssfm",
            time_step=config.engine.time_step if time_step is None else time_step,
            num_steps=config.engine.num_steps if num_steps is None else num_steps,
        ),
        geometry=replace(
            geometry,
            mode=geometry.mode if geometry_mode is None else geometry_mode,
        ),
        spectral=replace(spectral, dealias_fraction=None),
    )


def _write_generated_config(config: SimulationConfig, configs_dir: Path, name: str) -> Path:
    path = contained_path(
        configs_dir,
        safe_filename(name, default="fractal-validation", suffixes=(".yaml",)),
    )
    write_config(config, path)
    return path


def _run_generated_config(config_path: Path, output_root: Path) -> tuple[RunOutputs, dict[str, Any]]:
    outputs = execute_run_from_path(
        config_path=config_path,
        output_root=output_root,
    )
    verification = verify_run_path(outputs.run_dir)
    metrics = _load_metrics(outputs.run_dir)
    return outputs, {
        "success": verification.success,
        "checked_files": verification.checked_files,
        "errors": verification.errors,
        "metrics": metrics,
    }


def _run_variant(
    config: SimulationConfig,
    *,
    name: str,
    configs_dir: Path,
    runs_root: Path,
) -> dict[str, Any]:
    config_path = _write_generated_config(config, configs_dir, f"{name}.yaml")
    outputs, verification = _run_generated_config(config_path, runs_root)
    metrics = verification["metrics"]
    diagnostics = metrics.get("diagnostics") or {}
    return {
        "name": name,
        "config_path": str(config_path),
        "run_id": outputs.run_id,
        "run_dir": str(outputs.run_dir),
        "bundle_path": str(outputs.bundle_path),
        "verification": {
            "success": verification["success"],
            "checked_files": verification["checked_files"],
            "errors": verification["errors"],
        },
        "backend": metrics.get("backend"),
        "geometry_mode": diagnostics.get("geometry_mode"),
        "conservation_mode": diagnostics.get("conservation_mode"),
        "nonconservative_reasons": diagnostics.get("nonconservative_reasons", []),
        "time_step": config.engine.time_step,
        "num_steps": config.engine.num_steps,
        "final_time": round(config.engine.time_step * config.engine.num_steps, 15),
        "grid_shape": list(config.engine.grid_shape),
        "relative_norm_error": diagnostics.get("relative_norm_error"),
        "spectral_leakage": diagnostics.get("spectral_leakage"),
        "aliasing_ratio": diagnostics.get("aliasing_ratio"),
        "norm_drift": metrics.get("norm_drift"),
        "energy_drift": metrics.get("energy_drift"),
        "max_density": metrics.get("max_density"),
    }


def _run_convergence(
    base_config: SimulationConfig,
    *,
    configs_dir: Path,
    runs_root: Path,
    time_step_factors: tuple[float, ...],
) -> dict[str, Any]:
    base_dt = base_config.engine.time_step
    final_time = base_dt * base_config.engine.num_steps
    runs: list[dict[str, Any]] = []

    for factor in time_step_factors:
        dt = base_dt * factor
        steps = max(1, int(round(final_time / dt)))
        adjusted_dt = final_time / steps
        name = f"convergence-dt-{factor:g}".replace(".", "p")
        config = _clone_fractal_config(
            base_config,
            run_name=f"fractal-ssfm-{name}",
            time_step=adjusted_dt,
            num_steps=steps,
            geometry_mode="fuzzy_potential",
        )
        runs.append(
            _run_variant(
                config,
                name=name,
                configs_dir=configs_dir,
                runs_root=runs_root,
            )
        )

    comparisons: list[dict[str, Any]] = []
    for index in range(len(runs) - 1):
        coarse = runs[index]
        fine = runs[index + 1]
        error = _relative_l2_error(
            _state_vector(Path(coarse["run_dir"])),
            _state_vector(Path(fine["run_dir"])),
        )
        comparisons.append(
            {
                "coarse_run": coarse["name"],
                "fine_run": fine["name"],
                "relative_l2_error": error,
            }
        )

    estimate = None
    if len(comparisons) >= 2:
        first_error = comparisons[0]["relative_l2_error"]
        second_error = comparisons[1]["relative_l2_error"]
        if first_error > 0 and second_error > 0:
            estimate = math.log(first_error / second_error, 2.0)

    finite_errors = all(
        math.isfinite(comparison["relative_l2_error"])
        for comparison in comparisons
    )
    nonincreasing_errors = (
        len(comparisons) < 2
        or comparisons[-1]["relative_l2_error"] <= comparisons[0]["relative_l2_error"] * 1.25
    )
    checks = [
        _check(
            "convergence:finite-errors",
            finite_errors,
            "all convergence comparison errors are finite",
        ),
        _check(
            "convergence:refinement-trend",
            nonincreasing_errors,
            "refined comparison error is not larger than the coarse comparison envelope",
            estimate=estimate,
        ),
    ]
    return {
        "success": all(check["success"] for check in checks),
        "time_step_factors": list(time_step_factors),
        "target_final_time": round(final_time, 15),
        "runs": runs,
        "comparisons": comparisons,
        "estimated_order": estimate,
        "checks": checks,
    }


def _run_norm_conservation(
    base_config: SimulationConfig,
    *,
    configs_dir: Path,
    runs_root: Path,
    norm_tolerance: float,
) -> dict[str, Any]:
    config = _clone_fractal_config(
        base_config,
        run_name="fractal-ssfm-norm-conservation",
        geometry_mode="fuzzy_potential",
    )
    run = _run_variant(
        config,
        name="norm-conservation-fuzzy-potential",
        configs_dir=configs_dir,
        runs_root=runs_root,
    )
    relative_norm_error = abs(float(run["relative_norm_error"]))
    checks = [
        _check(
            "norm:fuzzy-potential-tolerance",
            relative_norm_error <= norm_tolerance,
            "fuzzy_potential relative norm error is within tolerance",
            observed=relative_norm_error,
            tolerance=norm_tolerance,
        ),
        _check(
            "norm:fuzzy-potential-conservation-mode",
            run["conservation_mode"] == "phase_only_fuzzy_potential",
            "fuzzy_potential is labelled as the phase-only conservation mode",
            observed=run["conservation_mode"],
        ),
    ]
    return {
        "success": all(check["success"] for check in checks),
        "norm_tolerance": norm_tolerance,
        "run": run,
        "checks": checks,
    }


def _run_geometry_comparison(
    base_config: SimulationConfig,
    *,
    configs_dir: Path,
    runs_root: Path,
) -> dict[str, Any]:
    variants = []
    for mode in ("fuzzy_potential", "soft_mask", "hard_mask"):
        config = _clone_fractal_config(
            base_config,
            run_name=f"fractal-ssfm-geometry-{mode}",
            geometry_mode=mode,
        )
        variants.append(
            _run_variant(
                config,
                name=f"geometry-{mode}",
                configs_dir=configs_dir,
                runs_root=runs_root,
            )
        )

    by_mode = {variant["geometry_mode"]: variant for variant in variants}
    checks = [
        _check(
            "geometry:fuzzy-potential-default",
            by_mode["fuzzy_potential"]["conservation_mode"] == "phase_only_fuzzy_potential",
            "fuzzy_potential remains the scientific default conservation posture",
            observed=by_mode["fuzzy_potential"]["conservation_mode"],
        ),
        _check(
            "geometry:soft-mask-labelled",
            by_mode["soft_mask"]["conservation_mode"] == "nonconservative_exploratory"
            and bool(by_mode["soft_mask"]["nonconservative_reasons"]),
            "soft_mask is explicitly labelled exploratory/non-conservative",
            observed=by_mode["soft_mask"]["nonconservative_reasons"],
        ),
        _check(
            "geometry:hard-mask-labelled",
            by_mode["hard_mask"]["conservation_mode"] == "nonconservative_exploratory"
            and bool(by_mode["hard_mask"]["nonconservative_reasons"]),
            "hard_mask is explicitly labelled exploratory/non-conservative",
            observed=by_mode["hard_mask"]["nonconservative_reasons"],
        ),
    ]
    return {
        "success": all(check["success"] for check in checks),
        "variants": variants,
        "checks": checks,
    }


def _markdown_checks(checks: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        status = "PASS" if check["success"] else "FAIL"
        lines.append(
            "| "
            f"{_table_cell(check['name'])} | "
            f"{status} | "
            f"{_table_cell(check['detail'])} |"
        )
    return lines


def write_fractal_validation_markdown_report(report: dict[str, Any], path: Path) -> None:
    status = "PASS" if report["success"] else "FAIL"
    convergence = report["convergence"]
    norm = report["norm_conservation"]
    geometry = report["geometry_comparison"]
    lines = [
        "# QS-DMSS Fractal SSFM Validation Summary",
        "",
        "This summary accompanies the machine-readable",
        f"`{FRACTAL_VALIDATION_JSON_REPORT}` report.",
        "",
        "The harness validates the experimental `numpy_fractal_ssfm` backend as an",
        "evidence-bundled nonlinear wave backend for quadrant-partitioned fuzzy",
        "fractal effective potentials. It is not peer-reviewed physical validation,",
        "exact fractal-boundary PDE solving, or direct atomic-void modeling.",
        "",
        f"Overall status: **{status}**",
        f"Generated at: `{report['generated_at']}`",
        f"Config path: `{report['config_path']}`",
        f"Output root: `{report['output_root']}`",
        f"JSON report: `{report['report_path']}`",
        "",
        "## Strang Convergence",
        "",
        f"Estimated order: `{_format_value(convergence.get('estimated_order'))}`",
        "",
        "| Run | dt | steps | relative norm error | spectral leakage | aliasing ratio |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in convergence["runs"]:
        lines.append(
            "| "
            f"{_table_cell(run['name'])} | "
            f"{_table_cell(run['time_step'])} | "
            f"{_table_cell(run['num_steps'])} | "
            f"{_table_cell(run['relative_norm_error'])} | "
            f"{_table_cell(run['spectral_leakage'])} | "
            f"{_table_cell(run['aliasing_ratio'])} |"
        )

    lines.extend(["", "### Convergence Checks", "", *_markdown_checks(convergence["checks"])])

    lines.extend(
        [
            "",
            "## Norm Conservation",
            "",
            f"Tolerance: `{_format_value(norm['norm_tolerance'])}`",
            "",
            "| Run | geometry mode | conservation mode | relative norm error |",
            "| --- | --- | --- | ---: |",
        ]
    )
    norm_run = norm["run"]
    lines.append(
        "| "
        f"{_table_cell(norm_run['name'])} | "
        f"{_table_cell(norm_run['geometry_mode'])} | "
        f"{_table_cell(norm_run['conservation_mode'])} | "
        f"{_table_cell(norm_run['relative_norm_error'])} |"
    )
    lines.extend(["", "### Norm Checks", "", *_markdown_checks(norm["checks"])])

    lines.extend(
        [
            "",
            "## Geometry Comparison",
            "",
            "| Run | geometry mode | conservation mode | non-conservative reasons |",
            "| --- | --- | --- | --- |",
        ]
    )
    for variant in geometry["variants"]:
        lines.append(
            "| "
            f"{_table_cell(variant['name'])} | "
            f"{_table_cell(variant['geometry_mode'])} | "
            f"{_table_cell(variant['conservation_mode'])} | "
            f"{_table_cell(', '.join(variant['nonconservative_reasons']))} |"
        )
    lines.extend(["", "### Geometry Checks", "", *_markdown_checks(geometry["checks"]), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_fractal_ssfm(
    config_path: str | Path,
    output_root: str | Path | None = None,
    *,
    norm_tolerance: float = DEFAULT_NORM_TOLERANCE,
    time_step_factors: tuple[float, ...] = DEFAULT_TIME_STEP_FACTORS,
) -> dict[str, Any]:
    source_config_path = Path(config_path).resolve()
    base_config = load_config(source_config_path)
    if base_config.engine.backend != "numpy_fractal_ssfm":
        raise ValueError("Fractal SSFM validation requires backend='numpy_fractal_ssfm'")
    if base_config.geometry is None or base_config.spectral is None:
        raise ValueError("Fractal SSFM validation requires geometry and spectral sections")

    output_path = (
        Path(output_root).resolve()
        if output_root is not None
        else (Path.cwd() / "fractal-ssfm-validation").resolve()
    )
    output_path.mkdir(parents=True, exist_ok=True)
    configs_dir = output_path / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    runs_root = output_path / "runs"

    convergence = _run_convergence(
        base_config,
        configs_dir=configs_dir,
        runs_root=runs_root,
        time_step_factors=time_step_factors,
    )
    norm_conservation = _run_norm_conservation(
        base_config,
        configs_dir=configs_dir,
        runs_root=runs_root,
        norm_tolerance=norm_tolerance,
    )
    geometry_comparison = _run_geometry_comparison(
        base_config,
        configs_dir=configs_dir,
        runs_root=runs_root,
    )

    report = {
        "schema_version": FRACTAL_VALIDATION_REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(source_config_path),
        "output_root": str(output_path),
        "success": (
            convergence["success"]
            and norm_conservation["success"]
            and geometry_comparison["success"]
        ),
        "claim_boundary": (
            "Experimental pseudo-spectral nonlinear wave validation on a rectangular "
            "periodic grid; not exact fractal-boundary PDE solving, peer-reviewed "
            "physical validation, or direct atomic-void modeling."
        ),
        "convergence": convergence,
        "norm_conservation": norm_conservation,
        "geometry_comparison": geometry_comparison,
    }

    report_path = output_path / FRACTAL_VALIDATION_JSON_REPORT
    markdown_report_path = output_path / FRACTAL_VALIDATION_MARKDOWN_REPORT
    report["report_path"] = str(report_path)
    report["markdown_report_path"] = str(markdown_report_path)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_fractal_validation_markdown_report(report, markdown_report_path)
    return report
