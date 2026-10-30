"""EH-013: response-policy parity, not error/status or session normalization."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import pytest
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.testclient import TestClient

from qs_dmss.cockpit import api

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = "C:/private/eh013-secret <script>exception text</script>"
ROBOTS = "noindex, nofollow, noarchive, nosnippet"
COOKIE = "eh013_existing_session"


def make_app(tmp_path, monkeypatch, hosted):
    monkeypatch.setenv("QS_DMSS_AI_ENABLED", "0")
    app = api.create_app(
        repo_root=ROOT, output_root=tmp_path / "runs", hosted_demo=hosted
    )
    assert app.state.ai_runtime.provider is None
    return app


def assert_policy(response, path):
    for name, value in api.BASELINE_SECURITY_HEADERS.items():
        assert response.headers[name] == value
    if path.startswith(api.NOINDEX_RESPONSE_PATHS):
        assert response.headers["x-robots-tag"] == ROBOTS
    else:
        assert "x-robots-tag" not in response.headers
    if path.startswith("/api/"):
        assert response.headers["cache-control"] == "no-store"
    else:
        assert "cache-control" not in response.headers


def assert_generic_error(response, path):
    assert response.status_code == 500
    assert response.json() == {"detail": api.GENERIC_COCKPIT_ERROR_DETAIL}
    assert response.headers["content-type"] == "application/json"
    assert int(response.headers["content-length"]) == len(response.content)
    assert PRIVATE not in response.text and "Traceback" not in response.text
    # The existing outer 500 path must not create/refresh a session cookie.
    assert "set-cookie" not in response.headers
    assert_policy(response, path)


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize("existing_cookie", [False, True])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_unhandled_failure_keeps_body_log_and_cookie_contract(
    tmp_path, monkeypatch, caplog, hosted, existing_cookie, method
):
    app = make_app(tmp_path, monkeypatch, hosted)
    path = "/api/eh013-failure"

    @app.api_route(path, methods=["GET", "POST"])
    async def broken():
        raise RuntimeError(PRIVATE)

    with TestClient(app, raise_server_exceptions=False) as client:
        if existing_cookie:
            client.cookies.set(api.HOSTED_DEMO_COOKIE_NAME, COOKIE)
        caplog.set_level(logging.ERROR, logger="qs_dmss.cockpit")
        response = client.request(method, path)
        assert_generic_error(response, path)
        records = [r for r in caplog.records if r.name == "qs_dmss.cockpit"]
        assert [r.getMessage() for r in records] == [
            f"cockpit_request_failed method={method} path={path} "
            "exception_type=RuntimeError"
        ]
        assert PRIVATE not in caplog.text
        if existing_cookie:
            assert client.cookies[api.HOSTED_DEMO_COOKIE_NAME] == COOKIE
        else:
            assert api.HOSTED_DEMO_COOKIE_NAME not in client.cookies
        healthy = client.get("/robots.txt")
        assert healthy.status_code == 200
        assert (api.HOSTED_DEMO_COOKIE_NAME in healthy.cookies) is hosted


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize("error", [RuntimeError, PermissionError])
def test_dependency_failure_gets_policy(tmp_path, monkeypatch, hosted, error):
    app = make_app(tmp_path, monkeypatch, hosted)
    path = "/api/eh013-dependency"

    def broken_dependency():
        raise error(PRIVATE)

    @app.get(path)
    async def endpoint(value=Depends(broken_dependency)):
        pytest.fail("A failed dependency must not reach the handler")

    with TestClient(app, raise_server_exceptions=False) as client:
        assert_generic_error(client.get(path), path)


def test_hosted_session_setup_failure_gets_policy(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch, True)

    def broken_cleanup(*args, **kwargs):
        raise OSError(PRIVATE)

    monkeypatch.setattr(api.CockpitService, "cleanup_hosted_sessions", broken_cleanup)
    with TestClient(app, raise_server_exceptions=False) as client:
        assert_generic_error(client.get("/api/health"), "/api/health")


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize("directory", [False, True], ids=["missing", "directory"])
def test_file_response_failure_before_start_gets_policy(
    tmp_path, monkeypatch, hosted, directory
):
    app = make_app(tmp_path, monkeypatch, hosted)
    path = "/api/eh013-file"
    artifact = tmp_path / "private-artifact"
    if directory:
        artifact.mkdir()

    @app.get(path)
    async def broken_file():
        return FileResponse(artifact)

    with TestClient(app, raise_server_exceptions=False) as client:
        assert_generic_error(client.get(path), path)
    assert artifact.is_dir() is directory


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize(
    "path",
    ["/api/eh013", "/docs/eh013", "/redoc/eh013", "/openapi.json/eh013", "/api", "/eh013"],
)
def test_normal_and_unhandled_policy_use_same_path_rules(
    tmp_path, monkeypatch, hosted, path
):
    app = make_app(tmp_path, monkeypatch, hosted)

    @app.get(path)
    async def endpoint(fail: bool = False):
        if fail:
            raise RuntimeError(PRIVATE)
        return {"status": "synthetic"}

    with TestClient(app, raise_server_exceptions=False) as client:
        normal = client.get(path)
        assert normal.status_code == 200 and normal.json() == {"status": "synthetic"}
        assert_policy(normal, path)
        assert (api.HOSTED_DEMO_COOKIE_NAME in normal.cookies) is hosted
        assert_generic_error(client.get(path, params={"fail": "true"}), path)


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize("prefix", ["/api/", "/public/"])
def test_existing_report_policy_and_authored_errors_are_not_overwritten(
    tmp_path, monkeypatch, hosted, prefix
):
    app = make_app(tmp_path, monkeypatch, hosted)
    path = prefix + "eh013-policy"
    csp = "default-src 'none'; sandbox"

    @app.get(path)
    async def endpoint(refuse: bool = False):
        headers = {
            "Content-Security-Policy": csp,
            "Cache-Control": "private, max-age=60",
            "X-Robots-Tag": "none",
        }
        if refuse:
            raise HTTPException(status_code=409, detail="synthetic conflict", headers=headers)
        return HTMLResponse("<p>synthetic report</p>", headers=headers)

    with TestClient(app, raise_server_exceptions=False) as client:
        for refuse in (False, True):
            response = client.get(path, params={"refuse": str(refuse).lower()})
            assert response.status_code == (409 if refuse else 200)
            if refuse:
                assert response.json() == {"detail": "synthetic conflict"}
            else:
                assert response.text == "<p>synthetic report</p>"
            assert response.headers["content-security-policy"] == csp
            assert response.headers["cache-control"] == (
                "no-store" if prefix == "/api/" else "private, max-age=60"
            )
            assert response.headers["x-robots-tag"] == (ROBOTS if prefix == "/api/" else "none")
            for name, value in api.BASELINE_SECURITY_HEADERS.items():
                if name != "Content-Security-Policy":
                    assert response.headers[name] == value
            assert (api.HOSTED_DEMO_COOKIE_NAME in response.cookies) is hosted


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
def test_unhandled_exception_still_propagates_to_server(tmp_path, monkeypatch, hosted):
    app = make_app(tmp_path, monkeypatch, hosted)

    @app.get("/api/eh013-propagates")
    async def broken():
        raise RuntimeError(PRIVATE)

    with TestClient(app) as client, pytest.raises(RuntimeError, match="eh013-secret"):
        client.get("/api/eh013-propagates")


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
def test_started_stream_is_not_replaced_by_error_json(tmp_path, monkeypatch, hosted):
    app = make_app(tmp_path, monkeypatch, hosted)
    events = []

    async def body():
        yield b"retained-prefix"
        raise RuntimeError(PRIVATE)

    @app.get("/api/eh013-stream")
    async def stream():
        return StreamingResponse(body(), media_type="text/plain")

    async def exercise():
        async def receive():
            await asyncio.Event().wait()

        async def send(message):
            events.append(message.copy())

        scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
            "http_version": "1.1", "method": "GET", "scheme": "http",
            "path": "/api/eh013-stream", "raw_path": b"/api/eh013-stream",
            "query_string": b"", "root_path": "", "headers": [],
            "client": ("127.0.0.1", 10000), "server": ("testserver", 80),
        }
        await asyncio.wait_for(app(scope, receive, send), timeout=5)

    with pytest.raises(RuntimeError, match="eh013-secret"):
        asyncio.run(exercise())
    starts = [event for event in events if event["type"] == "http.response.start"]
    assert len(starts) == 1 and starts[0]["status"] == 200
    headers = {name.decode(): value.decode() for name, value in starts[0]["headers"]}
    assert headers["cache-control"] == "no-store"
    assert headers["x-robots-tag"] == ROBOTS
    for name, value in api.BASELINE_SECURITY_HEADERS.items():
        assert headers[name.lower()] == value
    assert ("set-cookie" in headers) is hosted
    raw = b"".join(event.get("body", b"") for event in events)
    assert raw == b"retained-prefix"
    assert api.GENERIC_COCKPIT_ERROR_DETAIL.encode() not in raw
