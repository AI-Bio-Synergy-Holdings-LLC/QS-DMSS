from __future__ import annotations

import hashlib
import json
import zipfile
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import qs_dmss.cockpit.robustness as robustness
from qs_dmss.cockpit.api import create_app
from qs_dmss.evidence.bundle import (
    create_bundle_zip_for_directory,
    write_manifest_for_directory,
)
from qs_dmss.robustness import RobustnessRequest, canonical_json, score_recorded_rows


def _write(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


@pytest.fixture
def service(tmp_path):
    root = tmp_path / "experiments" / "campaign-a"
    profile = {
        "objective": {
            "name": "Stability",
            "summary": "Test",
            "primary_metric": "energy_drift",
            "goal": "minimize_abs",
        },
        "constraints": {"require_verification": True},
        "ranking": {
            "primary_metric_weight": 2.0,
            "weights": {
                "energy_drift": 1.0,
                "norm_drift": 1.0,
                "max_density": 0.5,
                "elapsed_seconds": 0.25,
            },
        },
    }
    rows = [
        {
            "run_id": name,
            "name": name,
            "energy_drift": drift,
            "norm_drift": 0.001,
            "max_density": density,
            "elapsed_seconds": elapsed,
            "verification_success": True,
        }
        for name, drift, density, elapsed in [
            ("run-a", 0.01, 1.0, 2.0),
            ("run-b", 0.03, 2.0, 1.0),
        ]
    ]
    comparison = score_recorded_rows(rows, profile)
    comparison["schema_version"] = 1
    _write(root / "comparison.json", comparison)
    _write(
        root / "experiment.json",
        {
            "schema_version": 1,
            "experiment_id": "campaign-a",
            "kind": "campaign",
            "label": "Recorded campaign",
            "run_ids": [row["run_id"] for row in rows],
            "run_count": 2,
            "decision": comparison["decision"],
        },
    )
    for row in rows:
        _write(
            root / "runs" / row["run_id"] / "metrics.json",
            {**row, "energy_diagnostic_convention": "fft_cell_measure_v2"},
        )
        _write(
            root / "runs" / row["run_id"] / "run.json",
            {"run_id": row["run_id"], "elapsed_seconds": row["elapsed_seconds"]},
        )
    write_manifest_for_directory(root)
    create_bundle_zip_for_directory(root)
    return robustness.CockpitRobustnessService(root.parent)


def _request(service):
    source = service.source("campaign-a")
    return RobustnessRequest.model_validate(
        {
            "experiment_id": "campaign-a",
            "profile": source["comparison"]["decision"]["profile"],
            "preferred_run_id": "run-a",
            "source_fingerprint": source["source_fingerprint"],
            "weight_values": [0.0, 1.0, 4.0],
        }
    )


def test_snapshot_save_reopen_bundle_and_original_immutability(service):
    source = service.experiments_root / "campaign-a"
    originals = {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in source.rglob("*")
        if path.is_file()
    }
    payload = _request(service)
    preview = service.preview(payload)
    saved = service.save(payload)
    reopened = service.load(saved["analysis_id"])
    assert reopened == saved
    assert saved["current"] == preview["current"]
    assert saved["sensitivity"] == preview["sensitivity"]
    assert saved["profile"] == payload.profile.model_dump(exclude_none=True)
    assert (
        saved["source"]["sha256"]["comparison.json"]
        == hashlib.sha256(originals["comparison.json"]).hexdigest()
    )
    assert len(service.analyses()["items"]) == 1
    with zipfile.ZipFile(service.bundle(saved["analysis_id"])) as archive:
        names = archive.namelist()
        retained = archive.read(f"{saved['analysis_id']}/source/comparison.json")
        assert retained == originals["comparison.json"]
        assert f"{saved['analysis_id']}/analysis.json" in names
        assert f"{saved['analysis_id']}/source/evidence_bundle.zip" not in names
    assert originals == {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in source.rglob("*")
        if path.is_file()
    }
    # Reopen without the original campaign: retained evidence is sufficient to inspect.
    source.rename(source.with_name("removed-campaign"))
    assert service.load(saved["analysis_id"])["source"]["experiment_id"] == "campaign-a"


def test_changed_source_fingerprint_conflicts_instead_of_saving(service):
    payload = _request(service)
    root = service.experiments_root / "campaign-a"
    record = json.loads((root / "experiment.json").read_bytes())
    record["label"] = "Changed"
    _write(root / "experiment.json", record)
    write_manifest_for_directory(root)
    create_bundle_zip_for_directory(root)
    for operation in (service.preview, service.save):
        with pytest.raises(HTTPException) as error:
            operation(payload)
        assert error.value.status_code == 409
    assert not service._analysis_root().exists()


@pytest.mark.parametrize(
    "file", ["comparison.json", "runs/run-a/metrics.json", "runs/run-a/run.json"]
)
def test_tampered_used_metadata_is_rejected(service, file):
    (service.experiments_root / "campaign-a" / file).write_bytes(b"{}")
    with pytest.raises(ValueError, match="integrity"):
        service.source("campaign-a")


def test_mixed_and_legacy_energy_conventions(service):
    root = service.experiments_root / "campaign-a"
    path = root / "runs/run-a/metrics.json"
    metrics = json.loads(path.read_bytes())
    metrics["energy_diagnostic_convention"] = "graph_mass_stiffness_v1"
    _write(path, metrics)
    write_manifest_for_directory(root)
    with pytest.raises(ValueError, match="Mixed energy"):
        service.source("campaign-a")
    for path in root.glob("runs/*/metrics.json"):
        metrics = json.loads(path.read_bytes())
        metrics.pop("energy_diagnostic_convention")
        _write(path, metrics)
    write_manifest_for_directory(root)
    assert service.source("campaign-a")["legacy_convention"] is True


def test_inconsistent_metric_identity_and_failed_campaign_are_rejected(service):
    root = service.experiments_root / "campaign-a"
    path = root / "comparison.json"
    comparison = json.loads(path.read_bytes())
    comparison["rows"][0]["energy_drift"] = 0.8
    _write(path, comparison)
    write_manifest_for_directory(root)
    with pytest.raises(ValueError, match="disagree"):
        service.source("campaign-a")
    record = json.loads((root / "experiment.json").read_bytes())
    record["status"] = "failed"
    _write(root / "experiment.json", record)
    write_manifest_for_directory(root)
    assert service.sources()["items"] == []
    with pytest.raises(ValueError, match="completed campaign"):
        service.source("campaign-a")


def test_saved_analysis_integrity_is_checked(service):
    saved = service.save(_request(service))
    path = service._analysis_root() / saved["analysis_id"] / "analysis.json"
    path.write_bytes(b"{}")
    with pytest.raises(ValueError, match="integrity"):
        service.load(saved["analysis_id"])
    with pytest.raises(ValueError, match="integrity"):
        service.bundle(saved["analysis_id"])


def test_saved_bundle_and_retained_source_are_verified(service):
    saved = service.save(_request(service))
    root = service._analysis_root() / saved["analysis_id"]
    bundle = root / "evidence_bundle.zip"
    original = bundle.read_bytes()
    bundle.write_bytes(b"not a bundle")
    with pytest.raises(ValueError, match="bundle failed"):
        service.bundle(saved["analysis_id"])
    bundle.write_bytes(original)
    (root / "source/comparison.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="integrity"):
        service.load(saved["analysis_id"])


def test_failed_save_removes_only_its_pending_directory(service, monkeypatch):
    original = service.experiments_root / "campaign-a/experiment.json"
    before = original.read_bytes()

    def fail_manifest(_):
        assert service.analyses()["items"] == []  # Partial writes are never visible.
        raise OSError("simulated storage failure")

    monkeypatch.setattr(robustness, "write_manifest_for_directory", fail_manifest)
    with pytest.raises(OSError, match="simulated"):
        service.save(_request(service))
    assert not list(service._analysis_root().glob("*/analysis.json"))
    assert not list((service._analysis_root() / "_pending").iterdir())
    assert original.read_bytes() == before


def test_limits_and_path_escape_fail_closed(service, monkeypatch):
    for operation in (service.source, service.load):
        with pytest.raises(HTTPException) as error:
            operation("../campaign-a")
        assert error.value.status_code == 404
    monkeypatch.setattr(robustness, "MAX_SOURCE_BYTES", 20)
    with pytest.raises(ValueError, match="resource limit"):
        service.source("campaign-a")


def test_id_collision_retries_and_incomplete_save_is_removed(service, monkeypatch):
    class ID:
        hex = "1" * 32

    destination = service._analysis_root() / f"robustness-{ID.hex}"
    destination.mkdir(parents=True)
    monkeypatch.setattr(robustness.uuid, "uuid4", lambda: ID())
    with pytest.raises(HTTPException) as error:
        service.save(_request(service))
    assert error.value.status_code == 503
    assert destination.exists()


def test_real_campaign_http_workflow_and_hosted_boundary(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    client = TestClient(
        create_app(repo_root=repo, output_root=tmp_path / "runs", hosted_demo=False)
    )
    template = client.get("/api/campaign-studies/self-interaction-sweep").json()[
        "template"
    ]
    config = deepcopy(template["config"])
    config["campaign"]["max_runs"] = 2
    config["campaign"]["dimensions"] = [{"path": "engine.g_int", "values": [0.0, 0.1]}]
    launch = client.post("/api/campaigns", json={"config": config}).json()
    identifier = launch["artifact"]["summary"]["experiment_id"]
    assert (
        client.get("/api/robustness/sources").json()["items"][0]["experiment_id"]
        == identifier
    )
    source = client.get(f"/api/robustness/sources/{identifier}").json()
    payload = {
        "experiment_id": identifier,
        "source_fingerprint": source["source_fingerprint"],
        "profile": source["comparison"]["decision"]["profile"],
        "preferred_run_id": source["comparison"]["decision"]["recommended_run_id"],
        "weight_values": [0.0, 1.0, 4.0],
    }
    preview = client.post("/api/robustness/preview", json=payload)
    assert preview.status_code == 200, preview.text
    assert (
        preview.json()["current"]["decision"]["recommended_run_id"]
        == source["comparison"]["decision"]["recommended_run_id"]
    )
    assert preview.json()["current"]["rows"] == source["comparison"]["rows"]
    report = client.get(launch["artifact"]["urls"]["report"])
    assert report.headers["x-frame-options"] == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in report.headers["content-security-policy"]
    assert client.get("/").headers["x-frame-options"] == "DENY"
    workbook = client.get(launch["artifact"]["urls"]["workbook"])
    assert workbook.status_code == 200
    assert 'id="workbook-print"' in workbook.text
    assert 'onclick="window.print()"' not in workbook.text
    assert "addEventListener('click',()=>window.print())" in workbook.text
    saved = client.post("/api/robustness/analyses", json=payload).json()
    assert (
        client.get(f"/api/robustness/analyses/{saved['analysis_id']}").json() == saved
    )
    assert client.get(saved["urls"]["bundle"]).status_code == 200
    assert (
        client.get(saved["urls"]["bundle"]).headers["x-content-type-options"]
        == "nosniff"
    )
    assert (
        client.post(
            "/api/robustness/preview", json={**payload, "unexpected": True}
        ).status_code
        == 422
    )
    assert client.get("/api/robustness/sources/nonexistent").status_code == 404
    hosted = TestClient(
        create_app(
            repo_root=repo, output_root=tmp_path / "hosted/runs", hosted_demo=True
        )
    )
    assert hosted.get("/api/robustness/sources").json()["available"] is False
    assert hosted.post("/api/robustness/preview", json=payload).status_code == 403
    assert hosted.post("/api/robustness/analyses", json=payload).status_code == 403
    assert hosted.get("/api/robustness/analyses").status_code == 403


def test_http_errors_never_disclose_parser_text_or_paths(service):
    repo = Path(__file__).resolve().parents[1]
    client = TestClient(
        create_app(
            repo_root=repo,
            output_root=service.experiments_root.parent / "runs",
            hosted_demo=False,
        )
    )
    path = service.experiments_root / "campaign-a" / "manifest.sha256.json"
    path.write_bytes(b"<img src=x onerror=alert(1)>")
    response = client.get("/api/robustness/sources/campaign-a")
    assert response.status_code == 400
    assert "<img" not in response.text
    assert str(service.experiments_root) not in response.text


@pytest.mark.parametrize(
    "entry",
    [
        None,
        {"path": 1},
        {"path": "x", "sha256": "bad", "size_bytes": 1},
        {"path": "x", "sha256": "0" * 64, "size_bytes": True},
    ],
)
def test_invalid_manifest_entries_fail_with_authored_error(service, entry):
    path = service.experiments_root / "campaign-a/manifest.sha256.json"
    _write(path, {"algorithm": "sha256", "files": [entry]})
    with pytest.raises(ValueError, match="invalid file entry"):
        service.source("campaign-a")


def test_retained_source_total_limit_is_enforced_on_reopen(service, monkeypatch):
    saved = service.save(_request(service))
    monkeypatch.setattr(robustness, "MAX_SOURCE_BYTES", 20)
    with pytest.raises(ValueError, match="Retained source exceeds"):
        service.load(saved["analysis_id"])


@pytest.mark.parametrize("decision", ["invalid", [1], True, 7])
def test_sources_skip_non_object_decisions_without_hiding_healthy_sources(
    service, decision
):
    root = service.experiments_root / "campaign-a"
    record = json.loads((root / "experiment.json").read_bytes())
    _write(
        service.experiments_root / "campaign-bad/experiment.json",
        {**record, "experiment_id": "campaign-bad", "decision": decision},
    )
    assert [item["experiment_id"] for item in service.sources()["items"]] == [
        "campaign-a"
    ]


@pytest.mark.parametrize("decision", ["invalid", [1], True])
def test_non_object_comparison_decision_returns_authored_http_error(service, decision):
    root = service.experiments_root / "campaign-a"
    comparison = json.loads((root / "comparison.json").read_bytes())
    _write(root / "comparison.json", {**comparison, "decision": decision})
    write_manifest_for_directory(root)
    client = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=service.experiments_root.parent / "runs",
            hosted_demo=False,
        )
    )
    response = client.get("/api/robustness/sources/campaign-a")
    assert response.status_code == 400
    assert response.json()["detail"] == "Campaign has no shared scoring profile"


@pytest.mark.parametrize("failure", ["tampered", "unreadable"])
def test_saved_listing_skips_bad_artifacts_but_direct_access_stays_closed(
    service, monkeypatch, failure
):
    invalid = service.save(_request(service))
    healthy = service.save(_request(service))
    path = service._analysis_root() / invalid["analysis_id"] / "analysis.json"
    if failure == "tampered":
        path.write_bytes(b"{}")
    else:
        original_stat = Path.stat

        def stat(candidate, *args, **kwargs):
            if candidate == path:
                raise OSError("simulated unreadable artifact")
            return original_stat(candidate, *args, **kwargs)

        monkeypatch.setattr(Path, "stat", stat)
        original_read = robustness._read_bytes

        def read(candidate, limit=robustness.MAX_FILE_BYTES):
            if candidate == path:
                raise OSError("simulated unreadable artifact")
            return original_read(candidate, limit)

        monkeypatch.setattr(robustness, "_read_bytes", read)
    assert [item["analysis_id"] for item in service.analyses()["items"]] == [
        healthy["analysis_id"]
    ]
    assert service.load(healthy["analysis_id"]) == healthy
    with pytest.raises((ValueError, OSError)):
        service.load(invalid["analysis_id"])
    client = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=service.experiments_root.parent / "runs",
            hosted_demo=False,
        )
    )
    response = client.get("/api/robustness/analyses")
    assert response.status_code == 200
    assert [item["analysis_id"] for item in response.json()["items"]] == [
        healthy["analysis_id"]
    ]
    assert (
        client.get(f"/api/robustness/analyses/{invalid['analysis_id']}").status_code
        == 400
    )
