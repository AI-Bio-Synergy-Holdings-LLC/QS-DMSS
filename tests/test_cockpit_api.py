from __future__ import annotations

from copy import deepcopy
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
    assert 'id="labEvidenceExplorer"' in root.text
    assert 'id="labReportPreviewBody"' in root.text
    assert 'id="labArtifactPreview"' in root.text
    assert 'id="labInterpretationSummary"' in root.text
    assert 'id="labMeaningList"' in root.text
    assert 'id="labNonClaimList"' in root.text
    assert 'id="launchLabComparisonButton"' in root.text
    assert 'id="labComparisonSummary"' in root.text
    assert 'id="labComparisonMeaningList"' in root.text
    assert 'id="researchObjectExportPanel"' in root.text
    assert 'id="composeResearchObjectButton"' in root.text
    assert 'id="researchObjectSurface"' in root.text
    assert 'id="researchObjectCta" hidden' in root.text
    assert 'id="scenarioLibraryPanel"' in root.text
    assert 'id="scenarioBadges"' in root.text
    assert 'id="scenarioArtifacts"' in root.text
    assert 'id="labCampaignStudioPanel"' in root.text
    assert 'id="campaignStudioDimensions"' in root.text
    assert 'id="campaignStudioEditor"' in root.text
    assert 'id="campaignStudioFields"' in root.text
    assert 'id="campaignStudioDecisionFields"' in root.text
    assert 'id="campaignStudioScoringContract"' in root.text
    assert 'id="launchCampaignStudioButton"' in root.text
    assert 'id="resetCampaignStudioButton"' in root.text
    assert 'id="campaignStudyTemplatePanel"' in root.text
    assert 'id="campaignStudyTemplateSelect"' in root.text
    assert 'id="saveCampaignStudyTemplateButton"' in root.text
    assert 'id="loadCampaignStudyTemplateButton"' in root.text
    assert 'id="runCampaignStudyTemplateButton"' in root.text
    assert 'id="downloadCampaignStudyTemplateLink"' in root.text
    assert 'id="importCampaignStudyTemplateInput"' in root.text
    markdown_link = re.search(r'<a[^>]+id="labMarkdownLink"[^>]*>', root.text)
    json_link = re.search(r'<a[^>]+id="labJsonLink"[^>]*>', root.text)
    research_object_button = re.search(
        r'<button[^>]+id="composeResearchObjectButton"[^>]*>',
        root.text,
    )
    research_object_download = re.search(
        r'<a[^>]+id="researchObjectDownloadLink"[^>]*>',
        root.text,
    )
    assert markdown_link is not None
    assert json_link is not None
    assert research_object_button is not None
    assert research_object_download is not None
    assert "disabled" in research_object_button.group(0)
    for report_link in (markdown_link.group(0), json_link.group(0)):
        assert "href=" not in report_link
        assert 'aria-disabled="true"' in report_link
        assert 'tabindex="-1"' in report_link
    assert "href=" not in research_object_download.group(0)
    assert 'aria-disabled="true"' in research_object_download.group(0)
    assert 'tabindex="-1"' in research_object_download.group(0)

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
    scenario = showcase_body["items"][0]
    assert scenario["label"] == "Canonical Simulation Showcase"
    assert scenario["purpose"].startswith("Demonstrate the full QS-DMSS")
    assert scenario["expected_runtime"].startswith("Fast smoke")
    assert {item["label"] for item in scenario["readiness_badges"]} >= {
        "Packaged",
        "Replayable",
    }
    assert {item["label"] for item in scenario["output_artifacts"]} >= {
        "Evidence bundle",
        "SVG figures",
    }
    assert scenario["limitations"]
    assert scenario["guided_comparison"]["planned_run_count"] == 3
    assert {
        variant["slug"]
        for variant in scenario["guided_comparison"]["variants"]
    } == {
        "baseline",
        "wider-packet",
        "stronger-interaction",
    }
    campaign_studio = showcase_body["campaign_studio"]
    assert campaign_studio["available"] is True
    assert campaign_studio["label"] == "Stability frontier campaign"
    assert campaign_studio["max_runs"] == 6
    assert campaign_studio["planned_run_count"] == 6
    assert campaign_studio["dimension_count"] == 2
    assert campaign_studio["objective"]["name"] == "Stability-first recommendation"
    assert campaign_studio["objective"]["supported_metrics"] == [
        "energy_drift",
        "norm_drift",
        "max_density",
        "elapsed_seconds",
    ]
    assert campaign_studio["constraint_values"]["require_verification"] is True
    assert campaign_studio["ranking"]["weights"]["energy_drift"] == 1.0
    assert {item["label"] for item in campaign_studio["readiness_badges"]} >= {
        "Grid editor",
        "Objective editor",
        "Study templates",
    }
    assert campaign_studio["current_boundary"].startswith("Campaign Studio now edits, saves")

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
    interpretation = lab_mode["report"]["interpretation"]
    assert interpretation["plain_language_summary"].startswith("This showcase starts")
    assert interpretation["what_this_result_means"]
    assert interpretation["what_this_result_does_not_claim"]
    assert interpretation["review_prompt"]
    assert {item["artifact_key"] for item in interpretation["artifact_callouts"]} == {
        "energy_history_svg",
        "midplane_density_svg",
        "midplane_slice_csv",
        "radial_density_svg",
        "radial_profile_csv",
        "step_history_csv",
    }
    assert lab_mode["artifact_links"]
    assert {item["key"] for item in lab_mode["artifact_links"]} == {
        "energy_history_svg",
        "midplane_density_svg",
        "midplane_slice_csv",
        "radial_density_svg",
        "radial_profile_csv",
        "step_history_csv",
    }
    assert {item["kind"] for item in lab_mode["artifact_links"]} == {"csv", "svg"}
    assert all(item["previewable"] for item in lab_mode["artifact_links"])

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
    assert "## Guided Interpretation" in markdown_report.text
    assert "### What This Result Does Not Claim" in markdown_report.text

    json_report = client.get(lab_mode["urls"]["json_report"])
    assert json_report.status_code == 200
    assert json_report.json()["run"]["run_id"] == run_id
    assert json_report.json()["interpretation"]["artifact_callouts"]

    artifact_payload = client.get(lab_mode["artifact_links"][0]["url"])
    assert artifact_payload.status_code == 200


def test_cockpit_api_launches_guided_showcase_comparison(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    comparison_payload = client.post("/api/showcases/canonical-simulation/compare")
    assert comparison_payload.status_code == 200
    guided = comparison_payload.json()

    assert guided["scenario"]["name"] == "canonical-simulation"
    assert len(guided["runs"]) == 3
    assert len(guided["comparison"]["rows"]) == 3
    assert guided["comparison"]["shared_experiment"]["kind"] == "guided-comparison"
    assert guided["comparison"]["shared_experiment"]["strategy"] == "packaged-variants"
    assert guided["artifact"]["summary"]["kind"] == "guided-comparison"
    assert guided["artifact"]["summary"]["run_count"] == 3
    assert guided["artifact"]["summary"]["experiment_id"].startswith("guided-comparison-")
    assert guided["urls"]["report"].endswith("/report")
    assert guided["urls"]["bundle"].endswith("/bundle")

    guide = guided["guide"]
    assert guide["plain_language_summary"].startswith("QS-DMSS ran the canonical showcase")
    assert len(guide["what_changed"]) >= 4
    assert len(guide["what_to_inspect"]) >= 3
    assert guide["what_this_does_not_claim"]
    assert "review comment" in guide["review_prompt"]

    variant_labels = {
        row["parameter_value_label"] for row in guided["comparison"]["rows"]
    }
    assert variant_labels == {"Baseline", "Wider packet", "Stronger interaction"}

    experiment_report = client.get(guided["urls"]["report"])
    assert experiment_report.status_code == 200
    assert "QS-DMSS Experiment Report" in experiment_report.text

    experiment_bundle = client.get(guided["urls"]["bundle"])
    assert experiment_bundle.status_code == 200
    assert experiment_bundle.headers["content-type"].startswith("application/zip")


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


def test_cockpit_api_launch_campaign_with_edited_grid(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]
    edited_config = config_item["config"]
    edited_config["campaign"] = dict(edited_config["campaign"])
    edited_config["campaign"]["max_runs"] = 4
    edited_config["campaign"]["dimensions"] = [
        {"path": "engine.g_int", "values": [0.02, 0.08]},
        {"path": "engine.time_step", "values": [0.02]},
    ]

    campaign_payload = client.post(
        "/api/campaigns",
        json={"config": edited_config, "source_name": "campaign-studio.yaml"},
    )
    assert campaign_payload.status_code == 200
    campaign = campaign_payload.json()
    assert campaign["campaign"]["planned_run_count"] == 2
    assert campaign["campaign"]["dimensions"][0]["values"] == [0.02, 0.08]
    assert campaign["campaign"]["dimensions"][1]["values"] == [0.02]
    assert len(campaign["runs"]) == 2
    assert campaign["comparison"]["decision"]["available"] is True
    assert campaign["artifact"]["summary"]["recommended_run_id"] == campaign["campaign"]["recommended_run_id"]

    run_detail = client.get(f"/api/runs/{campaign['runs'][0]['run_id']}")
    assert run_detail.status_code == 200
    detail = run_detail.json()
    assert detail["run_record"]["source_config_name"] == "campaign-studio.yaml"
    assert detail["run_record"]["experiment"]["variant_label"] in {
        "Interaction=0.02 | Time Step=0.02",
        "Interaction=0.08 | Time Step=0.02",
    }

    experiment_detail = client.get(f"/api/experiments/{campaign['campaign']['id']}")
    assert experiment_detail.status_code == 200
    experiment = experiment_detail.json()
    assert experiment["comparison"]["shared_experiment"]["dimensions"][0]["path"] == "engine.g_int"
    assert experiment["summary"]["run_count"] == 2


def test_cockpit_api_launch_campaign_with_edited_decision_profile(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]
    edited_config = deepcopy(config_item["config"])
    edited_config["objective"] = {
        "name": "Density-first cockpit recommendation",
        "summary": "Prefer the variant that produces the strongest peak density in the fast demo.",
        "primary_metric": "max_density",
        "goal": "maximize",
    }
    edited_config["constraints"] = {
        "max_abs_energy_drift": 0.5,
        "max_abs_norm_drift": 0.5,
        "min_max_density": 0.1,
        "max_elapsed_seconds": 10.0,
        "require_verification": False,
    }
    edited_config["ranking"] = {
        "primary_metric_weight": 3.0,
        "weights": {
            "energy_drift": 0.0,
            "norm_drift": 0.0,
            "max_density": 1.0,
            "elapsed_seconds": 0.0,
        },
    }
    edited_config["campaign"] = dict(edited_config["campaign"])
    edited_config["campaign"]["max_runs"] = 4
    edited_config["campaign"]["dimensions"] = [
        {"path": "engine.g_int", "values": [0.02, 0.08]},
        {"path": "engine.time_step", "values": [0.02]},
    ]

    campaign_payload = client.post(
        "/api/campaigns",
        json={"config": edited_config, "source_name": "campaign-studio.yaml"},
    )
    assert campaign_payload.status_code == 200
    campaign = campaign_payload.json()
    run_ids = {run["run_id"] for run in campaign["runs"]}
    decision = campaign["comparison"]["decision"]

    assert campaign["campaign"]["planned_run_count"] == 2
    assert decision["available"] is True
    assert decision["profile"]["objective"]["name"] == "Density-first cockpit recommendation"
    assert decision["profile"]["objective"]["primary_metric"] == "max_density"
    assert decision["profile"]["objective"]["goal"] == "maximize"
    assert decision["profile"]["constraints"]["require_verification"] is False
    assert decision["profile"]["ranking"]["primary_metric_weight"] == 3.0
    assert decision["profile"]["ranking"]["weights"]["max_density"] == 1.0
    assert decision["recommended_run_id"] in run_ids
    assert campaign["artifact"]["summary"]["recommended_run_id"] == decision["recommended_run_id"]

    run_detail = client.get(f"/api/runs/{campaign['runs'][0]['run_id']}")
    assert run_detail.status_code == 200
    detail = run_detail.json()
    assert detail["run_record"]["decision_profile"]["objective"]["name"] == (
        "Density-first cockpit recommendation"
    )


def test_cockpit_api_saves_imports_and_launches_campaign_study_templates(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    empty_templates = client.get("/api/campaign-studies")
    assert empty_templates.status_code == 200
    assert empty_templates.json()["items"] == []

    config_item = client.get("/api/configs").json()["items"][0]
    edited_config = deepcopy(config_item["config"])
    edited_config["objective"] = {
        "name": "Reusable density-first study",
        "summary": "Prefer the run with stronger peak density while preserving evidence.",
        "primary_metric": "max_density",
        "goal": "maximize",
    }
    edited_config["constraints"] = {
        "require_verification": True,
        "max_abs_energy_drift": 0.5,
        "max_abs_norm_drift": 0.5,
    }
    edited_config["ranking"] = {
        "primary_metric_weight": 3.0,
        "weights": {
            "energy_drift": 0.0,
            "norm_drift": 0.0,
            "max_density": 1.0,
            "elapsed_seconds": 0.0,
        },
    }
    edited_config["campaign"] = dict(edited_config["campaign"])
    edited_config["campaign"]["max_runs"] = 4
    edited_config["campaign"]["dimensions"] = [
        {"path": "engine.g_int", "values": [0.02, 0.08]},
        {"path": "engine.time_step", "values": [0.02]},
    ]

    save_payload = client.post(
        "/api/campaign-studies",
        json={
            "template": {
                "label": "Density-first reusable study",
                "description": "A two-run imported/exportable Campaign Studio design.",
                "source_config_name": "../campaign-study",
                "config": edited_config,
            },
        },
    )
    assert save_payload.status_code == 200
    saved = save_payload.json()
    template_id = saved["summary"]["template_id"]
    assert saved["summary"]["planned_run_count"] == 2
    assert saved["summary"]["objective_name"] == "Reusable density-first study"
    assert saved["summary"]["primary_metric"] == "max_density"
    assert saved["summary"]["source_config_name"] == "campaign-study.yaml"
    assert saved["template"]["scoring_contract"]["objective"]["goal"] == "maximize"
    assert saved["template"]["campaign"]["dimensions"][0]["values"] == [0.02, 0.08]
    assert saved["urls"]["download"].endswith("/download")
    assert (tmp_path / "experiments" / "campaign-studies" / f"{template_id}.json").exists()

    listed = client.get("/api/campaign-studies")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["template_id"] == template_id

    detail = client.get(f"/api/campaign-studies/{template_id}")
    assert detail.status_code == 200
    assert detail.json()["template"]["config"]["objective"]["name"] == (
        "Reusable density-first study"
    )

    download = client.get(f"/api/campaign-studies/{template_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/json")
    exported_template = download.json()
    assert exported_template["template_id"] == template_id

    imported_payload = client.post(
        "/api/campaign-studies/import",
        json={"template": exported_template},
    )
    assert imported_payload.status_code == 200
    imported = imported_payload.json()
    assert imported["summary"]["template_id"] != template_id
    assert imported["template"]["imported_from_template_id"] == template_id
    assert imported["template"]["config"] == exported_template["config"]

    campaign_payload = client.post(
        "/api/campaigns",
        json={
            "config": saved["template"]["config"],
            "source_name": saved["summary"]["source_config_name"],
        },
    )
    assert campaign_payload.status_code == 200
    campaign = campaign_payload.json()
    assert campaign["campaign"]["planned_run_count"] == 2
    assert campaign["comparison"]["decision"]["profile"]["objective"]["name"] == (
        "Reusable density-first study"
    )
    assert campaign["campaign"]["recommended_run_id"] in {
        run["run_id"] for run in campaign["runs"]
    }


def test_cockpit_api_rejects_invalid_edited_decision_profile(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]
    edited_config = deepcopy(config_item["config"])
    edited_config["objective"] = dict(edited_config["objective"])
    edited_config["objective"]["primary_metric"] = "unknown_metric"

    campaign_payload = client.post(
        "/api/campaigns",
        json={"config": edited_config, "source_name": "campaign-studio.yaml"},
    )
    assert campaign_payload.status_code == 400
    assert "objective.primary_metric" in campaign_payload.json()["detail"]


def test_cockpit_api_rejects_too_small_edited_campaign_grid(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]
    edited_config = config_item["config"]
    edited_config["campaign"] = dict(edited_config["campaign"])
    edited_config["campaign"]["dimensions"] = [
        {"path": "engine.g_int", "values": [0.02]},
        {"path": "engine.time_step", "values": [0.02]},
    ]

    campaign_payload = client.post(
        "/api/campaigns",
        json={"config": edited_config, "source_name": "campaign-studio.yaml"},
    )
    assert campaign_payload.status_code == 400
    assert campaign_payload.json()["detail"] == "Campaign requires at least two planned runs"


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
