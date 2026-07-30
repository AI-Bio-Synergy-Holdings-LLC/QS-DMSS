from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from qs_dmss.cockpit.api import AIDraftRequest, CockpitService


def _service(tmp_path: Path) -> CockpitService:
    output_root = tmp_path / "runs"
    experiments_root = tmp_path / "experiments"
    jobs_root = tmp_path / "jobs"
    for path in (output_root, experiments_root, jobs_root):
        path.mkdir(parents=True)
    return CockpitService(
        repo_root=tmp_path,
        output_root=output_root,
        experiments_root=experiments_root,
        jobs_root=jobs_root,
        config_root=tmp_path / "configs",
        static_root=tmp_path / "static",
    )


def _scenario_summary() -> dict:
    return {
        "name": "canonical-simulation",
        "label": "Canonical simulation",
        "run_name": "canonical-run",
        "grid_label": "32 × 32",
        "steps": 24,
        "purpose": "Exercise a deterministic packaged study.",
        "description": "A bounded numerical workflow.",
        "claim_boundary": "Workflow evidence only.",
        "limitations": ["No physical calibration."],
        "next_actions": ["Review the evidence."],
        "guided_comparison": {"parameter_path": "engine.dt"},
        "internal_path": "C:/private/scenario.yaml",
    }


def _run_detail(run_id: str = "run-a") -> dict:
    history = [
        {
            "step": step,
            "time": step / 10,
            "norm": 1.0,
            "energy": 2.0 + step,
            "max_density": 3.0 + step,
            "internal_snapshot_path": f"C:/private/snapshot-{step}.npy",
        }
        for step in range(20)
    ]
    return {
        "summary": {
            "run_id": run_id,
            "name": "canonical-run",
            "config_name": "canonical.yaml",
            "seed": 7,
            "grid_label": "32 × 32",
            "steps": 24,
            "status": "complete",
            "finished_at": "2026-07-29T12:00:00Z",
            "elapsed_seconds": 1.25,
            "config_digest": "config-digest",
            "energy_drift": 0.01,
            "norm_drift": 0.02,
            "bundle_size_bytes": 1024,
            "bundle_sha256": "a" * 64,
            "run_dir": "C:/private/run-a",
        },
        "metrics": {
            "energy_drift": 0.01,
            "norm_drift": 0.02,
            "relative_norm_drift": 0.03,
            "max_density": 4.0,
            "elapsed_seconds": 1.25,
            "history": history,
            "profile_path": "C:/private/profile.json",
        },
        "verification": {
            "success": True,
            "checked_files": 6,
            "manifest_path": "C:/private/manifest.sha256.json",
        },
        "evidence": {
            "file_count": 6,
            "bundle_size_bytes": 1024,
            "bundle_sha256": "a" * 64,
            "bundle_path": "C:/private/evidence.zip",
        },
    }


def _experiment_detail(
    *,
    scenario_name: str = "canonical-simulation",
    run_ids: tuple[str, ...] = ("run-b", "run-a"),
    row_ids: tuple[str, ...] | None = None,
) -> dict:
    row_ids = row_ids or run_ids
    rows = [
        {
            "run_id": run_id,
            "name": f"variant-{index}",
            "seed": index,
            "parameter_path": "engine.dt",
            "parameter_label": "Time step",
            "parameter_value": index / 10,
            "parameter_value_label": f"{index / 10:.1f}",
            "variant": f"variant-{index}",
            "variant_label": f"Variant {index}",
            "energy_drift": index / 100,
            "norm_drift": index / 200,
            "max_density": 2.0 + index,
            "elapsed_seconds": 1.0 + index,
            "verification_success": True,
            "delta_from_baseline": {"energy_drift": index / 1000},
            "run_dir": f"C:/private/{run_id}",
        }
        for index, run_id in enumerate(row_ids, start=1)
    ]
    return {
        "summary": {
            "experiment_id": "experiment-a",
            "label": "Guided comparison",
            "kind": "guided-comparison",
            "status": "complete",
            "created_at": "2026-07-29T12:00:00Z",
            "baseline_run_id": run_ids[-1],
            "run_count": len(run_ids),
            "run_ids": list(run_ids),
            "bundle_sha256": "b" * 64,
            "experiment_dir": "C:/private/experiment-a",
        },
        "execution_job": {
            "spec": {
                "metadata": {
                    "scenario": scenario_name,
                    "private_path": "C:/private/job.json",
                }
            }
        },
        "comparison": {
            "baseline_run_id": run_ids[-1],
            "shared_experiment": {
                "id": "experiment-a",
                "label": "Guided comparison",
                "kind": "guided-comparison",
                "strategy": "one-factor-at-a-time",
                "dimension_count": 1,
                "dimensions": [{"parameter_path": "engine.dt"}],
                "parameter_path": "engine.dt",
                "parameter_label": "Time step",
                "private_field": "omit",
            },
            "rows": rows,
            "ranges": {
                "energy_drift": {"min": 0.01, "max": 0.02},
                "norm_drift": {"min": 0.005, "max": 0.01},
                "max_density": {"min": 3.0, "max": 4.0},
                "elapsed_seconds": {"min": 2.0, "max": 3.0},
                "private_range": {"min": 0, "max": 1},
            },
            "highlights": {
                "lowest_abs_energy_drift_run_id": run_ids[0],
                "lowest_abs_norm_drift_run_id": run_ids[0],
                "highest_max_density_run_id": run_ids[-1],
                "private_highlight": run_ids[-1],
            },
            "decision": {
                "available": True,
                "mode": "ranked",
                "status": "qualified",
                "reason": "Recorded metric tradeoff.",
                "recommended_run_id": run_ids[0],
                "recommended_score": 0.9,
                "recommended_status": "qualified",
                "primary_metric": "energy_drift",
                "primary_metric_label": "Energy drift",
                "primary_goal": "minimize_abs",
                "primary_target_value": None,
                "qualified_run_count": len(run_ids),
                "total_run_count": len(run_ids),
                "ranked_run_ids": list(run_ids),
                "profile": {"private": True},
            },
        },
    }


def test_ai_context_preserves_scenario_only_contract_and_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(tmp_path)
    monkeypatch.setattr(
        CockpitService,
        "_build_showcase_summary",
        lambda self, scenario_name: _scenario_summary(),
    )

    context, subject = service.build_ai_evidence_context(
        AIDraftRequest(intent="next", scenario_name="canonical-simulation")
    )

    assert subject == {
        "scenario_name": "canonical-simulation",
        "run_id": None,
        "experiment_id": None,
    }
    assert context == {
        "schema_version": 1,
        "intent": "next",
        "intent_label": "Next-experiment proposal",
        "artifacts": [
            {
                "id": "scenario-contract/canonical-simulation",
                "kind": "scenario_contract",
                "sha256": context["artifacts"][0]["sha256"],
                "data": {
                    key: value
                    for key, value in _scenario_summary().items()
                    if key != "internal_path"
                },
            }
        ],
        "policy": {
            "advisory_only": True,
            "human_review_required": True,
            "tools_available": False,
            "run_launch_allowed": False,
            "artifact_mutation_allowed": False,
            "external_sources_allowed": False,
        },
    }
    assert len(context["artifacts"][0]["sha256"]) == 64


def test_ai_context_bounds_run_history_filters_fields_and_matches_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(tmp_path)
    report_path = tmp_path / "showcase-report.json"
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2026-07-29T12:00:00Z",
                "scenario": "canonical-simulation",
                "scenario_title": "Canonical simulation",
                "scenario_narrative": "Recorded workflow evidence.",
                "claim_boundary": "Workflow evidence only.",
                "success": True,
                "metrics": {"energy_drift": 0.01},
                "interpretation": {"summary": "Numerical result."},
                "verification": {
                    "success": True,
                    "checked_files": 6,
                    "manifest_path": "C:/private/manifest.json",
                },
                "replay": {
                    "run_id": "run-a",
                    "verification_success": True,
                    "final_density_allclose": True,
                    "max_abs_density_delta": 0.0,
                    "replay_dir": "C:/private/replay",
                },
                "artifacts": {"density": {}, "metrics": {}},
                "run": {"run_id": "run-a", "run_dir": "C:/private/run-a"},
                "private_path": "C:/private/report.json",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        CockpitService,
        "_build_showcase_summary",
        lambda self, scenario_name: _scenario_summary(),
    )
    monkeypatch.setattr(
        CockpitService,
        "get_run_detail",
        lambda self, run_id: _run_detail(run_id),
    )
    monkeypatch.setattr(
        CockpitService,
        "showcase_json_path",
        lambda self, scenario_name: report_path,
    )

    context, subject = service.build_ai_evidence_context(
        AIDraftRequest(
            intent="summary",
            scenario_name="canonical-simulation",
            run_id="run-a",
        )
    )

    assert subject == {
        "scenario_name": "canonical-simulation",
        "run_id": "run-a",
        "experiment_id": None,
    }
    assert [artifact["kind"] for artifact in context["artifacts"]] == [
        "scenario_contract",
        "run_summary",
        "run_metrics",
        "manifest_verification",
        "showcase_report",
    ]
    artifacts = {
        artifact["kind"]: artifact["data"] for artifact in context["artifacts"]
    }
    assert "run_dir" not in artifacts["run_summary"]
    assert "history" not in artifacts["run_metrics"]
    assert [
        snapshot["step"] for snapshot in artifacts["run_metrics"]["history_excerpt"]
    ] == [*range(8), *range(12, 20)]
    assert all(
        "internal_snapshot_path" not in snapshot
        for snapshot in artifacts["run_metrics"]["history_excerpt"]
    )
    assert artifacts["manifest_verification"] == {
        "success": True,
        "checked_files": 6,
        "evidence": {
            "file_count": 6,
            "bundle_size_bytes": 1024,
            "bundle_sha256": "a" * 64,
        },
    }
    assert artifacts["showcase_report"]["artifact_keys"] == ["density", "metrics"]
    assert set(artifacts["showcase_report"]["verification"]) == {
        "success",
        "checked_files",
    }
    assert set(artifacts["showcase_report"]["replay"]) == {
        "run_id",
        "verification_success",
        "final_density_allclose",
        "max_abs_density_delta",
    }
    assert "private_path" not in artifacts["showcase_report"]


def test_ai_context_preserves_successful_claim_intent_and_label(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(tmp_path)
    monkeypatch.setattr(
        CockpitService,
        "_build_showcase_summary",
        lambda self, scenario_name: _scenario_summary(),
    )
    monkeypatch.setattr(
        CockpitService,
        "get_run_detail",
        lambda self, run_id: _run_detail(run_id),
    )
    monkeypatch.setattr(
        CockpitService,
        "showcase_json_path",
        lambda self, scenario_name: tmp_path / "missing-report.json",
    )

    context, _ = service.build_ai_evidence_context(
        AIDraftRequest(
            intent="claim",
            scenario_name="canonical-simulation",
            run_id="run-a",
        )
    )

    assert context["intent"] == "claim"
    assert context["intent_label"] == "Claim-boundary review"
    assert [artifact["kind"] for artifact in context["artifacts"]] == [
        "scenario_contract",
        "run_summary",
        "run_metrics",
        "manifest_verification",
    ]


def test_ai_context_preserves_comparison_row_order_and_recommendation_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(tmp_path)
    monkeypatch.setattr(
        CockpitService,
        "_build_showcase_summary",
        lambda self, scenario_name: _scenario_summary(),
    )
    monkeypatch.setattr(
        CockpitService,
        "get_experiment_detail",
        lambda self, experiment_id: _experiment_detail(),
    )

    context, subject = service.build_ai_evidence_context(
        AIDraftRequest(
            intent="comparison",
            scenario_name="canonical-simulation",
            experiment_id="experiment-a",
        )
    )

    assert subject == {
        "scenario_name": "canonical-simulation",
        "run_id": None,
        "experiment_id": "experiment-a",
    }
    assert [artifact["kind"] for artifact in context["artifacts"]] == [
        "scenario_contract",
        "run_comparison",
    ]
    comparison = context["artifacts"][1]["data"]
    assert [row["run_id"] for row in comparison["rows"]] == ["run-b", "run-a"]
    assert all("run_dir" not in row for row in comparison["rows"])
    assert "private_field" not in comparison["shared_experiment"]
    assert "private_range" not in comparison["ranges"]
    assert "private_highlight" not in comparison["highlights"]
    assert "profile" not in comparison["decision"]
    assert comparison["decision"]["recommended_run_id"] == "run-b"
    assert comparison["decision"]["ranked_run_ids"] == ["run-b", "run-a"]


@pytest.mark.parametrize(
    ("payload", "detail"),
    [
        (
            AIDraftRequest(intent="summary", scenario_name="canonical-simulation"),
            "Evidence summary and claim-boundary review require a recorded run.",
        ),
        (
            AIDraftRequest(intent="claim", scenario_name="canonical-simulation"),
            "Evidence summary and claim-boundary review require a recorded run.",
        ),
        (
            AIDraftRequest(intent="comparison", scenario_name="canonical-simulation"),
            "Comparison critique requires a recorded comparison experiment.",
        ),
    ],
)
def test_ai_context_preserves_required_resource_errors(
    tmp_path: Path,
    payload: AIDraftRequest,
    detail: str,
) -> None:
    with pytest.raises(HTTPException) as raised:
        _service(tmp_path).build_ai_evidence_context(payload)

    assert raised.value.status_code == 400
    assert raised.value.detail == detail


@pytest.mark.parametrize(
    ("experiment", "run_detail", "payload", "detail"),
    [
        (
            _experiment_detail(scenario_name="different-scenario"),
            None,
            AIDraftRequest(
                intent="comparison",
                scenario_name="canonical-simulation",
                experiment_id="experiment-a",
            ),
            "The selected comparison does not belong to the selected packaged scenario.",
        ),
        (
            _experiment_detail(),
            None,
            AIDraftRequest(
                intent="next",
                scenario_name="canonical-simulation",
                run_id="run-outside",
                experiment_id="experiment-a",
            ),
            "The selected run is not part of the selected comparison.",
        ),
        (
            _experiment_detail(row_ids=("run-b", "run-outside")),
            None,
            AIDraftRequest(
                intent="comparison",
                scenario_name="canonical-simulation",
                experiment_id="experiment-a",
            ),
            (
                "The selected comparison contains a run outside its "
                "recorded experiment lineage."
            ),
        ),
        (
            None,
            {
                **_run_detail("run-a"),
                "summary": {
                    **_run_detail("run-a")["summary"],
                    "name": "different-run-name",
                },
            },
            AIDraftRequest(
                intent="next",
                scenario_name="canonical-simulation",
                run_id="run-a",
            ),
            "The selected run does not belong to the selected packaged scenario.",
        ),
    ],
)
def test_ai_context_preserves_lineage_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    experiment: dict | None,
    run_detail: dict | None,
    payload: AIDraftRequest,
    detail: str,
) -> None:
    service = _service(tmp_path)
    monkeypatch.setattr(
        CockpitService,
        "_build_showcase_summary",
        lambda self, scenario_name: _scenario_summary(),
    )
    if experiment is not None:
        monkeypatch.setattr(
            CockpitService,
            "get_experiment_detail",
            lambda self, experiment_id: experiment,
        )
    if run_detail is not None:
        monkeypatch.setattr(
            CockpitService,
            "get_run_detail",
            lambda self, run_id: run_detail,
        )

    with pytest.raises(HTTPException) as raised:
        service.build_ai_evidence_context(payload)

    assert raised.value.status_code == 400
    assert raised.value.detail == detail
