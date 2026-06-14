from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from qs_dmss.core.solver import QuantumScalarDarkMatterSolver
from qs_dmss.decision import evaluate_run_decision
from qs_dmss.evidence.bundle import (
    build_environment_lock,
    create_bundle_zip,
    write_manifest,
    write_report,
)
from qs_dmss.execution import (
    ExecutionArtifact,
    ExecutionJobHandle,
    ExecutionJobResult,
    ExecutionJobSpec,
    ExecutionJobStatus,
    ExecutorCapabilities,
    LocalJobRegistry,
)
from qs_dmss.io.config import SimulationConfig, load_config, write_config
from qs_dmss.run.ledger import (
    create_run_record,
    prepare_run_workspace,
    resolve_run_output_root,
    write_energy_csv,
)


@dataclass(frozen=True)
class RunOutputs:
    run_id: str
    run_dir: Path
    bundle_path: Path
    job_id: str | None = None
    job_record_path: Path | None = None


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


class LocalExecutor:
    """Synchronous local executor adapter over the existing QS-DMSS runner."""

    def __init__(self, registry: LocalJobRegistry):
        self.registry = registry

    @property
    def capabilities(self) -> ExecutorCapabilities:
        return ExecutorCapabilities(
            backend="local",
            supports_campaigns=True,
            supports_replay=True,
            supports_cancellation=False,
            supports_artifact_collection=True,
            requires_credentials=False,
            notes=("Synchronous adapter over the local NumPy runner.",),
        )

    def submit(self, spec: ExecutionJobSpec) -> ExecutionJobHandle:
        return self.registry.create(spec, backend=self.capabilities.backend)

    def status(self, handle: ExecutionJobHandle) -> ExecutionJobStatus:
        return self.registry.status(handle)

    def collect(self, handle: ExecutionJobHandle) -> ExecutionJobResult:
        record = self.registry.get(handle.job_id)
        result = record.get("result")
        if not result:
            return ExecutionJobResult(
                handle=handle,
                state=record["state"],
                error=record.get("metadata", {}).get("error"),
            )
        artifacts = tuple(
            ExecutionArtifact(
                role=item["role"],
                path=Path(item["path"]) if item.get("path") else None,
                uri=item.get("uri"),
                sha256=item.get("sha256"),
                media_type=item.get("media_type"),
                label=item.get("label"),
            )
            for item in result.get("artifacts", [])
        )
        return ExecutionJobResult(
            handle=handle,
            state=result["state"],
            run_id=result.get("run_id"),
            experiment_id=result.get("experiment_id"),
            run_dir=Path(result["run_dir"]) if result.get("run_dir") else None,
            experiment_dir=Path(result["experiment_dir"]) if result.get("experiment_dir") else None,
            artifacts=artifacts,
            metrics=result.get("metrics"),
            error=result.get("error"),
        )

    def execute_run(
        self,
        *,
        config: SimulationConfig,
        source_config_path: Path,
        output_root: Path,
        replayed_from: str | None = None,
        experiment: dict[str, Any] | None = None,
    ) -> RunOutputs:
        spec = ExecutionJobSpec(
            config=config.to_dict(),
            source_name=source_config_path.name,
            output_root=output_root,
            experiment=experiment,
            labels=self._labels_for_run(replayed_from, experiment),
            metadata={
                "source_config_path": str(source_config_path),
                "replayed_from": replayed_from,
            },
        )
        handle = self.submit(spec)
        self.registry.update(
            handle,
            "running",
            message="Local QS-DMSS run started.",
            progress=0.25,
        )

        try:
            outputs = _execute_run_direct(
                config=config,
                source_config_path=source_config_path,
                output_root=output_root,
                replayed_from=replayed_from,
                experiment=experiment,
                execution_job={
                    "job_id": handle.job_id,
                    "backend": handle.backend,
                    "registry_path": handle.status_uri,
                },
            )
            self.registry.update(
                handle,
                "collecting",
                message="Local run complete; collecting evidence artifacts.",
                progress=0.9,
            )
            metrics = _read_json(outputs.run_dir / "metrics.json")
            result = ExecutionJobResult(
                handle=ExecutionJobHandle(
                    job_id=handle.job_id,
                    backend=handle.backend,
                    state="succeeded",
                    status_uri=handle.status_uri,
                ),
                state="succeeded",
                run_id=outputs.run_id,
                run_dir=outputs.run_dir,
                artifacts=(
                    ExecutionArtifact(
                        role="run_directory",
                        path=outputs.run_dir,
                        label="Run directory",
                    ),
                    ExecutionArtifact(
                        role="evidence_bundle",
                        path=outputs.bundle_path,
                        media_type="application/zip",
                        label="Evidence bundle",
                    ),
                    ExecutionArtifact(
                        role="report",
                        path=outputs.run_dir / "report.html",
                        media_type="text/html",
                        label="Evidence report",
                    ),
                    ExecutionArtifact(
                        role="metrics",
                        path=outputs.run_dir / "metrics.json",
                        media_type="application/json",
                        label="Metrics",
                    ),
                    ExecutionArtifact(
                        role="manifest",
                        path=outputs.run_dir / "manifest.sha256.json",
                        media_type="application/json",
                        label="Manifest",
                    ),
                ),
                metrics=metrics,
            )
            self.registry.complete(handle, result)
            return RunOutputs(
                run_id=outputs.run_id,
                run_dir=outputs.run_dir,
                bundle_path=outputs.bundle_path,
                job_id=handle.job_id,
                job_record_path=Path(handle.status_uri) if handle.status_uri else None,
            )
        except Exception as exc:
            self.registry.fail(handle, exc)
            raise

    def _labels_for_run(
        self,
        replayed_from: str | None,
        experiment: dict[str, Any] | None,
    ) -> tuple[str, ...]:
        labels = ["run"]
        if replayed_from:
            labels.append("replay")
        if experiment:
            labels.append(str(experiment.get("kind", "experiment")))
        return tuple(labels)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _execute_run_direct(
    config: SimulationConfig,
    source_config_path: Path,
    output_root: Path | None = None,
    replayed_from: str | None = None,
    experiment: dict | None = None,
    execution_job: dict | None = None,
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
        execution_job=execution_job,
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


def execute_run(
    config: SimulationConfig,
    source_config_path: Path,
    output_root: Path | None = None,
    replayed_from: str | None = None,
    experiment: dict | None = None,
) -> RunOutputs:
    resolved_output_root = resolve_run_output_root(
        config,
        source_config_path,
        output_root,
    )
    executor = LocalExecutor(LocalJobRegistry.for_output_root(resolved_output_root))
    return executor.execute_run(
        config=config,
        source_config_path=source_config_path,
        output_root=resolved_output_root,
        replayed_from=replayed_from,
        experiment=experiment,
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
