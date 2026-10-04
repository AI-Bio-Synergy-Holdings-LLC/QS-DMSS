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
MAX_REPORT_BYTES = 4 * 1024 * 1024
MAX_REPORT_CSP_BYTES = 8 * 1024


def _csp_hash(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(digest).decode("ascii") + "'"


def report_preview_headers(path: Path, baseline: dict[str, str]) -> dict[str, str]:
    # Avoid unbounded reads of locally modified files. Oversized previews keep
    # inline styles blocked, as do invalid UTF-8 reports. External framing is denied.
    with path.open("rb") as handle:
        payload = handle.read(MAX_REPORT_BYTES + 1)
    text = None
    if len(payload) <= MAX_REPORT_BYTES:
        try:
            text = payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError:
            pass  # Serve unchanged bytes without authorizing artifact styles.
    policy = baseline["Content-Security-Policy"].replace(
        "frame-ancestors 'none'", "frame-ancestors 'self'"
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
    # Budget the complete CSP value, including baseline and fixed script hashes.
    # Preserve the trusted baseline even if it is already larger than the budget;
    # artifact styles must never increase an oversized policy or be partly admitted.
    policy_bytes = len(policy.encode("utf-8"))
    styles: list[str] = []
    seen: set[str] = set()
    if text is not None and policy_bytes < MAX_REPORT_CSP_BYTES:
        for match in STYLE_BLOCK.finditer(text):
            style = _csp_hash(match.group(1))
            if style in seen:
                continue
            policy_bytes += 1 + len(style)  # Hash tokens are ASCII; one separator.
            if policy_bytes > MAX_REPORT_CSP_BYTES:
                styles = []
                break
            seen.add(style)
            styles.append(style)
    if styles:
        policy = policy.replace(
            "style-src 'self'", "style-src 'self' " + " ".join(styles)
        )
    return {"Content-Security-Policy": policy, "X-Frame-Options": "SAMEORIGIN"}
