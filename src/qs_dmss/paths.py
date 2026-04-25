from __future__ import annotations

from pathlib import Path


def discover_repo_root(start_path: Path | None = None) -> Path:
    candidate = (start_path or Path.cwd()).resolve()
    search_roots = [candidate, *candidate.parents]
    for root in search_roots:
        if (root / ".git").exists() or (root / "pyproject.toml").exists():
            return root
    return candidate


def configs_root(repo_root: Path) -> Path:
    return repo_root / "configs"


def runs_root(repo_root: Path) -> Path:
    return repo_root / "runs"
