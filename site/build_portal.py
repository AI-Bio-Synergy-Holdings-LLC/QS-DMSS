from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parent
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
BRANCH_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,254}")
VERSION_PATTERN = re.compile(
    r'<meta\s+name="application-version"\s+content="([^"]+)"\s*/?>'
)


def _git_value(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=SITE_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _portal_version() -> str:
    index = (SITE_ROOT / "index.html").read_text(encoding="utf-8")
    match = VERSION_PATTERN.search(index)
    if not match:
        raise RuntimeError("site/index.html is missing application-version metadata")
    return match.group(1)


def _deployment_identity() -> tuple[str, str, str]:
    is_render = os.environ.get("RENDER", "").lower() == "true"
    provider = "render" if is_render else "local"
    commit = (
        os.environ.get("RENDER_GIT_COMMIT")
        if is_render
        else _git_value("rev-parse", "HEAD")
    )
    branch = (
        os.environ.get("RENDER_GIT_BRANCH")
        if is_render
        else _git_value("branch", "--show-current")
    )
    normalized_commit = (commit or "").strip().lower()
    normalized_branch = (branch or "").strip()
    if not COMMIT_PATTERN.fullmatch(normalized_commit):
        raise RuntimeError("a full 40-character Git commit is required")
    if not BRANCH_PATTERN.fullmatch(normalized_branch):
        raise RuntimeError("a valid Git branch is required")
    return provider, normalized_commit, normalized_branch


def build_deployment_metadata(output_path: Path) -> dict[str, object]:
    provider, commit, branch = _deployment_identity()
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload: dict[str, object] = {
        "schema_version": 1,
        "service": "qs-dmss-studio-portal",
        "version": _portal_version(),
        "deployment": {
            "provider": provider,
            "git_commit": commit,
            "git_branch": branch,
            "generated_at": generated_at,
        },
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate public QS-DMSS portal deployment provenance."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=SITE_ROOT / "deployment.json",
        help="Output path (default: site/deployment.json)",
    )
    args = parser.parse_args()
    payload = build_deployment_metadata(args.output)
    deployment = payload["deployment"]
    assert isinstance(deployment, dict)
    print(
        "Generated portal provenance for "
        f"{deployment['git_commit']} at {args.output}"
    )


if __name__ == "__main__":
    main()
