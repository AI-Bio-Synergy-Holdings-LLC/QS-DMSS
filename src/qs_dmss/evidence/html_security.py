"""Narrow CSP for generated same-origin report previews."""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

# Keep the prior fixed tab script admitted for immutable historical workbooks.
LEGACY_WORKBOOK_TABS_SCRIPT = (
    "const tabs=[...document.querySelectorAll('[role=tab]')];"
    "tabs.forEach(tab=>tab.addEventListener('click',()=>{tabs.forEach(item=>{"
    "const selected=item===tab;item.setAttribute('aria-selected',String(selected));"
    "document.getElementById(item.getAttribute('aria-controls')).hidden=!selected;"
    "});}));"
)
WORKBOOK_TABS_SCRIPT = (
    LEGACY_WORKBOOK_TABS_SCRIPT
    + "document.getElementById('workbook-print')?.addEventListener('click',()=>window.print());"
)
STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.IGNORECASE | re.DOTALL)


def _csp_hash(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(digest).decode("ascii") + "'"


def report_preview_headers(path: Path, baseline: dict[str, str]) -> dict[str, str]:
    # Avoid unbounded reads of locally modified files. Oversized previews keep
    # inline styles blocked, as do invalid UTF-8 reports. External framing is denied.
    with path.open("rb") as handle:
        payload = handle.read(4 * 1024 * 1024 + 1)
    styles = []
    if len(payload) <= 4 * 1024 * 1024:
        try:
            text = payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError:
            text = None  # Serve unchanged bytes without authorizing artifact styles.
        if text is not None:
            styles = [_csp_hash(style) for style in STYLE_BLOCK.findall(text)]
    policy = baseline["Content-Security-Policy"].replace(
        "frame-ancestors 'none'", "frame-ancestors 'self'"
    )
    if styles:
        policy = policy.replace(
            "style-src 'self'", "style-src 'self' " + " ".join(styles)
        )
    # Never hash and authorize arbitrary scripts from the artifact contents.
    policy = policy.replace(
        "script-src 'self'",
        "script-src 'self' "
        + " ".join(
            _csp_hash(script)
            for script in (WORKBOOK_TABS_SCRIPT, LEGACY_WORKBOOK_TABS_SCRIPT)
        ),
    )
    return {"Content-Security-Policy": policy, "X-Frame-Options": "SAMEORIGIN"}
