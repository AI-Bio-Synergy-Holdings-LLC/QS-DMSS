from __future__ import annotations

from qs_dmss.decision import decision_profile_from_config, evaluate_run_decision
from qs_dmss.experiment import build_run_comparison
from qs_dmss.io.config import parse_config


def _decision_config() -> dict:
    return {
        "run": {"name": "decision-demo", "seed": 7, "output_root": "runs"},
        "engine": {
            "backend": "numpy",
            "grid_shape": [8, 8, 8],
            "box_size": 1.0,
            "mass": 1.0,
            "g_int": 0.05,
            "time_step": 0.02,
            "num_steps": 6,
            "log_every": 1,
        },
        "initial": {
            "kind": "gaussian",
            "amplitude": 1.0,
            "width": 0.2,
            "random_phase": True,
        },
        "objective": {
            "name": "Stability-first recommendation",
            "summary": "Prefer low drift with verified evidence while keeping density high enough for a credible final state.",
            "primary_metric": "energy_drift",
            "goal": "minimize_abs",
        },
        "constraints": {
            "max_abs_energy_drift": 0.2,
            "max_abs_norm_drift": 0.2,
            "min_max_density": 0.5,
            "max_elapsed_seconds": 5.0,
            "require_verification": True,
        },
        "ranking": {
            "primary_metric_weight": 2.4,
            "weights": {
                "energy_drift": 1.0,
                "norm_drift": 0.9,
                "max_density": 0.7,
                "elapsed_seconds": 0.3,
            },
        },
    }


def test_parse_config_and_evaluate_run_decision() -> None:
    config = parse_config(_decision_config())
    decision = evaluate_run_decision(
        config,
        {
            "energy_drift": 0.01,
            "norm_drift": 0.02,
            "max_density": 0.9,
            "elapsed_seconds": 0.3,
            "history": [],
        },
        verification_success=True,
    )

    assert decision is not None
    assert decision["status"] == "qualified"
    assert decision["primary_objective"]["metric"] == "energy_drift"
    assert decision["profile"]["ranking"]["primary_metric_weight"] == 2.4


def test_comparison_returns_ranked_recommendation_for_shared_profile() -> None:
    config = parse_config(_decision_config())
    profile = decision_profile_from_config(config)
    assert profile is not None

    run_details = [
        {
            "summary": {"run_id": "run-a"},
            "config": config.to_dict(),
            "run_record": {
                "run_id": "run-a",
                "name": "run-a",
                "source_config_name": "demo.yaml",
                "seed": 7,
                "finished_at": "2026-04-25T00:00:00Z",
                "elapsed_seconds": 0.4,
                "experiment": None,
                "decision_profile": profile,
            },
            "metrics": {
                "energy_drift": 0.01,
                "norm_drift": 0.03,
                "max_density": 0.9,
            },
            "evidence": {"bundle_size_label": "1.00 KB"},
            "verification": {"success": True},
        },
        {
            "summary": {"run_id": "run-b"},
            "config": config.to_dict(),
            "run_record": {
                "run_id": "run-b",
                "name": "run-b",
                "source_config_name": "demo.yaml",
                "seed": 7,
                "finished_at": "2026-04-25T00:00:01Z",
                "elapsed_seconds": 0.6,
                "experiment": None,
                "decision_profile": profile,
            },
            "metrics": {
                "energy_drift": 0.03,
                "norm_drift": 0.05,
                "max_density": 0.7,
            },
            "evidence": {"bundle_size_label": "1.20 KB"},
            "verification": {"success": True},
        },
    ]

    comparison = build_run_comparison(run_details)

    assert comparison["decision"]["available"] is True
    assert comparison["decision"]["recommended_run_id"] == "run-a"
    assert comparison["rows"][0]["decision_rank"] == 1
    assert comparison["rows"][1]["decision_rank"] == 2


def test_comparison_preserves_evidence_for_mixed_objective_profiles() -> None:
    stability_config = parse_config(_decision_config())
    density_mapping = _decision_config()
    density_mapping["objective"] = {
        "name": "Density-response review",
        "summary": "Inspect the largest terminal density response.",
        "primary_metric": "max_density",
        "goal": "maximize",
    }
    density_config = parse_config(density_mapping)

    run_details = []
    for run_id, config, energy_drift, max_density in (
        ("run-stability", stability_config, 0.01, 0.7),
        ("run-density", density_config, 0.03, 0.9),
    ):
        run_details.append(
            {
                "summary": {"run_id": run_id},
                "config": config.to_dict(),
                "run_record": {
                    "run_id": run_id,
                    "name": run_id,
                    "source_config_name": f"{run_id}.yaml",
                    "seed": 7,
                    "finished_at": "2026-04-25T00:00:00Z",
                    "elapsed_seconds": 0.4,
                    "experiment": None,
                    "decision_profile": decision_profile_from_config(config),
                },
                "metrics": {
                    "energy_drift": energy_drift,
                    "norm_drift": 0.02,
                    "max_density": max_density,
                },
                "evidence": {"bundle_size_label": "1.00 KB"},
                "verification": {"success": True},
            }
        )

    comparison = build_run_comparison(run_details)
    decision = comparison["decision"]

    assert decision["available"] is False
    assert decision["mode"] == "evidence_only"
    assert decision["status"] == "evidence_only"
    assert decision["objective_profile_status"] == "mixed"
    assert decision["profile_count"] == 2
    assert {group["objective_name"] for group in decision["profile_groups"]} == {
        "Density-response review",
        "Stability-first recommendation",
    }
    assert all("decision_score" not in row for row in comparison["rows"])
    assert comparison["ranges"]["max_density"]["span"] == 0.2
