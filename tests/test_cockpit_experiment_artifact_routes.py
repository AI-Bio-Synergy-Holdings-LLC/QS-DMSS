"""Experiment delivery HTTP characterization with synthetic, unchanged artifacts."""

from __future__ import annotations

import base64
import hashlib
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from qs_dmss.cockpit.api import (
    BASELINE_SECURITY_HEADERS,
    GENERIC_COCKPIT_ERROR_DETAIL,
    HOSTED_DEMO_COOKIE_NAME,
    create_app,
)
from qs_dmss.evidence.html_security import WORKBOOK_TABS_SCRIPT

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "experiment with spaces"
DELIVERY = (
    (
        "bundle",
        "experiment_bundle_download",
        "experiment_bundle_path",
        "evidence_bundle.zip",
        "application/zip",
        "comparison-bundle.zip",
    ),
    (
        "report",
        "experiment_report",
        "experiment_report_path",
        "report.html",
        "text/html; charset=utf-8",
        None,
    ),
    (
        "workbook",
        "experiment_workbook",
        "experiment_workbook_path",
        "workbook.html",
        "text/html; charset=utf-8",
        None,
    ),
    (
        "workbook/download",
        "experiment_workbook_download",
        "experiment_workbook_path",
        "workbook.html",
        "text/html; charset=utf-8",
        "research-workbook.html",
    ),
)


def setup_client(tmp_path, *, hosted=False):
    output = tmp_path / "runs"
    app = create_app(repo_root=ROOT, output_root=output, hosted_demo=hosted)
    client = TestClient(app, raise_server_exceptions=False)
    experiments = tmp_path / "experiments"
    if hosted:
        client.cookies.set(
            HOSTED_DEMO_COOKIE_NAME,
            "experiment_delivery_session",
            domain="testserver.local",
            path="/",
        )
        assert client.get("/robots.txt").status_code == 200
        experiments = (
            output / "sessions" / "experiment_delivery_session" / "experiments"
        )
    return SimpleNamespace(
        app=app,
        client=client,
        output=output,
        experiments=experiments,
        base_experiments=tmp_path / "experiments",
    )


def seed_experiment(root, experiment_id=EXPERIMENT_ID, marker="synthetic"):
    directory = root / experiment_id
    directory.mkdir(parents=True)
    (directory / "experiment.json").write_bytes(b'{"synthetic":true}\n')
    for name in ("report.html", "workbook.html"):
        (directory / name).write_text(
            f"<!doctype html><style>body{{color:teal}}</style><h1>{marker} {name}</h1>"
            f"<script>{WORKBOOK_TABS_SCRIPT}</script>",
            encoding="utf-8",
        )
    with zipfile.ZipFile(directory / "evidence_bundle.zip", "w") as archive:
        archive.writestr("synthetic.txt", marker)
    return directory


def headers_are_preserved(response, *, preview=False):
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive, nosnippet"
    for name, value in BASELINE_SECURITY_HEADERS.items():
        if preview and name in {"Content-Security-Policy", "X-Frame-Options"}:
            continue
        assert response.headers[name] == value
    if preview:
        assert response.headers["x-frame-options"] == "SAMEORIGIN"
        assert "frame-ancestors 'self'" in response.headers["content-security-policy"]
        assert "'unsafe-inline'" not in response.headers["content-security-policy"]
    else:
        assert response.headers["x-frame-options"] == "DENY"


def delivery_routes(app):
    paths = {f"/api/experiments/{{experiment_id}}/{suffix}" for suffix, *_ in DELIVERY}
    return [route for route in app.routes if getattr(route, "path", None) in paths]


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
def test_delivery_preserves_bytes_headers_and_sources(
    tmp_path,
    hosted,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
):
    ctx = setup_client(tmp_path, hosted=hosted)
    directory = seed_experiment(ctx.experiments)
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    response = ctx.client.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}")
    assert response.status_code == 200 and response.content == before[source]
    assert response.headers["content-type"] == media
    assert int(response.headers["content-length"]) == len(response.content)
    assert response.headers["etag"] and response.headers["last-modified"]
    preview = filename is None
    headers_are_preserved(response, preview=preview)
    if filename:
        assert response.headers["content-disposition"] == (
            f'attachment; filename="experiment-with-spaces-{filename}"'
        )
    else:
        assert "content-disposition" not in response.headers
        encoded = base64.b64encode(
            hashlib.sha256(b"body{color:teal}").digest()
        ).decode()
        assert f"sha256-{encoded}" in response.headers["content-security-policy"]
    assert {p.name: p.read_bytes() for p in directory.iterdir()} == before
    assert (HOSTED_DEMO_COOKIE_NAME in response.cookies) is hosted


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
@pytest.mark.parametrize("experiment_id", ["missing", "%2e%2e", "%2e%2e%5coutside"])
def test_missing_and_escaping_experiment_error_contract(
    tmp_path,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
    experiment_id,
):
    ctx = setup_client(tmp_path)
    seed_experiment(tmp_path, "outside")
    response = ctx.client.get(f"/api/experiments/{experiment_id}/{suffix}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Experiment not found"}
    headers_are_preserved(response)


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
def test_missing_artifact_error_contract(
    tmp_path,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
):
    ctx = setup_client(tmp_path)
    directory = seed_experiment(ctx.experiments)
    (directory / source).unlink()
    response = ctx.client.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}")
    artifact = "workbook" if suffix.startswith("workbook") else suffix
    assert response.status_code == 404
    assert response.json() == {"detail": f"Experiment {artifact} not found"}
    headers_are_preserved(response)


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
@pytest.mark.parametrize("extra", [0, 1])
def test_hosted_download_limit_is_inclusive(
    tmp_path,
    monkeypatch,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
    extra,
):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "32")
    ctx = setup_client(tmp_path, hosted=True)
    directory = seed_experiment(ctx.experiments)
    path = directory / source
    path.write_bytes(b"x" * (32 + extra))
    response = ctx.client.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}")
    assert response.status_code == (413 if extra else 200)
    if extra:
        assert response.json() == {
            "detail": "Hosted demo artifact exceeds the download size cap."
        }
    else:
        assert response.content == path.read_bytes()
    headers_are_preserved(response, preview=not extra and filename is None)


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
def test_local_delivery_is_not_subject_to_hosted_cap(
    tmp_path,
    monkeypatch,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "1")
    ctx = setup_client(tmp_path)
    directory = seed_experiment(ctx.experiments)
    response = ctx.client.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}")
    assert (
        response.status_code == 200
        and response.content == (directory / source).read_bytes()
    )


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
def test_hosted_sessions_cannot_read_peer_or_base_experiments(
    tmp_path,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
):
    ctx = setup_client(tmp_path, hosted=True)
    first = seed_experiment(ctx.experiments, marker="first session")
    seed_experiment(ctx.base_experiments, "base-only")
    other = TestClient(ctx.app, raise_server_exceptions=False)
    other.cookies.set(
        HOSTED_DEMO_COOKIE_NAME,
        "other_experiment_session",
        domain="testserver.local",
        path="/",
    )
    assert other.get("/robots.txt").status_code == 200
    for experiment_id in (EXPERIMENT_ID, "base-only"):
        response = other.get(f"/api/experiments/{experiment_id}/{suffix}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Experiment not found"}
    peer_root = ctx.output / "sessions" / "other_experiment_session" / "experiments"
    second = seed_experiment(peer_root, marker="second session")
    assert (
        ctx.client.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}").content
        == (first / source).read_bytes()
    )
    assert (
        other.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}").content
        == (second / source).read_bytes()
    )


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
def test_ranges_and_unsatisfiable_range_contract(
    tmp_path,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
):
    ctx = setup_client(tmp_path)
    directory = seed_experiment(ctx.experiments)
    raw = (directory / source).read_bytes()
    url = f"/api/experiments/{EXPERIMENT_ID}/{suffix}"
    response = ctx.client.get(url, headers={"Range": "bytes=0-3"})
    assert response.status_code == 206 and response.content == raw[:4]
    assert response.headers["content-range"] == f"bytes 0-3/{len(raw)}"
    assert response.headers["content-type"] == media
    headers_are_preserved(response, preview=filename is None)
    response = ctx.client.get(url, headers={"Range": "bytes=999999-"})
    assert response.status_code == 416
    assert response.headers["content-range"] == f"bytes */{len(raw)}"
    headers_are_preserved(response)


def test_order_names_dependencies_and_openapi_contract(tmp_path):
    ctx = setup_client(tmp_path)
    routes = delivery_routes(ctx.app)
    assert [(r.path, r.name, r.methods) for r in routes] == [
        (f"/api/experiments/{{experiment_id}}/{suffix}", name, {"GET"})
        for suffix, name, *_ in DELIVERY
    ]
    order = [getattr(route, "path", None) for route in ctx.app.routes]
    first = order.index("/api/experiments/{experiment_id}/bundle")
    assert order[first - 1] == "/api/runs/{run_id}/report"
    assert order[first : first + 4] == [route.path for route in routes]
    assert first + 4 == len(order)
    dependencies = [r.dependant.dependencies[0] for r in routes]
    assert all(
        d.name == "active_service" and d.call is dependencies[0].call
        for d in dependencies
    )
    schema = ctx.app.openapi()
    for suffix, name, *_ in DELIVERY:
        operation = schema["paths"][f"/api/experiments/{{experiment_id}}/{suffix}"][
            "get"
        ]
        assert operation["operationId"] == (
            f"{name}_api_experiments__experiment_id__{suffix.replace('/', '_')}_get"
        )
        assert operation["parameters"] == [
            {
                "name": "experiment_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "title": "Experiment Id"},
            }
        ]
        assert operation["responses"] == {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"schema": {}}},
            },
            "422": {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/HTTPValidationError"},
                    }
                },
            },
        }


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
def test_dependency_override_resolution_and_guard_order(
    tmp_path,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
):
    ctx = setup_client(tmp_path)
    path = tmp_path / "injected.html"
    path.write_bytes(b"synthetic overridden response")
    calls = []

    def locate(experiment_id):
        calls.append(("resolve", experiment_id))
        return path

    def guard(selected):
        calls.append(("guard", selected))

    injected = SimpleNamespace(
        **{resolver: locate}, assert_hosted_download_allowed=guard
    )
    dependency = delivery_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: injected
    response = ctx.client.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}")
    assert response.status_code == 200 and response.content == path.read_bytes()
    assert calls == [("resolve", EXPERIMENT_ID), ("guard", path)]


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
def test_guard_refusal_precedes_file_response(
    tmp_path,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
):
    ctx = setup_client(tmp_path)
    missing = tmp_path / "does-not-exist.html"

    def guard(path):
        assert path == missing
        raise HTTPException(status_code=413, detail="synthetic guard refusal")

    dependency = delivery_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{resolver: lambda _: missing},
        assert_hosted_download_allowed=guard,
    )
    response = ctx.client.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}")
    assert response.status_code == 413
    assert response.json() == {"detail": "synthetic guard refusal"}
    headers_are_preserved(response)


@pytest.mark.parametrize("suffix,name,resolver,source,media,filename", DELIVERY)
def test_unexpected_resolver_failure_is_sanitized(
    tmp_path,
    suffix,
    name,
    resolver,
    source,
    media,
    filename,
):
    ctx = setup_client(tmp_path)

    def broken(_):
        raise RuntimeError("private/path <script>not a public error</script>")

    dependency = delivery_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{resolver: broken}
    )
    response = ctx.client.get(f"/api/experiments/{EXPERIMENT_ID}/{suffix}")
    assert response.status_code == 500
    assert response.json() == {"detail": GENERIC_COCKPIT_ERROR_DETAIL}
    assert "private/path" not in response.text and "<script>" not in response.text
