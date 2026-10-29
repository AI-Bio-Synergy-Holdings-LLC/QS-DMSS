"""Characterize showcase delivery with synthetic files, never a showcase execution."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import NamedTuple

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from qs_dmss.cockpit.api import (
    BASELINE_SECURITY_HEADERS,
    GENERIC_COCKPIT_ERROR_DETAIL,
    HOSTED_DEMO_COOKIE_NAME,
    create_app,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "canonical-simulation"
COOKIE = "showcase_delivery_session"


class Delivery(NamedTuple):
    suffix: str
    resolver: str
    relative: str
    media: str
    filename: str | None


CASES = (
    Delivery(
        "report",
        "showcase_markdown_path",
        "simulation-showcase.md",
        "text/markdown; charset=utf-8",
        None,
    ),
    Delivery(
        "report.json",
        "showcase_json_path",
        "simulation-showcase.json",
        "application/json",
        None,
    ),
    Delivery(
        "artifacts/plot.svg",
        "showcase_artifact_path",
        "artifacts/plot.svg",
        "image/svg+xml",
        "plot.svg",
    ),
    Delivery(
        "artifacts/table.csv",
        "showcase_artifact_path",
        "artifacts/table.csv",
        "text/csv; charset=utf-8",
        "table.csv",
    ),
    Delivery(
        "artifacts/state.bin",
        "showcase_artifact_path",
        "artifacts/state.bin",
        "application/octet-stream",
        "state.bin",
    ),
    Delivery(
        "artifacts/upper.SVG",
        "showcase_artifact_path",
        "artifacts/upper.SVG",
        "application/octet-stream",
        "upper.SVG",
    ),
    Delivery(
        "artifacts/page.html",
        "showcase_artifact_path",
        "artifacts/page.html",
        "application/octet-stream",
        "page.html",
    ),
)
ROUTES = (
    ("report", "showcase_markdown_report"),
    ("report.json", "showcase_json_report"),
    ("artifacts/{artifact_name}", "showcase_artifact"),
)
ERRORS = {
    "showcase_markdown_path": "Showcase report not found",
    "showcase_json_path": "Showcase JSON report not found",
    "showcase_artifact_path": "Showcase artifact not found",
}


def setup_client(tmp_path, *, hosted=False):
    output = tmp_path / "runs"
    app = create_app(repo_root=ROOT, output_root=output, hosted_demo=hosted)
    client = TestClient(app, raise_server_exceptions=False)
    if hosted:
        client.cookies.set(
            HOSTED_DEMO_COOKIE_NAME, COOKIE, domain="testserver.local", path="/"
        )
        assert client.get("/robots.txt").status_code == 200
    return SimpleNamespace(
        app=app,
        client=client,
        output=output,
        showcases=output / "sessions" / COOKIE / "showcases"
        if hosted
        else tmp_path / "showcases",
        base_showcases=tmp_path / "showcases",
    )


def seed_showcase(root, marker="synthetic"):
    directory = root / SCENARIO
    files = {
        "simulation-showcase.md": f"# {marker} π\n\nRecorded fixture only.\n".encode(),
        "simulation-showcase.json": (
            '{ "marker": "' + marker + '", "value": 1.00 }\n'
        ).encode(),
        "artifacts/plot.svg": f'<svg xmlns="http://www.w3.org/2000/svg"><title>{marker}</title></svg>'.encode(),
        "artifacts/table.csv": f"label,value\n{marker},1\n".encode(),
        "artifacts/state.bin": b"\x00\xff" + marker.encode(),
        "artifacts/upper.SVG": f"<svg><title>{marker}</title></svg>".encode(),
        "artifacts/page.html": f"<script>{marker}</script>".encode(),
        "artifacts/raw-name.svg": b"<svg><title>normalized name</title></svg>",
        "artifacts/artifact": b"synthetic default filename",
    }
    for name, value in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    return directory


def file_bytes(directory):
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in directory.rglob("*")
        if p.is_file()
    }


def assert_headers(response):
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive, nosnippet"
    for name, value in BASELINE_SECURITY_HEADERS.items():
        assert response.headers[name] == value
    assert response.headers["x-frame-options"] == "DENY"


def delivery_routes(app):
    paths = {f"/api/showcases/{{scenario}}/{suffix}" for suffix, _ in ROUTES}
    return [r for r in app.routes if getattr(r, "path", None) in paths]


def request_url(case, scenario=SCENARIO):
    return f"/api/showcases/{scenario}/{case.suffix}"


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.suffix)
def test_delivery_preserves_exact_bytes_media_and_security(tmp_path, hosted, case):
    ctx = setup_client(tmp_path, hosted=hosted)
    directory = seed_showcase(ctx.showcases)
    before = file_bytes(directory)
    response = ctx.client.get(request_url(case))
    assert response.status_code == 200 and response.content == before[case.relative]
    assert response.headers["content-type"] == case.media
    assert int(response.headers["content-length"]) == len(response.content)
    assert response.headers["etag"] and response.headers["last-modified"]
    assert_headers(response)
    if case.filename:
        assert (
            response.headers["content-disposition"]
            == f'attachment; filename="{case.filename}"'
        )
    else:
        assert "content-disposition" not in response.headers
    assert file_bytes(directory) == before
    assert (HOSTED_DEMO_COOKIE_NAME in response.cookies) is hosted


@pytest.mark.parametrize("case", CASES[:3], ids=lambda c: c.suffix)
@pytest.mark.parametrize("scenario", ["unknown-showcase", "%2e%2e%5cnot-a-showcase"])
def test_unknown_scenario_error_is_exact(tmp_path, case, scenario):
    ctx = setup_client(tmp_path)
    response = ctx.client.get(request_url(case, scenario))
    assert response.status_code == 404
    assert response.json() == {"detail": "Showcase scenario not found"}
    assert_headers(response)
    assert not ctx.showcases.exists()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.suffix)
def test_missing_output_does_not_run_or_create_showcase(tmp_path, case):
    ctx = setup_client(tmp_path)
    response = ctx.client.get(request_url(case))
    assert response.status_code == 404
    assert response.json() == {"detail": ERRORS[case.resolver]}
    assert_headers(response)
    assert not ctx.showcases.exists()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.suffix)
def test_missing_file_is_not_regenerated(tmp_path, case):
    ctx = setup_client(tmp_path)
    directory = seed_showcase(ctx.showcases)
    (directory / case.relative).unlink()
    before = file_bytes(directory)
    response = ctx.client.get(request_url(case))
    assert response.status_code == 404
    assert response.json() == {"detail": ERRORS[case.resolver]}
    assert file_bytes(directory) == before


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.suffix)
@pytest.mark.parametrize("extra", [0, 1])
def test_hosted_download_cap_is_inclusive(tmp_path, monkeypatch, case, extra):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "32")
    ctx = setup_client(tmp_path, hosted=True)
    directory = seed_showcase(ctx.showcases)
    path = directory / case.relative
    path.write_bytes(b"x" * (32 + extra))
    response = ctx.client.get(request_url(case))
    assert response.status_code == (413 if extra else 200)
    if extra:
        assert response.json() == {
            "detail": "Hosted demo artifact exceeds the download size cap."
        }
    else:
        assert response.content == path.read_bytes()
    assert_headers(response)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.suffix)
def test_local_delivery_keeps_hosted_cap_disabled(tmp_path, monkeypatch, case):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "1")
    ctx = setup_client(tmp_path)
    directory = seed_showcase(ctx.showcases)
    response = ctx.client.get(request_url(case))
    assert (
        response.status_code == 200
        and response.content == (directory / case.relative).read_bytes()
    )


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.suffix)
def test_hosted_peer_and_base_outputs_remain_isolated(tmp_path, case):
    ctx = setup_client(tmp_path, hosted=True)
    first = seed_showcase(ctx.showcases, "first")
    seed_showcase(ctx.base_showcases, "base")
    peer = TestClient(ctx.app, raise_server_exceptions=False)
    peer.cookies.set(
        HOSTED_DEMO_COOKIE_NAME,
        "showcase_peer_session",
        domain="testserver.local",
        path="/",
    )
    response = peer.get(request_url(case))
    assert response.status_code == 404 and response.json() == {
        "detail": ERRORS[case.resolver]
    }
    second = seed_showcase(
        ctx.output / "sessions/showcase_peer_session/showcases", "second"
    )
    assert (
        ctx.client.get(request_url(case)).content
        == (first / case.relative).read_bytes()
    )
    assert peer.get(request_url(case)).content == (second / case.relative).read_bytes()
    assert ctx.client.cookies[HOSTED_DEMO_COOKIE_NAME] == COOKIE
    assert peer.cookies[HOSTED_DEMO_COOKIE_NAME] == "showcase_peer_session"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.suffix)
def test_range_and_unsatisfiable_range_contract(tmp_path, case):
    ctx = setup_client(tmp_path)
    directory = seed_showcase(ctx.showcases)
    raw = (directory / case.relative).read_bytes()
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


@pytest.mark.parametrize(
    "scenario", ["canonical-simulation.yaml", "folder%5ccanonical-simulation"]
)
def test_existing_scenario_alias_normalization_is_preserved(tmp_path, scenario):
    ctx = setup_client(tmp_path)
    directory = seed_showcase(ctx.showcases)
    response = ctx.client.get(request_url(CASES[0], scenario))
    assert (
        response.status_code == 200
        and response.content == (directory / CASES[0].relative).read_bytes()
    )


@pytest.mark.parametrize(
    "name,target",
    [
        ("raw%20name.svg", "raw-name.svg"),
        ("%2e%2e%5cplot.svg", "plot.svg"),
        ("%2e%2e", "artifact"),
    ],
)
def test_existing_artifact_basename_normalization_is_preserved(tmp_path, name, target):
    ctx = setup_client(tmp_path)
    directory = seed_showcase(ctx.showcases)
    (tmp_path / "plot.svg").write_bytes(b"outside must not be read")
    response = ctx.client.get(f"/api/showcases/{SCENARIO}/artifacts/{name}")
    assert (
        response.status_code == 200
        and response.content == (directory / "artifacts" / target).read_bytes()
    )
    assert response.headers["content-disposition"] == f'attachment; filename="{target}"'


def test_artifact_directory_is_not_served(tmp_path):
    ctx = setup_client(tmp_path)
    directory = seed_showcase(ctx.showcases)
    (directory / "artifacts/not-a-file").mkdir()
    response = ctx.client.get(f"/api/showcases/{SCENARIO}/artifacts/not-a-file")
    assert response.status_code == 404 and response.json() == {
        "detail": "Showcase artifact not found"
    }


def test_route_order_names_dependencies_and_openapi(tmp_path):
    ctx = setup_client(tmp_path)
    routes = delivery_routes(ctx.app)
    assert [(r.path, r.name, r.methods) for r in routes] == [
        (f"/api/showcases/{{scenario}}/{suffix}", name, {"GET"})
        for suffix, name in ROUTES
    ]
    order = [getattr(r, "path", None) for r in ctx.app.routes]
    first = order.index(routes[0].path)
    assert order[first - 1] == "/api/showcases/{scenario}/compare"
    assert order[first : first + 3] == [r.path for r in routes]
    assert order[first + 3] == "/api/runs"
    dependencies = [r.dependant.dependencies[0] for r in routes]
    assert all(
        d.name == "active_service" and d.call is dependencies[0].call
        for d in dependencies
    )
    for (suffix, name), route in zip(ROUTES, routes):
        operation = ctx.app.openapi()["paths"][route.path]["get"]
        clean_suffix = (
            suffix.replace(".", "_")
            .replace("/", "_")
            .replace("{", "_")
            .replace("}", "_")
        )
        assert (
            operation["operationId"]
            == f"{name}_api_showcases__scenario__{clean_suffix}_get"
        )
        parameters = [
            {
                "name": "scenario",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "title": "Scenario"},
            }
        ]
        if "artifact_name" in suffix:
            parameters.append(
                {
                    "name": "artifact_name",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "title": "Artifact Name"},
                }
            )
        assert operation["parameters"] == parameters
        assert operation["responses"] == {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"schema": {}}},
            },
            "422": {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                    }
                },
            },
        }


@pytest.mark.parametrize("case", CASES[:3], ids=lambda c: c.suffix)
def test_dependency_override_and_guard_order(tmp_path, case):
    ctx = setup_client(tmp_path)
    path = tmp_path / "injected.bin"
    path.write_bytes(b"synthetic dependency override")
    calls = []

    def resolve(*args):
        calls.append(("resolve", *args))
        return path

    def guard(selected):
        calls.append(("guard", selected))

    dependency = delivery_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{case.resolver: resolve},
        assert_hosted_download_allowed=guard,
    )
    response = ctx.client.get(request_url(case))
    assert response.status_code == 200 and response.content == path.read_bytes()
    args = (SCENARIO, case.filename) if case.filename else (SCENARIO,)
    assert calls == [("resolve", *args), ("guard", path)]


@pytest.mark.parametrize("case", CASES[:3], ids=lambda c: c.suffix)
def test_guard_refusal_precedes_file_access(tmp_path, case):
    ctx = setup_client(tmp_path)
    missing = tmp_path / "missing.bin"

    def guard(path):
        assert path == missing
        raise HTTPException(status_code=413, detail="synthetic guard refusal")

    dependency = delivery_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{case.resolver: lambda *args: missing},
        assert_hosted_download_allowed=guard,
    )
    response = ctx.client.get(request_url(case))
    assert response.status_code == 413 and response.json() == {
        "detail": "synthetic guard refusal"
    }
    assert_headers(response)


@pytest.mark.parametrize("case", CASES[:3], ids=lambda c: c.suffix)
def test_unexpected_resolution_error_stays_sanitized(tmp_path, case):
    ctx = setup_client(tmp_path)

    def broken(*args):
        raise RuntimeError("private/path <script>not public</script>")

    dependency = delivery_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        **{case.resolver: broken}
    )
    response = ctx.client.get(request_url(case))
    assert response.status_code == 500 and response.json() == {
        "detail": GENERIC_COCKPIT_ERROR_DETAIL
    }
    assert "private/path" not in response.text and "<script>" not in response.text
