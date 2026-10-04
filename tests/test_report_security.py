from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qs_dmss.cockpit.api import BASELINE_SECURITY_HEADERS, create_app
from qs_dmss.evidence import html_security
from qs_dmss.evidence.html_security import (
    LEGACY_WORKBOOK_TABS_SCRIPT,
    WORKBOOK_TABS_SCRIPT,
    report_preview_headers,
)


def _hash(text):
    return "sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode()


def _directive(policy, name):
    return next(part.strip() for part in policy.split(";") if part.strip().startswith(name))


def test_report_csp_only_allows_same_origin_and_exact_styles_and_fixed_script(tmp_path):
    path = tmp_path / "report.html"
    style = "\nbody { color: #173d37; }\n"
    malicious = "alert('untrusted metadata')"
    path.write_bytes(
        (f"<style>{style}</style><script>{malicious}</script>")
        .replace("\n", "\r\n")
        .encode()
    )
    headers = report_preview_headers(path, BASELINE_SECURITY_HEADERS)
    assert headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in headers["Content-Security-Policy"]
    assert _hash(style) in headers["Content-Security-Policy"]
    assert _hash(WORKBOOK_TABS_SCRIPT) in headers["Content-Security-Policy"]
    assert _hash(LEGACY_WORKBOOK_TABS_SCRIPT) in headers["Content-Security-Policy"]
    assert _hash(malicious) not in headers["Content-Security-Policy"]
    assert "unsafe-inline" not in headers["Content-Security-Policy"]
    assert "unsafe-hashes" not in headers["Content-Security-Policy"]
    assert BASELINE_SECURITY_HEADERS["X-Frame-Options"] == "DENY"


def test_oversized_report_never_authorizes_arbitrary_inline_content(tmp_path):
    path = tmp_path / "report.html"
    path.write_bytes(b"<style>body{color:red}</style>" + b" " * (4 * 1024 * 1024))
    headers = report_preview_headers(path, BASELINE_SECURITY_HEADERS)
    assert _hash("body{color:red}") not in headers["Content-Security-Policy"]


@pytest.mark.parametrize("invalid", [b"\xff", b"\xc3", b"\x80"])
def test_invalid_utf8_never_authorizes_any_artifact_inline_content(tmp_path, invalid):
    path = tmp_path / "report.html"
    style = "body{color:red}"
    script = "alert('untrusted metadata')"
    payload = f"<style>{style}</style><script>{script}</script>".encode() + invalid
    path.write_bytes(payload)
    headers = report_preview_headers(path, BASELINE_SECURITY_HEADERS)
    policy = headers["Content-Security-Policy"]
    assert _directive(policy, "style-src") == _directive(
        BASELINE_SECURITY_HEADERS["Content-Security-Policy"], "style-src"
    )
    assert _hash(style) not in policy
    assert _hash(script) not in policy
    assert _hash(WORKBOOK_TABS_SCRIPT) in policy
    assert _hash(LEGACY_WORKBOOK_TABS_SCRIPT) in policy
    assert "unsafe-inline" not in policy
    assert "unsafe-hashes" not in policy
    assert "frame-ancestors 'self'" in policy
    assert headers["X-Frame-Options"] == "SAMEORIGIN"
    assert path.read_bytes() == payload
    assert BASELINE_SECURITY_HEADERS["X-Frame-Options"] == "DENY"


@pytest.mark.parametrize(
    "kind,filename,route",
    [
        ("runs", "report.html", "/api/runs/report-test/report"),
        ("experiments", "report.html", "/api/experiments/report-test/report"),
        ("experiments", "workbook.html", "/api/experiments/report-test/workbook"),
    ],
)
def test_invalid_utf8_report_http_keeps_bytes_and_fail_closed_headers(
    tmp_path, kind, filename, route
):
    root = tmp_path / kind / "report-test"
    root.mkdir(parents=True)
    record = "run.json" if kind == "runs" else "experiment.json"
    (root / record).write_text("{}", encoding="utf-8")
    payload = b"<style>body{color:red}</style><script>alert(1)</script>\xff"
    path = root / filename
    path.write_bytes(payload)
    client = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=tmp_path / "runs",
            hosted_demo=False,
        )
    )
    response = client.get(route)
    assert response.status_code == 200
    assert response.content == payload
    assert _directive(response.headers["content-security-policy"], "style-src") == (
        _directive(BASELINE_SECURITY_HEADERS["Content-Security-Policy"], "style-src")
    )
    assert _hash("body{color:red}") not in response.headers["content-security-policy"]
    assert _hash("alert(1)") not in response.headers["content-security-policy"]
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert path.read_bytes() == payload


def test_report_style_hashes_are_deduplicated_in_first_seen_order(tmp_path):
    path = tmp_path / "report.html"
    styles = ["body{color:red}", "p{color:blue}", "body{color:red}"]
    payload = "".join(f"<style>{style}</style>" for style in styles).encode()
    path.write_bytes(payload)
    policy = report_preview_headers(path, BASELINE_SECURITY_HEADERS)[
        "Content-Security-Policy"
    ]
    admitted = [
        token
        for token in _directive(policy, "style-src").split()
        if token.startswith("'sha256-")
    ]
    assert admitted == [f"'{_hash(style)}'" for style in styles[:2]]
    assert len(policy.encode()) <= 8 * 1024
    assert path.read_bytes() == payload


def test_four_mib_repeated_styles_do_not_amplify_csp(tmp_path):
    path = tmp_path / "report.html"
    payload = b"<style>x</style>" * 262144
    assert len(payload) == 4 * 1024 * 1024
    path.write_bytes(payload)
    policy = report_preview_headers(path, BASELINE_SECURITY_HEADERS)[
        "Content-Security-Policy"
    ]
    assert _directive(policy, "style-src").count(_hash("x")) == 1
    assert len(policy.encode()) <= 8 * 1024
    assert path.read_bytes() == payload


def test_distinct_styles_exceeding_budget_fail_closed_and_stop_hashing(
    tmp_path, monkeypatch
):
    path = tmp_path / "report.html"
    payload = b"".join(
        f"<style>/*{index}*/</style>".encode() for index in range(4096)
    )
    path.write_bytes(payload)
    empty = tmp_path / "empty.html"
    empty.write_bytes(b"")
    expected = report_preview_headers(empty, BASELINE_SECURITY_HEADERS)
    real_hash = html_security._csp_hash
    calls = []

    def counted_hash(content):
        calls.append(content)
        return real_hash(content)

    monkeypatch.setattr(html_security, "_csp_hash", counted_hash)
    headers = report_preview_headers(path, BASELINE_SECURITY_HEADERS)
    assert headers == expected  # No partial artifact-style allowlist.
    assert len(headers["Content-Security-Policy"].encode()) <= 8 * 1024
    token_bytes = len((" " + real_hash("/*0*/")).encode())
    remaining = 8 * 1024 - len(expected["Content-Security-Policy"].encode())
    # Two fixed script hashes plus only enough unique styles to detect overflow.
    assert len(calls) <= 2 + remaining // token_bytes + 1
    assert path.read_bytes() == payload


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_csp_budget_counts_baseline_and_fixed_scripts_at_byte_boundary(tmp_path, offset):
    empty = tmp_path / "empty.html"
    empty.write_bytes(b"")
    style = "body{color:red}"
    path = tmp_path / "report.html"
    payload = f"<style>{style}</style>".encode()
    path.write_bytes(payload)
    baseline = dict(BASELINE_SECURITY_HEADERS)
    baseline["Content-Security-Policy"] += "; report-uri /"
    policy = report_preview_headers(empty, baseline)["Content-Security-Policy"]
    token_bytes = len((" '" + _hash(style) + "'").encode())
    padding = 8 * 1024 - token_bytes - len(policy.encode()) + offset
    baseline["Content-Security-Policy"] += "a" * padding
    expected = report_preview_headers(empty, baseline)
    headers = report_preview_headers(path, baseline)
    policy = headers["Content-Security-Policy"]
    if offset <= 0:
        assert _hash(style) in _directive(policy, "style-src")
        assert len(policy.encode()) == 8 * 1024 + offset
    else:
        assert headers == expected
    assert _hash(WORKBOOK_TABS_SCRIPT) in policy
    assert _hash(LEGACY_WORKBOOK_TABS_SCRIPT) in policy
    assert path.read_bytes() == payload


def test_already_large_trusted_baseline_is_preserved_without_artifact_hashes(tmp_path):
    empty = tmp_path / "empty.html"
    empty.write_bytes(b"")
    path = tmp_path / "report.html"
    path.write_bytes(b"<style>body{color:red}</style>")
    baseline = dict(BASELINE_SECURITY_HEADERS)
    baseline["Content-Security-Policy"] += "; report-uri /" + "a" * (8 * 1024)
    expected = report_preview_headers(empty, baseline)
    assert report_preview_headers(path, baseline) == expected
    assert baseline["X-Frame-Options"] == "DENY"


@pytest.mark.parametrize("repeated", [False, True])
@pytest.mark.parametrize(
    "kind,filename,route",
    [
        ("runs", "report.html", "/api/runs/report-test/report"),
        ("experiments", "report.html", "/api/experiments/report-test/report"),
        ("experiments", "workbook.html", "/api/experiments/report-test/workbook"),
    ],
)
def test_style_heavy_report_http_keeps_bytes_and_bounded_fail_closed_headers(
    tmp_path, kind, filename, route, repeated
):
    root = tmp_path / kind / "report-test"
    root.mkdir(parents=True)
    record = "run.json" if kind == "runs" else "experiment.json"
    (root / record).write_text("{}", encoding="utf-8")
    payload = (
        b"<style>x</style>" * 262144
        if repeated
        else b"".join(f"<style>/*{i}*/</style>".encode() for i in range(4096))
    )
    path = root / filename
    path.write_bytes(payload)
    client = TestClient(
        create_app(
            repo_root=Path(__file__).resolve().parents[1],
            output_root=tmp_path / "runs",
            hosted_demo=False,
        )
    )
    response = client.get(route)
    assert response.status_code == 200
    assert response.content == payload
    policy = response.headers["content-security-policy"]
    assert len(policy.encode()) <= 8 * 1024
    if repeated:
        assert _directive(policy, "style-src").count(_hash("x")) == 1
    else:
        assert _directive(policy, "style-src") == _directive(
            BASELINE_SECURITY_HEADERS["Content-Security-Policy"], "style-src"
        )
    assert _hash(WORKBOOK_TABS_SCRIPT) in policy
    assert _hash(LEGACY_WORKBOOK_TABS_SCRIPT) in policy
    assert "unsafe-inline" not in policy
    assert "unsafe-hashes" not in policy
    assert "frame-ancestors 'self'" in policy
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert path.read_bytes() == payload
