from __future__ import annotations

import os
import re
from collections.abc import Mapping


_GIT_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
_GIT_BRANCH_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,254}")


def _validated_git_commit(value: str | None) -> str | None:
    candidate = (value or "").strip().lower()
    return candidate if _GIT_COMMIT_PATTERN.fullmatch(candidate) else None


def _validated_git_branch(value: str | None) -> str | None:
    candidate = (value or "").strip()
    return candidate if _GIT_BRANCH_PATTERN.fullmatch(candidate) else None


def public_deployment_provenance(
    environ: Mapping[str, str] | None = None,
) -> dict[str, str | None]:
    """Return public, path-free deployment identity for health responses."""

    values = os.environ if environ is None else environ
    is_render = values.get("RENDER", "").lower() == "true"
    return {
        "provider": "render" if is_render else "local",
        "git_commit": (
            _validated_git_commit(values.get("RENDER_GIT_COMMIT"))
            if is_render
            else None
        ),
        "git_branch": (
            _validated_git_branch(values.get("RENDER_GIT_BRANCH"))
            if is_render
            else None
        ),
    }
