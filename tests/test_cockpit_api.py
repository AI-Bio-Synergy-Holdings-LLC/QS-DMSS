from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from qs_dmss.cockpit import api as cockpit_api
from qs_dmss.cockpit.api import create_app


def test_cockpit_api_launch_verify_and_replay(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    assert "QS-DMSS Run Cockpit" in root.text
    assert 'id="labProgressText"' in root.text
    markdown_link = re.search(r'<a[^>]+id="labMarkdownLink"[^>]*>', root.text)
    json_link = re.search(r'<a[^>]+id="labJsonLink"[^>]*>', root.text)
    assert markdown_link is not None
    assert json_link is not None
    for report_link in (markdown_link.group(0), json_link.group(0)):
        assert "href=" not in report_link
        assert 'aria-disabled="true"' in report_link
        assert 'tabindex="-1"' in report_link

    config_payload = client.get("/api/configs")
    assert config_payload.status_code == 200
    config_item = config_payload.json()["items"][0]
    assert config_item["name"] == "demo.yaml"

    launch_payload = client.post(
        "/api/runs",
        json={"config": config_item["config"], "source_name": config_item["name"]},
    )
    assert launch_payload.status_code == 200
    created_run = launch_payload.json()
    run_id = created_run["summary"]["run_id"]

    runs_payload = client.get("/api/runs")
    assert runs_payload.status_code == 200
    assert runs_payload.json()["items"][0]["run_id"] == run_id

    verify_payload = client.post(f"/api/runs/{run_id}/verify")
    assert verify_payload.status_code == 200
    assert verify_payload.json()["success"] is True

    bundle_payload = client.get(f"/api/runs/{run_id}/bundle")
    assert bundle_payload.status_code == 200
    assert bundle_payload.headers["content-type"].startswith("application/zip")

    report_payload = client.get(f"/api/runs/{run_id}/report")
    assert report_payload.status_code == 200
    assert "QS-DMSS Evidence Report" in report_payload.text

    replay_payload = client.post(f"/api/runs/{run_id}/replay")
    assert replay_payload.status_code == 200
    replay_run = replay_payload.json()
    assert replay_run["run_record"]["replayed_from"] == run_id


def test_cockpit_api_sanitizes_source_name(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]
    launch_payload = client.post(
        "/api/runs",
        json={
            "config": config_item["config"],
            "source_name": "../../outside/evil",
        },
    )

    assert launch_payload.status_code == 200
    run_record = launch_payload.json()["run_record"]
    assert run_record["source_config_name"] == "evil.yaml"
    assert ".." not in run_record["source_config_name"]
    assert "/" not in run_record["source_config_name"]
    assert "\\" not in run_record["source_config_name"]


def test_cockpit_api_uses_bundled_configs_when_repo_has_none(tmp_path: Path) -> None:
    app = create_app(repo_root=tmp_path, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_payload = client.get("/api/configs")
    assert config_payload.status_code == 200
    body = config_payload.json()
    assert body["default_name"] == "demo.yaml"
    assert body["items"][0]["path"] == "configs/demo.yaml"


def test_cockpit_api_launches_lab_mode_showcase(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    showcase_payload = client.get("/api/showcases")
    assert showcase_payload.status_code == 200
    showcase_body = showcase_payload.json()
    assert showcase_body["default_name"] == "canonical-simulation"
    assert showcase_body["items"][0]["name"] == "canonical-simulation"

    launch_payload = client.post("/api/showcases/canonical-simulation/run")
    assert launch_payload.status_code == 200
    lab_mode = launch_payload.json()
    run_id = lab_mode["run"]["summary"]["run_id"]
    replay_id = lab_mode["replay_run"]["summary"]["run_id"]

    assert lab_mode["scenario"]["name"] == "canonical-simulation"
    assert lab_mode["report"]["success"] is True
    assert lab_mode["report"]["run"]["run_id"] == run_id
    assert lab_mode["report"]["replay"]["run_id"] == replay_id
    assert lab_mode["report"]["replay"]["final_density_allclose"] is True
    assert lab_mode["artifact_links"]

    runs_payload = client.get("/api/runs")
    assert runs_payload.status_code == 200
    run_ids = {item["run_id"] for item in runs_payload.json()["items"]}
    assert {run_id, replay_id}.issubset(run_ids)

    run_detail = client.get(f"/api/runs/{run_id}")
    assert run_detail.status_code == 200
    assert run_detail.json()["urls"]["bundle"].endswith("/bundle")

    markdown_report = client.get(lab_mode["urls"]["markdown_report"])
    assert markdown_report.status_code == 200
    assert "QS-DMSS Canonical Simulation Showcase" in markdown_report.text

    json_report = client.get(lab_mode["urls"]["json_report"])
    assert json_report.status_code == 200
    assert json_report.json()["run"]["run_id"] == run_id

    artifact_payload = client.get(lab_mode["artifact_links"][0]["url"])
    assert artifact_payload.status_code == 200


def test_cockpit_api_launch_sweep_and_compare(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]
    parameters_payload = client.get("/api/sweeps/parameters")
    assert parameters_payload.status_code == 200
    assert any(item["path"] == "engine.g_int" for item in parameters_payload.json()["items"])

    sweep_payload = client.post(
        "/api/sweeps",
        json={
            "config": config_item["config"],
            "parameter_path": "engine.g_int",
            "values": [0.02, 0.05],
            "source_name": config_item["name"],
            "experiment_name": "interaction sweep",
        },
    )
    assert sweep_payload.status_code == 200
    sweep = sweep_payload.json()
    assert sweep["experiment"]["label"] == "interaction sweep"
    assert len(sweep["runs"]) == 2
    assert sweep["comparison"]["shared_experiment"]["parameter_path"] == "engine.g_int"
    assert len(sweep["comparison"]["rows"]) == 2
    assert sweep["comparison"]["decision"]["available"] is True
    assert sweep["comparison"]["decision"]["recommended_run_id"] in {
        run["run_id"] for run in sweep["runs"]
    }
    assert sweep["artifact"]["summary"]["experiment_id"] == sweep["experiment"]["id"]
    assert sweep["artifact"]["summary"]["kind"] == "sweep"
    assert sweep["artifact"]["summary"]["run_count"] == 2
    assert sweep["artifact"]["summary"]["recommended_run_id"] == sweep["comparison"]["decision"]["recommended_run_id"]

    runs_payload = client.get("/api/runs")
    assert runs_payload.status_code == 200
    run_items = runs_payload.json()["items"][:2]
    assert all(item["experiment"]["id"] == sweep["experiment"]["id"] for item in run_items)

    compare_payload = client.post(
        "/api/compare",
        json={"run_ids": [run["run_id"] for run in sweep["runs"]]},
    )
    assert compare_payload.status_code == 200
    comparison = compare_payload.json()
    assert comparison["baseline_run_id"] == sweep["runs"][0]["run_id"]
    assert len(comparison["rows"]) == 2
    assert comparison["highlights"]["lowest_abs_energy_drift_run_id"] in {
        run["run_id"] for run in sweep["runs"]
    }

    detail_payload = client.get(f"/api/runs/{sweep['runs'][0]['run_id']}")
    assert detail_payload.status_code == 200
    detail = detail_payload.json()
    assert detail["run_record"]["experiment"]["label"] == "interaction sweep"
    assert detail["run_record"]["experiment"]["parameter_value_label"] in {"0.02", "0.05"}
    assert detail["decision"]["available"] is True
    assert detail["decision"]["profile"]["objective"]["name"] == "Stability-first recommendation"

    experiments_payload = client.get("/api/experiments")
    assert experiments_payload.status_code == 200
    experiment_items = experiments_payload.json()["items"]
    assert experiment_items[0]["experiment_id"] == sweep["experiment"]["id"]
    assert experiment_items[0]["decision_available"] is True

    experiment_detail_payload = client.get(f"/api/experiments/{sweep['experiment']['id']}")
    assert experiment_detail_payload.status_code == 200
    experiment_detail = experiment_detail_payload.json()
    assert experiment_detail["summary"]["label"] == "interaction sweep"
    assert experiment_detail["comparison"]["shared_experiment"]["id"] == sweep["experiment"]["id"]
    assert experiment_detail["decision"]["available"] is True
    assert experiment_detail["decision"]["recommended_run_id"] == sweep["comparison"]["decision"]["recommended_run_id"]

    experiment_bundle_payload = client.get(f"/api/experiments/{sweep['experiment']['id']}/bundle")
    assert experiment_bundle_payload.status_code == 200
    assert experiment_bundle_payload.headers["content-type"].startswith("application/zip")

    experiment_report_payload = client.get(f"/api/experiments/{sweep['experiment']['id']}/report")
    assert experiment_report_payload.status_code == 200
    assert "QS-DMSS Experiment Report" in experiment_report_payload.text
    assert "Recommendation" in experiment_report_payload.text


def test_cockpit_api_save_manual_experiment(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]

    first_run = client.post(
        "/api/runs",
        json={"config": config_item["config"], "source_name": config_item["name"]},
    )
    assert first_run.status_code == 200

    second_config = dict(config_item["config"])
    second_config["run"] = dict(config_item["config"]["run"])
    second_config["engine"] = dict(config_item["config"]["engine"])
    second_config["initial"] = dict(config_item["config"]["initial"])
    second_config["run"]["name"] = "demo-alt"
    second_config["engine"]["g_int"] = 0.05
    second_run = client.post(
        "/api/runs",
        json={"config": second_config, "source_name": "demo-alt.yaml"},
    )
    assert second_run.status_code == 200

    run_ids = [
        first_run.json()["summary"]["run_id"],
        second_run.json()["summary"]["run_id"],
    ]
    experiment_payload = client.post(
        "/api/experiments",
        json={"run_ids": run_ids, "label": "manual comparison"},
    )
    assert experiment_payload.status_code == 200
    experiment_detail = experiment_payload.json()
    assert experiment_detail["summary"]["label"] == "manual comparison"
    assert experiment_detail["summary"]["kind"] == "comparison"
    assert experiment_detail["comparison"]["baseline_run_id"] == run_ids[0]
    assert len(experiment_detail["experiment_record"]["runs"]) == 2
    assert experiment_detail["decision"]["available"] is True
    assert experiment_detail["decision"]["recommended_run_id"] in set(run_ids)
    assert experiment_detail["experiment_record"]["runs"][0]["artifacts"]["bundle"].endswith(
        "evidence_bundle.zip"
    )


def test_cockpit_api_launch_campaign(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]
    campaign_payload = client.post(
        "/api/campaigns",
        json={"config": config_item["config"], "source_name": "../../outside/campaign"},
    )
    assert campaign_payload.status_code == 200
    campaign = campaign_payload.json()
    assert campaign["campaign"]["label"] == "Stability frontier campaign"
    assert campaign["campaign"]["strategy"] == "grid"
    assert campaign["campaign"]["dimension_count"] == 2
    assert campaign["campaign"]["planned_run_count"] == 6
    assert len(campaign["runs"]) == 6
    assert campaign["comparison"]["decision"]["available"] is True
    assert campaign["artifact"]["summary"]["kind"] == "campaign"
    assert campaign["artifact"]["summary"]["run_count"] == 6
    assert campaign["artifact"]["summary"]["recommended_run_id"] == campaign["campaign"]["recommended_run_id"]
    assert campaign["comparison"]["shared_experiment"]["kind"] == "campaign"
    assert campaign["comparison"]["shared_experiment"]["dimension_count"] == 2

    run_detail = client.get(f"/api/runs/{campaign['runs'][0]['run_id']}")
    assert run_detail.status_code == 200
    detail = run_detail.json()
    assert detail["run_record"]["source_config_name"] == "campaign.yaml"
    assert detail["run_record"]["experiment"]["kind"] == "campaign"
    assert detail["run_record"]["experiment"]["strategy"] == "grid"
    assert len(detail["run_record"]["experiment"]["variant"]) == 2
    assert "variant_label" in detail["run_record"]["experiment"]

    experiment_detail = client.get(f"/api/experiments/{campaign['campaign']['id']}")
    assert experiment_detail.status_code == 200
    experiment = experiment_detail.json()
    assert experiment["summary"]["kind"] == "campaign"
    assert experiment["comparison"]["shared_experiment"]["kind"] == "campaign"
    assert len(experiment["comparison"]["shared_experiment"]["dimensions"]) == 2
    assert "QS-DMSS Experiment Report" in client.get(experiment["urls"]["report"]).text


def test_cockpit_api_campaign_failure_persists_failed_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    real_execute = cockpit_api.execute_run
    call_count = 0

    def flaky_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("simulated variant failure")
        return real_execute(*args, **kwargs)

    monkeypatch.setattr(cockpit_api, "execute_run", flaky_execute)

    config_item = client.get("/api/configs").json()["items"][0]
    campaign_payload = client.post(
        "/api/campaigns",
        json={"config": config_item["config"], "source_name": config_item["name"]},
    )
    assert campaign_payload.status_code == 500
    failure_detail = campaign_payload.json()["detail"]
    assert failure_detail["message"] == "Campaign failed; a failed campaign artifact was saved."
    assert failure_detail["error"] == "simulated variant failure"
    assert len(failure_detail["run_ids"]) == 1

    experiment_payload = client.get(f"/api/experiments/{failure_detail['experiment_id']}")
    assert experiment_payload.status_code == 200
    experiment = experiment_payload.json()
    assert experiment["summary"]["status"] == "failed"
    assert experiment["summary"]["kind"] == "campaign"
    assert experiment["summary"]["run_count"] == 1
    assert experiment["experiment_record"]["failure"]["completed_run_count"] == 1
    assert experiment["experiment_record"]["failure"]["planned_run_count"] == 6
    assert experiment["comparison"]["status"] == "failed"
    assert experiment["decision"]["available"] is False

    bundle_payload = client.get(experiment["urls"]["bundle"])
    assert bundle_payload.status_code == 200
    assert bundle_payload.headers["content-type"].startswith("application/zip")

    report_payload = client.get(experiment["urls"]["report"])
    assert report_payload.status_code == 200
    assert "Failed Campaign Report" in report_payload.text
