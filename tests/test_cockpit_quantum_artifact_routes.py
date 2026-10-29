"""Characterize quantum artifact transport with synthetic files, never a harness run."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from qs_dmss import quantum_showcase
from qs_dmss.cockpit import api

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "quantum-synthetic-run"
FILES = {
    "report": ("quantum-compilation-validation.json", "application/json"),
    "summary": ("quantum-compilation-validation.html", "text/html; charset=utf-8"),
    "markdown": ("quantum-compilation-validation.md", "text/markdown; charset=utf-8"),
    "matrix": ("quantum-compilation-matrix.csv", "text/csv; charset=utf-8"),
    "manifest": ("manifest.sha256.json", "application/json"),
    "bundle": ("quantum-compilation-evidence.zip", "application/zip"),
}
ROUTES = (
    ("/api/quantum-validation/files/{artifact_name}", "quantum_validation_artifact"),
    (
        "/api/quantum-validation/runs/{run_id}/files/{artifact_name}",
        "quantum_validation_run_artifact",
    ),
)
HTML_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


def seed(directory, marker):
    directory.mkdir(parents=True, exist_ok=True)
    for key, (filename, _) in FILES.items():
        if key == "summary":
            raw = f"<!doctype html><p>{marker} π</p><script>not executed</script>\n".encode()
        elif key in {"report", "manifest"}:
            raw = ('{ "marker": "' + marker + '", "value": 1.00 }\n').encode()
        else:
            raw = b"\x00\xff" + f"synthetic {marker} {key}\n".encode()
        (directory / filename).write_bytes(raw)
    return directory


def setup_client(tmp_path, monkeypatch, *, hosted=False):
    packaged = seed(tmp_path / "packaged", "snapshot")
    monkeypatch.setattr(
        quantum_showcase, "quantum_compilation_showcase_root", lambda: packaged
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Artifact GET must not execute the quantum harness")

    monkeypatch.setattr(api, "validate_fractal_quantum_compilation", forbidden)
    output = tmp_path / "runs"
    app = api.create_app(repo_root=ROOT, output_root=output, hosted_demo=hosted)
    return SimpleNamespace(
        app=app,
        client=TestClient(app, raise_server_exceptions=False),
        output=output,
        packaged=packaged,
        local=seed(output / "quantum-validations" / RUN_ID, "local run"),
    )


def url(local, artifact, run_id=RUN_ID):
    prefix = (
        f"/api/quantum-validation/runs/{run_id}" if local else "/api/quantum-validation"
    )
    return f"{prefix}/files/{artifact}"


def routes(app):
    paths = {path for path, _ in ROUTES}
    return [r for r in app.routes if getattr(r, "path", None) in paths]


def snapshot(directory):
    return {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}


def assert_headers(response, *, html=False):
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive, nosnippet"
    for name, value in api.BASELINE_SECURITY_HEADERS.items():
        if name.lower() != "content-security-policy":
            assert response.headers[name] == value
    assert response.headers["content-security-policy"] == (
        HTML_CSP if html else api.BASELINE_SECURITY_HEADERS["Content-Security-Policy"]
    )
    assert response.headers["x-frame-options"] == "DENY"


@pytest.mark.parametrize("local", [False, True], ids=["packaged", "local-run"])
@pytest.mark.parametrize("key", FILES)
@pytest.mark.parametrize("alias", [False, True], ids=["key", "filename"])
def test_delivery_bytes_media_aliases_and_security(
    tmp_path, monkeypatch, local, key, alias
):
    ctx = setup_client(tmp_path, monkeypatch)
    filename, media = FILES[key]
    directory = ctx.local if local else ctx.packaged
    before = snapshot(directory)
    response = ctx.client.get(url(local, filename if alias else key))
    assert response.status_code == 200 and response.content == before[filename]
    assert response.headers["content-type"] == media
    assert int(response.headers["content-length"]) == len(response.content)
    assert response.headers["etag"] and response.headers["last-modified"]
    assert_headers(response, html=key == "summary")
    if key == "summary":
        assert "content-disposition" not in response.headers
    else:
        assert (
            response.headers["content-disposition"]
            == f'attachment; filename="{filename}"'
        )
    assert snapshot(directory) == before


@pytest.mark.parametrize("key", FILES)
def test_hosted_packaged_downloads_do_not_expose_local_runs(tmp_path, monkeypatch, key):
    ctx = setup_client(tmp_path, monkeypatch, hosted=True)
    filename, media = FILES[key]
    response = ctx.client.get(url(False, key))
    assert (
        response.status_code == 200
        and response.content == (ctx.packaged / filename).read_bytes()
    )
    assert response.headers["content-type"] == media
    assert_headers(response, html=key == "summary")
    assert api.HOSTED_DEMO_COOKIE_NAME in response.cookies
    for client in (ctx.client, TestClient(ctx.app, raise_server_exceptions=False)):
        for name in (key, filename):
            denied = client.get(url(True, name))
            assert denied.status_code == 404 and denied.json() == {
                "detail": "Quantum artifact not found"
            }
            assert_headers(denied)


@pytest.mark.parametrize("key", FILES)
@pytest.mark.parametrize("extra", [0, 1])
def test_hosted_packaged_cap_is_inclusive(tmp_path, monkeypatch, key, extra):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "32")
    ctx = setup_client(tmp_path, monkeypatch, hosted=True)
    path = ctx.packaged / FILES[key][0]
    path.write_bytes(b"x" * (32 + extra))
    response = ctx.client.get(url(False, key))
    assert response.status_code == (413 if extra else 200)
    if extra:
        assert response.json() == {
            "detail": "Hosted demo artifact exceeds the download size cap."
        }
    else:
        assert response.content == path.read_bytes()
    assert_headers(response, html=key == "summary" and not extra)


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("key", FILES)
def test_local_mode_does_not_apply_hosted_cap(tmp_path, monkeypatch, local, key):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "1")
    ctx = setup_client(tmp_path, monkeypatch)
    response = ctx.client.get(url(local, key))
    assert response.status_code == 200


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("key", FILES)
def test_range_and_unsatisfiable_range_contract(tmp_path, monkeypatch, local, key):
    ctx = setup_client(tmp_path, monkeypatch)
    raw = ((ctx.local if local else ctx.packaged) / FILES[key][0]).read_bytes()
    response = ctx.client.get(url(local, key), headers={"Range": "bytes=0-3"})
    assert response.status_code == 206 and response.content == raw[:4]
    assert response.headers["content-range"] == f"bytes 0-3/{len(raw)}"
    assert response.headers["content-type"] == FILES[key][1]
    assert_headers(response, html=key == "summary")
    response = ctx.client.get(url(local, key), headers={"Range": "bytes=999999-"})
    assert (
        response.status_code == 416
        and response.headers["content-range"] == f"bytes */{len(raw)}"
    )
    # Starlette creates a separate error response: baseline CSP, not preview CSP.
    assert_headers(response)


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("key", FILES)
@pytest.mark.parametrize("directory", [False, True], ids=["absent", "directory"])
def test_missing_artifact_is_not_regenerated(
    tmp_path, monkeypatch, local, key, directory
):
    ctx = setup_client(tmp_path, monkeypatch)
    root = ctx.local if local else ctx.packaged
    path = root / FILES[key][0]
    path.unlink()
    if directory:
        path.mkdir()
    before = snapshot(root)
    response = ctx.client.get(url(local, key))
    assert response.status_code == 404 and response.json() == {
        "detail": "Quantum artifact not found"
    }
    assert_headers(response)
    assert snapshot(root) == before and path.is_dir() is directory


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize(
    "name", ["unknown", "REPORT", "%20report", "%2e%2e%5creport", "%2e%2e"]
)
def test_allowlist_rejects_nonaliases_exactly(tmp_path, monkeypatch, local, name):
    ctx = setup_client(tmp_path, monkeypatch)
    (tmp_path / "report").write_bytes(b"outside fixture must not be served")
    response = ctx.client.get(url(local, name))
    assert response.status_code == 404 and response.json() == {
        "detail": "Quantum artifact not found"
    }
    assert_headers(response)


@pytest.mark.parametrize(
    "run_id", ["missing-run", "%2e%2e", "bad%20name", "bad%5cname"]
)
def test_run_identity_errors_are_preserved(tmp_path, monkeypatch, run_id):
    ctx = setup_client(tmp_path, monkeypatch)
    response = ctx.client.get(url(True, "report", run_id))
    assert response.status_code == 404 and response.json() == {
        "detail": "Quantum validation run not found"
    }
    assert_headers(response)


def test_absent_local_root_keeps_existing_directory_creation_only(
    tmp_path, monkeypatch
):
    ctx = setup_client(tmp_path, monkeypatch)
    empty = tmp_path / "empty-output"
    dependency = routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: api.CockpitService.create(
        repo_root=ROOT, output_root=empty, hosted_demo=False
    )
    response = ctx.client.get(url(True, "report", "missing-run"))
    assert response.status_code == 404 and response.json() == {
        "detail": "Quantum validation run not found"
    }
    assert list((empty / "quantum-validations").iterdir()) == []


def test_route_order_names_dependencies_and_openapi(tmp_path, monkeypatch):
    ctx = setup_client(tmp_path, monkeypatch)
    selected = routes(ctx.app)
    assert [(r.path, r.name, r.methods) for r in selected] == [
        (p, n, {"GET"}) for p, n in ROUTES
    ]
    order = [getattr(r, "path", None) for r in ctx.app.routes]
    first = order.index(ROUTES[0][0])
    assert order[first - 1] == "/api/quantum-validation/runs"
    assert order[first : first + 2] == [p for p, _ in ROUTES]
    assert order[first + 2] == "/api/showcases/{scenario}/run"
    dependency = selected[0].dependant.dependencies[0].call
    for local, route in enumerate(selected):
        assert len(route.dependant.dependencies) == 1
        assert route.dependant.dependencies[0].call is dependency
        operation = ctx.app.openapi()["paths"][route.path]["get"]
        names = ["run_id", "artifact_name"] if local else ["artifact_name"]
        assert operation["parameters"] == [
            {
                "name": name,
                "in": "path",
                "required": True,
                "schema": {"type": "string", "title": name.replace("_", " ").title()},
            }
            for name in names
        ]
        assert (
            operation["operationId"]
            == route.name
            + route.path.replace("/", "_")
            .replace("{", "_")
            .replace("}", "_")
            .replace("-", "_")
            + "_get"
        )
        assert set(operation["responses"]) == {"200", "422"}


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("suffix", [".bin", ".HTML"])
def test_dependency_override_resolution_key_and_guard_order(
    tmp_path, monkeypatch, local, suffix
):
    calls = []

    def key(name):
        calls.append(("key", name))
        return "report"

    monkeypatch.setattr(api, "quantum_compilation_showcase_artifact_key", key)
    ctx = setup_client(tmp_path, monkeypatch)
    path = tmp_path / ("injected" + suffix)
    path.write_bytes(b"synthetic injected transport")

    def resolve(*args):
        calls.append(("resolve", *args))
        return path

    def guard(selected):
        calls.append(("guard", selected))

    resolver = (
        "quantum_validation_run_artifact_path"
        if local
        else "quantum_validation_artifact_path"
    )
    dependency = routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{resolver: resolve}, assert_hosted_download_allowed=guard
    )
    response = ctx.client.get(url(local, "report"))
    assert response.status_code == 200 and response.content == path.read_bytes()
    assert calls == [
        ("resolve", *((RUN_ID, "report") if local else ("report",))),
        ("key", "report"),
        ("guard", path),
    ]
    assert response.headers["content-type"] == (
        "text/html; charset=utf-8" if suffix == ".HTML" else "application/json"
    )
    assert_headers(response, html=suffix == ".HTML")


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("suffix", [".bin", ".html"])
def test_guard_refusal_precedes_file_access(tmp_path, monkeypatch, local, suffix):
    ctx = setup_client(tmp_path, monkeypatch)
    missing = tmp_path / ("not-there" + suffix)

    def refuse(path):
        assert path == missing
        raise HTTPException(status_code=413, detail="synthetic refusal")

    dependency = routes(ctx.app)[0].dependant.dependencies[0].call
    resolver = (
        "quantum_validation_run_artifact_path"
        if local
        else "quantum_validation_artifact_path"
    )
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{resolver: lambda *args: missing}, assert_hosted_download_allowed=refuse
    )
    response = ctx.client.get(url(local, "report"))
    assert response.status_code == 413 and response.json() == {
        "detail": "synthetic refusal"
    }
    assert_headers(response)


@pytest.mark.parametrize("local", [False, True])
def test_key_resolution_error_contract_is_preserved(tmp_path, monkeypatch, local):
    def broken(name):
        raise ValueError("private/path <script>not public</script>")

    monkeypatch.setattr(api, "quantum_compilation_showcase_artifact_key", broken)
    ctx = setup_client(tmp_path, monkeypatch)
    response = ctx.client.get(url(local, "report"))
    assert response.status_code == (404 if local else 500)
    assert response.json() == {
        "detail": "Quantum artifact not found"
        if local
        else api.GENERIC_COCKPIT_ERROR_DETAIL
    }
    assert "private/path" not in response.text and "<script>" not in response.text


@pytest.mark.parametrize("local", [False, True])
def test_unexpected_lookup_error_is_sanitized(tmp_path, monkeypatch, local):
    ctx = setup_client(tmp_path, monkeypatch)

    def broken(*args):
        raise RuntimeError("private/path <script>not public</script>")

    dependency = routes(ctx.app)[0].dependant.dependencies[0].call
    resolver = (
        "quantum_validation_run_artifact_path"
        if local
        else "quantum_validation_artifact_path"
    )
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{resolver: broken}
    )
    response = ctx.client.get(url(local, "report"))
    assert response.status_code == 500 and response.json() == {
        "detail": api.GENERIC_COCKPIT_ERROR_DETAIL
    }
    assert "private/path" not in response.text and "<script>" not in response.text


@pytest.mark.parametrize("local", [False, True])
def test_delivery_remains_get_only(tmp_path, monkeypatch, local):
    ctx = setup_client(tmp_path, monkeypatch)
    for method in ("HEAD", "POST"):
        response = ctx.client.request(method, url(local, "report"))
        assert response.status_code == 405 and response.headers["allow"] == "GET"
