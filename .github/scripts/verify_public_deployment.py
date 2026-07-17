from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any


COMMON_SECURITY_HEADERS = (
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "strict-transport-security",
)
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


def _fetch_json(
    url: str,
    expected_commit: str,
) -> tuple[dict[str, Any], Mapping[str, str]]:
    separator = "&" if "?" in url else "?"
    cache_busted_url = (
        f"{url}{separator}expected_commit="
        f"{urllib.parse.quote(expected_commit, safe='')}"
    )
    request = urllib.request.Request(
        cache_busted_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "QS-DMSS-deployment-verifier/1",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
        headers = {name.lower(): value for name, value in response.headers.items()}
    if not isinstance(payload, dict):
        raise ValueError(f"{url} did not return a JSON object")
    return payload, headers


def _require_security_headers(
    headers: Mapping[str, str],
    *,
    require_permissions_policy: bool,
) -> None:
    required = list(COMMON_SECURITY_HEADERS)
    if require_permissions_policy:
        required.append("permissions-policy")
    missing = [name for name in required if not headers.get(name)]
    if missing:
        raise ValueError(f"missing security headers: {', '.join(missing)}")


def _deployment_field(payload: Mapping[str, Any], field: str) -> str | None:
    deployment = payload.get("deployment")
    if not isinstance(deployment, dict):
        return None
    value = deployment.get(field)
    return value if isinstance(value, str) else None


def verify_once(
    *,
    portal_url: str,
    app_health_url: str,
    expected_commit: str,
    expected_version: str,
) -> None:
    portal, portal_headers = _fetch_json(portal_url, expected_commit)
    app, app_headers = _fetch_json(app_health_url, expected_commit)

    _require_security_headers(portal_headers, require_permissions_policy=True)
    _require_security_headers(app_headers, require_permissions_policy=False)

    if portal.get("version") != expected_version:
        raise ValueError(
            f"portal version {portal.get('version')!r} != {expected_version!r}"
        )
    if app.get("version") != expected_version:
        raise ValueError(f"app version {app.get('version')!r} != {expected_version!r}")
    if app.get("status") != "ok":
        raise ValueError(f"app status is {app.get('status')!r}, expected 'ok'")

    if _deployment_field(portal, "provider") != "render":
        raise ValueError("portal provenance provider is not 'render'")
    if _deployment_field(app, "provider") != "render":
        raise ValueError("app provenance provider is not 'render'")
    if _deployment_field(portal, "git_branch") != "main":
        raise ValueError("portal provenance branch is not 'main'")
    if _deployment_field(app, "git_branch") != "main":
        raise ValueError("app provenance branch is not 'main'")

    portal_commit = _deployment_field(portal, "git_commit")
    app_commit = _deployment_field(app, "git_commit")
    if portal_commit != expected_commit:
        raise ValueError(
            f"portal commit {portal_commit!r} != expected {expected_commit!r}"
        )
    if app_commit != expected_commit:
        raise ValueError(f"app commit {app_commit!r} != expected {expected_commit!r}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wait for both public QS-DMSS surfaces to deploy one Git commit."
    )
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument(
        "--portal-url",
        default="https://qs-dmss.studio/deployment.json",
    )
    parser.add_argument(
        "--app-health-url",
        default="https://app.qs-dmss.studio/api/health",
    )
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument("--interval-seconds", type=int, default=20)
    args = parser.parse_args()

    expected_commit = args.expected_commit.strip().lower()
    if not COMMIT_PATTERN.fullmatch(expected_commit):
        parser.error("--expected-commit must be a full 40-character hexadecimal SHA")
    if args.timeout_seconds < 1 or args.interval_seconds < 1:
        parser.error("timeout and interval must be positive")

    deadline = time.monotonic() + args.timeout_seconds
    attempt = 0
    last_error = "verification did not run"
    while time.monotonic() < deadline:
        attempt += 1
        try:
            verify_once(
                portal_url=args.portal_url,
                app_health_url=args.app_health_url,
                expected_commit=expected_commit,
                expected_version=args.expected_version,
            )
        except (ValueError, OSError, urllib.error.HTTPError) as exc:
            last_error = str(exc)
            print(f"Attempt {attempt}: deployment not converged ({last_error})")
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(args.interval_seconds, remaining))
            continue
        print(
            "Verified portal and app deployment: "
            f"version={args.expected_version} commit={expected_commit}"
        )
        return
    raise SystemExit(
        f"Deployment did not converge within {args.timeout_seconds}s: {last_error}"
    )


if __name__ == "__main__":
    main()
