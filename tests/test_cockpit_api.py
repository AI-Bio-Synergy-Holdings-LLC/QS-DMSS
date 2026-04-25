from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from qs_dmss.cockpit.api import create_app


def test_cockpit_api_launch_verify_and_replay(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    assert "QS-DMSS Run Cockpit" in root.text

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
