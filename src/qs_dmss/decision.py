from __future__ import annotations

import json
from typing import Any

from qs_dmss.io.config import (
    ConstraintConfig,
    RankingConfig,
    SimulationConfig,
    SUPPORTED_DECISION_METRICS,
)

METRIC_LABELS = {
    "energy_drift": "Energy Drift",
    "norm_drift": "Norm Drift",
    "max_density": "Max Density",
    "elapsed_seconds": "Elapsed Seconds",
}
DEFAULT_METRIC_GOALS = {
    "energy_drift": "minimize_abs",
    "norm_drift": "minimize_abs",
    "max_density": "maximize",
    "elapsed_seconds": "minimize",
}


def _default_constraints_payload() -> dict[str, Any]:
    return {"require_verification": True}


def _default_ranking_payload() -> dict[str, Any]:
    return RankingConfig().to_dict()


def decision_profile_from_config(config: SimulationConfig) -> dict[str, Any] | None:
    if config.objective is None:
        return None
    return {
        "objective": config.objective.to_dict(),
        "constraints": {
            **_default_constraints_payload(),
            **(config.constraints or ConstraintConfig()).to_dict(),
        },
        "ranking": (config.ranking or RankingConfig()).to_dict(),
    }


def decision_profile_from_mapping(config_mapping: dict[str, Any]) -> dict[str, Any] | None:
    objective = config_mapping.get("objective")
    if not isinstance(objective, dict):
        return None
    constraints = config_mapping.get("constraints")
    ranking = config_mapping.get("ranking")
    return {
        "objective": objective,
        "constraints": {
            **_default_constraints_payload(),
            **(constraints if isinstance(constraints, dict) else {}),
        },
        "ranking": {
            **_default_ranking_payload(),
            **(ranking if isinstance(ranking, dict) else {}),
        },
    }


def _canonical_profile(profile: dict[str, Any]) -> str:
    return json.dumps(profile, sort_keys=True, separators=(",", ":"))


def _profile_groups(
    profiles: list[dict[str, Any] | None],
    run_details: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for profile, detail in zip(profiles, run_details):
        if profile is None:
            continue
        canonical = _canonical_profile(profile)
        objective = profile.get("objective") or {}
        group = grouped.setdefault(
            canonical,
            {
                "objective_name": str(objective.get("name") or "Unnamed objective"),
                "primary_metric": str(objective.get("primary_metric") or "-"),
                "goal": str(objective.get("goal") or "-"),
                "run_ids": [],
            },
        )
        run_record = detail.get("run_record") or {}
        summary = detail.get("summary") or {}
        run_id = run_record.get("run_id") or summary.get("run_id") or ""
        group["run_ids"].append(str(run_id))
    return list(grouped.values())


def _shared_decision_profile(
    run_details: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str, str, list[dict[str, Any]]]:
    profiles: list[dict[str, Any] | None] = []
    for detail in run_details:
        run_record = detail.get("run_record") or {}
        profile = run_record.get("decision_profile")
        if not isinstance(profile, dict):
            profile = decision_profile_from_mapping(detail.get("config") or {})
        profiles.append(profile if isinstance(profile, dict) else None)

    available_profiles = [profile for profile in profiles if profile is not None]
    groups = _profile_groups(profiles, run_details)
    if not available_profiles:
        return (
            None,
            "No objective profile is configured for the selected runs. Metrics and "
            "deltas remain available for evidence-only comparison.",
            "unconfigured",
            groups,
        )
    if len(available_profiles) != len(profiles):
        return (
            None,
            "Some selected runs are missing an objective profile. Metrics and deltas "
            "remain comparable, but QS-DMSS will not rank runs under an incomplete "
            "scoring contract.",
            "partial",
            groups,
        )

    canonical_profiles = {_canonical_profile(profile) for profile in available_profiles}
    if len(canonical_profiles) != 1:
        return (
            None,
            "Selected runs use different objective profiles. QS-DMSS preserves an "
            "evidence-only comparison and does not force one recommendation across "
            "incompatible scoring contracts.",
            "mixed",
            groups,
        )

    return available_profiles[0], "", "shared", groups


def _metric_value(row: dict[str, Any], metric: str) -> float:
    return float(row[metric])


def _goal_for_metric(profile: dict[str, Any], metric: str) -> str:
    objective = profile["objective"]
    if metric == objective["primary_metric"]:
        return str(objective["goal"])
    return DEFAULT_METRIC_GOALS[metric]


def _objective_value(
    row: dict[str, Any],
    metric: str,
    goal: str,
    target_value: float | None = None,
) -> float:
    actual_value = _metric_value(row, metric)
    if goal == "maximize":
        return actual_value
    if goal == "minimize":
        return actual_value
    if goal == "minimize_abs":
        return abs(actual_value)
    if goal == "target":
        if target_value is None:
            raise ValueError("target_value is required for target-based objectives")
        return abs(actual_value - target_value)
    raise ValueError(f"Unsupported decision goal: {goal}")


def _format_metric_value(metric: str, value: float) -> str:
    if metric in {"energy_drift", "norm_drift"}:
        return f"{value:.3e}"
    if metric == "elapsed_seconds":
        return f"{value:.3f}s"
    return f"{value:g}"


def _build_constraint_checks(
    constraints: dict[str, Any],
    row: dict[str, Any],
    verification_success: bool,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    if constraints.get("max_abs_energy_drift") is not None:
        threshold = float(constraints["max_abs_energy_drift"])
        actual = abs(float(row["energy_drift"]))
        checks.append(
            {
                "id": "max_abs_energy_drift",
                "label": f"Absolute energy drift <= {_format_metric_value('energy_drift', threshold)}",
                "actual_value": actual,
                "actual_display": _format_metric_value("energy_drift", actual),
                "threshold_value": threshold,
                "passed": actual <= threshold,
            }
        )

    if constraints.get("max_abs_norm_drift") is not None:
        threshold = float(constraints["max_abs_norm_drift"])
        actual = abs(float(row["norm_drift"]))
        checks.append(
            {
                "id": "max_abs_norm_drift",
                "label": f"Absolute norm drift <= {_format_metric_value('norm_drift', threshold)}",
                "actual_value": actual,
                "actual_display": _format_metric_value("norm_drift", actual),
                "threshold_value": threshold,
                "passed": actual <= threshold,
            }
        )

    if constraints.get("min_max_density") is not None:
        threshold = float(constraints["min_max_density"])
        actual = float(row["max_density"])
        checks.append(
            {
                "id": "min_max_density",
                "label": f"Max density >= {_format_metric_value('max_density', threshold)}",
                "actual_value": actual,
                "actual_display": _format_metric_value("max_density", actual),
                "threshold_value": threshold,
                "passed": actual >= threshold,
            }
        )

    if constraints.get("max_elapsed_seconds") is not None:
        threshold = float(constraints["max_elapsed_seconds"])
        actual = float(row["elapsed_seconds"])
        checks.append(
            {
                "id": "max_elapsed_seconds",
                "label": f"Elapsed seconds <= {_format_metric_value('elapsed_seconds', threshold)}",
                "actual_value": actual,
                "actual_display": _format_metric_value("elapsed_seconds", actual),
                "threshold_value": threshold,
                "passed": actual <= threshold,
            }
        )

    if constraints.get("require_verification", True):
        checks.append(
            {
                "id": "require_verification",
                "label": "Evidence bundle verification must pass",
                "actual_value": 1 if verification_success else 0,
                "actual_display": "verified" if verification_success else "failed",
                "threshold_value": 1,
                "passed": verification_success,
            }
        )

    return checks


def _evaluate_row_decision(
    profile: dict[str, Any],
    row: dict[str, Any],
    verification_success: bool,
) -> dict[str, Any]:
    objective = profile["objective"]
    primary_metric = str(objective["primary_metric"])
    primary_goal = str(objective["goal"])
    target_value = objective.get("target_value")
    primary_actual_value = _metric_value(row, primary_metric)
    primary_objective_value = _objective_value(
        row,
        primary_metric,
        primary_goal,
        float(target_value) if target_value is not None else None,
    )
    checks = _build_constraint_checks(profile["constraints"], row, verification_success)
    failures = [check["label"] for check in checks if not check["passed"]]

    if failures:
        status = "out_of_bounds"
        reason = f"Run violates {len(failures)} active constraint(s)."
    else:
        status = "qualified"
        reason = "Run satisfies every active constraint."

    return {
        "status": status,
        "reason": reason,
        "qualified": not failures,
        "constraint_failures": failures,
        "constraint_failure_count": len(failures),
        "constraints": {
            "active_count": len(checks),
            "checks": checks,
        },
        "primary_objective": {
            "metric": primary_metric,
            "label": METRIC_LABELS[primary_metric],
            "goal": primary_goal,
            "target_value": target_value,
            "actual_value": primary_actual_value,
            "actual_display": _format_metric_value(primary_metric, primary_actual_value),
            "objective_value": primary_objective_value,
        },
    }


def evaluate_run_decision(
    config: SimulationConfig,
    metrics: dict[str, Any],
    *,
    verification_success: bool,
) -> dict[str, Any] | None:
    profile = decision_profile_from_config(config)
    if profile is None:
        return None
    row = {
        "energy_drift": metrics["energy_drift"],
        "norm_drift": metrics["norm_drift"],
        "max_density": metrics["max_density"],
        "elapsed_seconds": metrics["elapsed_seconds"],
    }
    evaluation = _evaluate_row_decision(profile, row, verification_success)
    return {
        "available": True,
        "status": evaluation["status"],
        "reason": evaluation["reason"],
        "profile": profile,
        "constraints": evaluation["constraints"],
        "primary_objective": evaluation["primary_objective"],
    }


def _metric_scores_for_rows(
    rows: list[dict[str, Any]],
    metric: str,
    goal: str,
    target_value: float | None,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    objective_values = [
        _objective_value(row, metric, goal, target_value)
        for row in rows
    ]
    minimum = min(objective_values)
    maximum = max(objective_values)
    span = maximum - minimum

    normalized: dict[str, float] = {}
    components: list[dict[str, Any]] = []
    for row, objective_value in zip(rows, objective_values):
        run_id = str(row["run_id"])
        if span == 0:
            score = 1.0
        elif goal == "maximize":
            score = (objective_value - minimum) / span
        else:
            score = (maximum - objective_value) / span
        normalized[run_id] = score
        components.append(
            {
                "metric": metric,
                "label": METRIC_LABELS[metric],
                "goal": goal,
                "target_value": target_value,
                "raw_value": _metric_value(row, metric),
                "objective_value": objective_value,
                "normalized_score": round(score, 6),
            }
        )
    return normalized, components


def apply_decision_profile(
    comparison: dict[str, Any],
    run_details: list[dict[str, Any]],
) -> dict[str, Any]:
    profile, unavailable_reason, profile_status, profile_groups = _shared_decision_profile(
        run_details
    )
    rows = comparison["rows"]
    if profile is None:
        return {
            "available": False,
            "status": "evidence_only",
            "mode": "evidence_only",
            "objective_profile_status": profile_status,
            "profile_count": len(profile_groups),
            "profile_groups": profile_groups,
            "reason": unavailable_reason,
        }

    ranking = profile["ranking"]
    objective = profile["objective"]
    weights = {
        metric: float(weight)
        for metric, weight in dict(ranking["weights"]).items()
        if metric in SUPPORTED_DECISION_METRICS
    }
    primary_metric = str(objective["primary_metric"])
    weights[primary_metric] = weights.get(primary_metric, 0.0) + float(
        ranking.get("primary_metric_weight", 2.0)
    )
    active_weights = {
        metric: weight
        for metric, weight in weights.items()
        if weight > 0
    }

    metric_scores: dict[str, dict[str, float]] = {}
    metric_components_by_run: dict[str, list[dict[str, Any]]] = {
        row["run_id"]: [] for row in rows
    }

    for metric, weight in active_weights.items():
        goal = _goal_for_metric(profile, metric)
        target_value = objective.get("target_value") if metric == primary_metric else None
        normalized_scores, components = _metric_scores_for_rows(
            rows,
            metric,
            goal,
            float(target_value) if target_value is not None else None,
        )
        metric_scores[metric] = normalized_scores
        for component, row in zip(components, rows):
            metric_components_by_run[row["run_id"]].append(
                {
                    **component,
                    "weight": round(weight, 6),
                    "score_contribution": round(component["normalized_score"] * weight, 6),
                }
            )

    if not metric_scores:
        return {
            "available": False,
            "status": "unconfigured",
            "mode": "evidence_only",
            "objective_profile_status": "shared",
            "profile_count": len(profile_groups),
            "profile_groups": profile_groups,
            "reason": "The objective profile has no positive ranking weights, so QS-DMSS cannot rank the runs.",
        }

    total_weight = sum(active_weights.values())
    row_decisions: list[dict[str, Any]] = []
    for detail, row in zip(run_details, rows):
        evaluation = _evaluate_row_decision(
            profile,
            row,
            bool(detail["verification"]["success"]),
        )
        weighted_score = 0.0
        for metric, weight in active_weights.items():
            weighted_score += metric_scores[metric][row["run_id"]] * weight
        score = weighted_score / total_weight if total_weight else 0.0
        row_decisions.append(
            {
                "run_id": row["run_id"],
                "score": round(score, 6),
                "evaluation": evaluation,
                "components": metric_components_by_run[row["run_id"]],
            }
        )

    qualified = [
        item for item in row_decisions if item["evaluation"]["qualified"]
    ]
    ranking_pool = qualified or row_decisions
    status = "qualified" if qualified else "fallback"
    reason = (
        "Recommended run satisfies every active constraint and achieved the strongest weighted score."
        if qualified
        else "No run satisfied every active constraint, so QS-DMSS fell back to the strongest weighted score overall."
    )

    primary_goal = str(objective["goal"])
    primary_target = objective.get("target_value")

    def sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
        primary_value = item["evaluation"]["primary_objective"]["objective_value"]
        return (
            -item["score"],
            primary_value if primary_goal != "maximize" else -primary_value,
            item["evaluation"]["constraint_failure_count"],
            float(next(row for row in rows if row["run_id"] == item["run_id"])["elapsed_seconds"]),
            item["run_id"],
        )

    ranked = sorted(ranking_pool, key=sort_key)
    full_ranked = sorted(
        row_decisions,
        key=lambda item: (
            not item["evaluation"]["qualified"],
            *sort_key(item),
        ),
    )
    recommended = ranked[0]

    rank_lookup = {item["run_id"]: index for index, item in enumerate(full_ranked, start=1)}
    score_lookup = {item["run_id"]: item["score"] for item in full_ranked}
    evaluation_lookup = {item["run_id"]: item["evaluation"] for item in full_ranked}
    components_lookup = {item["run_id"]: item["components"] for item in full_ranked}

    for row in rows:
        evaluation = evaluation_lookup[row["run_id"]]
        row["decision_rank"] = rank_lookup[row["run_id"]]
        row["decision_score"] = score_lookup[row["run_id"]]
        row["decision_qualified"] = evaluation["qualified"]
        row["decision_status"] = evaluation["status"]
        row["constraint_failures"] = evaluation["constraint_failures"]
        row["constraint_failure_count"] = evaluation["constraint_failure_count"]
        row["primary_objective_value"] = evaluation["primary_objective"]["actual_value"]
        row["primary_objective_display"] = evaluation["primary_objective"]["actual_display"]
        row["decision_components"] = components_lookup[row["run_id"]]

    recommended_evaluation = recommended["evaluation"]
    return {
        "available": True,
        "mode": "ranked",
        "objective_profile_status": "shared",
        "profile_count": 1,
        "profile_groups": profile_groups,
        "status": status,
        "reason": reason,
        "profile": profile,
        "recommended_run_id": recommended["run_id"],
        "recommended_score": recommended["score"],
        "recommended_status": recommended_evaluation["status"],
        "recommended_constraint_failures": recommended_evaluation["constraint_failures"],
        "primary_metric": primary_metric,
        "primary_metric_label": METRIC_LABELS[primary_metric],
        "primary_goal": primary_goal,
        "primary_target_value": primary_target,
        "qualified_run_count": len(qualified),
        "total_run_count": len(rows),
        "ranked_run_ids": [item["run_id"] for item in full_ranked],
    }
