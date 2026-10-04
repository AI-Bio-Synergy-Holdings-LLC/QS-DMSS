"""Bounded, recorded-result sensitivity analysis; never executes a solver."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from qs_dmss.decision import apply_explicit_decision_profile
from qs_dmss.io.config import RankingConfig

Metric = Literal["energy_drift", "norm_drift", "max_density", "elapsed_seconds"]
Weight = Annotated[float, Field(strict=True, ge=0, le=10000, allow_inf_nan=False)]
Number = Annotated[float, Field(strict=True, ge=-1e12, le=1e12, allow_inf_nan=False)]
Limit = Annotated[float, Field(strict=True, ge=0, le=1e12, allow_inf_nan=False)]
SCORING_CONVENTION = "campaign_minmax_weighted_v1"
ANALYSIS_CONVENTION = "one_weight_grid_v1"
CLAIM_BOUNDARY = (
    "Preference sensitivity over recorded configurations, not a probability of "
    "optimality, new simulation, AI advice, or independent scientific assessment. "
    "Min-max scores depend on this candidate set. Runtime is environment-dependent; "
    "density is a chosen objective, not evidence of physical correctness."
)


class RobustnessError(ValueError):
    """Application-authored, path-free messages safe to show as plain text."""


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RobustnessObjective(ClosedModel):
    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=2000)
    primary_metric: Metric
    goal: Literal["minimize", "maximize", "minimize_abs", "target"]
    target_value: Number | None = None

    @model_validator(mode="after")
    def target_required(self):
        if self.goal == "target" and self.target_value is None:
            raise ValueError("A target objective requires target_value")
        return self


class RobustnessConstraints(ClosedModel):
    max_abs_energy_drift: Limit | None = None
    max_abs_norm_drift: Limit | None = None
    min_max_density: Number | None = None
    max_elapsed_seconds: Limit | None = None
    require_verification: Annotated[bool, Field(strict=True)] = True


class RobustnessRanking(ClosedModel):
    primary_metric_weight: Weight = 2.0
    weights: dict[Metric, Weight] = Field(
        default_factory=lambda: RankingConfig().weights_dict()
    )

    @model_validator(mode="after")
    def complete_weights(self):
        # Canonical iteration order survives JSON round trips of saved profiles.
        self.weights = dict(
            sorted({**RankingConfig().weights_dict(), **self.weights}.items())
        )
        if self.primary_metric_weight + sum(self.weights.values()) <= 0:
            raise ValueError("At least one effective scoring weight must be positive")
        return self


class RobustnessProfile(ClosedModel):
    objective: RobustnessObjective
    constraints: RobustnessConstraints = Field(default_factory=RobustnessConstraints)
    ranking: RobustnessRanking = Field(default_factory=RobustnessRanking)


class RobustnessRequest(ClosedModel):
    experiment_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$")
    profile: RobustnessProfile
    preferred_run_id: str = Field(min_length=1, max_length=200)
    sensitivity_metric: Metric = "elapsed_seconds"
    weight_values: list[Weight] = Field(min_length=2, max_length=41)
    # Optimistic pin: changes between opening, previewing and saving are rejected.
    source_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def distinct_grid(self):
        if len(set(self.weight_values)) != len(self.weight_values):
            raise ValueError("Sensitivity weights must be distinct")
        return self


def canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def score_recorded_rows(rows: list[dict], profile: dict) -> dict:
    comparison = {"rows": deepcopy(rows)}
    decision = apply_explicit_decision_profile(
        comparison,
        profile,
        {row["run_id"]: row["verification_success"] for row in rows},
    )
    if not decision["available"]:
        raise RobustnessError(decision["reason"])
    return {"decision": decision, "rows": comparison["rows"]}


def build_robustness_analysis(rows: list[dict], request: RobustnessRequest) -> dict:
    """Use the same scoring, constraint, rounding and tie contracts as campaigns."""
    if request.preferred_run_id not in {row["run_id"] for row in rows}:
        raise RobustnessError("Preferred configuration is not in the source campaign")
    profile = request.profile.model_dump(exclude_none=True)
    current = score_recorded_rows(rows, profile)
    cases = []
    for weight in request.weight_values:
        case_profile = deepcopy(profile)
        case_profile["ranking"]["weights"][request.sensitivity_metric] = weight
        result = score_recorded_rows(rows, case_profile)
        preferred = next(
            row for row in result["rows"] if row["run_id"] == request.preferred_run_id
        )
        cases.append(
            {
                "weight": weight,
                "profile": case_profile,
                "recommended_run_id": result["decision"]["recommended_run_id"],
                "status": result["decision"]["status"],
                "preferred_rank": preferred["decision_rank"],
                "preferred_score": preferred["decision_score"],
                "preferred_qualified": preferred["decision_qualified"],
                "rows": [
                    {
                        key: row[key]
                        for key in (
                            "run_id",
                            "decision_rank",
                            "decision_score",
                            "decision_qualified",
                            "constraint_failures",
                        )
                    }
                    for row in result["rows"]
                ],
            }
        )
    return {
        "schema_version": 1,
        "scoring_convention": SCORING_CONVENTION,
        "analysis_convention": ANALYSIS_CONVENTION,
        "evidence_kind": "derived_numerical_preference_analysis",
        "ai_advice": None,
        "independent_scientific_assessment": "not_established",
        "claim_boundary": CLAIM_BOUNDARY,
        "request": request.model_dump(exclude_none=True),
        "profile": profile,
        "profile_sha256": fingerprint(profile),
        "current": current,
        "sensitivity": {
            "metric": request.sensitivity_metric,
            "varied_component": "ranking.weights (primary-metric bonus stays fixed)",
            "cases": cases,
            "preferred_win_count": sum(
                case["recommended_run_id"] == request.preferred_run_id
                and case["status"] == "qualified"
                for case in cases
            ),
            "case_count": len(cases),
            "qualification_fallback_count": sum(
                case["status"] == "fallback" for case in cases
            ),
            "preferred_rank_range": [
                min(case["preferred_rank"] for case in cases),
                max(case["preferred_rank"] for case in cases),
            ],
            "interpretation": "Counts describe only this explicit one-weight grid; they are not probabilities or global robustness bounds.",
        },
    }
