from __future__ import annotations

from pathlib import Path


def package_root() -> Path:
    return Path(__file__).resolve().parent


def bundled_assets_root() -> Path:
    return package_root() / "assets"


def _is_repo_candidate(root: Path) -> bool:
    has_repo_marker = (root / ".git").exists() or (root / "pyproject.toml").exists()
    has_project_shape = (root / "src" / "qs_dmss").exists()
    return has_repo_marker and has_project_shape


def discover_repo_root(start_path: Path | None = None) -> Path:
    candidate = (start_path or Path.cwd()).resolve()
    search_roots = [candidate, *candidate.parents]
    for root in search_roots:
        if _is_repo_candidate(root):
            return root
    return candidate


def configs_root(repo_root: Path) -> Path:
    repo_configs = repo_root / "configs"
    if repo_configs.exists():
        return repo_configs
    bundled_configs = bundled_assets_root() / "configs"
    if bundled_configs.exists():
        return bundled_configs
    return repo_configs


def schemas_root(repo_root: Path) -> Path:
    repo_schemas = repo_root / "schemas"
    if repo_schemas.exists():
        return repo_schemas
    bundled_schemas = bundled_assets_root() / "schemas"
    if bundled_schemas.exists():
        return bundled_schemas
    return repo_schemas


def demo_config_path(repo_root: Path | None = None) -> Path:
    root = repo_root or discover_repo_root()
    path = configs_root(root) / "demo.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Bundled demo config not found at {path}")
    return path


def runs_root(repo_root: Path) -> Path:
    return repo_root / "runs"


def experiments_root(
    repo_root: Path,
    output_root: Path | None = None,
) -> Path:
    if output_root is not None:
        return output_root.resolve().parent / "experiments"
    return repo_root / "experiments"
