from __future__ import annotations

from pathlib import Path

import pytest

from qs_dmss.experiment import build_campaign_plan
from qs_dmss.io.config import load_config, parse_config


def test_build_campaign_plan_from_demo_config() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config = load_config(repo_root / "configs" / "demo.yaml").to_dict()

    plan = build_campaign_plan(config)

    assert plan["label"] == "Stability frontier campaign"
    assert plan["strategy"] == "grid"
    assert plan["dimension_count"] == 2
    assert plan["planned_run_count"] == 6
    assert len(plan["variants"]) == 6
    assert plan["variants"][0]["variant_label"]


def test_parse_config_requires_objective_when_campaign_present() -> None:
    with pytest.raises(ValueError, match="objective"):
        parse_config(
            {
                "run": {"name": "demo", "seed": 1},
                "engine": {
                    "backend": "numpy",
                    "grid_shape": [8, 8, 8],
                    "box_size": 1.0,
                    "mass": 1.0,
                    "g_int": 0.05,
                    "time_step": 0.02,
                    "num_steps": 4,
                },
                "initial": {
                    "kind": "gaussian",
                    "amplitude": 1.0,
                    "width": 0.2,
                    "random_phase": True,
                },
                "campaign": {
                    "label": "invalid campaign",
                    "dimensions": [
                        {"path": "engine.g_int", "values": [0.02, 0.05]},
                    ],
                },
            }
        )


def test_parse_config_rejects_bool_integer_values() -> None:
    base_config = {
        "run": {"name": "demo", "seed": 1},
        "engine": {
            "backend": "numpy",
            "grid_shape": [8, 8, 8],
            "box_size": 1.0,
            "mass": 1.0,
            "g_int": 0.05,
            "time_step": 0.02,
            "num_steps": 4,
        },
        "initial": {
            "kind": "gaussian",
            "amplitude": 1.0,
            "width": 0.2,
            "random_phase": True,
        },
    }

    seed_config = {
        **base_config,
        "run": {**base_config["run"], "seed": True},
    }
    with pytest.raises(ValueError, match="run.seed"):
        parse_config(seed_config)

    steps_config = {
        **base_config,
        "engine": {**base_config["engine"], "num_steps": True},
    }
    with pytest.raises(ValueError, match="engine.num_steps"):
        parse_config(steps_config)

    grid_config = {
        **base_config,
        "engine": {**base_config["engine"], "grid_shape": [True, 8, 8]},
    }
    with pytest.raises(ValueError, match="engine.grid_shape"):
        parse_config(grid_config)
