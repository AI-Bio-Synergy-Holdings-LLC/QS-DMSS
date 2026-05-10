from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from qs_dmss.app import execute_run_from_path, replay_run
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.paths import bundled_assets_root, contained_path, safe_filename


BENCHMARK_REPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class BenchmarkScenario:
    name: str
    config_path: Path
    expected_path: Path


def benchmark_assets_root() -> Path:
    root = bundled_assets_root() / "benchmarks"
    if not root.exists():
        raise FileNotFoundError(f"Benchmark assets not found at {root}")
    return root


def benchmark_scenarios_root() -> Path:
    root = benchmark_assets_root() / "scenarios"
    if not root.exists():
        raise FileNotFoundError(f"Benchmark scenarios not found at {root}")
    return root


def benchmark_expected_root() -> Path:
    root = benchmark_assets_root() / "expected"
    if not root.exists():
        raise FileNotFoundError(f"Benchmark expected metrics not found at {root}")
    return root


def list_benchmark_scenarios() -> list[str]:
    return sorted(path.stem for path in benchmark_scenarios_root().glob("*.yaml"))


def _normalize_scenario_name(name: str) -> str:
    filename = safe_filename(name, default="scenario", suffixes=(".yaml",))
    return Path(filename).stem


def resolve_benchmark_scenario(name: str) -> BenchmarkScenario:
    scenario_name = _normalize_scenario_name(name)
    config_path = contained_path(
        benchmark_scenarios_root(),
        f"{scenario_name}.yaml",
    )
    expected_path = contained_path(
        benchmark_expected_root(),
        f"{scenario_name}.metrics.json",
    )
    if not config_path.exists():
        raise FileNotFoundError(f"Benchmark scenario not found: {scenario_name}")
    if not expected_path.exists():
        raise FileNotFoundError(f"Benchmark expected metrics not found: {scenario_name}")
    return BenchmarkScenario(
        name=scenario_name,
        config_path=config_path,
        expected_path=expected_path,
    )


def _load_expected(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError(f"Unsupported benchmark expected-metrics schema: {path}")
    if not isinstance(payload.get("metric_envelopes"), dict):
        raise ValueError(f"Benchmark expected metrics missing envelopes: {path}")
    return payload


def _check(name: str, passed: bool, detail: str, **extra: Any) -> dict[str, Any]:
    return {
        "name": name,
        "success": passed,
        "detail": detail,
        **extra,
    }


def _check_metric_envelope(
    metric_name: str,
    observed: float,
    envelope: dict[str, Any],
) -> dict[str, Any]:
    passed = True
    failures: list[str] = []

    if "min" in envelope and observed < float(envelope["min"]):
        passed = False
        failures.append(f"{observed} < min {envelope['min']}")
    if "max" in envelope and observed > float(envelope["max"]):
        passed = False
        failures.append(f"{observed} > max {envelope['max']}")
    if "abs_max" in envelope and abs(observed) > float(envelope["abs_max"]):
        passed = False
        failures.append(f"|{observed}| > {envelope['abs_max']}")

    detail = "within expected envelope" if passed else "; ".join(failures)
    return _check(
        name=f"metric:{metric_name}",
        passed=passed,
        detail=detail,
        observed=observed,
        expected=envelope,
    )


def _check_history(metrics: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    history_expectations = expected.get("history", {})
    history = metrics.get("history")
    if not isinstance(history, list) or not history:
        return [_check("history", False, "metrics.history is missing or empty")]

    checks: list[dict[str, Any]] = []
    expected_points = history_expectations.get("expected_points")
    if expected_points is not None:
        observed_points = len(history)
        checks.append(
            _check(
                "history:points",
                observed_points == int(expected_points),
                "history point count matches"
                if observed_points == int(expected_points)
                else "history point count differs",
                observed=observed_points,
                expected=expected_points,
            )
        )

    expected_final_step = history_expectations.get("expected_final_step")
    if expected_final_step is not None:
        observed_final_step = history[-1].get("step")
        checks.append(
            _check(
                "history:final_step",
                observed_final_step == int(expected_final_step),
                "final step matches"
                if observed_final_step == int(expected_final_step)
                else "final step differs",
                observed=observed_final_step,
                expected=expected_final_step,
            )
        )

    return checks


def _validate_metric_envelopes(
    metrics: dict[str, Any],
    expected: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for metric_name, envelope in expected["metric_envelopes"].items():
        observed = metrics.get(metric_name)
        if not isinstance(observed, (int, float)) or isinstance(observed, bool):
            checks.append(
                _check(
                    name=f"metric:{metric_name}",
                    passed=False,
                    detail="metric missing or non-numeric",
                    observed=observed,
                    expected=envelope,
                )
            )
            continue
        checks.append(_check_metric_envelope(metric_name, float(observed), envelope))
    return checks


def _compare_replay_density(
    run_dir: Path,
    replay_dir: Path,
    expected: dict[str, Any],
) -> dict[str, Any]:
    replay_expectations = expected.get("replay", {})
    rtol = float(replay_expectations.get("density_allclose_rtol", 1e-10))
    atol = float(replay_expectations.get("density_allclose_atol", 1e-12))
    original_density = np.load(run_dir / "artifacts" / "final_density.npy")
    replay_density = np.load(replay_dir / "artifacts" / "final_density.npy")
    passed = bool(np.allclose(original_density, replay_density, rtol=rtol, atol=atol))
    return _check(
        "replay:final_density",
        passed,
        "replay final density matches"
        if passed
        else "replay final density differs beyond tolerance",
        expected={"rtol": rtol, "atol": atol},
    )


def _validate_one_scenario(
    scenario: BenchmarkScenario,
    output_root: Path,
    *,
    replay: bool,
) -> dict[str, Any]:
    expected = _load_expected(scenario.expected_path)
    checks: list[dict[str, Any]] = []
    scenario_report: dict[str, Any] = {
        "scenario": scenario.name,
        "description": expected.get("description", ""),
        "config_path": str(scenario.config_path),
        "expected_path": str(scenario.expected_path),
        "success": False,
        "checks": checks,
    }

    try:
        outputs = execute_run_from_path(
            scenario.config_path,
            output_root=output_root / "runs",
        )
        scenario_report.update(
            {
                "run_id": outputs.run_id,
                "run_dir": str(outputs.run_dir),
                "bundle_path": str(outputs.bundle_path),
            }
        )
        verification = verify_run_path(outputs.run_dir)
        checks.append(
            _check(
                "evidence:verify",
                verification.success,
                "run evidence verification passed"
                if verification.success
                else "run evidence verification failed",
                checked_files=verification.checked_files,
                errors=verification.errors,
            )
        )

        metrics = json.loads((outputs.run_dir / "metrics.json").read_text(encoding="utf-8"))
        checks.extend(_validate_metric_envelopes(metrics, expected))
        checks.extend(_check_history(metrics, expected))
        scenario_report["metrics"] = {
            metric: metrics.get(metric)
            for metric in expected["metric_envelopes"]
        }

        if replay:
            replay_outputs = replay_run(
                outputs.run_dir,
                output_root=output_root / "replays",
            )
            scenario_report.update(
                {
                    "replay_run_id": replay_outputs.run_id,
                    "replay_run_dir": str(replay_outputs.run_dir),
                    "replay_bundle_path": str(replay_outputs.bundle_path),
                }
            )
            replay_verification = verify_run_path(replay_outputs.run_dir)
            checks.append(
                _check(
                    "replay:verify",
                    replay_verification.success,
                    "replay evidence verification passed"
                    if replay_verification.success
                    else "replay evidence verification failed",
                    checked_files=replay_verification.checked_files,
                    errors=replay_verification.errors,
                )
            )
            checks.append(
                _compare_replay_density(
                    outputs.run_dir,
                    replay_outputs.run_dir,
                    expected,
                )
            )
    except Exception as exc:  # pragma: no cover - exercised through CLI failure paths.
        checks.append(
            _check(
                "scenario:execute",
                False,
                f"{type(exc).__name__}: {exc}",
            )
        )

    scenario_report["success"] = all(check["success"] for check in checks)
    return scenario_report


def validate_benchmark_scenarios(
    scenarios: list[str] | tuple[str, ...] | None = None,
    output_root: str | Path | None = None,
    *,
    replay: bool = True,
) -> dict[str, Any]:
    output_path = (
        Path(output_root).resolve()
        if output_root is not None
        else (Path.cwd() / "benchmark-validation").resolve()
    )
    output_path.mkdir(parents=True, exist_ok=True)

    scenario_names = list(scenarios) if scenarios else list_benchmark_scenarios()
    if not scenario_names:
        raise ValueError("No benchmark scenarios were selected")

    resolved_scenarios = [resolve_benchmark_scenario(name) for name in scenario_names]
    report = {
        "schema_version": BENCHMARK_REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_root": str(output_path),
        "replay_enabled": replay,
        "success": False,
        "scenarios": [
            _validate_one_scenario(
                scenario,
                output_path,
                replay=replay,
            )
            for scenario in resolved_scenarios
        ],
    }
    report["success"] = all(scenario["success"] for scenario in report["scenarios"])

    report_path = output_path / "benchmark-validation.json"
    report["report_path"] = str(report_path)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report
