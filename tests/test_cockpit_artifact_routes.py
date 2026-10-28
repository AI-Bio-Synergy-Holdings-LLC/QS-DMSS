"""HTTP characterization of run-artifact delivery; synthetic files only."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from qs_dmss.cockpit.api import (
    BASELINE_SECURITY_HEADERS,
    GENERIC_COCKPIT_ERROR_DETAIL,
    HOSTED_DEMO_COOKIE_NAME,
    create_app,
)

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = (
    ("bundle", "bundle_download", "application/zip", "evidence-bundle.zip"),
    ("review-bundle", "review_bundle_download", "application/zip", "review-bundle.zip"),
    ("state-bundle", "state_bundle_download", "application/zip", "state-bundle.zip"),
    ("report", "run_report", "text/html; charset=utf-8", None),
)
RUN_ID = "run with spaces"


def setup_client(tmp_path, *, hosted=False):
    output = tmp_path / "runs"
    app = create_app(repo_root=ROOT, output_root=output, hosted_demo=hosted)
    client = TestClient(app, raise_server_exceptions=False)
    run_root = output
    if hosted:
        # Delivery characterization uses a valid, deterministic session rather
        # than testing the separate random session-ID generator.
        client.cookies.set(
            HOSTED_DEMO_COOKIE_NAME,
            "artifact_delivery_session",
            domain="testserver.local",
            path="/",
        )
        assert client.get("/robots.txt").status_code == 200
        run_root = (
            output / "sessions" / client.cookies[HOSTED_DEMO_COOKIE_NAME] / "runs"
        )
    return SimpleNamespace(app=app, client=client, output=output, run_root=run_root)


def seed_run(run_root, run_id=RUN_ID, *, graph=False):
    run_dir = run_root / run_id
    files = {
        "run.json": b'{"run_id":"synthetic"}\n',
        "metrics.json": b'{"synthetic":true}\n',
        "config.yaml": b"# synthetic transport fixture\n",
        "manifest.sha256.json": b'{"files":{}}\n',
        "report.html": b"<!doctype html><h1>Synthetic transport report</h1>\n",
        "artifacts/final_state.npz": b"synthetic state bytes, not a computed state",
        "artifacts/final_density.npy": b"synthetic density bytes",
    }
    if graph:
        files["artifacts/graph_operator.npz"] = b"synthetic operator bytes"
    for name, content in files.items():
        path = run_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    with zipfile.ZipFile(run_dir / "evidence_bundle.zip", "w") as archive:
        archive.writestr("synthetic.txt", "transport-only fixture")
    return run_dir


def assert_common_headers(response, *, preview=False):
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
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


@pytest.mark.parametrize("hosted", [False, True], ids=["local", "hosted"])
@pytest.mark.parametrize("suffix,name,media,filename", DELIVERY)
def test_delivery_success_preserves_http_contract(
    tmp_path, hosted, suffix, name, media, filename
):
    ctx = setup_client(tmp_path, hosted=hosted)
    run_dir = seed_run(ctx.run_root)
    before = {
        p.relative_to(run_dir): p.read_bytes()
        for p in run_dir.rglob("*")
        if p.is_file()
    }
    response = ctx.client.get(f"/api/runs/{RUN_ID}/{suffix}")
    assert response.status_code == 200
    assert response.headers["content-type"] == media
    assert int(response.headers["content-length"]) == len(response.content)
    assert response.headers["etag"] and response.headers["last-modified"]
    assert_common_headers(response, preview=suffix == "report")
    if filename:
        assert response.headers["content-disposition"] == (
            f'attachment; filename="run-with-spaces-{filename}"'
        )
    else:
        assert "content-disposition" not in response.headers
    if suffix in {"bundle", "report"}:
        source = "evidence_bundle.zip" if suffix == "bundle" else "report.html"
        assert response.content == before[Path(source)]
    else:
        profile = "review" if suffix == "review-bundle" else "state"
        cached = (
            ctx.run_root / "_derived_bundles" / f"run-with-spaces-{profile}-bundle.zip"
        )
        assert response.content == cached.read_bytes()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert json.loads(archive.read("bundle-profile.json"))["profile"] == profile
    assert {
        p.relative_to(run_dir): p.read_bytes()
        for p in run_dir.rglob("*")
        if p.is_file()
    } == before
    assert (HOSTED_DEMO_COOKIE_NAME in response.cookies) is hosted


@pytest.mark.parametrize("profile", ["review", "state"])
@pytest.mark.parametrize("graph", [False, True])
def test_profile_creation_is_lazy_cached_and_preserves_contents(
    tmp_path, profile, graph
):
    ctx = setup_client(tmp_path)
    run_dir = seed_run(ctx.run_root, graph=graph)
    derived = ctx.run_root / "_derived_bundles"
    assert not derived.exists()
    url = f"/api/runs/{RUN_ID}/{profile}-bundle"
    first = ctx.client.get(url)
    assert first.status_code == 200
    expected = ["config.yaml", "metrics.json", "run.json"]
    if profile == "review":
        expected += ["report.html", "manifest.sha256.json"]
        missing = ["energy.csv", "environment.lock.json"]
    else:
        expected += [
            "manifest.sha256.json",
            "artifacts/final_density.npy",
            "artifacts/final_state.npz",
        ]
        missing = []
    if graph:
        expected += ["artifacts/graph_operator.npz"]
    with zipfile.ZipFile(io.BytesIO(first.content)) as archive:
        assert archive.namelist() == ["bundle-profile.json", *expected]
        record = json.loads(archive.read("bundle-profile.json"))
        assert record["included_files"] == expected
        assert record["missing_optional_files"] == missing
        assert record["run_id"] == RUN_ID and record["schema_version"] == "1.0"
        assert record["generated_at"].endswith("+00:00")
        for name in expected:
            assert archive.read(name) == (run_dir / name).read_bytes()
    cached = derived / f"run-with-spaces-{profile}-bundle.zip"
    stamp = cached.stat().st_mtime_ns
    (run_dir / "metrics.json").write_bytes(b'{"later":true}\n')
    second = ctx.client.get(url)
    assert second.content == first.content == cached.read_bytes()
    assert cached.stat().st_mtime_ns == stamp


@pytest.mark.parametrize("suffix,name,media,filename", DELIVERY)
@pytest.mark.parametrize("run_id", ["missing", "%2e%2e"])
def test_missing_and_escaping_run_errors_are_exact(
    tmp_path, suffix, name, media, filename, run_id
):
    ctx = setup_client(tmp_path)
    # Existing parent/sibling files must not be exposed through a run identifier.
    seed_run(tmp_path, "outside")
    response = ctx.client.get(f"/api/runs/{run_id}/{suffix}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found"}
    assert_common_headers(response)
    assert not (ctx.run_root / "_derived_bundles").exists()


@pytest.mark.parametrize(
    "suffix,source,detail",
    [
        ("bundle", "evidence_bundle.zip", "Evidence bundle not found"),
        ("report", "report.html", "Run report not found"),
    ],
)
def test_missing_artifact_errors_are_exact(tmp_path, suffix, source, detail):
    ctx = setup_client(tmp_path)
    run_dir = seed_run(ctx.run_root)
    (run_dir / source).unlink()
    response = ctx.client.get(f"/api/runs/{RUN_ID}/{suffix}")
    assert response.status_code == 404 and response.json() == {"detail": detail}
    assert_common_headers(response)


@pytest.mark.parametrize("suffix,name,media,filename", DELIVERY)
@pytest.mark.parametrize("extra", [0, 1])
def test_hosted_download_ceiling_is_inclusive(
    tmp_path, monkeypatch, suffix, name, media, filename, extra
):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "32")
    ctx = setup_client(tmp_path, hosted=True)
    run_dir = seed_run(ctx.run_root)
    if suffix in {"bundle", "report"}:
        path = run_dir / (
            "evidence_bundle.zip" if suffix == "bundle" else "report.html"
        )
    else:
        profile = "review" if suffix == "review-bundle" else "state"
        path = (
            ctx.run_root / "_derived_bundles" / f"run-with-spaces-{profile}-bundle.zip"
        )
        path.parent.mkdir()
    path.write_bytes(b"x" * (32 + extra))
    response = ctx.client.get(f"/api/runs/{RUN_ID}/{suffix}")
    assert response.status_code == (413 if extra else 200)
    if extra:
        assert response.json() == {
            "detail": "Hosted demo artifact exceeds the download size cap."
        }
        assert_common_headers(response)
    else:
        assert response.content == path.read_bytes()
        assert_common_headers(response, preview=suffix == "report")


@pytest.mark.parametrize("profile", ["review", "state"])
def test_hosted_profile_is_created_before_existing_size_guard(
    tmp_path, monkeypatch, profile
):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", "1")
    ctx = setup_client(tmp_path, hosted=True)
    seed_run(ctx.run_root)
    response = ctx.client.get(f"/api/runs/{RUN_ID}/{profile}-bundle")
    assert response.status_code == 413
    cached = ctx.run_root / "_derived_bundles" / f"run-with-spaces-{profile}-bundle.zip"
    assert cached.is_file()  # Existing lazy-generation semantics, not a policy change.


def test_hosted_sessions_cannot_download_each_others_or_base_artifacts(tmp_path):
    ctx = setup_client(tmp_path, hosted=True)
    seed_run(ctx.run_root)
    seed_run(ctx.output, "base-only")
    other = TestClient(ctx.app)
    assert other.get("/robots.txt").status_code == 200
    assert (
        other.cookies[HOSTED_DEMO_COOKIE_NAME]
        != ctx.client.cookies[HOSTED_DEMO_COOKIE_NAME]
    )
    for suffix, *_ in DELIVERY:
        for run_id in (RUN_ID, "base-only"):
            response = other.get(f"/api/runs/{run_id}/{suffix}")
            assert response.status_code == 404 and response.json() == {
                "detail": "Run not found"
            }
        assert ctx.client.get(f"/api/runs/{RUN_ID}/{suffix}").status_code == 200


@pytest.mark.parametrize("suffix,name,media,filename", DELIVERY)
def test_file_range_and_unsatisfiable_range_are_preserved(
    tmp_path, suffix, name, media, filename
):
    ctx = setup_client(tmp_path)
    seed_run(ctx.run_root)
    url = f"/api/runs/{RUN_ID}/{suffix}"
    full = ctx.client.get(url)
    partial = ctx.client.get(url, headers={"Range": "bytes=0-3"})
    assert partial.status_code == 206 and partial.content == full.content[:4]
    assert partial.headers["content-range"] == f"bytes 0-3/{len(full.content)}"
    assert partial.headers["content-type"] == media
    assert_common_headers(partial, preview=suffix == "report")
    invalid = ctx.client.get(url, headers={"Range": "bytes=999999-"})
    assert invalid.status_code == 416
    assert invalid.headers["content-range"] == f"bytes */{len(full.content)}"
    assert_common_headers(invalid)


def delivery_routes(app):
    paths = {f"/api/runs/{{run_id}}/{suffix}" for suffix, *_ in DELIVERY}
    return [route for route in app.routes if getattr(route, "path", None) in paths]


def test_route_order_names_dependencies_and_openapi_are_preserved(tmp_path):
    ctx = setup_client(tmp_path)
    routes = delivery_routes(ctx.app)
    assert [(r.path, r.name, r.methods) for r in routes] == [
        (f"/api/runs/{{run_id}}/{suffix}", name, {"GET"})
        for suffix, name, *_ in DELIVERY
    ]
    route_order = [getattr(route, "path", None) for route in ctx.app.routes]
    first = route_order.index("/api/runs/{run_id}/bundle")
    assert route_order[first - 1] == "/api/runs/{run_id}/replay"
    assert route_order[first + 4] == "/api/experiments/{experiment_id}/bundle"
    dependencies = [r.dependant.dependencies[0] for r in routes]
    assert all(
        d.name == "active_service" and d.call is dependencies[0].call
        for d in dependencies
    )
    schema = ctx.app.openapi()
    for suffix, name, *_ in DELIVERY:
        operation = schema["paths"][f"/api/runs/{{run_id}}/{suffix}"]["get"]
        assert (
            operation["operationId"]
            == f"{name}_api_runs__run_id__{suffix.replace('-', '_')}_get"
        )
        assert operation["parameters"] == [
            {
                "name": "run_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "title": "Run Id"},
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
                        "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                    }
                },
            },
        }


@pytest.mark.parametrize("suffix,name,media,filename", DELIVERY)
def test_existing_dependency_override_and_guard_order_are_preserved(
    tmp_path, suffix, name, media, filename
):
    ctx = setup_client(tmp_path)
    path = tmp_path / "injected.html"
    path.write_bytes(b"synthetic dependency override")
    calls = []

    def locate(*args):
        calls.append(("resolve", *args))
        return path

    def guard(value):
        calls.append(("guard", value))

    injected = SimpleNamespace(
        bundle_path=locate,
        report_path=locate,
        run_bundle_profile_path=locate,
        assert_hosted_download_allowed=guard,
    )
    dependency = delivery_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: injected
    response = ctx.client.get(f"/api/runs/{RUN_ID}/{suffix}")
    assert response.status_code == 200 and response.content == path.read_bytes()
    args = (
        (RUN_ID, suffix.split("-")[0])
        if suffix in {"review-bundle", "state-bundle"}
        else (RUN_ID,)
    )
    assert calls == [("resolve", *args), ("guard", path)]


def test_unexpected_artifact_failure_remains_sanitized(tmp_path):
    ctx = setup_client(tmp_path)

    def broken(_run_id):
        raise RuntimeError("private/path <script>not a public error</script>")

    dependency = delivery_routes(ctx.app)[0].dependant.dependencies[0].call
    ctx.app.dependency_overrides[dependency] = lambda: SimpleNamespace(
        bundle_path=broken
    )
    response = ctx.client.get("/api/runs/any/bundle")
    assert response.status_code == 500
    assert response.json() == {"detail": GENERIC_COCKPIT_ERROR_DETAIL}
    assert "private/path" not in response.text and "<script>" not in response.text
