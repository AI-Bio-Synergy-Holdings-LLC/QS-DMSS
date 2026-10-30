"""Characterize remaining export downloads with synthetic persisted files only."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import NamedTuple

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from qs_dmss.cockpit import api

ROOT = Path(__file__).resolve().parents[1]
AI_ID = "ai-20261029T000000Z-1234abcd"
OBJECT_ID = "synthetic-export"
COOKIE = "export_delivery_session"


class Delivery(NamedTuple):
    key: str
    route: str
    name: str
    parameter: str
    lookup: str
    media: str
    error: str
    previous: str
    following: str


CASES = (
    Delivery(
        "ai",
        "/api/ai/drafts/{interaction_id}/bundle",
        "ai_draft_bundle",
        "interaction_id",
        "ai_draft_bundle_path",
        "application/zip",
        "AI advisory draft not found",
        "/api/ai/drafts/{interaction_id}/review",
        "/api/configs",
    ),
    Delivery(
        "campaign",
        "/api/campaign-studies/{template_id}/download",
        "campaign_study_download",
        "template_id",
        "campaign_study_template_path",
        "application/json",
        "Campaign study template not found",
        "/api/campaign-studies/{template_id}",
        "/api/sweeps",
    ),
    Delivery(
        "research",
        "/api/research-objects/{export_id}/download",
        "research_object_download",
        "export_id",
        "research_object_markdown_path",
        "text/markdown; charset=utf-8",
        "Research object export not found",
        "/api/research-objects/export",
        "/api/workspaces",
    ),
    Delivery(
        "workspace",
        "/api/workspaces/{workspace_id}/download",
        "workspace_download",
        "workspace_id",
        "workspace_path",
        "application/json",
        "Workspace export not found",
        "/api/workspaces/{workspace_id}",
        "/api/runs/{run_id}/verify",
    ),
)


def identity(case):
    return AI_ID if case.key == "ai" else OBJECT_ID


def request_url(case, selected=None):
    return case.route.replace("{" + case.parameter + "}", selected or identity(case))


def seed(run_root, experiments, marker):
    paths = {
        "ai": run_root / "ai-interactions" / AI_ID / "ai-advisory-bundle.zip",
        "campaign": experiments / "campaign-studies" / f"{OBJECT_ID}.json",
        "research": experiments / "research-objects" / OBJECT_ID / "research-object.md",
        "workspace": experiments / "workspaces" / OBJECT_ID / "workspace.json",
    }
    for key, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (
            f"# {marker} π\n<script>text, not HTML</script>\n".encode()
            if key == "research"
            else ('{ "marker": "' + marker + '", "value": 1.00 }\n').encode()
        )
        if key == "ai":
            raw = b"PK\x03\x04synthetic transport bytes " + marker.encode()
        path.write_bytes(raw)
    metadata = paths["research"].with_name("research-object.json")
    metadata.write_text(
        '{"export":{"file_name":"research-review.md"}}\n', encoding="utf-8"
    )
    return paths


def setup_client(tmp_path, monkeypatch, *, hosted=False):
    monkeypatch.setenv("QS_DMSS_AI_ENABLED", "0")

    def forbidden(*args, **kwargs):
        raise AssertionError("Download must not execute, generate or export anything")

    for name in (
        "generate_ai_draft",
        "export_research_object",
        "export_workspace",
        "launch_campaign",
    ):
        monkeypatch.setattr(api.CockpitService, name, forbidden)
    output = tmp_path / "runs"
    app = api.create_app(repo_root=ROOT, output_root=output, hosted_demo=hosted)
    client = TestClient(app, raise_server_exceptions=False)
    if hosted:
        client.cookies.set(
            api.HOSTED_DEMO_COOKIE_NAME, COOKIE, domain="testserver.local", path="/"
        )
        assert client.get("/robots.txt").status_code == 200
    root = output / "sessions" / COOKIE if hosted else tmp_path
    paths = seed(root / "runs", root / "experiments", "first")
    assert app.state.ai_runtime.provider is None
    return SimpleNamespace(
        app=app, client=client, output=output, paths=paths, root=root
    )


def assert_headers(response):
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive, nosnippet"
    for name, value in api.BASELINE_SECURITY_HEADERS.items():
        assert response.headers[name] == value
    assert response.headers["x-frame-options"] == "DENY"


def assert_existing_server_error(response):
    """Freeze the pre-existing outer error response; header hardening is separate."""
    assert response.status_code == 500
    assert response.json() == {"detail": api.GENERIC_COCKPIT_ERROR_DETAIL}
    assert dict(response.headers) == {
        "content-length": str(len(response.content)),
        "content-type": "application/json",
    }


def filename(case):
    return {
        "ai": f"{AI_ID}-ai-advisory-bundle.zip",
        "campaign": f"{OBJECT_ID}.json",
        "research": "research-review.md",
        "workspace": "workspace.json",
    }[case.key]


def selected_routes(app):
    return [
        r for r in app.routes if getattr(r, "path", None) in {c.route for c in CASES}
    ]


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_exact_bytes_attachments_security_and_no_regeneration(
    tmp_path, monkeypatch, hosted, case
):
    ctx = setup_client(tmp_path, monkeypatch, hosted=hosted)
    before = {k: p.read_bytes() for k, p in ctx.paths.items()}
    response = ctx.client.get(request_url(case))
    assert response.status_code == 200 and response.content == before[case.key]
    assert response.headers["content-type"] == case.media
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{filename(case)}"'
    )
    assert int(response.headers["content-length"]) == len(response.content)
    assert response.headers["etag"] and response.headers["last-modified"]
    assert_headers(response)
    assert {k: p.read_bytes() for k, p in ctx.paths.items()} == before
    assert (api.HOSTED_DEMO_COOKIE_NAME in response.cookies) is hosted


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
@pytest.mark.parametrize("extra", [0, 1])
def test_hosted_cap_is_inclusive(tmp_path, monkeypatch, case, extra):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "32")
    ctx = setup_client(tmp_path, monkeypatch, hosted=True)
    ctx.paths[case.key].write_bytes(b"x" * (32 + extra))
    response = ctx.client.get(request_url(case))
    assert response.status_code == (413 if extra else 200)
    if extra:
        assert response.json() == {
            "detail": "Hosted demo artifact exceeds the download size cap."
        }
    else:
        assert response.content == b"x" * 32
    assert_headers(response)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_local_mode_does_not_apply_hosted_cap(tmp_path, monkeypatch, case):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "1")
    ctx = setup_client(tmp_path, monkeypatch)
    assert ctx.client.get(request_url(case)).content == ctx.paths[case.key].read_bytes()


@pytest.mark.parametrize("hosted", [False, True])
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_ranges_preserve_transport_contract(tmp_path, monkeypatch, hosted, case):
    ctx = setup_client(tmp_path, monkeypatch, hosted=hosted)
    raw = ctx.paths[case.key].read_bytes()
    response = ctx.client.get(request_url(case), headers={"Range": "bytes=0-3"})
    assert response.status_code == 206 and response.content == raw[:4]
    assert response.headers["content-range"] == f"bytes 0-3/{len(raw)}"
    assert response.headers["content-type"] == case.media
    assert_headers(response)
    response = ctx.client.get(request_url(case), headers={"Range": "bytes=999999-"})
    assert (
        response.status_code == 416
        and response.headers["content-range"] == f"bytes */{len(raw)}"
    )
    assert_headers(response)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_hosted_session_and_base_outputs_remain_isolated(tmp_path, monkeypatch, case):
    ctx = setup_client(tmp_path, monkeypatch, hosted=True)
    seed(ctx.output, tmp_path / "experiments", "base must not leak")
    peer = TestClient(ctx.app, raise_server_exceptions=False)
    peer.cookies.set(
        api.HOSTED_DEMO_COOKIE_NAME,
        "export_peer_session",
        domain="testserver.local",
        path="/",
    )
    denied = peer.get(request_url(case))
    assert denied.status_code == 404 and denied.json() == {"detail": case.error}
    peer_root = ctx.output / "sessions/export_peer_session"
    peer_paths = seed(peer_root / "runs", peer_root / "experiments", "second")
    assert ctx.client.get(request_url(case)).content == ctx.paths[case.key].read_bytes()
    assert peer.get(request_url(case)).content == peer_paths[case.key].read_bytes()
    assert ctx.client.cookies[api.HOSTED_DEMO_COOKIE_NAME] == COOKIE
    assert peer.cookies[api.HOSTED_DEMO_COOKIE_NAME] == "export_peer_session"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_missing_identity_errors_are_exact(tmp_path, monkeypatch, case):
    ctx = setup_client(tmp_path, monkeypatch)
    selected = "ai-20261029T000000Z-00000000" if case.key == "ai" else "missing-export"
    response = ctx.client.get(request_url(case, selected))
    assert response.status_code == 404 and response.json() == {"detail": case.error}
    assert_headers(response)


@pytest.mark.parametrize("directory", [False, True], ids=["absent", "directory"])
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
def test_missing_artifact_contract_without_regeneration(
    tmp_path, monkeypatch, case, directory, hosted
):
    ctx = setup_client(tmp_path, monkeypatch, hosted=hosted)
    path = ctx.paths[case.key]
    path.unlink()
    if directory:
        path.mkdir()
    response = ctx.client.get(request_url(case))
    expected = (
        500 if case.key == "ai" or (directory and case.key == "research") else 404
    )
    guard_missing = hosted and expected == 500 and not directory
    if guard_missing:
        expected = 404
    assert response.status_code == expected
    assert response.json() == {
        "detail": (
            api.GENERIC_COCKPIT_ERROR_DETAIL
            if expected == 500
            else "Artifact not found"
            if guard_missing
            else case.error
        )
    }
    if expected == 500:
        assert_existing_server_error(response)
    else:
        assert_headers(response)
    assert path.is_dir() is directory and not path.is_file()


@pytest.mark.parametrize("case", CASES[1:], ids=lambda c: c.key)
@pytest.mark.parametrize("prefix", ["folder%5c", "%20"])
def test_existing_id_normalization_is_preserved(tmp_path, monkeypatch, case, prefix):
    ctx = setup_client(tmp_path, monkeypatch)
    response = ctx.client.get(request_url(case, prefix + OBJECT_ID))
    assert (
        response.status_code == 200
        and response.content == ctx.paths[case.key].read_bytes()
    )


@pytest.mark.parametrize("selected", ["bad-id", "%2e%2e%5c" + AI_ID, AI_ID.upper()])
def test_ai_identity_stays_strict(tmp_path, monkeypatch, selected):
    ctx = setup_client(tmp_path, monkeypatch)
    response = ctx.client.get(request_url(CASES[0], selected))
    assert response.status_code == 404 and response.json() == {"detail": CASES[0].error}


@pytest.mark.parametrize(
    "stored,expected",
    [
        ("Review report.html", "Review-report.html.md"),
        (None, "qs-dmss-research-object.md"),
    ],
)
def test_research_download_filename_is_metadata_derived(
    tmp_path, monkeypatch, stored, expected
):
    ctx = setup_client(tmp_path, monkeypatch)
    ctx.paths["research"].with_name("research-object.json").write_text(
        json.dumps({"export": {"file_name": stored}}), encoding="utf-8"
    )
    response = ctx.client.get(request_url(CASES[2]))
    assert (
        response.status_code == 200
        and response.content == ctx.paths["research"].read_bytes()
    )
    assert (
        response.headers["content-disposition"] == f'attachment; filename="{expected}"'
    )
    assert_headers(response)


def test_campaign_local_precedence_and_packaged_fallback(tmp_path, monkeypatch):
    ctx = setup_client(tmp_path, monkeypatch)
    assets = tmp_path / "synthetic-assets"
    packaged = assets / "campaign-studies" / f"{OBJECT_ID}.json"
    packaged.parent.mkdir(parents=True)
    packaged.write_bytes(b'{ "packaged": true }\n')
    monkeypatch.setattr(api, "bundled_assets_root", lambda: assets)
    assert (
        ctx.client.get(request_url(CASES[1])).content
        == ctx.paths["campaign"].read_bytes()
    )
    ctx.paths["campaign"].unlink()
    response = ctx.client.get(request_url(CASES[1], OBJECT_ID + ".json"))
    assert response.status_code == 200 and response.content == packaged.read_bytes()
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{OBJECT_ID}.json"'
    )


def test_route_positions_dependencies_and_openapi(tmp_path, monkeypatch):
    ctx = setup_client(tmp_path, monkeypatch)
    routes = selected_routes(ctx.app)
    assert [(r.path, r.name, r.methods) for r in routes] == [
        (c.route, c.name, {"GET"}) for c in CASES
    ]
    dependency = routes[0].dependant.dependencies[0].call
    order = [getattr(r, "path", None) for r in ctx.app.routes]
    for route, case in zip(routes, CASES):
        index = order.index(case.route)
        assert order[index - 1] == case.previous and order[index + 1] == case.following
        assert (
            len(route.dependant.dependencies) == 1
            and route.dependant.dependencies[0].call is dependency
        )
        operation = ctx.app.openapi()["paths"][case.route]["get"]
        assert (
            operation["operationId"]
            == case.name
            + case.route.replace("/", "_")
            .replace("-", "_")
            .replace("{", "_")
            .replace("}", "_")
            + "_get"
        )
        assert operation["parameters"] == [
            {
                "name": case.parameter,
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string",
                    "title": case.parameter.replace("_", " ").title(),
                },
            }
        ]
        assert set(operation["responses"]) == {"200", "422"}


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
@pytest.mark.parametrize("suffix", [".bin", ".html"])
def test_dependency_override_and_guard_order(tmp_path, monkeypatch, case, suffix):
    ctx = setup_client(tmp_path, monkeypatch)
    path = tmp_path / ("injected" + suffix)
    path.write_bytes(b"synthetic dependency override")
    calls = []

    def resolve(selected):
        calls.append(("resolve", selected))
        return (path, "injected.md") if case.key == "research" else path

    def guard(selected):
        calls.append(("guard", selected))

    dependency = selected_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{case.lookup: resolve}, assert_hosted_download_allowed=guard
    )
    response = ctx.client.get(request_url(case))
    assert response.status_code == 200 and response.content == path.read_bytes()
    assert response.headers["content-type"] == case.media
    assert calls == [("resolve", identity(case)), ("guard", path)]
    assert_headers(response)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_guard_refusal_precedes_file_access(tmp_path, monkeypatch, case):
    ctx = setup_client(tmp_path, monkeypatch)
    missing = tmp_path / "not-there.bin"

    def guard(path):
        assert path == missing
        raise HTTPException(status_code=413, detail="synthetic guard refusal")

    def resolve(selected):
        return (missing, "injected.md") if case.key == "research" else missing

    dependency = selected_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{case.lookup: resolve}, assert_hosted_download_allowed=guard
    )
    response = ctx.client.get(request_url(case))
    assert response.status_code == 413 and response.json() == {
        "detail": "synthetic guard refusal"
    }
    assert_headers(response)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
@pytest.mark.parametrize("error", [RuntimeError, FileNotFoundError])
def test_lookup_failures_preserve_error_contract(tmp_path, monkeypatch, case, error):
    ctx = setup_client(tmp_path, monkeypatch)

    def broken(selected):
        raise error("private/path <script>must not leak</script>")

    dependency = selected_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{case.lookup: broken}
    )
    response = ctx.client.get(request_url(case))
    missing_ai = case.key == "ai" and error is FileNotFoundError
    assert response.status_code == (404 if missing_ai else 500)
    assert response.json() == {
        "detail": case.error if missing_ai else api.GENERIC_COCKPIT_ERROR_DETAIL
    }
    assert "private/path" not in response.text and "<script>" not in response.text
    if not missing_ai:
        assert_existing_server_error(response)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_existing_http_errors_pass_through(tmp_path, monkeypatch, case):
    ctx = setup_client(tmp_path, monkeypatch)

    def refuse(selected):
        raise HTTPException(status_code=403, detail="synthetic refusal")

    dependency = selected_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{case.lookup: refuse}
    )
    response = ctx.client.get(request_url(case))
    assert response.status_code == 403 and response.json() == {
        "detail": "synthetic refusal"
    }


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_download_remains_get_only(tmp_path, monkeypatch, case):
    ctx = setup_client(tmp_path, monkeypatch)
    for method in ("HEAD", "POST"):
        response = ctx.client.request(method, request_url(case))
        assert response.status_code == 405 and response.headers["allow"] == "GET"
