"""Narrow CSP for generated same-origin report previews."""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

# The only inline script admitted is this fixed, core-owned workbook tab control.
WORKBOOK_TABS_SCRIPT = (
    "const tabs=[...document.querySelectorAll('[role=tab]')];"
    "tabs.forEach(tab=>tab.addEventListener('click',()=>{tabs.forEach(item=>{"
    "const selected=item===tab;item.setAttribute('aria-selected',String(selected));"
    "document.getElementById(item.getAttribute('aria-controls')).hidden=!selected;"
    "});}));"
)
STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.IGNORECASE | re.DOTALL)


def _csp_hash(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(digest).decode("ascii") + "'"


def report_preview_headers(path: Path, baseline: dict[str, str]) -> dict[str, str]:
    # Avoid unbounded reads of locally modified files. Oversized previews keep
    # inline styles blocked; external framing is always denied.
    with path.open("rb") as handle:
        payload = handle.read(4 * 1024 * 1024 + 1)
    styles = []
    if len(payload) <= 4 * 1024 * 1024:
        text = payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
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
        "script-src 'self'", "script-src 'self' " + _csp_hash(WORKBOOK_TABS_SCRIPT)
    )
    return {"Content-Security-Policy": policy, "X-Frame-Options": "SAMEORIGIN"}
