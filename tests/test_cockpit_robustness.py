from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

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


_MISSING = object()
_METRICS = ("energy_drift", "norm_drift", "max_density", "elapsed_seconds")


def _replace_captured_metric(service, metric, comparison_value, captured_value):
    root = service.experiments_root / "campaign-a"
    comparison = json.loads((root / "comparison.json").read_bytes())
    comparison["rows"][0][metric] = comparison_value
    comparison = score_recorded_rows(
        comparison["rows"], comparison["decision"]["profile"]
    )
    _write(root / "comparison.json", {**comparison, "schema_version": 1})
    record = json.loads((root / "experiment.json").read_bytes())
    _write(root / "experiment.json", {**record, "decision": comparison["decision"]})
    filename = "run.json" if metric == "elapsed_seconds" else "metrics.json"
    path = root / "runs" / "run-a" / filename
    captured = json.loads(path.read_bytes())
    if captured_value is _MISSING:
        captured.pop(metric)
    else:
        captured[metric] = captured_value
    _write(path, captured)
    # Valid hashes alone must not turn malformed metric types into numeric evidence.
    write_manifest_for_directory(root)
    create_bundle_zip_for_directory(root)


@pytest.mark.parametrize("metric", _METRICS)
@pytest.mark.parametrize(
    "captured_value",
    [
        pytest.param(True, id="true-equals-one"),
        pytest.param(False, id="false-equals-zero"),
        pytest.param(None, id="null"),
        pytest.param("1", id="numeric-string"),
        pytest.param([], id="array"),
        pytest.param({}, id="object"),
        pytest.param(_MISSING, id="missing"),
    ],
)
def test_malformed_captured_metrics_fail_closed_before_preview_or_save(
    service, metric, captured_value
):
    payload = _request(service)
    comparison_value = (
        float(captured_value) if isinstance(captured_value, bool) else 1.0
    )
    _replace_captured_metric(service, metric, comparison_value, captured_value)
    for operation, argument in (
        (service.source, "campaign-a"),
        (service.preview, payload),
        (service.save, payload),
    ):
        with pytest.raises(ValueError, match="disagree with captured run evidence"):
            operation(argument)
    client = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=service.experiments_root.parent / "runs",
            hosted_demo=False,
        )
    )
    responses = [client.get("/api/robustness/sources/campaign-a")]
    responses.extend(
        client.post(endpoint, json=payload.model_dump(mode="json"))
        for endpoint in ("/api/robustness/preview", "/api/robustness/analyses")
    )
    for response in responses:
        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Comparison metrics disagree with captured run evidence or exceed limits"
        )
        assert str(service.experiments_root) not in response.text
    assert not service._analysis_root().exists()


@pytest.mark.parametrize("metric", _METRICS)
@pytest.mark.parametrize(
    "comparison_value,captured_value", [(0, 0.0), (1, 1.0), (0.0, 0), (1.0, 1)]
)
def test_captured_integer_float_equality_remains_compatible(
    service, metric, comparison_value, captured_value
):
    _replace_captured_metric(service, metric, comparison_value, captured_value)
    source = service.source("campaign-a")
    payload = _request(service)
    preview = service.preview(payload)
    assert preview["current"]["rows"] == source["comparison"]["rows"]
    saved = service.save(payload)
    assert saved["current"] == preview["current"]
    assert service.load(saved["analysis_id"]) == saved


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


@pytest.mark.parametrize("convention", [None, 7, "", "   ", False, [], {}])
def test_explicit_malformed_energy_conventions_are_rejected(service, convention):
    root = service.experiments_root / "campaign-a"
    for path in root.glob("runs/*/metrics.json"):
        metrics = json.loads(path.read_bytes())
        _write(path, {**metrics, "energy_diagnostic_convention": convention})
    write_manifest_for_directory(root)
    with pytest.raises(ValueError, match="convention must be a non-empty string"):
        service.source("campaign-a")
    client = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=service.experiments_root.parent / "runs",
            hosted_demo=False,
        )
    )
    response = client.get("/api/robustness/sources/campaign-a")
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Energy diagnostic convention must be a non-empty string"
    )


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


@pytest.mark.parametrize("count", [1, 3, 201])
def test_saved_listing_reads_only_bounded_summary_metadata(service, monkeypatch, count):
    root = service._analysis_root()
    for index in range(count):
        identifier = f"summary-{index}"
        directory = root / identifier
        _write(
            directory / "analysis.json",
            {
                "analysis_id": identifier,
                "created_at": "2026-10-04T00:00:00+00:00",
                "profile_sha256": "0" * 64,
                "source": {"label": "Metadata-only fixture"},
            },
        )
        write_manifest_for_directory(directory)
        os.utime(directory / "analysis.json", (index + 1, index + 1))
    reads = []
    original_read = robustness._read_bytes

    def read(path, limit=robustness.MAX_FILE_BYTES):
        assert path.name in {"manifest.sha256.json", "analysis.json"}
        assert "source" not in path.parts
        reads.append((path, limit))
        return original_read(path, limit)

    monkeypatch.setattr(robustness, "_read_bytes", read)
    items = service.analyses()["items"]
    assert [item["analysis_id"] for item in items] == [
        f"summary-{index}" for index in range(count - 1, max(-1, count - 201), -1)
    ]
    assert all(item["integrity_scope"] == "analysis_json_only" for item in items)
    assert len(reads) == 2 * min(count, 200)
    assert all(limit == robustness.MAX_FILE_BYTES for _, limit in reads)


@pytest.mark.parametrize("failure", ["source", "bundle", "missing_bundle"])
def test_summary_listing_defers_full_checks_but_http_open_export_fail_closed(
    service, failure
):
    saved = service.save(_request(service))
    root = service._analysis_root() / saved["analysis_id"]
    if failure == "source":
        (root / "source/comparison.json").write_bytes(b"{}")
    elif failure == "bundle":
        (root / "evidence_bundle.zip").write_bytes(b"invalid bundle")
    else:
        (root / "evidence_bundle.zip").unlink()
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
        saved["analysis_id"]
    ]
    assert response.json()["items"][0]["integrity_scope"] == "analysis_json_only"
    for suffix in ("", "/bundle"):
        response = client.get(
            f"/api/robustness/analyses/{saved['analysis_id']}{suffix}"
        )
        assert response.status_code == 400
        assert str(root) not in response.text


@pytest.mark.parametrize(
    "failure",
    [
        "identity",
        "missing_field",
        "manifest",
        "source_type",
        "created_type",
        "profile_hash",
    ],
)
def test_saved_listing_skips_invalid_summary_without_hiding_valid_metadata(
    service, failure
):
    invalid = service.save(_request(service))
    healthy = service.save(_request(service))
    root = service._analysis_root() / invalid["analysis_id"]
    if failure == "manifest":
        (root / "manifest.sha256.json").write_bytes(b"invalid JSON")
    else:
        record = json.loads((root / "analysis.json").read_bytes())
        if failure == "identity":
            record["analysis_id"] = "wrong-identity"
        elif failure == "missing_field":
            record.pop("source")
        elif failure == "source_type":
            record["source"] = None
        elif failure == "created_type":
            record["created_at"] = []
        else:
            record["profile_sha256"] = "not-a-sha256"
        _write(root / "analysis.json", record)
        write_manifest_for_directory(root)
    assert [item["analysis_id"] for item in service.analyses()["items"]] == [
        healthy["analysis_id"]
    ]


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


@pytest.mark.parametrize("storage", ["no_experiments", "no_analyses", "empty_analyses"])
def test_empty_saved_listing_is_successful_without_creating_storage(tmp_path, storage):
    experiments = tmp_path / "experiments"
    root = experiments / "_robustness"
    if storage == "no_analyses":
        experiments.mkdir()
    elif storage == "empty_analyses":
        root.mkdir(parents=True)
    before = (experiments.exists(), root.exists())
    service = robustness.CockpitRobustnessService(experiments)
    assert service.analyses() == {"items": []}
    assert (experiments.exists(), root.exists()) == before
    client = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=tmp_path / "runs",
            hosted_demo=False,
        )
    )
    # Cockpit startup may create general workspace folders; listing must not
    # create the separate robustness evidence store or mutate workspace state.
    before = (experiments.exists(), root.exists())
    assert client.get("/api/robustness/sources").json() == {
        "available": True,
        "items": [],
    }
    response = client.get("/api/robustness/analyses")
    assert response.status_code == 200
    assert response.json() == {"items": []}
    assert client.get("/api/robustness/analyses/missing").status_code == 404
    assert (experiments.exists(), root.exists()) == before
    hosted = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=tmp_path / "runs",
            hosted_demo=True,
        )
    )
    assert hosted.get("/api/robustness/analyses").status_code == 403
    assert (experiments.exists(), root.exists()) == before


@pytest.mark.parametrize("error_type", [PermissionError, NotADirectoryError])
def test_saved_listing_does_not_mask_root_storage_errors(
    tmp_path, monkeypatch, error_type
):
    experiments = tmp_path / "experiments"
    root = experiments / "_robustness"
    original_scandir = os.scandir

    def scandir(candidate):
        if candidate == root:
            raise error_type("simulated storage error with private path")
        return original_scandir(candidate)

    monkeypatch.setattr(os, "scandir", scandir)
    service = robustness.CockpitRobustnessService(experiments)
    with pytest.raises(error_type):
        service.analyses()
    client = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=tmp_path / "runs",
            hosted_demo=False,
        )
    )
    response = client.get("/api/robustness/analyses")
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Recorded robustness evidence is invalid, incompatible, or exceeds resource limits"
    )
    assert "private path" not in response.text


def _client(service, *, raise_server_exceptions=True):
    return TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=service.experiments_root.parent / "runs",
            hosted_demo=False,
        ),
        raise_server_exceptions=raise_server_exceptions,
    )


@pytest.mark.parametrize("collection", ["sources", "analyses"])
@pytest.mark.parametrize("real_symlink", [False, True], ids=["virtual", "real-symlink"])
def test_sibling_artifact_aliases_are_excluded_and_direct_access_is_not_found(
    service, monkeypatch, collection, real_symlink
):
    request = _request(service)
    if collection == "sources":
        identifier = "campaign-a"
        root = service.experiments_root
        endpoints = [f"/api/robustness/sources/{identifier}"]
        alias_endpoints = ["/api/robustness/sources/campaign-z-alias"]
        alias_id = "campaign-z-alias"
    else:
        identifier = service.save(request)["analysis_id"]
        root = service._analysis_root()
        endpoints = [
            f"/api/robustness/analyses/{identifier}{suffix}"
            for suffix in ("", "/bundle")
        ]
        alias_id = "robustness-z-alias"
        alias_endpoints = [
            f"/api/robustness/analyses/{alias_id}{suffix}" for suffix in ("", "/bundle")
        ]
    artifact = root / identifier
    alias = root / alias_id
    before = {
        path.relative_to(artifact): path.read_bytes()
        for path in artifact.rglob("*")
        if path.is_file()
    }
    if real_symlink:
        try:
            alias.symlink_to(artifact, target_is_directory=True)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                pytest.skip(
                    "Windows symlink creation requires an unavailable privilege"
                )
            raise
    else:
        resolve, scan = robustness.contained_path, robustness._discovery_entries

        def resolved(base, *parts):
            return (
                artifact
                if base == root and parts == (alias_id,)
                else resolve(base, *parts)
            )

        monkeypatch.setattr(robustness, "contained_path", resolved)
        monkeypatch.setattr(
            robustness,
            "_discovery_entries",
            lambda base: [alias, artifact] if base == root else scan(base),
        )
    client = _client(service)
    listing = client.get(f"/api/robustness/{collection}")
    assert listing.status_code == 200
    key = "experiment_id" if collection == "sources" else "analysis_id"
    assert [item[key] for item in listing.json()["items"]] == [identifier]
    for endpoint in endpoints:
        assert client.get(endpoint).status_code == 200
    rejected = [client.get(endpoint) for endpoint in alias_endpoints]
    if collection == "sources":
        rejected.extend(
            client.post(
                endpoint,
                json={**request.model_dump(mode="json"), "experiment_id": alias_id},
            )
            for endpoint in ("/api/robustness/preview", "/api/robustness/analyses")
        )
        assert not service._analysis_root().exists()
    for response in rejected:
        assert response.status_code == 404
        assert response.json() == {"detail": "Recorded artifact not found"}
        assert str(root) not in response.text
    assert before == {
        path.relative_to(artifact): path.read_bytes()
        for path in artifact.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize("collection", ["sources", "analyses"])
def test_aliases_cannot_consume_the_healthy_candidate_window(
    service, monkeypatch, collection
):
    if collection == "sources":
        identifier, root = "campaign-a", service.experiments_root
    else:
        identifier = service.save(_request(service))["analysis_id"]
        root = service._analysis_root()
    artifact = root / identifier
    aliases = {f"alias-{index:03d}": artifact for index in range(200)}
    resolve, scan, read = (
        robustness.contained_path,
        robustness._discovery_entries,
        robustness._read_bytes,
    )
    reads = []

    def resolved(base, *parts):
        if base == root and len(parts) == 1 and parts[0] in aliases:
            return aliases[parts[0]]
        return resolve(base, *parts)

    def recorded_read(path, limit=robustness.MAX_FILE_BYTES):
        reads.append(path.name)
        return read(path, limit)

    monkeypatch.setattr(robustness, "contained_path", resolved)
    monkeypatch.setattr(
        robustness,
        "_discovery_entries",
        lambda base: (
            [*(root / name for name in aliases), artifact]
            if base == root
            else scan(base)
        ),
    )
    monkeypatch.setattr(robustness, "_read_bytes", recorded_read)
    response = _client(service).get(f"/api/robustness/{collection}")
    assert response.status_code == 200
    key = "experiment_id" if collection == "sources" else "analysis_id"
    assert [item[key] for item in response.json()["items"]] == [identifier]
    assert reads == (
        ["experiment.json"]
        if collection == "sources"
        else ["manifest.sha256.json", "analysis.json"]
    )


_DEEP_JSON = b'{"nested":' + b"[" * 8192 + b"0" + b"]" * 8192 + b"}"


def _inject_recursive_parser_error(monkeypatch):
    """Make the parser exception portable without changing healthy JSON reads."""
    parse = robustness._json

    def recursive(payload):
        if payload == _DEEP_JSON:
            # CPython build/version-specific C-stack limits vary. This is an
            # exception-boundary contract, not a claimed universal depth limit.
            raise RecursionError("Injected parser recursion limit")
        return parse(payload)

    monkeypatch.setattr(robustness, "_json", recursive)


@pytest.mark.parametrize(
    "relative",
    [
        "manifest.sha256.json",
        "experiment.json",
        "comparison.json",
        "runs/run-a/metrics.json",
        "runs/run-a/run.json",
    ],
)
@pytest.mark.parametrize("operation", ["source", "preview", "save"])
def test_recursive_source_json_is_sanitized_before_persistence(
    service, monkeypatch, relative, operation
):
    _inject_recursive_parser_error(monkeypatch)
    request = _request(service)
    root = service.experiments_root / "campaign-a"
    path = root / relative
    path.write_bytes(_DEEP_JSON)
    if relative != "manifest.sha256.json":
        write_manifest_for_directory(root)
        create_bundle_zip_for_directory(root)
    before = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    client = _client(service, raise_server_exceptions=False)
    response = (
        client.get("/api/robustness/sources/campaign-a")
        if operation == "source"
        else client.post(
            "/api/robustness/preview"
            if operation == "preview"
            else "/api/robustness/analyses",
            json=request.model_dump(mode="json"),
        )
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Recorded robustness evidence is invalid, incompatible, or exceeds resource limits"
    }
    assert str(root) not in response.text and "RecursionError" not in response.text
    assert not service._analysis_root().exists()
    assert before == {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize("relative", ["manifest.sha256.json", "analysis.json"])
@pytest.mark.parametrize("suffix", ["", "/bundle"], ids=["open", "export"])
def test_recursive_saved_json_is_sanitized_without_rewriting_evidence(
    service, monkeypatch, relative, suffix
):
    _inject_recursive_parser_error(monkeypatch)
    saved = service.save(_request(service))
    root = service._analysis_root() / saved["analysis_id"]
    (root / relative).write_bytes(_DEEP_JSON)
    if relative != "manifest.sha256.json":
        write_manifest_for_directory(root)
    before = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    response = _client(service, raise_server_exceptions=False).get(
        f"/api/robustness/analyses/{saved['analysis_id']}{suffix}"
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Recorded robustness evidence is invalid, incompatible, or exceeds resource limits"
    }
    assert str(root) not in response.text and "RecursionError" not in response.text
    assert before == {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    "relative",
    [
        "manifest.sha256.json",
        "bundle.sha256",
        "evidence_bundle.zip",
        "source/comparison.json",
    ],
)
@pytest.mark.parametrize(
    "real_symlink", [False, True], ids=["resolved-escape", "real-symlink"]
)
def test_retained_children_cannot_read_symlink_targets_outside_artifact(
    service, monkeypatch, relative, real_symlink
):
    saved = service.save(_request(service))
    root = service._analysis_root() / saved["analysis_id"]
    child = root / relative
    external = service.experiments_root.parent / "outside-artifact" / child.name
    external.parent.mkdir(exist_ok=True)
    original = child.read_bytes()
    external.write_bytes(original)
    if real_symlink:
        child.unlink()
        try:
            child.symlink_to(external)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                pytest.skip(
                    "Windows symlink creation requires an unavailable privilege"
                )
            raise
    else:
        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            return (
                external if path == child else original_resolve(path, *args, **kwargs)
            )

        monkeypatch.setattr(Path, "resolve", resolve)
    reads = []
    original_read = robustness._read_bytes

    def read(path, limit=robustness.MAX_FILE_BYTES):
        reads.append(path)
        return original_read(path, limit)

    monkeypatch.setattr(robustness, "_read_bytes", read)
    for operation in (service.load, service.bundle, service.bundle_snapshot):
        with pytest.raises(ValueError, match="escapes expected root"):
            operation(saved["analysis_id"])
    for suffix in ("", "/bundle"):
        response = _client(service).get(
            f"/api/robustness/analyses/{saved['analysis_id']}{suffix}"
        )
        assert response.status_code == 400
        assert str(external) not in response.text
    assert all(path.resolve() != external.resolve() for path in reads)
    assert external.read_bytes() == original


def test_bundle_path_resolves_contained_alias_and_http_serves_verified_snapshot(
    service, monkeypatch
):
    saved = service.save(_request(service))
    root = service._analysis_root() / saved["analysis_id"]
    path = root / "evidence_bundle.zip"
    original = path.read_bytes()
    assert service.bundle(saved["analysis_id"]) == path.resolve()
    snapshot = robustness.CockpitRobustnessService.bundle_snapshot

    def swap_after_verification(active, identifier):
        payload = snapshot(active, identifier)
        path.write_bytes(b"changed after validation; never serve this")
        return payload

    monkeypatch.setattr(
        robustness.CockpitRobustnessService, "bundle_snapshot", swap_after_verification
    )
    response = _client(service).get(saved["urls"]["bundle"])
    assert response.status_code == 200
    assert response.content == original
    assert hashlib.sha256(response.content).hexdigest() == saved["bundle_sha256"]
    assert response.headers["content-type"] == "application/zip"
    assert int(response.headers["content-length"]) == len(original)
    assert response.headers["content-disposition"] == (
        f'attachment; filename="{saved["analysis_id"]}.zip"'
    )
    assert response.headers["x-content-type-options"] == "nosniff"
    assert path.read_bytes() != original  # A path-based reread would have served this.


def test_campaign_discovery_isolates_unreadable_literal_child(service, monkeypatch):
    bad = service.experiments_root / "campaign-z" / "experiment.json"
    _write(
        bad,
        json.loads(
            (service.experiments_root / "campaign-a/experiment.json").read_bytes()
        ),
    )
    original_stat = Path.stat

    def stat(candidate, *args, **kwargs):
        if candidate == bad:
            raise PermissionError("simulated unreadable campaign")
        return original_stat(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", stat)
    assert [item["experiment_id"] for item in service.sources()["items"]] == [
        "campaign-a"
    ]
    response = _client(service).get("/api/robustness/sources")
    assert response.status_code == 200
    assert [item["experiment_id"] for item in response.json()["items"]] == [
        "campaign-a"
    ]


@pytest.mark.parametrize("collection", ["sources", "analyses"])
@pytest.mark.parametrize("count", [4096, 4097, 5000])
def test_discovery_streams_at_most_ceiling_plus_one_without_reading_or_deleting(
    service, monkeypatch, collection, count
):
    saved = service.save(_request(service))
    client = _client(service)  # General cockpit startup is outside the discovery probe.
    root = (
        service.experiments_root
        if collection == "sources"
        else service._analysis_root()
    )
    consumed = []

    class Entry:
        def __init__(self, index):
            self.name = f"absent-{index}"

    class Scan:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def __iter__(self):
            for index in range(count):
                consumed.append(index)
                yield Entry(index)

    original_scan = os.scandir
    monkeypatch.setattr(
        os,
        "scandir",
        lambda candidate: Scan() if candidate == root else original_scan(candidate),
    )
    read = robustness._read_bytes
    reads = []

    def counted_read(path, limit=robustness.MAX_FILE_BYTES):
        reads.append(path)
        return read(path, limit)

    monkeypatch.setattr(robustness, "_read_bytes", counted_read)
    response = client.get(f"/api/robustness/{collection}")
    assert len(consumed) == min(count, 4097)
    assert reads == []
    if count == 4096:
        assert response.status_code == 200
        assert response.json()["items"] == []
    else:
        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Robustness discovery exceeds the 4096-entry scan limit; "
            "open a known artifact directly or use a smaller evidence root"
        )
    assert service.load(saved["analysis_id"]) == saved
    assert service.source("campaign-a")["experiment_id"] == "campaign-a"
    assert (
        root / ("campaign-a" if collection == "sources" else saved["analysis_id"])
    ).exists()


def test_campaign_discovery_preserves_descending_order_and_200_candidate_cap(service):
    record = json.loads(
        (service.experiments_root / "campaign-a/experiment.json").read_bytes()
    )
    for index in range(201):
        identifier = f"campaign-{index:03d}"
        _write(
            service.experiments_root / identifier / "experiment.json",
            {**record, "experiment_id": identifier},
        )
    assert [item["experiment_id"] for item in service.sources()["items"]] == [
        "campaign-a",
        *[f"campaign-{index:03d}" for index in range(200, 1, -1)],
    ]


def _intercept_source_bundle(
    service, patches, *, reported_size, size, short_read=None, content=None
):
    path = (service.experiments_root / "campaign-a/evidence_bundle.zip").resolve()
    original_open, original_stat = Path.open, Path.stat
    streams = []

    class Stream:
        consumed = 0
        closed = False

        def __init__(self):
            self.requests = []

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.closed = True

        def read(self, requested):
            assert requested > 0
            self.requests.append((self.consumed, requested))
            # The never-ending-source probe fails safely if the production guard
            # is absent; it must not itself perform unbounded test I/O.
            if size is None and self.consumed > robustness.MAX_BUNDLE_BYTES + 1:
                raise AssertionError("Growing-stream probe exceeded its test budget")
            count = min(requested, short_read) if short_read else requested
            if size is not None:
                count = min(count, size - self.consumed)
            if content is None:
                chunk = b"x" * count
            else:
                chunk = content[self.consumed : self.consumed + count]
            self.consumed += len(chunk)
            return chunk

    def opened(candidate, *args, **kwargs):
        if candidate == path:
            assert args == ("rb",) and not kwargs
            stream = Stream()
            streams.append(stream)
            return stream
        return original_open(candidate, *args, **kwargs)

    def stat(candidate, *args, **kwargs):
        return (
            SimpleNamespace(st_size=reported_size)
            if candidate == path
            else original_stat(candidate, *args, **kwargs)
        )

    patches.setattr(Path, "open", opened)
    patches.setattr(Path, "stat", stat)
    return streams


def _assert_stream_bound(streams, limit):
    assert streams and all(stream.closed for stream in streams)
    for stream in streams:
        assert stream.consumed <= limit + 1
        assert all(
            requested <= min(1024 * 1024, limit - consumed + 1)
            for consumed, requested in stream.requests
        )


@pytest.mark.parametrize("limit", [8, 1024 * 1024 + 8, 64 * 1024 * 1024])
@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_source_bundle_stream_enforces_exact_boundary_after_underreported_stat(
    service, monkeypatch, limit, offset
):
    original = (
        service.experiments_root / "campaign-a/evidence_bundle.zip"
    ).read_bytes()
    size = limit + offset
    with monkeypatch.context() as patches:
        patches.setattr(robustness, "MAX_BUNDLE_BYTES", limit)
        streams = _intercept_source_bundle(service, patches, reported_size=4, size=size)
        if offset > 0:
            with pytest.raises(
                ValueError,
                match="^Source bundle exceeds the robustness resource limit$",
            ):
                service.source("campaign-a")
        else:
            result = service.source("campaign-a")
            digest = hashlib.sha256()
            for start in range(0, size, 1024 * 1024):
                digest.update(b"x" * min(1024 * 1024, size - start))
            assert result["sha256"]["evidence_bundle.zip"] == digest.hexdigest()
            assert (
                service.source("campaign-a")["source_fingerprint"]
                == result["source_fingerprint"]
            )
            assert all(stream.consumed == size for stream in streams)
        _assert_stream_bound(streams, limit)
    assert (
        service.experiments_root / "campaign-a/evidence_bundle.zip"
    ).read_bytes() == original


def test_source_bundle_stream_stops_a_never_ending_short_read_source(
    service, monkeypatch
):
    with monkeypatch.context() as patches:
        patches.setattr(robustness, "MAX_BUNDLE_BYTES", 8)
        streams = _intercept_source_bundle(
            service, patches, reported_size=4, size=None, short_read=3
        )
        with pytest.raises(
            ValueError, match="^Source bundle exceeds the robustness resource limit$"
        ):
            service.source("campaign-a")
        assert streams[0].consumed == 9
        assert streams[0].requests == [(0, 9), (3, 6), (6, 3)]
        _assert_stream_bound(streams, 8)


def test_source_bundle_initial_size_rejection_does_not_open_stream(
    service, monkeypatch
):
    with monkeypatch.context() as patches:
        patches.setattr(robustness, "MAX_BUNDLE_BYTES", 8)
        streams = _intercept_source_bundle(service, patches, reported_size=9, size=9)
        with pytest.raises(
            ValueError, match="^Source bundle exceeds the robustness resource limit$"
        ):
            service.source("campaign-a")
        assert streams == []


def test_source_bundle_short_reads_preserve_existing_hash_pin_preview_and_save(
    service, monkeypatch
):
    original_source = service.source("campaign-a")
    request = _request(service)
    bundle = service.experiments_root / "campaign-a/evidence_bundle.zip"
    original = bundle.read_bytes()
    with monkeypatch.context() as patches:
        streams = _intercept_source_bundle(
            service,
            patches,
            reported_size=len(original),
            size=len(original),
            short_read=13,
            content=original,
        )
        assert service.source("campaign-a") == original_source
        preview = service.preview(request)
        assert preview["source"]["source_fingerprint"] == request.source_fingerprint
        saved = service.save(request)
        assert saved["source"] == preview["source"]
        assert service.load(saved["analysis_id"]) == saved
        assert all(stream.consumed == len(original) for stream in streams)
        _assert_stream_bound(streams, robustness.MAX_BUNDLE_BYTES)
    assert bundle.read_bytes() == original


def _listing_json(value):
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("label", {}),
        ("label", []),
        ("label", 1),
        ("label", False),
        ("label", "x" * 513),
        ("label", "\udfff"),
        ("run_count", {}),
        ("run_count", []),
        ("run_count", "2"),
        ("run_count", True),
        ("run_count", 2.0),
        ("run_count", -1),
        ("run_count", 65),
        ("run_count", None),
        ("run_count", _MISSING),
        ("created_at", {}),
        ("created_at", []),
        ("created_at", True),
        ("created_at", 1),
        ("created_at", "x" * 65),
        ("created_at", "\udfff"),
    ],
)
def test_source_listing_isolates_invalid_scalar_summaries(service, field, value):
    original = service.experiments_root / "campaign-a/experiment.json"
    before = original.read_bytes()
    record = json.loads(before)
    record["experiment_id"] = "campaign-z"
    if value is _MISSING:
        record.pop(field, None)
    else:
        record[field] = value
    invalid = service.experiments_root / "campaign-z/experiment.json"
    _write(invalid, record)
    invalid_before = invalid.read_bytes()
    response = _client(service).get("/api/robustness/sources")
    assert response.status_code == 200
    assert [item["experiment_id"] for item in response.json()["items"]] == [
        "campaign-a"
    ]
    assert original.read_bytes() == before
    assert invalid.read_bytes() == invalid_before


@pytest.mark.parametrize("label", [None, "", _MISSING])
def test_source_listing_preserves_missing_label_and_timestamp_compatibility(
    service, label
):
    path = service.experiments_root / "campaign-a/experiment.json"
    record = json.loads(path.read_bytes())
    if label is _MISSING:
        record.pop("label")
    else:
        record["label"] = label
    record.pop("created_at", None)
    _write(path, record)
    assert service.sources()["items"] == [
        {
            "experiment_id": "campaign-a",
            "label": "campaign-a",
            "run_count": 2,
            "created_at": None,
        }
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (("created_at",), {}),
        (("created_at",), True),
        (("created_at",), "x" * 65),
        (("created_at",), "\udfff"),
        (("source", "label"), {}),
        (("source", "label"), []),
        (("source", "label"), 1),
        (("source", "label"), None),
        (("source", "label"), ""),
        (("source", "label"), "x" * 513),
        (("source", "label"), "\udfff"),
        (("source", "label"), _MISSING),
        (("source", "experiment_id"), {}),
        (("source", "experiment_id"), "../outside"),
        (("source", "experiment_id"), "x" * 201),
        (("source", "source_fingerprint"), {}),
        (("source", "source_fingerprint"), "x" * 64),
        (("source", "legacy_convention"), "false"),
        (("source", "legacy_convention"), 0),
    ],
)
def test_analysis_listing_isolates_invalid_compact_summaries(service, field, value):
    healthy = service.save(_request(service))
    result = deepcopy(healthy)
    result["analysis_id"] = "summary-invalid"
    parent = result if len(field) == 1 else result[field[0]]
    if value is _MISSING:
        parent.pop(field[-1], None)
    else:
        parent[field[-1]] = value
    directory = service._analysis_root() / "summary-invalid"
    _write(directory / "analysis.json", result)
    write_manifest_for_directory(directory)
    before = (directory / "analysis.json").read_bytes()
    response = _client(service).get("/api/robustness/analyses")
    assert response.status_code == 200
    assert [item["analysis_id"] for item in response.json()["items"]] == [
        healthy["analysis_id"]
    ]
    assert (directory / "analysis.json").read_bytes() == before
    assert service.load(healthy["analysis_id"]) == healthy


def test_analysis_listing_projects_small_source_but_direct_access_retains_provenance(
    service,
):
    saved = service.save(_request(service))
    directory = service._analysis_root() / saved["analysis_id"]
    result = json.loads((directory / "analysis.json").read_bytes())
    result["source"]["extra"] = {"large_unknown_payload": "x" * (1024 * 1024)}
    _write(directory / "analysis.json", result)
    write_manifest_for_directory(directory)
    bundle = create_bundle_zip_for_directory(directory)
    (directory / "bundle.sha256").write_text(
        hashlib.sha256(bundle.read_bytes()).hexdigest(), encoding="ascii"
    )
    before = (directory / "analysis.json").read_bytes()
    listing = service.analyses()
    assert listing["items"][0] == {
        "analysis_id": saved["analysis_id"],
        "created_at": saved["created_at"],
        "profile_sha256": saved["profile_sha256"],
        "source": {
            key: saved["source"][key]
            for key in (
                "label",
                "experiment_id",
                "source_fingerprint",
                "legacy_convention",
            )
        },
        "integrity_scope": "analysis_json_only",
    }
    assert len(_listing_json(listing)) < 1024
    assert (
        service.load(saved["analysis_id"])["source"]["extra"]
        == result["source"]["extra"]
    )
    assert service.bundle_snapshot(saved["analysis_id"]) == bundle.read_bytes()
    assert (directory / "analysis.json").read_bytes() == before


@pytest.mark.parametrize("collection", ["sources", "analyses"])
@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_listing_aggregate_ceiling_counts_complete_json_and_fails_explicitly(
    service, monkeypatch, collection, offset
):
    if collection == "sources":
        original = service.experiments_root / "campaign-a/experiment.json"
        record = json.loads(original.read_bytes())
        record.update(label='Literal <script> & "quote" \\ \n 🧪', created_at=None)
        _write(original, record)
        _write(
            service.experiments_root / "campaign-b/experiment.json",
            {**record, "experiment_id": "campaign-b"},
        )
    else:
        service.save(_request(service))
        service.save(_request(service))
    expected = getattr(service, collection)()
    assert len(expected["items"]) == 2
    response_size = len(_listing_json(expected))
    monkeypatch.setattr(
        robustness, "MAX_LISTING_RESPONSE_BYTES", response_size + offset, raising=False
    )
    client = _client(service)
    response = client.get(f"/api/robustness/{collection}")
    if offset < 0:
        assert response.status_code == 400
        assert response.json() == {
            "detail": "Robustness listing exceeds the response resource limit; "
            "open a known artifact directly or use a smaller evidence root"
        }
        assert str(service.experiments_root) not in response.text
        with pytest.raises(ValueError, match="listing exceeds the response"):
            getattr(service, collection)()
    else:
        assert response.status_code == 200
        assert response.json() == expected
        assert len(response.content) == response_size
        assert int(response.headers["content-length"]) == response_size


@pytest.mark.parametrize("collection", ["sources", "analyses"])
def test_listing_budget_counts_empty_envelope_and_stops_before_more_reads(
    service, monkeypatch, collection
):
    root = (
        service.experiments_root
        if collection == "sources"
        else service._analysis_root()
    )
    empty = (
        {"available": True, "items": []} if collection == "sources" else {"items": []}
    )
    monkeypatch.setattr(robustness, "_discovery_entries", lambda _: [])
    size = len(_listing_json(empty))
    monkeypatch.setattr(robustness, "MAX_LISTING_RESPONSE_BYTES", size, raising=False)
    assert getattr(service, collection)() == empty
    monkeypatch.setattr(robustness, "MAX_LISTING_RESPONSE_BYTES", size - 1)
    with pytest.raises(ValueError, match="listing exceeds the response"):
        getattr(service, collection)()
    assert not (root / "_pending").exists()


@pytest.mark.parametrize("collection", ["sources", "analyses"])
def test_listing_response_budget_stops_on_overflow_before_next_record_read(
    service, monkeypatch, collection
):
    if collection == "sources":
        record = json.loads(
            (service.experiments_root / "campaign-a/experiment.json").read_bytes()
        )
        for identifier in ("campaign-b", "campaign-c"):
            _write(
                service.experiments_root / identifier / "experiment.json",
                {**record, "experiment_id": identifier},
            )
    else:
        for _ in range(3):
            service.save(_request(service))
    full = getattr(service, collection)()
    expected = {**full, "items": full["items"][:1]}
    monkeypatch.setattr(
        robustness,
        "MAX_LISTING_RESPONSE_BYTES",
        len(_listing_json(expected)),
        raising=False,
    )
    reads = []
    original = robustness._read_bytes

    def read(path, limit=robustness.MAX_FILE_BYTES):
        reads.append(path)
        return original(path, limit)

    monkeypatch.setattr(robustness, "_read_bytes", read)
    with pytest.raises(ValueError, match="listing exceeds the response"):
        getattr(service, collection)()
    assert len(reads) == (2 if collection == "sources" else 4)


@pytest.mark.parametrize("collection", ["sources", "analyses"])
def test_200_max_length_listing_summaries_stay_below_actual_response_ceiling(
    service, collection
):
    label = "\x00" * 512  # Six JSON bytes per character, not a character-count budget.
    timestamp = "\x00" * 64
    if collection == "sources":
        record = json.loads(
            (service.experiments_root / "campaign-a/experiment.json").read_bytes()
        )
        (service.experiments_root / "campaign-a/experiment.json").unlink()
        for index in range(200):
            identifier = f"campaign-{index:03d}-" + "x" * 187
            assert len(identifier) == 200
            _write(
                service.experiments_root / identifier / "experiment.json",
                {
                    **record,
                    "experiment_id": identifier,
                    "label": label,
                    "created_at": timestamp,
                    "run_count": 64,
                },
            )
    else:
        for index in range(200):
            identifier = f"summary-{index:03d}-" + "x" * 188
            assert len(identifier) == 200
            directory = service._analysis_root() / identifier
            _write(
                directory / "analysis.json",
                {
                    "analysis_id": identifier,
                    "created_at": timestamp,
                    "profile_sha256": "0" * 64,
                    "source": {
                        "label": label,
                        "experiment_id": "x" * 200,
                        "source_fingerprint": "1" * 64,
                        "legacy_convention": True,
                    },
                },
            )
            write_manifest_for_directory(directory)
            os.utime(directory / "analysis.json", (index + 1, index + 1))
    response = _client(service).get(f"/api/robustness/{collection}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 200
    assert len(response.content) <= 1024 * 1024
    print(f"{collection}: 200 max-length summaries, {len(response.content)} JSON bytes")


@pytest.mark.parametrize("collection", ["sources", "analyses"])
def test_listing_isolates_over_nested_json_records(service, collection):
    if collection == "sources":
        path = service.experiments_root / "campaign-z/experiment.json"
        expected = "campaign-a"
    else:
        saved = service.save(_request(service))
        path = service._analysis_root() / "summary-invalid/analysis.json"
        expected = saved["analysis_id"]
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b'{"nested":' + b"[" * 1200 + b"0" + b"]" * 1200 + b"}"
    path.write_bytes(payload)
    if collection == "analyses":
        write_manifest_for_directory(path.parent)
    response = _client(service).get(f"/api/robustness/{collection}")
    assert response.status_code == 200
    key = "experiment_id" if collection == "sources" else "analysis_id"
    assert [item[key] for item in response.json()["items"]] == [expected]
    assert path.read_bytes() == payload


@pytest.mark.parametrize(
    "recorded_id",
    [
        _MISSING,
        None,
        "",
        0,
        1,
        True,
        False,
        2.0,
        [],
        {},
        "campaign-a",
        "Campaign-z",
        "campaign-z/extra",
        "../campaign-z",
    ],
)
def test_source_discovery_excludes_inconsistent_identity_without_rewriting_evidence(
    service, recorded_id
):
    original = service.experiments_root / "campaign-a"
    request = _request(service)
    original_metadata = (original / "experiment.json").read_bytes()
    original_bundle = (original / "evidence_bundle.zip").read_bytes()
    copied = service.experiments_root / "campaign-z"
    shutil.copytree(original, copied)
    record = json.loads((copied / "experiment.json").read_bytes())
    if recorded_id is _MISSING:
        record.pop("experiment_id")
    else:
        record["experiment_id"] = recorded_id
    _write(copied / "experiment.json", record)
    # Integrity-valid copies isolate identity rejection from hash/parser failures.
    write_manifest_for_directory(copied)
    create_bundle_zip_for_directory(copied)
    copied_metadata = (copied / "experiment.json").read_bytes()
    copied_bundle = (copied / "evidence_bundle.zip").read_bytes()
    client = _client(service)
    response = client.get("/api/robustness/sources")
    assert response.status_code == 200
    assert [item["experiment_id"] for item in response.json()["items"]] == [
        "campaign-a"
    ]
    invalid_request = {**request.model_dump(mode="json"), "experiment_id": "campaign-z"}
    responses = [
        client.get("/api/robustness/sources/campaign-z"),
        client.post("/api/robustness/preview", json=invalid_request),
        client.post("/api/robustness/analyses", json=invalid_request),
    ]
    for response in responses:
        assert response.status_code == 400
        assert response.json() == {
            "detail": "Select a completed campaign with a recorded scoring profile"
        }
        assert str(copied) not in response.text
    assert not service._analysis_root().exists()
    assert (
        service.source("campaign-a")["source_fingerprint"] == request.source_fingerprint
    )
    assert (original / "experiment.json").read_bytes() == original_metadata
    assert (original / "evidence_bundle.zip").read_bytes() == original_bundle
    assert (copied / "experiment.json").read_bytes() == copied_metadata
    assert (copied / "evidence_bundle.zip").read_bytes() == copied_bundle


def test_identity_filtered_discovery_keeps_order_cap_and_metadata_only_reads(
    service, monkeypatch
):
    original = service.experiments_root / "campaign-a/experiment.json"
    record = json.loads(original.read_bytes())
    for index in range(201):
        identifier = f"campaign-{index:03d}"
        _write(
            service.experiments_root / identifier / "experiment.json",
            {**record, "experiment_id": identifier},
        )
    for identifier in ("campaign-z", "campaign-y"):
        _write(service.experiments_root / identifier / "experiment.json", record)
    reads = []
    read = robustness._read_bytes

    def metadata_only(path, limit=robustness.MAX_FILE_BYTES):
        assert path.name == "experiment.json"
        reads.append((path, limit))
        return read(path, limit)

    monkeypatch.setattr(robustness, "_read_bytes", metadata_only)
    client = _client(service)
    response = client.get("/api/robustness/sources")
    assert response.status_code == 200
    assert [item["experiment_id"] for item in response.json()["items"]] == [
        "campaign-a",
        *[f"campaign-{index:03d}" for index in range(200, 3, -1)],
    ]
    assert len(reads) == 200
    assert all(limit == robustness.MAX_FILE_BYTES for _, limit in reads)
    assert len(response.content) <= robustness.MAX_LISTING_RESPONSE_BYTES
    assert client.get("/api/robustness/sources/campaign-z/extra").status_code == 404


def test_identity_matched_discovery_selection_preserves_complete_workflow(service):
    # Mirror production: profiles are persisted in canonical JSON order before
    # campaign scoring. The generic fixture also supports in-memory-order tests.
    root = service.experiments_root / "campaign-a"
    comparison = json.loads((root / "comparison.json").read_bytes())
    comparison.update(
        score_recorded_rows(comparison["rows"], comparison["decision"]["profile"])
    )
    _write(root / "comparison.json", comparison)
    record = json.loads((root / "experiment.json").read_bytes())
    _write(root / "experiment.json", {**record, "decision": comparison["decision"]})
    write_manifest_for_directory(root)
    create_bundle_zip_for_directory(root)
    client = _client(service)
    response = client.get("/api/robustness/sources")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["experiment_id"] == "campaign-a"
    opened = client.get(f"/api/robustness/sources/{item['experiment_id']}")
    assert opened.status_code == 200
    request = _request(service).model_dump(mode="json")
    assert opened.json()["source_fingerprint"] == request["source_fingerprint"]
    preview = client.post("/api/robustness/preview", json=request)
    assert preview.status_code == 200
    assert preview.json()["current"]["rows"] == opened.json()["comparison"]["rows"]
    saved = client.post("/api/robustness/analyses", json=request)
    assert saved.status_code == 200
    record = saved.json()
    loaded = client.get(f"/api/robustness/analyses/{record['analysis_id']}")
    assert loaded.status_code == 200
    assert loaded.json() == record
    exported = client.get(record["urls"]["bundle"])
    assert exported.status_code == 200
    assert hashlib.sha256(exported.content).hexdigest() == record["bundle_sha256"]


@pytest.mark.parametrize("operation", ["source", "preview", "save"])
def test_growing_source_bundle_http_rejects_before_preview_or_persistence(
    service, monkeypatch, operation
):
    request = _request(service)
    client = _client(service)
    bundle = service.experiments_root / "campaign-a/evidence_bundle.zip"
    original = bundle.read_bytes()
    with monkeypatch.context() as patches:
        patches.setattr(robustness, "MAX_BUNDLE_BYTES", 8)
        streams = _intercept_source_bundle(
            service, patches, reported_size=4, size=12, short_read=3
        )
        with pytest.raises(
            ValueError, match="^Source bundle exceeds the robustness resource limit$"
        ):
            getattr(service, operation)(
                "campaign-a" if operation == "source" else request
            )
        if operation == "source":
            response = client.get("/api/robustness/sources/campaign-a")
        else:
            response = client.post(
                "/api/robustness/preview"
                if operation == "preview"
                else "/api/robustness/analyses",
                json=request.model_dump(mode="json"),
            )
        assert response.status_code == 400
        assert response.json() == {
            "detail": "Source bundle exceeds the robustness resource limit"
        }
        assert str(service.experiments_root) not in response.text
        assert len(streams) == 2 and all(stream.consumed == 9 for stream in streams)
        _assert_stream_bound(streams, 8)
        assert not service._analysis_root().exists()
    assert bundle.read_bytes() == original
