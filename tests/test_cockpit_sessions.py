"""Hosted-session continuity contracts, with deterministic entropy and synthetic files."""

from __future__ import annotations

import base64
import io
import json
import zipfile
from http.cookies import SimpleCookie
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qs_dmss.cockpit import api

ROOT = Path(__file__).resolve().parents[1]
COOKIE = api.HOSTED_DEMO_COOKIE_NAME
BOUNDARIES = (
    pytest.param(b"\xf8" + bytes(17), id="leading-hyphen"),
    pytest.param(bytes(17) + b"\x3e", id="trailing-hyphen"),
    pytest.param(b"\xf8" + bytes(16) + b"\x3e", id="both-hyphens"),
)
DELIVERIES = ("bundle", "review-bundle", "state-bundle", "report")


def entropy_sequence(monkeypatch, values):
    values = iter(values)
    calls = []

    def token_bytes(size):
        calls.append(size)
        assert size == 18, "Session entropy must retain the original 18-byte budget"
        try:
            value = next(values)
        except StopIteration:
            pytest.fail("Unexpected session rotation or entropy retry")
        assert len(value) == size
        return value

    monkeypatch.setattr(api.secrets, "token_bytes", token_bytes)
    return calls


def client_for(app, cookie=None):
    client = TestClient(app)
    if cookie is not None:
        client.cookies.set(COOKIE, cookie, domain="testserver.local", path="/")
    return client


def seed_artifacts(output, session_id=None, *, run_id="synthetic", marker="one"):
    root = output if session_id is None else output / "sessions" / session_id / "runs"
    run = root / run_id
    run.mkdir(parents=True)
    (run / "run.json").write_bytes(b"{}\n")
    (run / "metrics.json").write_text(
        json.dumps({"synthetic_marker": marker}) + "\n", encoding="utf-8"
    )
    (run / "config.yaml").write_bytes(b"# synthetic transport fixture\n")
    (run / "report.html").write_text(
        f"<!doctype html><h1>{marker}</h1>", encoding="utf-8"
    )
    with zipfile.ZipFile(run / "evidence_bundle.zip", "w") as archive:
        archive.writestr("synthetic.txt", marker)
    return run


@pytest.mark.parametrize(
    "raw",
    [
        *BOUNDARIES,
        pytest.param(b"\xff" * 18, id="underscores"),
        pytest.param(bytes(18), id="ordinary"),
    ],
)
def test_generated_ids_always_validate_and_retain_all_entropy(monkeypatch, raw):
    calls = entropy_sequence(monkeypatch, [raw])
    token = api._new_hosted_demo_session_id()
    assert api._is_valid_hosted_demo_session_id(token)
    # Both the legacy base64 encoding and a full hex encoding are lossless.
    # Trimming, replacing or discarding boundary characters is not acceptable.
    decoded = (
        bytes.fromhex(token) if len(token) == 36 else base64.urlsafe_b64decode(token)
    )
    assert decoded == raw
    assert calls == [18]


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        ("", False),
        ("a" * 15, False),
        ("a" * 16, True),
        ("a" * 64, True),
        ("a" * 65, False),
        ("-" + "a" * 23, False),
        ("a" * 23 + "-", False),
        ("." + "a" * 23, False),
        ("a" * 23 + ".", False),
        ("legacy_AbCd0123-xyz_token", True),
        ("_" * 24, True),
        ("a.b_c-d" + "0" * 12, True),
        ("../" + "a" * 24, False),
        ("a" * 12 + "/" + "b" * 12, False),
        ("a" * 12 + "\\" + "b" * 12, False),
        (" " + "a" * 24, False),
        ("a" * 23 + "é", False),
    ],
)
def test_existing_cookie_validation_contract_is_unchanged(value, expected):
    assert api._is_valid_hosted_demo_session_id(value) is expected


@pytest.mark.parametrize("raw", BOUNDARIES)
def test_first_response_cookie_matches_request_scoped_service(
    tmp_path, monkeypatch, raw
):
    calls = entropy_sequence(monkeypatch, [raw, b"\x01" * 18, b"\x02" * 18])
    output = tmp_path / "runs"
    app = api.create_app(repo_root=ROOT, output_root=output, hosted_demo=True)
    with client_for(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        cookie = client.cookies[COOKIE]
        service_session = response.json()["hosted_demo"]["session_id"]
        assert cookie == service_session
        assert api._is_valid_hosted_demo_session_id(cookie)
        assert (output / "sessions" / cookie / "runs").is_dir()
        assert response.cookies[COOKIE] == cookie
        assert calls == [18]


@pytest.mark.parametrize("raw", BOUNDARIES)
def test_generated_session_retains_artifact_access_across_requests(
    tmp_path, monkeypatch, raw
):
    calls = entropy_sequence(monkeypatch, [raw, b"\x01" * 18, b"\x02" * 18])
    output = tmp_path / "runs"
    app = api.create_app(repo_root=ROOT, output_root=output, hosted_demo=True)
    with client_for(app) as client:
        first = client.get("/api/health")
        assert first.status_code == 200
        session = first.json()["hosted_demo"]["session_id"]
        run = seed_artifacts(output, session)
        original = {p.name: p.read_bytes() for p in run.iterdir()}
        for suffix in DELIVERIES:
            response = client.get(f"/api/runs/synthetic/{suffix}")
            assert response.status_code == 200, (suffix, response.text)
            assert client.cookies[COOKIE] == session
            assert response.cookies[COOKIE] == session
        assert client.get("/api/health").json()["hosted_demo"]["session_id"] == session
        assert {p.name: p.read_bytes() for p in run.iterdir()} == original
        assert calls == [18]


@pytest.mark.parametrize(
    "legacy",
    ["a" * 16, "a" * 64, "legacy_AbCd0123-xyz_token", "_" * 24, "a.b_c-d" + "0" * 12],
)
def test_valid_existing_cookies_are_not_rotated(tmp_path, monkeypatch, legacy):
    def unexpected_generation():
        pytest.fail("A valid existing cookie must be reused")

    monkeypatch.setattr(api, "_new_hosted_demo_session_id", unexpected_generation)
    output = tmp_path / "runs"
    seed_artifacts(output, legacy)
    app = api.create_app(repo_root=ROOT, output_root=output, hosted_demo=True)
    with client_for(app, legacy) as client:
        assert client.get("/api/health").json()["hosted_demo"]["session_id"] == legacy
        for suffix in DELIVERIES:
            response = client.get(f"/api/runs/synthetic/{suffix}")
            assert response.status_code == 200
            assert client.cookies[COOKIE] == legacy


@pytest.mark.parametrize(
    "invalid", ["V" * 24 + "-", "." + "V" * 24, "../" + "V" * 24, "a" * 15, "a" * 65]
)
def test_invalid_cookies_rotate_without_aliasing_existing_sessions(
    tmp_path, monkeypatch, invalid
):
    calls = entropy_sequence(monkeypatch, [bytes(18)])
    output = tmp_path / "runs"
    victim = "V" * 24
    run = seed_artifacts(output, victim)
    original = (run / "evidence_bundle.zip").read_bytes()
    seed_artifacts(output, run_id="base-only")
    app = api.create_app(repo_root=ROOT, output_root=output, hosted_demo=True)
    with client_for(app, invalid) as client:
        response = client.get("/api/runs/synthetic/bundle")
        assert response.status_code == 404 and response.json() == {
            "detail": "Run not found"
        }
        new_session = client.cookies[COOKIE]
        assert api._is_valid_hosted_demo_session_id(new_session)
        assert new_session not in (invalid, victim)
        for run_id in ("synthetic", "base-only"):
            for suffix in DELIVERIES:
                assert client.get(f"/api/runs/{run_id}/{suffix}").status_code == 404
        assert (run / "evidence_bundle.zip").read_bytes() == original
        assert calls == [18]


def test_two_fresh_clients_remain_isolated_with_identical_run_names(
    tmp_path, monkeypatch
):
    calls = entropy_sequence(
        monkeypatch,
        [b"\xf8" + bytes(17), bytes(17) + b"\x3e", b"\x01" * 18, b"\x02" * 18],
    )
    output = tmp_path / "runs"
    app = api.create_app(repo_root=ROOT, output_root=output, hosted_demo=True)
    with client_for(app) as first, client_for(app) as second:
        a = first.get("/api/health").json()["hosted_demo"]["session_id"]
        b = second.get("/api/health").json()["hosted_demo"]["session_id"]
        assert first.cookies[COOKIE] == a and second.cookies[COOKIE] == b
        assert a != b
        seed_artifacts(output, a, marker="first")
        for suffix in DELIVERIES:
            assert second.get(f"/api/runs/synthetic/{suffix}").status_code == 404
        seed_artifacts(output, b, marker="second")
        for suffix in DELIVERIES:
            left = first.get(f"/api/runs/synthetic/{suffix}")
            right = second.get(f"/api/runs/synthetic/{suffix}")
            assert left.status_code == right.status_code == 200
            assert left.content != right.content
        with zipfile.ZipFile(
            io.BytesIO(first.get("/api/runs/synthetic/bundle").content)
        ) as archive:
            assert archive.read("synthetic.txt") == b"first"
        assert calls == [18, 18]


def test_cookie_attributes_ttl_and_resource_caps_are_preserved(tmp_path, monkeypatch):
    entropy_sequence(monkeypatch, [bytes(18)])
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO_TTL_SECONDS", "197")
    app = api.create_app(
        repo_root=ROOT, output_root=tmp_path / "runs", hosted_demo=True
    )
    with client_for(app) as client:
        response = client.get("/api/health")
        cookie = SimpleCookie(response.headers["set-cookie"])[COOKIE]
        assert cookie.value == response.json()["hosted_demo"]["session_id"]
        assert cookie["max-age"] == "197" and cookie["path"] == "/"
        assert cookie["httponly"] is True and cookie["samesite"] == "lax"
        assert not cookie["secure"]  # Existing cookie policy is not changed here.
        public = response.json()["hosted_demo"]
        for key, expected in {
            "session_ttl_seconds": 197,
            "max_campaign_runs": 5,
            "max_engine_steps": 12,
            "max_total_engine_steps": 60,
            "max_grid_cells": 4096,
            "max_artifact_bytes": 10 * 1024 * 1024,
            "one_active_job_per_session": True,
        }.items():
            assert public[key] == expected


def test_local_mode_does_not_generate_or_accept_hosted_sessions(tmp_path, monkeypatch):
    def unexpected_generation():
        pytest.fail("Local-only mode must not generate hosted sessions")

    monkeypatch.setattr(api, "_new_hosted_demo_session_id", unexpected_generation)
    output = tmp_path / "runs"
    seed_artifacts(output)
    app = api.create_app(repo_root=ROOT, output_root=output, hosted_demo=False)
    with client_for(app, "legacy_AbCd0123-xyz_token") as client:
        health = client.get("/api/health")
        assert health.json()["hosted_demo"]["session_id"] is None
        assert health.json()["hosted_demo"]["enabled"] is False
        for suffix in DELIVERIES:
            response = client.get(f"/api/runs/synthetic/{suffix}")
            assert response.status_code == 200 and COOKIE not in response.cookies
        assert not (output / "sessions").exists()
