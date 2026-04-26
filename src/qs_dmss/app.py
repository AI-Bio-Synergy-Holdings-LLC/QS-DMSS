from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from qs_dmss.core.solver import QuantumScalarDarkMatterSolver
from qs_dmss.decision import evaluate_run_decision
from qs_dmss.evidence.bundle import (
    build_environment_lock,
    create_bundle_zip,
    write_manifest,
    write_report,
)
from qs_dmss.io.config import SimulationConfig, load_config, write_config
from qs_dmss.run.ledger import (
    create_run_record,
    prepare_run_workspace,
    write_energy_csv,
)


@dataclass(frozen=True)
class RunOutputs:
    run_id: str
    run_dir: Path
    bundle_path: Path


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_metrics(
    config: SimulationConfig,
    history: list[dict],
    elapsed_seconds: float,
) -> dict:
    initial = history[0]
    final = history[-1]
    return {
        "schema_version": 1,
        "backend": config.engine.backend,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "history": history,
        "initial_norm": initial["norm"],
        "final_norm": final["norm"],
        "norm_drift": round(final["norm"] - initial["norm"], 12),
        "initial_energy": initial["energy"],
        "final_energy": final["energy"],
        "energy_drift": round(final["energy"] - initial["energy"], 12),
        "max_density": final["max_density"],
    }


def execute_run(
    config: SimulationConfig,
    source_config_path: Path,
    output_root: Path | None = None,
    replayed_from: str | None = None,
    experiment: dict | None = None,
) -> RunOutputs:
    workspace = prepare_run_workspace(
        config=config,
        source_config_path=source_config_path,
        output_root_override=output_root,
        replayed_from=replayed_from,
    )

    write_config(config, workspace.run_dir / "config.yaml")

    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()

    solver = QuantumScalarDarkMatterSolver(
        engine=config.engine,
        initial=config.initial,
        seed=config.run.seed,
    )
    result = solver.run()

    elapsed_seconds = time.perf_counter() - started
    finished_at = datetime.now(timezone.utc)

    np.save(workspace.artifacts_dir / "final_density.npy", result.density)
    np.savez(
        workspace.artifacts_dir / "final_state.npz",
        real=result.psi.real,
        imag=result.psi.imag,
    )

    write_energy_csv(workspace.run_dir / "energy.csv", result.history)

    metrics = _build_metrics(
        config=config,
        history=result.history,
        elapsed_seconds=elapsed_seconds,
    )
    _write_json(workspace.run_dir / "metrics.json", metrics)

    environment_lock = build_environment_lock()
    _write_json(workspace.run_dir / "environment.lock.json", environment_lock)

    run_record = create_run_record(
        workspace=workspace,
        config=config,
        source_config_path=source_config_path,
        started_at=started_at,
        finished_at=finished_at,
        elapsed_seconds=elapsed_seconds,
        metrics=metrics,
        experiment=experiment,
    )
    _write_json(workspace.run_dir / "run.json", run_record)

    run_decision = evaluate_run_decision(
        config,
        metrics,
        verification_success=True,
    )
    write_report(
        run_dir=workspace.run_dir,
        run_record=run_record,
        metrics=metrics,
        decision=run_decision,
    )

    write_manifest(workspace.run_dir)
    bundle_path = create_bundle_zip(workspace.run_dir)

    return RunOutputs(
        run_id=workspace.run_id,
        run_dir=workspace.run_dir,
        bundle_path=bundle_path,
    )


def execute_run_from_path(
    config_path: str | Path,
    output_root: str | Path | None = None,
    replayed_from: str | None = None,
    experiment: dict | None = None,
) -> RunOutputs:
    source_config_path = Path(config_path).resolve()
    config = load_config(source_config_path)
    resolved_output = Path(output_root).resolve() if output_root is not None else None
    return execute_run(
        config=config,
        source_config_path=source_config_path,
        output_root=resolved_output,
        replayed_from=replayed_from,
        experiment=experiment,
    )


def replay_run(
    run_dir: str | Path,
    output_root: str | Path | None = None,
    experiment: dict | None = None,
) -> RunOutputs:
    source_run_dir = Path(run_dir).resolve()
    run_record_path = source_run_dir / "run.json"
    if not run_record_path.exists():
        raise FileNotFoundError(f"Run record not found: {run_record_path}")

    run_record = json.loads(run_record_path.read_text(encoding="utf-8"))
    config_path = source_run_dir / "config.yaml"
    return execute_run_from_path(
        config_path=config_path,
        output_root=output_root,
        replayed_from=run_record.get("run_id"),
        experiment=experiment,
    )
