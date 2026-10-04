from __future__ import annotations

import base64
import hashlib

from qs_dmss.cockpit.api import BASELINE_SECURITY_HEADERS
from qs_dmss.evidence.html_security import (
    LEGACY_WORKBOOK_TABS_SCRIPT,
    WORKBOOK_TABS_SCRIPT,
    report_preview_headers,
)


def _hash(text):
    return "sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode()


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
