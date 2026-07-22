from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
import logging
import re
import shutil
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient
from httpx import Response

from qs_dmss import __version__
from qs_dmss.ai import AIGeneration
from qs_dmss.cockpit import api as cockpit_api
from qs_dmss.cockpit.api import create_app
from qs_dmss.quantum_showcase import quantum_compilation_showcase_root


class FakeEvidenceAIProvider:
    provider_id = "test-provider"
    model = "test-research-model"
    endpoint_scope = "local"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, *, intent, context, allowed_artifact_ids) -> AIGeneration:
        self.calls.append(
            {
                "intent": intent,
                "context": deepcopy(context),
                "allowed_artifact_ids": set(allowed_artifact_ids),
            }
        )
        preferred = next(
            (
                artifact_id
                for artifact_id in sorted(allowed_artifact_ids)
                if artifact_id.startswith("comparison/")
                or artifact_id.endswith("/metrics")
            ),
            sorted(allowed_artifact_ids)[0],
        )
        return AIGeneration(
            response={
                "schema_version": 1,
                "title": "Bounded evidence draft",
                "draft": "The recorded workflow evidence remains subject to human review.",
                "findings": [
                    {
                        "statement": "The selected artifact records inspectable workflow evidence.",
                        "artifact_ids": [preferred],
                    }
                ],
                "limitations": ["This draft does not establish physical validity."],
                "proposed_actions": ["Ask a researcher to review the cited artifact."],
            },
            provenance={
                "provider": self.provider_id,
                "model": self.model,
                "endpoint_scope": self.endpoint_scope,
                "context_sha256": hashlib.sha256(
                    json.dumps(context, sort_keys=True).encode("utf-8")
                ).hexdigest(),
                "tool_calls": [],
                "usage": {"total_tokens": 42},
            },
        )


class InvalidEvidenceAIProvider(FakeEvidenceAIProvider):
    def generate(self, *, intent, context, allowed_artifact_ids) -> AIGeneration:
        generation = super().generate(
            intent=intent,
            context=context,
            allowed_artifact_ids=allowed_artifact_ids,
        )
        generation.response["findings"][0]["artifact_ids"] = ["outside/context"]
        return generation


def assert_baseline_security_headers(response: Response) -> None:
    headers = response.headers
    for name, value in cockpit_api.BASELINE_SECURITY_HEADERS.items():
        assert headers[name.lower()] == value


def test_cockpit_public_discovery_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.delenv("RENDER_GIT_BRANCH", raising=False)
    monkeypatch.delenv("QS_DMSS_AI_ENABLED", raising=False)
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    assert root.headers["link"] == (
        '<https://app.qs-dmss.studio/>; rel="canonical"'
    )
    assert root.headers["cache-control"] == "no-cache, max-age=0, must-revalidate"
    assert "x-robots-tag" not in root.headers
    assert_baseline_security_headers(root)
    assert re.search(
        r'<link rel="stylesheet" href="/static/styles\.css\?v=[0-9a-f]{12}"',
        root.text,
    )
    assert re.search(
        r'<script type="module" src="/static/app\.js\?v=[0-9a-f]{12}"></script>',
        root.text,
    )
    assert "__QS_DMSS_STATIC_REVISION__" not in root.text
    assert '<link rel="canonical" href="https://app.qs-dmss.studio/"' in root.text
    assert 'name="robots" content="index, follow, max-image-preview:large"' in root.text
    assert 'property="og:type" content="website"' in root.text
    assert re.search(
        r'property="og:image"\s+'
        r'content="https://app\.qs-dmss\.studio/static/hosted-demo-social-preview-v0132\.png"',
        root.text,
    )
    assert 'name="twitter:card" content="summary_large_image"' in root.text

    json_ld_match = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        root.text,
        flags=re.DOTALL,
    )
    assert json_ld_match is not None
    structured_data = json.loads(json_ld_match.group(1))
    assert structured_data["@type"] == "WebApplication"
    assert structured_data["url"] == "https://app.qs-dmss.studio/"
    assert structured_data["softwareVersion"] == __version__
    assert structured_data["isPartOf"]["url"] == "https://qs-dmss.studio/"
    assert structured_data["publisher"]["name"] == "AI-Bio Synergy Holdings LLC"
    assert structured_data["citation"] == "https://doi.org/10.5281/zenodo.21366910"

    social_preview = client.get("/static/hosted-demo-social-preview-v0132.png")
    assert social_preview.status_code == 200
    assert social_preview.headers["content-type"].startswith("image/png")
    assert social_preview.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert int.from_bytes(social_preview.content[16:20], "big") == 1200
    assert int.from_bytes(social_preview.content[20:24], "big") == 630
    assert_baseline_security_headers(social_preview)

    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Disallow: /api/" in robots.text
    assert "Disallow: /openapi.json" in robots.text
    assert "Sitemap: https://app.qs-dmss.studio/sitemap.xml" in robots.text
    assert "x-robots-tag" not in robots.headers
    assert_baseline_security_headers(robots)

    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert sitemap.headers["content-type"].startswith("application/xml")
    assert "<loc>https://app.qs-dmss.studio/</loc>" in sitemap.text
    assert sitemap.text.count("<url>") == 1
    assert_baseline_security_headers(sitemap)

    health = client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.json()
    assert health_payload["version"] == __version__
    assert health_payload["ui_contract"] == "research-command-center-v2"
    assert health_payload["deployment"] == {
        "provider": "local",
        "git_commit": None,
        "git_branch": None,
    }
    assert health_payload["release"] == {
        "version": __version__,
        "tag": f"v{__version__}",
        "latest_archived_release_tag": "v0.13.2",
        "project_doi": "10.5281/zenodo.20074924",
        "project_doi_url": "https://doi.org/10.5281/zenodo.20074924",
        "archived_release_doi": "10.5281/zenodo.21366910",
        "archived_release_doi_url": "https://doi.org/10.5281/zenodo.21366910",
        "archived_release_record_url": "https://zenodo.org/records/21366910",
    }
    assert {
        "package_root",
        "repo_root",
        "output_root",
        "experiments_root",
        "jobs_root",
    }.isdisjoint(health_payload)
    capabilities = health_payload["capabilities"]
    assert capabilities["quantum_validation_snapshot"] is True
    assert capabilities["quantum_validation_live"] is capabilities["quantum_stack_available"]
    assert capabilities["client_sweep_preflight"] is True
    assert capabilities["hosted_custom_compute"] is True
    assert capabilities["ai_advisory_drafts"] is False
    assert health.headers["x-robots-tag"] == (
        "noindex, nofollow, noarchive, nosnippet"
    )
    assert_baseline_security_headers(health)

    ai_status = client.get("/api/ai/status")
    assert ai_status.status_code == 200
    assert ai_status.json()["availability"] == "disabled"
    assert ai_status.json()["available_in_current_mode"] is False
    assert ai_status.json()["data_policy"]["arbitrary_user_context_allowed"] is False

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert openapi.headers["x-robots-tag"] == (
        "noindex, nofollow, noarchive, nosnippet"
    )
    assert_baseline_security_headers(openapi)


def test_health_exposes_validated_render_deployment_provenance(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commit = "a" * 40
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("RENDER_GIT_COMMIT", commit.upper())
    monkeypatch.setenv("RENDER_GIT_BRANCH", "main")
    monkeypatch.setenv("RENDER_SERVICE_ID", "must-not-be-public")
    app = create_app(
        repo_root=Path(__file__).resolve().parents[1],
        output_root=tmp_path / "runs",
    )

    response = TestClient(app).get("/api/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["deployment"] == {
        "provider": "render",
        "git_commit": commit,
        "git_branch": "main",
    }
    assert "must-not-be-public" not in json.dumps(payload)


def test_cockpit_quantum_validation_showcase_is_read_only(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(
        repo_root=repo_root,
        output_root=tmp_path / "hosted-runs",
        hosted_demo=True,
    )
    client = TestClient(app)

    response = client.get("/api/quantum-validation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["showcase_id"] == "fractal-ssfm-compilation-v0.12.0"
    assert payload["status"] == "pass"
    assert payload["validation"]["rows_passing"] == 12
    assert payload["validation"]["row_count"] == 12
    assert payload["validation"]["reference_exact_rows"] == 6
    assert payload["validation"]["bounded_approximation_rows"] == 6
    assert payload["validation"]["archive"]["readable"] is True
    assert payload["validation"]["archive"]["contains_manifest"] is True
    assert payload["validation"]["archive"]["contains_html_report"] is True
    assert payload["execution_policy"] == {
        "credentials_read": False,
        "local_simulation_only": True,
        "max_authorized_cost_usd": 0.0,
        "provider": None,
        "remote_api_called": False,
        "submitted": False,
    }
    assert payload["recommended_configuration"]["topology_id"] == (
        "generic-all-to-all-5q"
    )
    assert payload["recommended_configuration"]["optimization_level"] == 3
    assert len(payload["bundle"]["sha256"]) == 64
    assert "hosted app does not transpile circuits" in payload["limitations"][0]

    expected_types = {
        "report": "application/json",
        "summary": "text/html",
        "markdown": "text/markdown",
        "matrix": "text/csv",
        "manifest": "application/json",
        "bundle": "application/zip",
    }
    for artifact_name, content_type in expected_types.items():
        download = client.get(payload["downloads"][artifact_name])
        assert download.status_code == 200
        assert download.headers["content-type"].startswith(content_type)
        if artifact_name == "summary":
            assert "content-disposition" not in download.headers
            assert "default-src 'none'" in download.headers["content-security-policy"]
            assert "QS-DMSS Quantum Compilation Validation" in download.text
            assert "What this does not claim" in download.text
        else:
            assert "attachment" in download.headers["content-disposition"]

    portable_json_link = client.get(
        "/api/quantum-validation/files/quantum-compilation-validation.json"
    )
    assert portable_json_link.status_code == 200
    assert portable_json_link.headers["content-type"].startswith("application/json")

    bundle = client.get(payload["downloads"]["bundle"])
    assert hashlib.sha256(bundle.content).hexdigest() == payload["bundle"]["sha256"]
    assert client.get("/api/quantum-validation/files/../../pyproject.toml").status_code == 404
    assert client.get("/api/quantum-validation/files/not-allowlisted").status_code == 404
    assert client.post("/api/quantum-validation").status_code == 405
    live_response = client.post(
        "/api/quantum-validation/runs",
        json={"shots": 128, "seed": 7},
    )
    assert live_response.status_code == 403
    assert "local full application" in live_response.json()["detail"]
    assert client.get("/api/jobs/not-a-job").status_code == 404


def test_cockpit_local_quantum_validation_runs_and_persists_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    def fake_validation(*, output_root: str | Path, **kwargs) -> dict:
        shutil.copytree(
            quantum_compilation_showcase_root(),
            Path(output_root),
            dirs_exist_ok=True,
        )
        return {"success": True, "parameters": kwargs}

    real_find_spec = cockpit_api.importlib.util.find_spec
    monkeypatch.setattr(
        cockpit_api.importlib.util,
        "find_spec",
        lambda name: object()
        if name in {"qiskit", "qiskit_aer"}
        else real_find_spec(name),
    )
    monkeypatch.setattr(
        cockpit_api,
        "validate_fractal_quantum_compilation",
        fake_validation,
    )

    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)
    response = client.post(
        "/api/quantum-validation/runs",
        json={
            "shots": 128,
            "seed": 11,
            "reference_tolerance": 1e-10,
            "compilation_tolerance": 1e-6,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "live_local_run"
    assert payload["status"] == "pass"
    assert payload["runtime"]["live_execution"] is True
    assert payload["runtime"]["package_version"] == __version__
    assert payload["run"]["package_version"] == __version__
    assert payload["run"]["runtime_mode"] == "local_full"
    assert payload["run"]["parameters"]["shots"] == 128
    assert payload["run"]["parameters"]["seed"] == 11
    assert payload["visualization"]["source_run_id"] == payload["run"]["run_id"]
    assert len(payload["visualization"]["resource_fingerprint"]) == 64
    assert payload["visualization"]["matrix_row_count"] == 12
    assert payload["visualization"]["matrix_resource_value_count"] == 24
    assert payload["visualization"]["attribution_component_count"] == 4
    assert payload["visualization"]["attribution_resource_value_count"] == 8
    assert Path(payload["run"]["output_directory"]).is_dir()
    assert payload["validation"]["rows_passing"] == 12
    assert payload["downloads"]["bundle"].startswith(
        f"/api/quantum-validation/runs/{payload['run']['run_id']}/files/"
    )

    latest = client.get("/api/quantum-validation/runs/latest")
    assert latest.status_code == 200
    assert latest.headers["cache-control"] == "no-store"
    assert latest.json()["available"] is True
    assert latest.json()["result"]["run"]["run_id"] == payload["run"]["run_id"]
    assert (
        latest.json()["result"]["visualization"]["resource_fingerprint"]
        == payload["visualization"]["resource_fingerprint"]
    )

    bundle = client.get(payload["downloads"]["bundle"])
    assert bundle.status_code == 200
    assert bundle.headers["content-type"].startswith("application/zip")
    traversal = client.get(
        f"/api/quantum-validation/runs/{payload['run']['run_id']}/files/not-allowlisted"
    )
    assert traversal.status_code == 404


def test_cockpit_api_launch_verify_and_replay(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    assert "QS-DMSS Studio" in root.text
    assert "Research Cockpit" in root.text
    assert 'href="/static/favicon.svg"' in root.text
    favicon = client.get("/static/favicon.svg")
    assert favicon.status_code == 200
    assert "QS-DMSS Studio" in favicon.text
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
    assert 'id="workspaceExportPanel"' in root.text
    assert 'id="workspaceCollaboratorName"' in root.text
    assert 'id="workspaceAnnotationText"' in root.text
    assert 'id="exportWorkspaceButton"' in root.text
    assert 'id="workspaceDownloadLink"' in root.text
    assert 'id="workspaceImportInput"' in root.text
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
    assert 'id="campaignStudyTemplateCards"' in root.text
    assert 'id="saveCampaignStudyTemplateButton"' in root.text
    assert 'id="loadCampaignStudyTemplateButton"' in root.text
    assert 'id="runCampaignStudyTemplateButton"' in root.text
    assert 'id="downloadCampaignStudyTemplateLink"' in root.text
    assert 'id="importCampaignStudyTemplateInput"' in root.text
    assert 'id="campaignStudyGuide"' in root.text
    assert 'id="campaignStudyGuideChangedList"' in root.text
    assert 'id="campaignStudyGuideMetricList"' in root.text
    assert 'id="statusJobId"' in root.text
    assert 'id="statusJobBackend"' in root.text
    assert 'id="experimentJobId"' in root.text
    assert 'id="jobProvenancePanel"' in root.text
    assert 'id="jobProvenanceTitle"' in root.text
    assert 'id="jobProvenanceLifecycle"' in root.text
    assert 'id="jobProvenanceArtifacts"' in root.text
    assert 'id="hostedDemoBanner"' in root.text
    assert 'id="quantum-validation"' in root.text
    assert 'id="quantumTopologyCharts"' in root.text
    assert 'id="quantumAttributionChart"' in root.text
    assert 'id="quantumMatrixBody"' in root.text
    assert 'aria-label="Quantum compilation validation matrix"' in root.text
    assert "Public hosted demo outputs are temporary" in root.text
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
    config_items = config_payload.json()["items"]
    config_item = config_items[0]
    assert config_item["name"] == "demo.yaml"
    assert len(config_items) >= 5
    assert {item["name"] for item in config_items}.issuperset(
        {
            "conservation_baseline.yaml",
            "interaction_response.yaml",
            "uniform_control.yaml",
        }
    )
    assert all(item["summary"] and item["evidence_focus"] for item in config_items)

    launch_payload = client.post(
        "/api/runs",
        json={"config": config_item["config"], "source_name": config_item["name"]},
    )
    assert launch_payload.status_code == 200
    created_run = launch_payload.json()
    run_id = created_run["summary"]["run_id"]
    execution_job = created_run["execution_job"]["summary"]
    job_id = execution_job["job_id"]
    assert execution_job["available"] is True
    assert execution_job["backend"] == "local"
    assert execution_job["state"] == "succeeded"
    assert execution_job["run_id"] == run_id
    assert {"evidence_bundle", "manifest", "metrics", "report"}.issubset(
        set(execution_job["artifact_roles"])
    )
    assert created_run["urls"]["job"].endswith("/job")

    runs_payload = client.get("/api/runs")
    assert runs_payload.status_code == 200
    listed_run = runs_payload.json()["items"][0]
    assert listed_run["run_id"] == run_id
    assert listed_run["execution_job"]["job_id"] == job_id

    run_job_payload = client.get(f"/api/runs/{run_id}/job")
    assert run_job_payload.status_code == 200
    run_job = run_job_payload.json()
    assert run_job["summary"]["job_id"] == job_id
    assert run_job["summary"]["state"] == "succeeded"
    assert run_job["result"]["run_id"] == run_id
    assert {"submitted", "running", "collecting", "succeeded"}.issubset(
        {event["state"] for event in run_job["lifecycle"]}
    )

    job_payload = client.get(f"/api/jobs/{job_id}")
    assert job_payload.status_code == 200
    assert job_payload.json()["summary"]["run_id"] == run_id

    verify_payload = client.post(f"/api/runs/{run_id}/verify")
    assert verify_payload.status_code == 200
    assert verify_payload.json()["success"] is True

    bundle_payload = client.get(f"/api/runs/{run_id}/bundle")
    assert bundle_payload.status_code == 200
    assert bundle_payload.headers["content-type"].startswith("application/zip")
    assert bundle_payload.headers["x-robots-tag"] == (
        "noindex, nofollow, noarchive, nosnippet"
    )

    assert created_run["urls"]["review_bundle"].endswith("/review-bundle")
    assert created_run["urls"]["state_bundle"].endswith("/state-bundle")
    review_bundle = client.get(created_run["urls"]["review_bundle"])
    state_bundle = client.get(created_run["urls"]["state_bundle"])
    assert review_bundle.status_code == 200
    assert state_bundle.status_code == 200
    with zipfile.ZipFile(io.BytesIO(review_bundle.content)) as archive:
        review_names = set(archive.namelist())
        review_profile = json.loads(archive.read("bundle-profile.json"))
    assert review_profile["profile"] == "review"
    assert review_profile["run_id"] == run_id
    assert {"report.html", "metrics.json", "environment.lock.json"}.issubset(review_names)
    assert "artifacts/final_state.npz" not in review_names
    with zipfile.ZipFile(io.BytesIO(state_bundle.content)) as archive:
        state_names = set(archive.namelist())
        state_profile = json.loads(archive.read("bundle-profile.json"))
    assert state_profile["profile"] == "state"
    assert {"artifacts/final_density.npy", "artifacts/final_state.npz"}.issubset(state_names)

    report_payload = client.get(f"/api/runs/{run_id}/report")
    assert report_payload.status_code == 200
    assert "QS-DMSS Evidence Report" in report_payload.text
    assert "Conservation evidence plate" in report_payload.text
    assert "Executive diagnostic summary" in report_payload.text
    assert "run_conservation_diagnostics" in report_payload.text
    assert "numerical conservation diagnostics; not physical validation" in report_payload.text
    assert report_payload.headers["x-robots-tag"] == (
        "noindex, nofollow, noarchive, nosnippet"
    )

    replay_payload = client.post(f"/api/runs/{run_id}/replay")
    assert replay_payload.status_code == 200
    replay_run = replay_payload.json()
    assert replay_run["run_record"]["replayed_from"] == run_id


def test_cockpit_hosted_demo_uses_session_scoped_outputs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(
        repo_root=repo_root,
        output_root=tmp_path / "hosted-runs",
        hosted_demo=True,
    )
    first_client = TestClient(app)
    second_client = TestClient(app)

    health = first_client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.json()
    assert health_payload["hosted_demo"]["enabled"] is True
    assert health_payload["hosted_demo"]["max_campaign_runs"] == 5
    assert health_payload["hosted_demo"]["read_only_surfaces"] == [
        "precomputed Fractal SSFM quantum compilation validation"
    ]
    capabilities = health_payload["capabilities"]
    assert capabilities["quantum_validation_snapshot"] is True
    assert capabilities["quantum_validation_live"] is False
    assert capabilities["client_sweep_preflight"] is True
    assert capabilities["hosted_custom_compute"] is False
    assert "qs_dmss_demo_session" in first_client.cookies
    assert {
        "package_root",
        "repo_root",
        "output_root",
        "experiments_root",
        "jobs_root",
    }.isdisjoint(health_payload)

    showcase_payload = first_client.post("/api/showcases/canonical-simulation/run")
    assert showcase_payload.status_code == 200
    first_runs = first_client.get("/api/runs")
    second_runs = second_client.get("/api/runs")
    assert first_runs.status_code == 200
    assert second_runs.status_code == 200
    assert first_runs.json()["items"]
    assert second_runs.json()["items"] == []


def test_cockpit_hosted_demo_restricts_custom_inputs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(
        repo_root=repo_root,
        output_root=tmp_path / "hosted-runs",
        hosted_demo=True,
    )
    client = TestClient(app)
    config_item = client.get("/api/configs").json()["items"][0]

    custom_run = client.post(
        "/api/runs",
        json={"config": config_item["config"], "source_name": "custom.yaml"},
    )
    assert custom_run.status_code == 403
    assert "arbitrary run configs" in custom_run.json()["detail"]

    custom_sweep = client.post(
        "/api/sweeps",
        json={
            "config": config_item["config"],
            "parameter_path": "engine.g_int",
            "values": [0.0, 0.1],
        },
    )
    assert custom_sweep.status_code == 403

    custom_campaign = client.post(
        "/api/campaigns",
        json={"config": config_item["config"], "source_name": "campaign.yaml"},
    )
    assert custom_campaign.status_code == 403
    assert "Self-Interaction Sweep" in custom_campaign.json()["detail"]

    save_template = client.post(
        "/api/campaign-studies",
        json={"template": {"label": "custom", "config": config_item["config"]}},
    )
    assert save_template.status_code == 403

    import_workspace = client.post(
        "/api/workspaces/import",
        json={"workspace": {"workspace_id": "uploaded"}},
    )
    assert import_workspace.status_code == 403


def test_cockpit_hosted_demo_allows_packaged_self_interaction_template(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(
        repo_root=repo_root,
        output_root=tmp_path / "hosted-runs",
        hosted_demo=True,
    )
    client = TestClient(app)

    detail_payload = client.get("/api/campaign-studies/self-interaction-sweep")
    assert detail_payload.status_code == 200
    template = detail_payload.json()["template"]

    campaign_payload = client.post(
        "/api/campaigns",
        json={
            "config": template["config"],
            "source_name": template["source_config_name"],
            "study_template_id": template["template_id"],
        },
    )
    assert campaign_payload.status_code == 200
    campaign = campaign_payload.json()
    assert campaign["campaign"]["planned_run_count"] == 5
    assert campaign["study_template"]["summary"]["template_id"] == "self-interaction-sweep"


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


def test_cockpit_ai_sidecar_is_bounded_reviewable_and_separate_from_evidence(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    provider = FakeEvidenceAIProvider()
    app = create_app(
        repo_root=repo_root,
        output_root=tmp_path / "runs",
        ai_provider=provider,
    )
    client = TestClient(app)

    status = client.get("/api/ai/status")
    assert status.status_code == 200
    assert status.json()["available_in_current_mode"] is True
    assert status.json()["execution_policy"] == {
        "advisory_only": True,
        "tools_available": False,
        "run_launch_allowed": False,
        "artifact_mutation_allowed": False,
        "human_review_required": True,
    }
    assert status.json()["data_policy"]["browser_supplies_identifiers_only"] is True

    missing_run = client.post(
        "/api/ai/drafts",
        json={"intent": "summary", "scenario_name": "canonical-simulation"},
    )
    assert missing_run.status_code == 400

    arbitrary_context = client.post(
        "/api/ai/drafts",
        json={
            "intent": "next",
            "scenario_name": "canonical-simulation",
            "context": {"secret": "must not be accepted"},
        },
    )
    assert arbitrary_context.status_code == 422

    launch = client.post("/api/showcases/canonical-simulation/run")
    assert launch.status_code == 200
    run_id = launch.json()["run"]["summary"]["run_id"]
    run_manifest = tmp_path / "runs" / run_id / "manifest.sha256.json"
    manifest_before = run_manifest.read_bytes()

    generated = client.post(
        "/api/ai/drafts",
        json={
            "intent": "summary",
            "scenario_name": "canonical-simulation",
            "run_id": run_id,
        },
    )
    assert generated.status_code == 200
    draft = generated.json()
    assert draft["status"] == "draft"
    assert draft["human_review"]["status"] == "pending"
    assert draft["claim_boundary"].startswith("AI-generated advisory annotation")
    assert draft["provenance"]["tool_calls"] == []
    assert run_manifest.read_bytes() == manifest_before

    serialized_context = json.dumps(provider.calls[-1]["context"])
    assert str(tmp_path) not in serialized_context
    assert "run_dir" not in serialized_context
    assert "bundle_path" not in serialized_context
    assert any(
        artifact["id"] == f"run/{run_id}/metrics"
        for artifact in provider.calls[-1]["context"]["artifacts"]
    )

    bundle = client.get(draft["urls"]["bundle"])
    assert bundle.status_code == 200
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
        names = set(archive.namelist())
    assert f"{draft['interaction_id']}/interaction.json" in names
    assert f"{draft['interaction_id']}/manifest.sha256.json" in names

    reviewed = client.post(
        draft["urls"]["review"],
        json={
            "status": "edited",
            "reviewer": "Research lead",
            "edited_draft": "Human-reviewed evidence wording.",
        },
    )
    assert reviewed.status_code == 200
    reviewed_record = reviewed.json()
    assert reviewed_record["status"] == "human_reviewed"
    assert reviewed_record["human_review"]["status"] == "edited"
    assert reviewed_record["human_review"]["edited_draft"] == (
        "Human-reviewed evidence wording."
    )
    assert reviewed_record["review_history"] == [reviewed_record["human_review"]]

    missing_comparison = client.post(
        "/api/ai/drafts",
        json={
            "intent": "comparison",
            "scenario_name": "canonical-simulation",
            "run_id": run_id,
        },
    )
    assert missing_comparison.status_code == 400

    comparison = client.post("/api/showcases/canonical-simulation/compare")
    assert comparison.status_code == 200
    experiment_id = comparison.json()["artifact"]["summary"]["experiment_id"]
    critique = client.post(
        "/api/ai/drafts",
        json={
            "intent": "comparison",
            "scenario_name": "canonical-simulation",
            "experiment_id": experiment_id,
        },
    )
    assert critique.status_code == 200, critique.text
    comparison_artifact = next(
        artifact
        for artifact in provider.calls[-1]["context"]["artifacts"]
        if artifact["id"] == f"comparison/{experiment_id}"
    )
    assert len(comparison_artifact["data"]["rows"]) == 3
    assert provider.calls[-1]["intent"] == "comparison"

    next_experiment = client.post(
        "/api/ai/drafts",
        json={
            "intent": "next",
            "scenario_name": "canonical-simulation",
            "run_id": run_id,
            "experiment_id": experiment_id,
        },
    )
    assert next_experiment.status_code == 200
    assert provider.calls[-1]["intent"] == "next"
    assert {
        artifact["kind"] for artifact in provider.calls[-1]["context"]["artifacts"]
    } >= {"run_metrics", "run_comparison"}


def test_cockpit_ai_sidecar_requires_separate_hosted_enablement(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("QS_DMSS_AI_ENABLED", "1")
    monkeypatch.setenv("QS_DMSS_AI_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("QS_DMSS_AI_MODEL", "local-research-model")
    monkeypatch.delenv("QS_DMSS_AI_HOSTED_ENABLED", raising=False)
    app = create_app(
        repo_root=Path(__file__).resolve().parents[1],
        output_root=tmp_path / "runs",
        hosted_demo=True,
    )
    client = TestClient(app)

    status = client.get("/api/ai/status")
    assert status.status_code == 200
    assert status.json()["availability"] == "hosted_disabled"
    assert status.json()["available_in_current_mode"] is False
    assert status.json()["provider"] is None
    assert status.json()["model"] is None
    assert status.json()["endpoint_scope"] is None

    generated = client.post(
        "/api/ai/drafts",
        json={"intent": "next", "scenario_name": "canonical-simulation"},
    )
    assert generated.status_code == 403
    assert "disabled in the public hosted demo" in generated.json()["detail"]


def test_cockpit_revalidates_provider_output_before_persisting(tmp_path: Path) -> None:
    output_root = tmp_path / "runs"
    app = create_app(
        repo_root=Path(__file__).resolve().parents[1],
        output_root=output_root,
        ai_provider=InvalidEvidenceAIProvider(),
    )
    client = TestClient(app)

    generated = client.post(
        "/api/ai/drafts",
        json={"intent": "next", "scenario_name": "canonical-simulation"},
    )
    assert generated.status_code == 502
    assert "No advisory artifact was created" in generated.json()["detail"]
    assert not (output_root / "ai-interactions").exists()


def test_cockpit_api_showcases_hides_internal_exception_details(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    def broken_campaign_studio_preview(self) -> dict:
        raise RuntimeError("internal secret path C:\\private\\qs-dmss")

    monkeypatch.setattr(
        cockpit_api.CockpitService,
        "campaign_studio_preview",
        broken_campaign_studio_preview,
    )
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    showcase_payload = client.get("/api/showcases")

    assert showcase_payload.status_code == 500
    assert showcase_payload.json() == {
        "detail": cockpit_api.GENERIC_COCKPIT_ERROR_DETAIL
    }
    assert "internal secret path" not in showcase_payload.text
    assert "Traceback" not in showcase_payload.text


def test_cockpit_api_campaign_studio_preview_hides_validation_details(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    def broken_campaign_plan(config: dict) -> dict:
        raise ValueError("sensitive campaign validation path C:\\private\\plan.yaml")

    monkeypatch.setattr(cockpit_api, "build_campaign_plan", broken_campaign_plan)
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    showcase_payload = client.get("/api/showcases")

    assert showcase_payload.status_code == 200
    campaign_studio = showcase_payload.json()["campaign_studio"]
    assert campaign_studio["available"] is False
    assert campaign_studio["summary"] == (
        "The default config is not a launchable campaign study yet."
    )
    assert "sensitive campaign validation path" not in showcase_payload.text
    assert "Traceback" not in showcase_payload.text


def test_cockpit_api_global_exception_handler_hides_internal_exception_details(
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    def broken_launch_showcase(self, scenario: str) -> dict:
        raise RuntimeError(f"sensitive scenario failure for {scenario}")

    monkeypatch.setattr(
        cockpit_api.CockpitService,
        "launch_showcase",
        broken_launch_showcase,
    )
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app, raise_server_exceptions=False)
    caplog.set_level(logging.ERROR, logger="qs_dmss.cockpit")

    showcase_payload = client.post("/api/showcases/canonical-simulation/run")

    assert showcase_payload.status_code == 500
    assert showcase_payload.json() == {
        "detail": cockpit_api.GENERIC_COCKPIT_ERROR_DETAIL
    }
    assert "sensitive scenario failure" not in showcase_payload.text
    assert "Traceback" not in showcase_payload.text
    assert (
        "cockpit_request_failed method=POST "
        "path=/api/showcases/canonical-simulation/run exception_type=RuntimeError"
    ) in caplog.text
    assert "sensitive scenario failure" not in caplog.text


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
    assert all(
        row["execution_job"]["state"] == "succeeded"
        for row in guided["comparison"]["rows"]
    )
    assert guided["comparison"]["shared_experiment"]["kind"] == "guided-comparison"
    assert guided["comparison"]["shared_experiment"]["strategy"] == "packaged-variants"
    assert guided["artifact"]["summary"]["kind"] == "guided-comparison"
    assert guided["artifact"]["summary"]["run_count"] == 3
    assert guided["artifact"]["summary"]["experiment_id"].startswith("guided-comparison-")
    parent_job = guided["execution_job"]["summary"]
    assert parent_job["state"] == "succeeded"
    assert parent_job["experiment_id"] == guided["artifact"]["summary"]["experiment_id"]
    assert set(parent_job["child_job_ids"]) == {
        row["execution_job"]["job_id"] for row in guided["comparison"]["rows"]
    }
    assert {"experiment_directory", "comparison", "evidence_bundle", "report"}.issubset(
        set(parent_job["artifact_roles"])
    )
    assert guided["urls"]["report"].endswith("/report")
    assert guided["urls"]["workbook"].endswith("/workbook")
    assert guided["urls"]["workbook_download"].endswith("/workbook/download")
    assert guided["urls"]["bundle"].endswith("/bundle")
    assert "workbook.html" in guided["artifact"]["evidence"]["artifact_paths"]
    assert len({run["config_digest"] for run in guided["runs"]}) == 3
    assert len({run["bundle_sha256"] for run in guided["runs"]}) == 3
    assert all(run["bundle_filename"].endswith("-evidence-bundle.zip") for run in guided["runs"])

    guide = guided["guide"]
    assert guide["plain_language_summary"].startswith("QS-DMSS ran the packaged showcase")
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
    assert "Variant evidence plate" in experiment_report.text
    assert "Interpretive comparison summary" in experiment_report.text
    assert "Smallest |energy drift|" in experiment_report.text
    assert "Marker key" in experiment_report.text
    assert "Dry-run Slurm" in experiment_report.text
    assert "Validation spine" in experiment_report.text
    assert "width:min(1480px" in experiment_report.text

    experiment_workbook = client.get(guided["urls"]["workbook"])
    assert experiment_workbook.status_code == 200
    assert "QS-DMSS Research Workbook" in experiment_workbook.text
    assert 'role="tablist"' in experiment_workbook.text
    assert "Embedded comparison data" in experiment_workbook.text
    assert "Interpretive comparison summary" in experiment_workbook.text
    assert experiment_workbook.text != experiment_report.text

    workbook_download = client.get(guided["urls"]["workbook_download"])
    assert workbook_download.status_code == 200
    assert "research-workbook.html" in workbook_download.headers["content-disposition"]

    experiment_bundle = client.get(guided["urls"]["bundle"])
    assert experiment_bundle.status_code == 200
    assert experiment_bundle.headers["content-type"].startswith("application/zip")
    experiment_id = guided["artifact"]["summary"]["experiment_id"]
    assert f'{experiment_id}-comparison-bundle.zip' in experiment_bundle.headers[
        "content-disposition"
    ]

    downloaded_hashes = set()
    for run in guided["runs"]:
        run_bundle = client.get(f'/api/runs/{run["run_id"]}/bundle')
        assert run_bundle.status_code == 200
        assert run["bundle_filename"] in run_bundle.headers["content-disposition"]
        digest = hashlib.sha256(run_bundle.content).hexdigest()
        assert digest == run["bundle_sha256"]
        downloaded_hashes.add(digest)
    assert len(downloaded_hashes) == 3


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
    assert sweep["execution_job"]["summary"]["experiment_id"] == sweep["experiment"]["id"]
    assert sweep["execution_job"]["summary"]["metadata"]["parameter_path"] == "engine.g_int"
    assert len(sweep["execution_job"]["summary"]["child_job_ids"]) == 2

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
    assert all(
        row["execution_job"]["backend"] == "local"
        for row in comparison["rows"]
    )
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


def test_cockpit_api_exports_evidence_only_mixed_objective_comparison(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    base_config = client.get("/api/configs").json()["items"][0]["config"]
    stability_config = deepcopy(base_config)
    stability_config["run"]["name"] = "stability-profile"
    density_config = deepcopy(base_config)
    density_config["run"]["name"] = "density-profile"
    density_config["objective"] = {
        "name": "Density-response review",
        "summary": "Inspect the largest terminal density response.",
        "primary_metric": "max_density",
        "goal": "maximize",
    }

    run_ids = []
    for source_name, config in (
        ("stability.yaml", stability_config),
        ("density.yaml", density_config),
    ):
        response = client.post(
            "/api/runs",
            json={"config": config, "source_name": source_name},
        )
        assert response.status_code == 200
        run_ids.append(response.json()["summary"]["run_id"])

    comparison_response = client.post("/api/compare", json={"run_ids": run_ids})
    assert comparison_response.status_code == 200
    comparison = comparison_response.json()
    assert comparison["decision"]["mode"] == "evidence_only"
    assert comparison["decision"]["objective_profile_status"] == "mixed"
    assert comparison["decision"]["profile_count"] == 2
    assert len(comparison["rows"]) == 2

    experiment_response = client.post(
        "/api/experiments",
        json={"run_ids": run_ids, "label": "mixed objective review"},
    )
    assert experiment_response.status_code == 200
    experiment = experiment_response.json()
    assert experiment["summary"]["recommended_run_id"] is None
    assert experiment["decision"]["mode"] == "evidence_only"

    report = client.get(experiment["urls"]["report"])
    assert report.status_code == 200
    assert "Evidence-only comparison" in report.text
    assert "No cross-profile winner" in report.text
    assert "Norm drift" in report.text
    assert "Evidence-only: no shared scoring contract" in report.text

    workbook = client.get(experiment["urls"]["workbook"])
    assert workbook.status_code == 200
    assert "No cross-profile winner" in workbook.text
    assert "select runs with one shared objective profile" in workbook.text


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
    parent_job = campaign["execution_job"]["summary"]
    assert parent_job["state"] == "succeeded"
    assert parent_job["experiment_id"] == campaign["campaign"]["id"]
    assert parent_job["metadata"]["planned_run_count"] == 6
    assert len(parent_job["child_job_ids"]) == 6
    assert all(
        row["execution_job"]["state"] == "succeeded"
        for row in campaign["comparison"]["rows"]
    )

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
    assert experiment["summary"]["execution_job"]["job_id"] == parent_job["job_id"]
    assert experiment["experiment_record"]["execution_job"]["job_id"] == parent_job["job_id"]
    assert experiment["urls"]["job"].endswith(parent_job["job_id"])
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

    initial_templates = client.get("/api/campaign-studies")
    assert initial_templates.status_code == 200
    assert [
        item["template_id"]
        for item in initial_templates.json()["items"]
    ] == ["self-interaction-sweep"]
    assert initial_templates.json()["items"][0]["packaged"] is True

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
    listed_items = listed.json()["items"]
    assert any(item["template_id"] == template_id for item in listed_items)

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
            "study_template_id": template_id,
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
    assert campaign["study_template"]["summary"]["template_id"] == template_id
    assert campaign["study_template"]["summary"]["last_run"]["status"] == "completed"
    assert campaign["study_template"]["summary"]["last_run"]["recommended_run_id"] == (
        campaign["campaign"]["recommended_run_id"]
    )
    assert campaign["study_template"]["summary"]["last_run"]["experiment_report_url"].endswith(
        "/report"
    )
    assert campaign["study_template"]["summary"]["last_run"]["experiment_bundle_url"].endswith(
        "/bundle"
    )

    updated_detail = client.get(f"/api/campaign-studies/{template_id}")
    assert updated_detail.status_code == 200
    last_run = updated_detail.json()["template"]["last_run"]
    assert last_run["experiment_id"] == campaign["artifact"]["summary"]["experiment_id"]
    assert last_run["run_count"] == 2
    assert last_run["recommended_run_id"] == campaign["campaign"]["recommended_run_id"]

    updated_list = client.get("/api/campaign-studies")
    assert updated_list.status_code == 200
    updated_summary = next(
        item for item in updated_list.json()["items"] if item["template_id"] == template_id
    )
    assert updated_summary["last_run"]["experiment_id"] == (
        campaign["artifact"]["summary"]["experiment_id"]
    )


def test_cockpit_api_lists_and_runs_packaged_self_interaction_study_template(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    templates_payload = client.get("/api/campaign-studies")
    assert templates_payload.status_code == 200
    templates = templates_payload.json()["items"]
    packaged = next(
        item for item in templates if item["template_id"] == "self-interaction-sweep"
    )
    assert packaged["label"] == "Self-Interaction Sweep"
    assert packaged["packaged"] is True
    assert packaged["origin"] == "packaged"
    assert "engine.g_int" in packaged["description"]
    assert packaged["expected_runtime"].startswith("Fast laptop/CI campaign")
    assert [metric["label"] for metric in packaged["metrics"]] == [
        "Energy drift",
        "Norm drift",
        "Max density",
        "Elapsed seconds",
    ]
    assert packaged["limitations"]
    assert packaged["non_claims"]
    assert packaged["interpretation"]["what_changed"][0].startswith("Only engine.g_int")
    assert not (tmp_path / "experiments" / "campaign-studies").exists()

    detail_payload = client.get("/api/campaign-studies/self-interaction-sweep")
    assert detail_payload.status_code == 200
    detail = detail_payload.json()
    template = detail["template"]
    assert template["config"]["campaign"]["dimensions"] == [
        {"path": "engine.g_int", "values": [0.0, 0.02, 0.05, 0.08, 0.12]}
    ]
    assert template["campaign"]["planned_run_count"] == 5

    campaign_payload = client.post(
        "/api/campaigns",
        json={
            "config": template["config"],
            "source_name": template["source_config_name"],
            "study_template_id": template["template_id"],
        },
    )
    assert campaign_payload.status_code == 200
    campaign = campaign_payload.json()
    assert campaign["campaign"]["label"] == "Self-interaction tangible utility sweep"
    assert campaign["campaign"]["planned_run_count"] == 5
    assert campaign["campaign"]["dimensions"][0]["path"] == "engine.g_int"
    assert len(campaign["runs"]) == 5
    assert campaign["comparison"]["decision"]["available"] is True
    assert campaign["guide"]["title"] == "Self-Interaction Sweep guided interpretation"
    assert any("Energy drift span" in item for item in campaign["guide"]["what_changed"])
    assert any("Max density" in item for item in campaign["guide"]["metric_meanings"])
    assert campaign["guide"]["what_this_does_not_claim"]
    assert campaign["artifact"]["summary"]["kind"] == "campaign"
    assert campaign["artifact"]["summary"]["run_count"] == 5
    assert campaign["study_template"]["summary"]["template_id"] == "self-interaction-sweep"
    assert campaign["study_template"]["summary"]["last_run"]["status"] == "completed"

    local_template = tmp_path / "experiments" / "campaign-studies" / "self-interaction-sweep.json"
    assert local_template.exists()
    local_payload = client.get("/api/campaign-studies/self-interaction-sweep")
    assert local_payload.status_code == 200
    assert local_payload.json()["summary"]["last_run"]["experiment_id"] == (
        campaign["artifact"]["summary"]["experiment_id"]
    )

    report_payload = client.get(campaign["artifact"]["urls"]["report"])
    assert report_payload.status_code == 200
    assert "QS-DMSS Experiment Report" in report_payload.text

    bundle_payload = client.get(campaign["artifact"]["urls"]["bundle"])
    assert bundle_payload.status_code == 200
    assert bundle_payload.headers["content-type"].startswith("application/zip")


def test_cockpit_api_exports_research_object_with_job_record(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    export_payload = client.post(
        "/api/research-objects/export",
        json={
            "research_object": {
                "fileName": "../portable-research-object",
                "markdown": "# Portable Research Object\n\nEvidence-ready export.\n",
                "runId": "campaign-20260101T000000Z-demo",
                "scenario": {"label": "Portable Campaign Study"},
                "campaignStudy": {"available": True},
            },
        },
    )

    assert export_payload.status_code == 200
    export = export_payload.json()
    export_id = export["export"]["id"]
    job = export["execution_job"]["summary"]
    assert export["export"]["file_name"] == "portable-research-object.md"
    assert export["export"]["download_url"].endswith(f"/{export_id}/download")
    assert job["state"] == "succeeded"
    assert job["experiment_id"] == export_id
    assert job["metadata"]["file_name"] == "portable-research-object.md"
    assert "research_object" in job["artifact_roles"]
    assert "Export Provenance" in export["research_object"]["markdown"]
    assert job["job_id"] in export["research_object"]["markdown"]

    job_payload = client.get(f"/api/jobs/{job['job_id']}")
    assert job_payload.status_code == 200
    assert job_payload.json()["result"]["experiment_id"] == export_id

    download_payload = client.get(export["export"]["download_url"])
    assert download_payload.status_code == 200
    assert download_payload.headers["content-type"].startswith("text/markdown")
    assert "Portable Research Object" in download_payload.text
    assert "Export Provenance" in download_payload.text

    blank_payload = client.post(
        "/api/research-objects/export",
        json={"research_object": {"fileName": "empty.md", "markdown": "   "}},
    )
    assert blank_payload.status_code == 400
    assert blank_payload.json()["detail"] == "Research object markdown is required"


def test_cockpit_api_exports_and_imports_workspace_metadata(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(repo_root=repo_root, output_root=tmp_path / "runs")
    client = TestClient(app)

    config_item = client.get("/api/configs").json()["items"][0]
    sweep_payload = client.post(
        "/api/sweeps",
        json={
            "config": config_item["config"],
            "parameter_path": "engine.g_int",
            "values": [0.02, 0.05],
            "source_name": "workspace-sweep.yaml",
            "experiment_name": "workspace interaction sweep",
        },
    )
    assert sweep_payload.status_code == 200
    sweep = sweep_payload.json()

    research_payload = client.post(
        "/api/research-objects/export",
        json={
            "research_object": {
                "fileName": "workspace-research-object.md",
                "markdown": "# Workspace Research Object\n\nEvidence context.\n",
                "runId": sweep["runs"][0]["run_id"],
                "scenario": {"label": "Workspace Interaction Sweep"},
                "campaignStudy": {"available": True},
            },
        },
    )
    assert research_payload.status_code == 200
    research_object = research_payload.json()

    workspace_payload = client.post(
        "/api/workspaces/export",
        json={
            "title": "Portable reviewer workspace",
            "description": "Handoff with run, experiment, template, and research object.",
            "collaborators": [
                {
                    "display_name": "Ada Reviewer",
                    "role": "reviewer",
                    "affiliation": "Remote lab",
                    "location_label": "EU",
                }
            ],
            "annotations": [
                {
                    "target_type": "experiment",
                    "target_id": sweep["experiment"]["id"],
                    "text": "Please inspect the recommendation rationale.",
                    "author": "Ada Reviewer",
                    "tags": ["handoff", "review"],
                }
            ],
            "run_ids": [sweep["runs"][0]["run_id"]],
            "experiment_ids": [sweep["experiment"]["id"]],
            "campaign_study_template_ids": ["self-interaction-sweep"],
            "research_object_ids": [research_object["export"]["id"]],
        },
    )
    assert workspace_payload.status_code == 200
    workspace_detail = workspace_payload.json()
    summary = workspace_detail["summary"]
    workspace = workspace_detail["workspace"]
    assert summary["title"] == "Portable reviewer workspace"
    assert summary["run_count"] == 1
    assert summary["experiment_count"] == 1
    assert summary["campaign_study_template_count"] == 1
    assert summary["research_object_count"] == 1
    assert summary["collaborator_count"] == 1
    assert summary["annotation_count"] == 1
    assert summary["job_count"] >= 1
    assert workspace["collaborators"][0]["display_name"] == "Ada Reviewer"
    assert workspace["annotations"][0]["target_id"] == sweep["experiment"]["id"]
    assert workspace["resources"]["runs"][0]["summary"]["run_id"] == sweep["runs"][0]["run_id"]
    assert (
        workspace["resources"]["campaign_study_templates"][0]["summary"]["template_id"]
        == "self-interaction-sweep"
    )
    assert (
        workspace["resources"]["research_objects"][0]["summary"]["id"]
        == research_object["export"]["id"]
    )

    list_payload = client.get("/api/workspaces")
    assert list_payload.status_code == 200
    assert list_payload.json()["items"][0]["workspace_id"] == summary["workspace_id"]

    download_payload = client.get(workspace_detail["urls"]["download"])
    assert download_payload.status_code == 200
    assert download_payload.headers["content-type"].startswith("application/json")
    assert download_payload.json()["workspace_id"] == summary["workspace_id"]

    import_payload = client.post(
        "/api/workspaces/import",
        json={"workspace": workspace},
    )
    assert import_payload.status_code == 200
    imported = import_payload.json()
    assert imported["summary"]["imported_from_workspace_id"] == summary["workspace_id"]
    assert imported["summary"]["campaign_study_template_count"] == 1
    assert imported["imported_campaign_studies"][0]["imported_from_template_id"] == (
        "self-interaction-sweep"
    )

    imported_template_path = (
        tmp_path
        / "experiments"
        / "campaign-studies"
        / f"{imported['imported_campaign_studies'][0]['template_id']}.json"
    )
    assert imported_template_path.exists()

    stale_payload = client.post(
        "/api/workspaces/export",
        json={
            "title": "Workspace with stale selection",
            "run_ids": ["missing-run-id"],
            "experiment_ids": ["missing-experiment-id"],
        },
    )
    assert stale_payload.status_code == 200
    stale_workspace = stale_payload.json()
    assert stale_workspace["summary"]["run_count"] == 0
    assert stale_workspace["summary"]["experiment_count"] == 0
    assert stale_workspace["summary"]["warning_count"] == 2
    assert {
        warning["resource_type"]
        for warning in stale_workspace["workspace"]["warnings"]
    } == {"run", "experiment"}

    invalid_payload = client.post(
        "/api/workspaces/export",
        json={
            "title": "Invalid workspace",
            "annotations": [
                {
                    "target_type": "remote-shell",
                    "target_id": "hpc-1",
                    "text": "This should not be accepted.",
                }
            ],
        },
    )
    assert invalid_payload.status_code == 400
    assert "Unsupported workspace annotation target_type" in invalid_payload.json()["detail"]


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
    assert experiment["summary"]["execution_job"]["state"] == "failed"
    assert experiment["summary"]["execution_job"]["experiment_id"] == (
        failure_detail["experiment_id"]
    )
    assert len(experiment["summary"]["execution_job"]["child_job_ids"]) == 1
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
