from __future__ import annotations

import csv
import re
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qs_dmss.io.config import SimulationConfig, config_digest


@dataclass(frozen=True)
class RunWorkspace:
    run_id: str
    run_dir: Path
    artifacts_dir: Path
    replayed_from: str | None
    repo_root: Path


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sanitize_name(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-")
    return sanitized or "run"


def _discover_repo_root(start_path: Path) -> Path:
    for candidate in [start_path, *start_path.parents]:
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return start_path


def _resolve_output_root(
    config: SimulationConfig,
    source_config_path: Path,
    repo_root: Path,
    output_root_override: Path | None,
) -> Path:
    if output_root_override is not None:
        return output_root_override.resolve()

    output_root = Path(config.run.output_root)
    if output_root.is_absolute():
        return output_root
    if repo_root.exists():
        return (repo_root / output_root).resolve()
    return (source_config_path.parent / output_root).resolve()


def prepare_run_workspace(
    config: SimulationConfig,
    source_config_path: Path,
    output_root_override: Path | None = None,
    replayed_from: str | None = None,
) -> RunWorkspace:
    repo_root = _discover_repo_root(source_config_path.resolve().parent)
    output_root = _resolve_output_root(
        config,
        source_config_path,
        repo_root,
        output_root_override,
    )
    output_root.mkdir(parents=True, exist_ok=True)

    run_id = f"{_sanitize_name(config.run.name)}-{_utc_timestamp()}-{uuid.uuid4().hex[:8]}"
    run_dir = output_root / run_id
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=False)

    return RunWorkspace(
        run_id=run_id,
        run_dir=run_dir,
        artifacts_dir=artifacts_dir,
        replayed_from=replayed_from,
        repo_root=repo_root,
    )


def _git_commit(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return completed.stdout.strip() or None


def create_run_record(
    workspace: RunWorkspace,
    config: SimulationConfig,
    source_config_path: Path,
    started_at: datetime,
    finished_at: datetime,
    elapsed_seconds: float,
    metrics: dict,
) -> dict:
    return {
        "schema_version": 1,
        "run_id": workspace.run_id,
        "name": config.run.name,
        "backend": config.engine.backend,
        "status": "completed",
        "replayed_from": workspace.replayed_from,
        "source_config_name": source_config_path.name,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "elapsed_seconds": round(elapsed_seconds, 6),
        "seed": config.run.seed,
        "config_digest": config_digest(config),
        "git_commit": _git_commit(workspace.repo_root),
        "artifacts": {
            "final_density": "artifacts/final_density.npy",
            "final_state": "artifacts/final_state.npz",
            "metrics": "metrics.json",
            "energy_history": "energy.csv",
            "environment_lock": "environment.lock.json",
            "report": "report.html",
            "manifest": "manifest.sha256.json",
            "bundle": "evidence_bundle.zip",
        },
        "summary": {
            "initial_norm": metrics["initial_norm"],
            "final_norm": metrics["final_norm"],
            "norm_drift": metrics["norm_drift"],
            "initial_energy": metrics["initial_energy"],
            "final_energy": metrics["final_energy"],
            "energy_drift": metrics["energy_drift"],
        },
        "replay_commands": {
            "verify": f"qs-dmss verify {workspace.run_dir}",
            "replay": f"qs-dmss replay {workspace.run_dir}",
        },
    }


def write_energy_csv(path: Path, history: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["step", "norm", "energy", "max_density"],
        )
        writer.writeheader()
        writer.writerows(history)
