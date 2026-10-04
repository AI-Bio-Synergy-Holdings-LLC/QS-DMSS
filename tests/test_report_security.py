from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qs_dmss.cockpit.api import BASELINE_SECURITY_HEADERS, create_app
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
