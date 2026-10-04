from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from qs_dmss.decision import apply_decision_profile, apply_explicit_decision_profile
from qs_dmss.robustness import (
    RobustnessRequest,
    build_robustness_analysis,
    score_recorded_rows,
)


def profile() -> dict:
    return {
        "objective": {
            "name": "Stability",
            "summary": "Recorded preference",
            "primary_metric": "energy_drift",
            "goal": "minimize_abs",
        },
        "constraints": {"require_verification": True},
        "ranking": {
            "primary_metric_weight": 0.0,
            "weights": {
                "energy_drift": 1.0,
                "norm_drift": 0.0,
                "max_density": 0.0,
                "elapsed_seconds": 0.0,
            },
        },
    }


def rows() -> list[dict]:
    return [
        {
            "run_id": "run-a",
            "name": "Stable",
            "energy_drift": -0.01,
            "norm_drift": 0.0,
            "max_density": 1.0,
            "elapsed_seconds": 2.0,
            "verification_success": True,
        },
        {
            "run_id": "run-b",
            "name": "Fast",
            "energy_drift": 0.03,
            "norm_drift": 0.0,
            "max_density": 2.0,
            "elapsed_seconds": 1.0,
            "verification_success": True,
        },
    ]


def request(**changes) -> RobustnessRequest:
    return RobustnessRequest.model_validate(
        {
            "experiment_id": "campaign-demo",
            "profile": profile(),
            "preferred_run_id": "run-a",
            "source_fingerprint": "a" * 64,
            "sensitivity_metric": "elapsed_seconds",
            "weight_values": [0.0, 1.0, 2.0],
            **changes,
        }
    )


def test_extracted_scoring_contract_preserves_shared_profile_payload_and_order():
    original = {"rows": rows()}
    details = [
        {
            "run_record": {"run_id": row["run_id"], "decision_profile": profile()},
            "verification": {"success": row["verification_success"]},
        }
        for row in rows()
    ]
    actual = apply_decision_profile(original, details)
    explicit_rows = {"rows": rows()}
    explicit = apply_explicit_decision_profile(
        explicit_rows,
        profile(),
        {"run-a": True, "run-b": True},
        profile_groups=actual["profile_groups"],
    )
    assert explicit == actual
    assert explicit_rows == original
    assert actual["ranked_run_ids"] == ["run-a", "run-b"]
    assert [row["decision_score"] for row in original["rows"]] == [1.0, 0.0]
    assert [row["decision_rank"] for row in original["rows"]] == [1, 2]
    assert [row["run_id"] for row in original["rows"]] == ["run-a", "run-b"]


def test_sensitivity_exposes_preference_switch_without_mutating_source():
    source = rows()
    before = deepcopy(source)
    result = build_robustness_analysis(source, request())
    assert source == before
    assert result["current"]["decision"]["recommended_run_id"] == "run-a"
    cases = result["sensitivity"]["cases"]
    # Exact weighted ties retain the existing primary-objective tie break.
    assert [case["recommended_run_id"] for case in cases] == ["run-a", "run-a", "run-b"]
    assert [case["preferred_score"] for case in cases] == [1.0, 0.5, 0.333333]
    assert result["sensitivity"]["preferred_win_count"] == 2
    assert result["sensitivity"]["preferred_rank_range"] == [1, 2]
    assert cases[2]["profile"]["ranking"]["weights"]["elapsed_seconds"] == 2.0
    assert result["ai_advice"] is None
    assert result["independent_scientific_assessment"] == "not_established"


def test_qualification_precedes_score_and_fallback_is_not_counted_as_a_win():
    constrained = profile()
    constrained["constraints"]["max_elapsed_seconds"] = 1.5
    result = build_robustness_analysis(rows(), request(profile=constrained))
    assert result["current"]["decision"]["recommended_run_id"] == "run-b"
    assert result["current"]["rows"][0]["decision_qualified"] is False
    assert result["sensitivity"]["preferred_win_count"] == 0
    constrained["constraints"]["max_elapsed_seconds"] = 0.5
    result = build_robustness_analysis(rows(), request(profile=constrained))
    assert result["current"]["decision"]["status"] == "fallback"
    assert result["sensitivity"]["preferred_win_count"] == 0
    assert result["sensitivity"]["qualification_fallback_count"] == 3


@pytest.mark.parametrize(
    "goal,target,winner",
    [
        ("maximize", None, "run-b"),
        ("minimize", None, "run-a"),
        ("target", 0.031, "run-b"),
    ],
)
def test_goal_contract(goal, target, winner):
    config = profile()
    config["objective"]["goal"] = goal
    if target is not None:
        config["objective"]["target_value"] = target
    assert (
        score_recorded_rows(rows(), config)["decision"]["recommended_run_id"] == winner
    )


def test_constant_metric_and_final_id_tie_break_are_unchanged():
    config = profile()
    config["objective"]["primary_metric"] = "norm_drift"
    config["ranking"]["weights"] = {"norm_drift": 1.0}
    source = rows()
    source[0]["elapsed_seconds"] = 1.0
    result = score_recorded_rows(list(reversed(source)), config)
    assert [row["decision_score"] for row in result["rows"]] == [1.0, 1.0]
    assert result["decision"]["recommended_run_id"] == "run-a"


@pytest.mark.parametrize(
    "change",
    [
        {"weight_values": [1.0, 1.0]},
        {"weight_values": [0.0]},
        {"weight_values": list(range(42))},
        {"weight_values": [0.0, float("nan")]},
        {"weight_values": [0.0, float("inf")]},
        {"weight_values": [0.0, -1.0]},
        {"weight_values": [0.0, True]},
        {"experiment_id": "../escape"},
        {"source_fingerprint": "not-a-hash"},
        {"sensitivity_metric": "unsupported"},
        {"unexpected": "ignored?"},
    ],
)
def test_request_rejects_invalid_or_unbounded_inputs(change):
    with pytest.raises(ValidationError):
        request(**change)


def test_profile_rejects_unknown_keys_zero_weights_and_missing_target():
    invalid = profile()
    invalid["ranking"]["weights"]["typo"] = 1.0
    with pytest.raises(ValidationError):
        request(profile=invalid)
    invalid = profile()
    invalid["ranking"]["weights"]["energy_drift"] = 0.0
    with pytest.raises(ValidationError):
        request(profile=invalid)
    invalid = profile()
    invalid["objective"]["goal"] = "target"
    with pytest.raises(ValidationError):
        request(profile=invalid)


def test_grid_that_disables_all_weights_is_explicitly_rejected():
    with pytest.raises(ValueError, match="no positive ranking weights"):
        build_robustness_analysis(rows(), request(sensitivity_metric="energy_drift"))
    with pytest.raises(ValueError, match="not in the source"):
        build_robustness_analysis(rows(), request(preferred_run_id="missing"))
