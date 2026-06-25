from __future__ import annotations

import re
from pathlib import Path

_SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def package_root() -> Path:
    return Path(__file__).resolve().parent


def bundled_assets_root() -> Path:
    return package_root() / "assets"


def safe_filename(
    value: str | None,
    *,
    default: str,
    suffixes: tuple[str, ...] = (),
) -> str:
    raw_value = (value or default).strip().replace("\\", "/")
    leaf_name = raw_value.rsplit("/", 1)[-1]
    sanitized = _SAFE_FILENAME_PATTERN.sub("-", leaf_name).strip(".-")
    if not sanitized:
        sanitized = default
    if suffixes and not sanitized.endswith(suffixes):
        sanitized = f"{sanitized}{suffixes[0]}"
    return sanitized


def contained_path(base_dir: Path, *parts: str | Path) -> Path:
    base_path = base_dir.resolve()
    candidate = base_path.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base_path)
    except ValueError as exc:
        raise ValueError(f"Path escapes expected root: {candidate}") from exc
    return candidate


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


def fractal_config_path(repo_root: Path | None = None) -> Path:
    root = repo_root or discover_repo_root()
    candidates = [
        configs_root(root) / "fractal_quadrant_ssfm.yaml",
        bundled_assets_root() / "configs" / "fractal_quadrant_ssfm.yaml",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Bundled Fractal SSFM config not found")


def runs_root(repo_root: Path) -> Path:
    return repo_root / "runs"


def experiments_root(
    repo_root: Path,
    output_root: Path | None = None,
) -> Path:
    if output_root is not None:
        return output_root.resolve().parent / "experiments"
    return repo_root / "experiments"
