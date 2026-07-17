from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import os
import secrets
import shutil
import threading
import time
import zipfile
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from qs_dmss import __version__
from qs_dmss.app import execute_run, replay_run as replay_existing_run
from qs_dmss.decision import evaluate_run_decision
from qs_dmss.deployment import public_deployment_provenance
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.execution import (
    ExecutionArtifact,
    ExecutionJobHandle,
    ExecutionJobResult,
    ExecutionJobSpec,
    JobState,
    LocalJobRegistry,
)
from qs_dmss.experiment import (
    apply_parameter_values,
    apply_sweep_value,
    build_campaign_context,
    build_campaign_plan,
    build_experiment_context,
    build_run_comparison,
    coerce_sweep_values,
    create_experiment_id,
    format_parameter_value,
    get_sweep_parameter,
    list_sweep_parameters,
    persist_failed_campaign_artifact,
    persist_experiment_artifact,
)
from qs_dmss.io.config import (
    SUPPORTED_DECISION_METRICS,
    SUPPORTED_OBJECTIVE_GOALS,
    load_config,
    parse_config,
)
from qs_dmss.paths import (
    bundled_assets_root,
    contained_path,
    configs_root,
    discover_repo_root,
    experiments_root,
    runs_root,
    safe_filename,
)
from qs_dmss.quantum_compilation import (
    BASIS_GATES,
    OPTIMIZATION_LEVELS,
    TOPOLOGY_PROFILES,
    validate_fractal_quantum_compilation,
)
from qs_dmss.quantum_showcase import (
    load_quantum_compilation_directory,
    load_quantum_compilation_showcase,
    quantum_compilation_artifact_path,
    quantum_compilation_showcase_artifact_key,
    quantum_compilation_showcase_path,
)
from qs_dmss.showcase import (
    DEFAULT_SHOWCASE_NAME,
    SHOWCASE_JSON_REPORT,
    SHOWCASE_MARKDOWN_REPORT,
    list_showcase_scenarios,
    resolve_showcase_scenario,
    run_simulation_showcase,
    showcase_scenario_metadata,
)


GENERIC_COCKPIT_ERROR_DETAIL = "Cockpit request failed; check server logs for details."
COCKPIT_LOGGER = logging.getLogger("qs_dmss.cockpit")
HOSTED_DEMO_COOKIE_NAME = "qs_dmss_demo_session"
HOSTED_DEMO_ENV_VAR = "QS_DMSS_HOSTED_DEMO"
HOSTED_DEMO_SELF_INTERACTION_TEMPLATE_ID = "self-interaction-sweep"
HOSTED_DEMO_PUBLIC_URL = "https://app.qs-dmss.studio/"
PROJECT_DOI = "10.5281/zenodo.20074924"
LATEST_ARCHIVED_RELEASE_TAG = "v0.13.2"
RELEASE_DOI = "10.5281/zenodo.21366910"
RELEASE_RECORD_URL = "https://zenodo.org/records/21366910"
HOSTED_DEMO_ROBOTS = """User-agent: *
Allow: /
Allow: /static/
Disallow: /api/
Disallow: /docs
Disallow: /redoc
Disallow: /openapi.json

Sitemap: https://app.qs-dmss.studio/sitemap.xml
"""
HOSTED_DEMO_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://app.qs-dmss.studio/</loc>
  </url>
</urlset>
"""
NOINDEX_RESPONSE_PATHS = ("/api/", "/docs", "/redoc", "/openapi.json")
BASELINE_SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; base-uri 'self'; object-src 'none'; "
        "script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; connect-src 'self'; frame-src 'self'; "
        "frame-ancestors 'none'; form-action 'self'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}
_HOSTED_DEMO_ACTIVE_JOBS: set[str] = set()
_HOSTED_DEMO_ACTIVE_JOBS_LOCK = threading.Lock()
_QUANTUM_VALIDATION_ACTIVE_LOCK = threading.Lock()
QUANTUM_RUN_METADATA = "cockpit-run.json"

CONFIG_CATALOG_METADATA: dict[str, dict[str, str]] = {
    "demo.yaml": {
        "label": "Stability Frontier Demo",
        "study_type": "Decision campaign",
        "summary": "Small deterministic Gaussian-packet study with an objective, constraints, ranking, and a six-run campaign matrix.",
        "evidence_focus": "Energy drift, norm drift, density retention, verification, and ranked selection.",
    },
    "conservation_baseline.yaml": {
        "label": "Conservation Baseline",
        "study_type": "Numerical control",
        "summary": "Non-interacting Gaussian packet used to establish the solver's conservation baseline before interaction terms are introduced.",
        "evidence_focus": "Relative energy and norm change under a declared zero-interaction control.",
    },
    "fractal_quadrant_ssfm.yaml": {
        "label": "Fractal Quadrant SSFM",
        "study_type": "Structured-potential study",
        "summary": "Fractal fuzzy-potential reference using the quadrant-aware split-step Fourier solver.",
        "evidence_focus": "Conservation diagnostics, spectral behavior, replay, and environment provenance.",
    },
    "interaction_response.yaml": {
        "label": "Interaction Response",
        "study_type": "Perturbation study",
        "summary": "Moderate self-interaction study for inspecting how a fixed initial packet responds to a declared nonlinear term.",
        "evidence_focus": "Energy and norm drift, peak density, elapsed time, and evidence verification.",
    },
    "uniform_control.yaml": {
        "label": "Uniform Field Control",
        "study_type": "Initial-state control",
        "summary": "Uniform-field control that separates initial-profile effects from Gaussian localization effects.",
        "evidence_focus": "Uniform-state stability, deterministic replay, and cross-profile comparison readiness.",
    },
}

RUN_BUNDLE_PROFILES: dict[str, dict[str, Any]] = {
    "review": {
        "title": "Scientific review bundle",
        "claim_boundary": (
            "Human-readable configuration, diagnostics, report, environment, and integrity records. "
            "This package supports review of numerical evidence; it is not physical validation."
        ),
        "files": (
            "config.yaml",
            "energy.csv",
            "environment.lock.json",
            "metrics.json",
            "run.json",
            "report.html",
            "manifest.sha256.json",
        ),
    },
    "state": {
        "title": "Reproducibility state bundle",
        "claim_boundary": (
            "Configuration, final numerical state, run metadata, metrics, and integrity manifest "
            "for controlled replay and downstream inspection."
        ),
        "files": (
            "config.yaml",
            "metrics.json",
            "run.json",
            "manifest.sha256.json",
            "artifacts/final_density.npy",
            "artifacts/final_state.npz",
        ),
    },
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quantum_visualization_lineage(payload: dict[str, Any], source_id: str) -> dict[str, Any]:
    matrix_resources = [
        {
            "topology_id": row.get("topology_id"),
            "optimization_level": row.get("optimization_level"),
            "depth": (row.get("resources") or {}).get("depth"),
            "two_qubit_gates": (row.get("resources") or {}).get("two_qubit_gates"),
        }
        for row in payload.get("matrix", [])
    ]
    attribution = (payload.get("recommended_configuration") or {}).get("attribution") or {}
    attribution_resources = {
        name: {
            "depth": resources.get("depth"),
            "two_qubit_gates": resources.get("two_qubit_gates"),
        }
        for name, resources in sorted(attribution.items())
    }
    chart_data = {
        "matrix_resources": matrix_resources,
        "recommended_attribution": attribution_resources,
    }
    encoded = json.dumps(
        chart_data,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "source_run_id": source_id,
        "resource_fingerprint": hashlib.sha256(encoded).hexdigest(),
        "matrix_row_count": len(matrix_resources),
        "matrix_resource_value_count": len(matrix_resources) * 2,
        "attribution_component_count": len(attribution_resources),
        "attribution_resource_value_count": len(attribution_resources) * 2,
    }


@dataclass(frozen=True)
class HostedDemoSettings:
    enabled: bool = False
    ttl_seconds: int = 60 * 60
    max_campaign_runs: int = 5
    max_engine_steps: int = 12
    max_total_engine_steps: int = 60
    max_grid_cells: int = 4096
    max_artifact_bytes: int = 10 * 1024 * 1024

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "session_ttl_seconds": self.ttl_seconds,
            "max_campaign_runs": self.max_campaign_runs,
            "max_engine_steps": self.max_engine_steps,
            "max_total_engine_steps": self.max_total_engine_steps,
            "max_grid_cells": self.max_grid_cells,
            "max_artifact_bytes": self.max_artifact_bytes,
            "one_active_job_per_session": True,
            "allowed_compute_paths": [
                "packaged Lab Mode showcase",
                "packaged guided comparison",
                "packaged self-interaction Campaign Studio study",
                "verification, replay, reports, bundles, and research-object export",
            ],
            "read_only_surfaces": [
                "precomputed Fractal SSFM quantum compilation validation",
            ],
            "temporary_output_notice": (
                "Public hosted demo outputs are temporary; do not upload sensitive data."
            ),
        }


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _hosted_demo_settings(enabled: bool | None = None) -> HostedDemoSettings:
    settings = HostedDemoSettings(
        enabled=_env_flag(HOSTED_DEMO_ENV_VAR),
        ttl_seconds=_env_int("QS_DMSS_HOSTED_DEMO_TTL_SECONDS", 60 * 60),
        max_campaign_runs=_env_int("QS_DMSS_HOSTED_DEMO_MAX_CAMPAIGN_RUNS", 5),
        max_engine_steps=_env_int("QS_DMSS_HOSTED_DEMO_MAX_ENGINE_STEPS", 12),
        max_total_engine_steps=_env_int("QS_DMSS_HOSTED_DEMO_MAX_TOTAL_ENGINE_STEPS", 60),
        max_grid_cells=_env_int("QS_DMSS_HOSTED_DEMO_MAX_GRID_CELLS", 4096),
        max_artifact_bytes=_env_int("QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES", 10 * 1024 * 1024),
    )
    if enabled is not None:
        settings = replace(settings, enabled=enabled)
    return settings


def _new_hosted_demo_session_id() -> str:
    return secrets.token_urlsafe(18)


def _is_valid_hosted_demo_session_id(value: str | None) -> bool:
    if not value or not (16 <= len(value) <= 64):
        return False
    return safe_filename(value, default="session") == value


def _grid_cell_count(config: dict[str, Any]) -> int:
    cells = 1
    for value in (config.get("engine") or {}).get("grid_shape") or []:
        try:
            cells *= int(value)
        except (TypeError, ValueError):
            return 0
    return cells


def _configured_engine_steps(config: dict[str, Any]) -> int:
    try:
        return int((config.get("engine") or {}).get("num_steps") or 0)
    except (TypeError, ValueError):
        return 0


class LaunchRunRequest(BaseModel):
    config: dict
    source_name: str = "cockpit.yaml"


class CompareRunsRequest(BaseModel):
    run_ids: list[str]


class CreateExperimentRequest(BaseModel):
    run_ids: list[str]
    label: str | None = None


class SweepRequest(BaseModel):
    config: dict
    parameter_path: str
    values: list[int | float | str]
    source_name: str = "sweep.yaml"
    experiment_name: str | None = None


class QuantumValidationRunRequest(BaseModel):
    shots: int = Field(default=4096, ge=128, le=100_000)
    seed: int = Field(default=7, ge=0)
    reference_tolerance: float = Field(default=1e-10, gt=0.0)
    compilation_tolerance: float = Field(default=1e-6, gt=0.0)


class LaunchCampaignRequest(BaseModel):
    config: dict
    source_name: str = "campaign.yaml"
    study_template_id: str | None = None


class CampaignStudyTemplateRequest(BaseModel):
    template: dict[str, Any]


class ResearchObjectExportRequest(BaseModel):
    research_object: dict[str, Any]


class WorkspaceExportRequest(BaseModel):
    title: str = "QS-DMSS workspace"
    description: str | None = None
    collaborators: list[dict[str, Any]] = Field(default_factory=list)
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    run_ids: list[str] = Field(default_factory=list)
    experiment_ids: list[str] = Field(default_factory=list)
    campaign_study_template_ids: list[str] = Field(default_factory=list)
    research_object_ids: list[str] = Field(default_factory=list)


class WorkspaceImportRequest(BaseModel):
    workspace: dict[str, Any]


@dataclass(frozen=True)
class CockpitService:
    repo_root: Path
    output_root: Path
    experiments_root: Path
    jobs_root: Path
    config_root: Path
    static_root: Path
    hosted_demo: HostedDemoSettings = field(default_factory=HostedDemoSettings)

    @classmethod
    def create(
        cls,
        repo_root: str | Path | None = None,
        output_root: str | Path | None = None,
        hosted_demo: bool | None = None,
    ) -> "CockpitService":
        resolved_repo_root = discover_repo_root(Path(repo_root) if repo_root else Path.cwd())
        hosted_settings = _hosted_demo_settings(hosted_demo)
        resolved_output_root = (
            Path(output_root).resolve() if output_root else runs_root(resolved_repo_root)
        )
        resolved_experiments_root = experiments_root(
            resolved_repo_root,
            resolved_output_root,
        )
        resolved_jobs_root = LocalJobRegistry.for_output_root(
            resolved_output_root
        ).jobs_root
        resolved_output_root.mkdir(parents=True, exist_ok=True)
        resolved_experiments_root.mkdir(parents=True, exist_ok=True)
        return cls(
            repo_root=resolved_repo_root,
            output_root=resolved_output_root,
            experiments_root=resolved_experiments_root,
            jobs_root=resolved_jobs_root,
            config_root=configs_root(resolved_repo_root),
            static_root=Path(__file__).resolve().parent / "static",
            hosted_demo=hosted_settings,
        )

    def for_hosted_session(self, session_id: str) -> "CockpitService":
        if not self.hosted_demo.enabled:
            return self
        session_name = safe_filename(session_id, default="session")
        session_root = contained_path(self.output_root / "sessions", session_name)
        session_output_root = session_root / "runs"
        session_experiments_root = session_root / "experiments"
        session_jobs_root = LocalJobRegistry.for_output_root(
            session_output_root,
        ).jobs_root
        session_output_root.mkdir(parents=True, exist_ok=True)
        session_experiments_root.mkdir(parents=True, exist_ok=True)
        session_jobs_root.mkdir(parents=True, exist_ok=True)
        os.utime(session_root, None)
        return replace(
            self,
            output_root=session_output_root,
            experiments_root=session_experiments_root,
            jobs_root=session_jobs_root,
        )

    def cleanup_hosted_sessions(
        self,
        *,
        now: float,
        last_cleanup_at: float,
    ) -> float:
        if not self.hosted_demo.enabled:
            return last_cleanup_at
        if now - last_cleanup_at < 60:
            return last_cleanup_at
        sessions_root = self.output_root / "sessions"
        if not sessions_root.exists():
            return now
        cutoff = now - self.hosted_demo.ttl_seconds
        for session_dir in sessions_root.iterdir():
            if not session_dir.is_dir():
                continue
            try:
                if session_dir.stat().st_mtime < cutoff:
                    shutil.rmtree(session_dir)
            except OSError:
                continue
        return now

    def hosted_demo_status(self, session_id: str | None = None) -> dict[str, Any]:
        payload = self.hosted_demo.as_public_dict()
        payload["session_id"] = session_id if self.hosted_demo.enabled else None
        return payload

    def assert_hosted_download_allowed(self, path: Path) -> None:
        if not self.hosted_demo.enabled:
            return
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise HTTPException(status_code=404, detail="Artifact not found") from exc
        if size > self.hosted_demo.max_artifact_bytes:
            raise HTTPException(
                status_code=413,
                detail="Hosted demo artifact exceeds the download size cap.",
            )

    def _assert_hosted_config_envelope(
        self,
        config: dict[str, Any],
        *,
        planned_run_count: int = 1,
    ) -> None:
        if not self.hosted_demo.enabled:
            return
        engine_steps = _configured_engine_steps(config)
        grid_cells = _grid_cell_count(config)
        total_steps = planned_run_count * engine_steps
        if planned_run_count > self.hosted_demo.max_campaign_runs:
            raise HTTPException(
                status_code=403,
                detail="Hosted demo campaigns are capped at five packaged runs.",
            )
        if engine_steps > self.hosted_demo.max_engine_steps:
            raise HTTPException(
                status_code=403,
                detail="Hosted demo run configs exceed the engine step cap.",
            )
        if total_steps > self.hosted_demo.max_total_engine_steps:
            raise HTTPException(
                status_code=403,
                detail="Hosted demo campaign exceeds the total configured step cap.",
            )
        if grid_cells > self.hosted_demo.max_grid_cells:
            raise HTTPException(
                status_code=403,
                detail="Hosted demo run configs exceed the grid-size cap.",
            )

    def _assert_hosted_packaged_campaign(
        self,
        payload: LaunchCampaignRequest,
        base_config: dict[str, Any],
        campaign_plan: dict[str, Any],
    ) -> None:
        if not self.hosted_demo.enabled:
            return
        if payload.study_template_id != HOSTED_DEMO_SELF_INTERACTION_TEMPLATE_ID:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo only runs the packaged Self-Interaction Sweep template. "
                    "Install QS-DMSS locally to edit or launch custom campaigns."
                ),
            )
        packaged_template = self._read_json(
            self._get_campaign_study_template_path(HOSTED_DEMO_SELF_INTERACTION_TEMPLATE_ID),
        )
        packaged_config = parse_config(packaged_template.get("config")).to_dict()
        if base_config != packaged_config:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo does not run edited Campaign Studio payloads. "
                    "Use the packaged Self-Interaction Sweep or install QS-DMSS locally."
                ),
            )
        self._assert_hosted_config_envelope(
            base_config,
            planned_run_count=campaign_plan["planned_run_count"],
        )

    def list_configs(self) -> list[dict]:
        items: list[dict] = []
        config_paths = sorted(
            self.config_root.glob("*.y*ml"),
            key=lambda path: (path.name != "demo.yaml", path.name),
        )
        for path in config_paths:
            config = load_config(path)
            metadata = CONFIG_CATALOG_METADATA.get(path.name, {})
            try:
                relative_path = path.relative_to(self.repo_root).as_posix()
            except ValueError:
                relative_path = f"configs/{path.name}"
            items.append(
                {
                    "label": metadata.get("label", path.stem.replace("_", " ").title()),
                    "name": path.name,
                    "path": relative_path,
                    "study_type": metadata.get("study_type", "Deterministic study"),
                    "summary": metadata.get(
                        "summary",
                        "Versioned local configuration with deterministic evidence capture.",
                    ),
                    "evidence_focus": metadata.get(
                        "evidence_focus",
                        "Run metrics, environment provenance, verification, and replay.",
                    ),
                    "config": config.to_dict(),
                }
            )
        return items

    def list_runs(self) -> list[dict]:
        return [self._build_run_summary(run_dir) for run_dir in self._list_run_dirs()]

    def list_experiments(self) -> list[dict]:
        return [
            self._build_experiment_summary(experiment_dir)
            for experiment_dir in self._list_experiment_dirs()
        ]

    def list_sweep_parameters(self) -> list[dict]:
        return list_sweep_parameters()

    def list_showcases(self) -> list[dict]:
        return [self._build_showcase_summary(name) for name in list_showcase_scenarios()]

    def quantum_runtime_status(self) -> dict[str, Any]:
        stack_available = bool(
            importlib.util.find_spec("qiskit")
            and importlib.util.find_spec("qiskit_aer")
        )
        return {
            "mode": "hosted_read_only" if self.hosted_demo.enabled else "local_full",
            "package_version": __version__,
            "live_execution": stack_available and not self.hosted_demo.enabled,
            "stack_available": stack_available,
            "install_command": "python -m pip install -e '.[quantum]'",
            "endpoint": "/api/quantum-validation/runs",
            "defaults": {
                "shots": 4096,
                "seed": 7,
                "reference_tolerance": 1e-10,
                "compilation_tolerance": 1e-6,
            },
            "matrix_scope": {
                "topology_count": len(TOPOLOGY_PROFILES),
                "optimization_levels": list(OPTIMIZATION_LEVELS),
                "row_count": len(TOPOLOGY_PROFILES) * len(OPTIMIZATION_LEVELS),
                "basis_gates": list(BASIS_GATES),
            },
            "execution_policy": {
                "local_simulation_only": True,
                "provider": None,
                "credentials_read": False,
                "submitted": False,
                "max_authorized_cost_usd": 0.0,
            },
        }

    def quantum_validation_showcase(self) -> dict[str, Any]:
        payload = load_quantum_compilation_showcase()
        bundle_path = quantum_compilation_showcase_path("bundle")
        payload["bundle"]["sha256"] = _file_sha256(bundle_path)
        payload["source"] = "packaged_snapshot"
        payload["runtime"] = self.quantum_runtime_status()
        payload["visualization"] = _quantum_visualization_lineage(
            payload,
            payload.get("showcase_id", "packaged-reference"),
        )
        return payload

    def quantum_validation_artifact_path(self, artifact_name: str) -> Path:
        try:
            return quantum_compilation_showcase_path(artifact_name)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail="Quantum artifact not found") from exc

    def _quantum_validation_runs_root(self) -> Path:
        root = contained_path(self.output_root, "quantum-validations")
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _quantum_validation_run_dir(self, run_id: str) -> Path:
        if not run_id or safe_filename(run_id, default="run") != run_id:
            raise HTTPException(status_code=404, detail="Quantum validation run not found")
        run_dir = contained_path(self._quantum_validation_runs_root(), run_id)
        if not run_dir.is_dir():
            raise HTTPException(status_code=404, detail="Quantum validation run not found")
        return run_dir

    def _load_quantum_validation_run(self, run_dir: Path) -> dict[str, Any]:
        run_id = run_dir.name
        payload = load_quantum_compilation_directory(
            run_dir,
            showcase_id=run_id,
            title="Live Fractal SSFM Quantum Compilation Validation",
            subtitle="Fresh local ideal-simulator compilation matrix and resource attribution",
            limitations=[
                "The run uses local ideal simulators and generic topology profiles, not a provider device or calibration snapshot.",
                "Resource counts are not runtime, price, error-rate, or quantum-advantage predictions.",
                "This workflow validates compilation semantics; it does not scientifically validate the underlying Fractal SSFM model.",
            ],
            download_prefix=f"/api/quantum-validation/runs/{run_id}/files",
        )
        metadata_path = run_dir / QUANTUM_RUN_METADATA
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.is_file()
            else {
                "run_id": run_id,
                "name": run_id,
                "generated_at": payload.get("generated_at"),
                "output_directory": str(run_dir),
            }
        )
        payload["source"] = "live_local_run"
        payload["runtime"] = self.quantum_runtime_status()
        payload["run"] = metadata
        payload["bundle"]["sha256"] = _file_sha256(
            quantum_compilation_artifact_path(run_dir, "bundle")
        )
        payload["visualization"] = _quantum_visualization_lineage(payload, run_id)
        return payload

    def latest_quantum_validation_run(self) -> dict[str, Any]:
        if self.hosted_demo.enabled:
            return {"available": False, "runtime": self.quantum_runtime_status()}
        candidates = sorted(
            (
                path
                for path in self._quantum_validation_runs_root().iterdir()
                if path.is_dir() and (path / "quantum-compilation-validation.json").is_file()
            ),
            key=lambda path: path.name,
            reverse=True,
        )
        if not candidates:
            return {"available": False, "runtime": self.quantum_runtime_status()}
        return {"available": True, "result": self._load_quantum_validation_run(candidates[0])}

    def run_quantum_validation(
        self,
        payload: QuantumValidationRunRequest,
    ) -> dict[str, Any]:
        if self.hosted_demo.enabled:
            raise HTTPException(
                status_code=403,
                detail="Live quantum validation is available only in the local full application.",
            )
        runtime = self.quantum_runtime_status()
        if not runtime["stack_available"]:
            raise HTTPException(
                status_code=503,
                detail=(
                    "The optional quantum simulator stack is not installed. "
                    "Run: python -m pip install -e '.[quantum]'"
                ),
            )

        started_at = datetime.now(timezone.utc)
        run_id = (
            f"quantum-compilation-{started_at.strftime('%Y%m%dT%H%M%SZ')}-"
            f"{secrets.token_hex(4)}"
        )
        run_dir = contained_path(self._quantum_validation_runs_root(), run_id)
        started_clock = time.perf_counter()
        validate_fractal_quantum_compilation(
            output_root=run_dir,
            shots=payload.shots,
            seed=payload.seed,
            reference_tolerance=payload.reference_tolerance,
            compilation_tolerance=payload.compilation_tolerance,
        )
        completed_at = datetime.now(timezone.utc)
        metadata = {
            "run_id": run_id,
            "name": run_id,
            "status": "complete",
            "package_version": __version__,
            "runtime_mode": runtime["mode"],
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": round(time.perf_counter() - started_clock, 3),
            "output_directory": str(run_dir),
            "parameters": payload.model_dump(),
        }
        (run_dir / QUANTUM_RUN_METADATA).write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return self._load_quantum_validation_run(run_dir)

    def quantum_validation_run_artifact_path(
        self,
        run_id: str,
        artifact_name: str,
    ) -> Path:
        if self.hosted_demo.enabled:
            raise HTTPException(status_code=404, detail="Quantum artifact not found")
        try:
            return quantum_compilation_artifact_path(
                self._quantum_validation_run_dir(run_id),
                artifact_name,
            )
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail="Quantum artifact not found") from exc

    def campaign_studio_preview(self) -> dict:
        configs = self.list_configs()
        default_config = configs[0] if configs else None
        if default_config is None:
            return {
                "available": False,
                "title": "Campaign Studio",
                "summary": "No packaged config is available for a campaign preview.",
                "current_boundary": "Add a config with objective and campaign sections to enable Campaign Studio.",
                "next_capabilities": [
                    "Scenario-linked campaign templates",
                    "Editable parameter-grid studies",
                    "Decision-profile editing",
                ],
            }

        config = default_config["config"]
        try:
            campaign_plan = build_campaign_plan(config)
        except ValueError:
            return {
                "available": False,
                "title": "Campaign Studio",
                "source_config_name": default_config["name"],
                "summary": "The default config is not a launchable campaign study yet.",
                "current_boundary": "This config can launch a run, but it does not define an automated campaign.",
                "next_capabilities": [
                    "Add a campaign section",
                    "Attach objective constraints",
                    "Save a comparison research object",
                ],
            }

        objective = config.get("objective") or {}
        constraints = {"require_verification": True, **(config.get("constraints") or {})}
        ranking = config.get("ranking") or {}
        return {
            "available": True,
            "title": "Campaign Studio",
            "source_config_name": default_config["name"],
            "label": campaign_plan["label"],
            "strategy": campaign_plan["strategy"],
            "max_runs": config.get("campaign", {}).get("max_runs", campaign_plan["planned_run_count"]),
            "planned_run_count": campaign_plan["planned_run_count"],
            "dimension_count": campaign_plan["dimension_count"],
            "dimensions": campaign_plan["dimensions"],
            "objective": {
                "name": objective.get("name", "No objective"),
                "summary": objective.get("summary", "No objective summary provided."),
                "primary_metric": objective.get("primary_metric"),
                "goal": objective.get("goal"),
                "target_value": objective.get("target_value"),
                "supported_metrics": list(SUPPORTED_DECISION_METRICS),
                "supported_goals": list(SUPPORTED_OBJECTIVE_GOALS),
            },
            "constraint_values": constraints,
            "constraints": [
                {"name": key, "value": value}
                for key, value in constraints.items()
            ],
            "ranking": {
                "primary_metric_weight": ranking.get("primary_metric_weight"),
                "weights": ranking.get("weights", {}),
            },
            "readiness_badges": [
                {"label": "Grid plan", "status": "ready"},
                {"label": "Objective scoring", "status": "ready"},
                {"label": "Evidence bundle", "status": "ready"},
                {"label": "Grid editor", "status": "ready"},
                {"label": "Objective editor", "status": "ready"},
                {"label": "Study templates", "status": "ready"},
            ],
            "summary": (
                "A packaged decision campaign can already expand a template into a "
                "multi-run search matrix, score every run, save reusable study templates, "
                "and export a comparison bundle."
            ),
            "current_boundary": (
                "Campaign Studio now edits, saves, reopens, imports, and exports reusable "
                "campaign study templates with the scoring contract attached."
            ),
            "next_capabilities": [
                "Richer template library metadata",
                "Template-to-publication export provenance",
                "Team-shared study template registries",
            ],
            "launch_endpoint": "/api/campaigns",
        }

    def list_campaign_study_templates(self) -> list[dict]:
        local_records: list[dict] = [
            self._read_json(path)
            for path in self._list_campaign_study_template_paths()
        ]
        local_records_by_id = {
            record["template_id"]: record
            for record in local_records
            if record.get("template_id")
        }
        packaged_ids: set[str] = set()
        summaries: list[dict] = []

        for packaged_path in self._list_packaged_campaign_study_template_paths():
            packaged_record = self._read_json(packaged_path)
            template_id = packaged_record.get("template_id")
            if not template_id:
                continue
            packaged_ids.add(template_id)
            summaries.append(
                self._build_campaign_study_summary(
                    local_records_by_id.get(template_id, packaged_record),
                )
            )

        for record in local_records:
            template_id = record.get("template_id")
            if template_id and template_id not in packaged_ids:
                summaries.append(self._build_campaign_study_summary(record))

        return summaries

    def get_campaign_study_template(self, template_id: str) -> dict:
        path = self._get_campaign_study_template_path(template_id)
        return self._build_campaign_study_detail(path)

    def campaign_study_template_path(self, template_id: str) -> Path:
        return self._get_campaign_study_template_path(template_id)

    def save_campaign_study_template(self, payload: CampaignStudyTemplateRequest) -> dict:
        if self.hosted_demo.enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo keeps study templates packaged and temporary. "
                    "Install QS-DMSS locally to save custom study templates."
                ),
            )
        try:
            record = self._normalize_campaign_study_template(payload.template)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        path = contained_path(
            self._campaign_studies_root(create=True),
            f"{record['template_id']}.json",
        )
        path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return self._build_campaign_study_detail(path)

    def import_campaign_study_template(self, payload: CampaignStudyTemplateRequest) -> dict:
        if self.hosted_demo.enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo does not accept uploaded study templates. "
                    "Install QS-DMSS locally to import portable campaign designs."
                ),
            )
        template = dict(payload.template)
        imported_from = template.get("template_id")
        if imported_from:
            template["imported_from_template_id"] = str(imported_from)
        return self.save_campaign_study_template(
            CampaignStudyTemplateRequest(template=template),
        )

    def get_run_detail(self, run_id: str) -> dict:
        run_dir = self._get_run_dir(run_id)
        return self._build_run_detail(run_dir)

    def get_run_job_detail(self, run_id: str) -> dict:
        run_dir = self._get_run_dir(run_id)
        run_record = self._read_json(run_dir / "run.json")
        reference = run_record.get("execution_job")
        detail = self._build_execution_job_detail(reference)
        if detail is None:
            raise HTTPException(status_code=404, detail="Run has no execution job provenance")
        return detail

    def get_job_detail(self, job_id: str) -> dict:
        return self._build_job_detail(self._get_job_record(job_id))

    def get_experiment_detail(self, experiment_id: str) -> dict:
        experiment_dir = self._get_experiment_dir(experiment_id)
        return self._build_experiment_detail(experiment_dir)

    def list_workspaces(self) -> list[dict]:
        return [
            self._build_workspace_summary(path)
            for path in self._list_workspace_paths()
        ]

    def get_workspace(self, workspace_id: str) -> dict:
        return self._build_workspace_detail(self._get_workspace_path(workspace_id))

    def export_workspace(self, payload: WorkspaceExportRequest) -> dict:
        if self.hosted_demo.enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo disables workspace snapshots because public outputs are temporary. "
                    "Use research-object export here, or install QS-DMSS locally for workspace export."
                ),
            )
        try:
            record = self._build_workspace_record(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        workspace_path = self._workspace_dir(
            record["workspace_id"],
            create=True,
        ) / "workspace.json"
        workspace_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return self._build_workspace_detail(workspace_path)

    def import_workspace(self, payload: WorkspaceImportRequest) -> dict:
        if self.hosted_demo.enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo does not accept uploaded workspace JSON. "
                    "Install QS-DMSS locally to import collaborator workspaces."
                ),
            )
        try:
            record = self._normalize_imported_workspace(payload.workspace)
            installed_templates = self._install_workspace_campaign_studies(record)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        workspace_path = self._workspace_dir(
            record["workspace_id"],
            create=True,
        ) / "workspace.json"
        workspace_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        detail = self._build_workspace_detail(workspace_path)
        detail["imported_campaign_studies"] = installed_templates
        return detail

    def workspace_path(self, workspace_id: str) -> Path:
        return self._get_workspace_path(workspace_id)

    def launch_run(self, payload: LaunchRunRequest) -> dict:
        if self.hosted_demo.enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo disables arbitrary run configs. "
                    "Use Lab Mode or install QS-DMSS locally for custom runs."
                ),
            )
        config = parse_config(payload.config)
        with TemporaryDirectory() as temp_dir:
            temp_path = self._temp_source_path(Path(temp_dir), payload.source_name)
            outputs = execute_run(
                config=config,
                source_config_path=temp_path,
                output_root=self.output_root,
            )
        return self._build_run_detail(outputs.run_dir)

    def verify_run(self, run_id: str) -> dict:
        run_dir = self._get_run_dir(run_id)
        verification = verify_run_path(run_dir)
        return {
            "run_id": run_id,
            "success": verification.success,
            "checked_files": verification.checked_files,
            "errors": verification.errors,
        }

    def replay_run(self, run_id: str) -> dict:
        run_dir = self._get_run_dir(run_id)
        outputs = replay_existing_run(run_dir, output_root=self.output_root)
        return self._build_run_detail(outputs.run_dir)

    def launch_showcase(self, scenario: str = DEFAULT_SHOWCASE_NAME) -> dict:
        selected = self._resolve_showcase_scenario(scenario)
        self._assert_hosted_config_envelope(load_config(selected.config_path).to_dict())
        showcase_root = self._showcase_output_root(selected.name, create=True)
        report = run_simulation_showcase(
            output_root=showcase_root,
            scenario=selected.name,
            runs_output_root=self.output_root,
            replay_output_root=self.output_root,
        )
        run_detail = self._build_run_detail(Path(report["run"]["run_dir"]))
        replay_detail = None
        if report.get("replay"):
            replay_detail = self._build_run_detail(Path(report["replay"]["run_dir"]))

        return {
            "scenario": self._build_showcase_summary(selected.name),
            "report": report,
            "run": run_detail,
            "replay_run": replay_detail,
            "artifact_links": self._build_showcase_artifact_links(selected.name, report),
            "urls": {
                "markdown_report": f"/api/showcases/{selected.name}/report",
                "json_report": f"/api/showcases/{selected.name}/report.json",
            },
        }

    def launch_showcase_comparison(self, scenario: str = DEFAULT_SHOWCASE_NAME) -> dict:
        selected = self._resolve_showcase_scenario(scenario)
        base_config = load_config(selected.config_path).to_dict()
        dimensions = self._guided_comparison_dimensions()
        variants = self._guided_comparison_variants(base_config)
        self._assert_hosted_config_envelope(
            base_config,
            planned_run_count=len(variants),
        )
        experiment_id = create_experiment_id("guided-comparison")
        experiment_label = f"{selected.name.replace('-', ' ').title()} guided comparison"
        parent_handle = self._start_parent_job(
            config=base_config,
            source_name=f"{selected.name}-guided-comparison",
            experiment={
                "id": experiment_id,
                "kind": "guided-comparison",
                "label": experiment_label,
                "planned_run_count": len(variants),
            },
            labels=("experiment", "guided-comparison", "multi-run"),
            metadata={
                "scenario": selected.name,
                "variant_count": len(variants),
            },
            message="Local guided comparison job started.",
        )

        run_dirs: list[Path] = []
        summaries: list[dict] = []
        details: list[dict] = []
        try:
            with TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                for ordinal, variant in enumerate(variants, start=1):
                    variant_config = self._guided_comparison_config(
                        base_config,
                        variant["values"],
                    )
                    temp_config_dir = temp_root / f"variant-{ordinal:02d}"
                    temp_config_dir.mkdir(parents=True, exist_ok=True)
                    temp_path = self._temp_source_path(
                        temp_config_dir,
                        f"{selected.name}-{variant['slug']}.yaml",
                    )
                    outputs = execute_run(
                        config=parse_config(variant_config),
                        source_config_path=temp_path,
                        output_root=self.output_root,
                        experiment=self._guided_comparison_context(
                            experiment_id=experiment_id,
                            label=experiment_label,
                            dimensions=dimensions,
                            variant=variant,
                            ordinal=ordinal,
                            total_runs=len(variants),
                        ),
                    )
                    run_dirs.append(outputs.run_dir)
                    detail = self._build_run_detail(outputs.run_dir)
                    details.append(detail)
                    summaries.append(detail["summary"])

            artifact_outputs = persist_experiment_artifact(
                run_dirs=run_dirs,
                run_details=details,
                experiments_root=self.experiments_root,
                label=experiment_label,
                experiment_id=experiment_id,
                kind="guided-comparison",
                execution_job=self._job_reference(parent_handle),
            )
            self._complete_experiment_job(
                parent_handle,
                experiment_id=artifact_outputs.experiment_id,
                experiment_dir=artifact_outputs.experiment_dir,
                bundle_path=artifact_outputs.bundle_path,
                run_details=details,
                message="Guided comparison job completed.",
            )
        except Exception as exc:
            self._job_registry().fail(parent_handle, exc)
            raise
        artifact_detail = self._build_experiment_detail(artifact_outputs.experiment_dir)

        return {
            "scenario": self._build_showcase_summary(selected.name),
            "comparison": artifact_detail["comparison"],
            "guide": self._build_guided_comparison_guide(artifact_detail["comparison"]),
            "runs": summaries,
            "artifact": artifact_detail,
            "execution_job": artifact_detail["execution_job"],
            "urls": artifact_detail["urls"],
        }

    def compare_runs(self, payload: CompareRunsRequest) -> dict:
        run_ids = [run_id for run_id in payload.run_ids if run_id]
        if len(run_ids) < 2:
            raise HTTPException(status_code=400, detail="Select at least two runs to compare")

        try:
            details = [self._build_run_detail(self._get_run_dir(run_id)) for run_id in run_ids]
            return build_run_comparison(details)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def create_experiment(self, payload: CreateExperimentRequest) -> dict:
        run_ids = [run_id for run_id in payload.run_ids if run_id]
        if len(run_ids) < 2:
            raise HTTPException(status_code=400, detail="Select at least two runs to save an experiment")

        experiment_id = create_experiment_id("comparison")
        experiment_label = payload.label or f"{len(run_ids)}-run comparison"
        parent_handle = self._start_parent_job(
            config={},
            source_name="manual-comparison",
            experiment={
                "id": experiment_id,
                "kind": "comparison",
                "label": experiment_label,
                "planned_run_count": len(run_ids),
            },
            labels=("experiment", "comparison", "multi-run"),
            metadata={"run_ids": run_ids},
            message="Local comparison artifact job started.",
        )
        try:
            run_dirs = [self._get_run_dir(run_id) for run_id in run_ids]
            details = [self._build_run_detail(run_dir) for run_dir in run_dirs]
            outputs = persist_experiment_artifact(
                run_dirs=run_dirs,
                run_details=details,
                experiments_root=self.experiments_root,
                label=experiment_label,
                experiment_id=experiment_id,
                kind="comparison",
                execution_job=self._job_reference(parent_handle),
            )
            self._complete_experiment_job(
                parent_handle,
                experiment_id=outputs.experiment_id,
                experiment_dir=outputs.experiment_dir,
                bundle_path=outputs.bundle_path,
                run_details=details,
                message="Comparison artifact job completed.",
            )
            return self._build_experiment_detail(outputs.experiment_dir)
        except ValueError as exc:
            self._job_registry().fail(parent_handle, exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            self._job_registry().fail(parent_handle, exc)
            raise

    def launch_sweep(self, payload: SweepRequest) -> dict:
        if self.hosted_demo.enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hosted demo disables arbitrary sweeps. "
                    "Run the packaged Self-Interaction Sweep template or install QS-DMSS locally."
                ),
            )
        try:
            base_config = parse_config(payload.config).to_dict()
            parameter = get_sweep_parameter(payload.parameter_path)
            values = coerce_sweep_values(parameter.path, payload.values)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        experiment_id = create_experiment_id("sweep")
        experiment_label = payload.experiment_name or f"{base_config['run']['name']} {parameter.label} sweep"
        parent_handle = self._start_parent_job(
            config=base_config,
            source_name=payload.source_name,
            experiment={
                "id": experiment_id,
                "kind": "sweep",
                "label": experiment_label,
                "parameter_path": parameter.path,
                "planned_run_count": len(values),
            },
            labels=("experiment", "sweep", "multi-run"),
            metadata={
                "parameter_path": parameter.path,
                "values": values,
                "planned_run_count": len(values),
            },
            message="Local sweep job started.",
        )

        run_dirs: list[Path] = []
        summaries: list[dict] = []
        details: list[dict] = []
        try:
            with TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                for index, value in enumerate(values, start=1):
                    varied_config = apply_sweep_value(base_config, parameter.path, value)
                    temp_config_dir = temp_root / f"run-{index:02d}"
                    temp_config_dir.mkdir(parents=True, exist_ok=True)
                    temp_path = self._temp_source_path(temp_config_dir, payload.source_name)
                    outputs = execute_run(
                        config=parse_config(varied_config),
                        source_config_path=temp_path,
                        output_root=self.output_root,
                        experiment=build_experiment_context(
                            experiment_id=experiment_id,
                            label=experiment_label,
                            parameter=parameter,
                            value=value,
                            ordinal=index,
                            total_runs=len(values),
                        ),
                    )
                    run_dirs.append(outputs.run_dir)
                    detail = self._build_run_detail(outputs.run_dir)
                    details.append(detail)
                    summaries.append(detail["summary"])

            comparison = build_run_comparison(details)
            artifact_outputs = persist_experiment_artifact(
                run_dirs=run_dirs,
                run_details=details,
                experiments_root=self.experiments_root,
                label=experiment_label,
                experiment_id=experiment_id,
                kind="sweep",
                execution_job=self._job_reference(parent_handle),
            )
            self._complete_experiment_job(
                parent_handle,
                experiment_id=artifact_outputs.experiment_id,
                experiment_dir=artifact_outputs.experiment_dir,
                bundle_path=artifact_outputs.bundle_path,
                run_details=details,
                message="Sweep artifact job completed.",
            )
        except Exception as exc:
            self._job_registry().fail(parent_handle, exc)
            raise
        artifact = self._build_experiment_detail(artifact_outputs.experiment_dir)

        return {
            "experiment": {
                "id": experiment_id,
                "label": experiment_label,
                "parameter_path": parameter.path,
                "parameter_label": parameter.label,
                "values": values,
                "run_ids": [summary["run_id"] for summary in summaries],
            },
            "runs": summaries,
            "comparison": comparison,
            "artifact": artifact,
            "execution_job": artifact["execution_job"],
        }

    def launch_campaign(self, payload: LaunchCampaignRequest) -> dict:
        try:
            base_config = parse_config(payload.config).to_dict()
            campaign_plan = build_campaign_plan(base_config)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        self._assert_hosted_packaged_campaign(payload, base_config, campaign_plan)

        study_template_path = None
        study_template_record = None
        if payload.study_template_id:
            study_template_path = self._ensure_local_campaign_study_template_path(
                payload.study_template_id,
            )
            study_template_record = self._read_json(study_template_path)

        run_dirs: list[Path] = []
        summaries: list[dict] = []
        details: list[dict] = []
        parent_handle = self._start_parent_job(
            config=base_config,
            source_name=payload.source_name,
            experiment={
                "id": campaign_plan["id"],
                "kind": "campaign",
                "label": campaign_plan["label"],
                "strategy": campaign_plan["strategy"],
                "planned_run_count": campaign_plan["planned_run_count"],
            },
            labels=("experiment", "campaign", "multi-run"),
            metadata={
                "dimension_count": campaign_plan["dimension_count"],
                "planned_run_count": campaign_plan["planned_run_count"],
                "study_template_id": payload.study_template_id,
            },
            message="Local campaign job started.",
        )
        try:
            with TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                for variant in campaign_plan["variants"]:
                    temp_config_dir = temp_root / f"run-{variant['ordinal']:02d}"
                    temp_config_dir.mkdir(parents=True, exist_ok=True)
                    temp_path = self._temp_source_path(temp_config_dir, payload.source_name)
                    outputs = execute_run(
                        config=parse_config(variant["config"]),
                        source_config_path=temp_path,
                        output_root=self.output_root,
                        experiment=build_campaign_context(
                            experiment_id=campaign_plan["id"],
                            label=campaign_plan["label"],
                            strategy=campaign_plan["strategy"],
                            dimensions=campaign_plan["dimensions"],
                            variant=variant["variant"],
                            ordinal=variant["ordinal"],
                            total_runs=campaign_plan["planned_run_count"],
                        ),
                    )
                    run_dirs.append(outputs.run_dir)
                    detail = self._build_run_detail(outputs.run_dir)
                    details.append(detail)
                    summaries.append(detail["summary"])
        except Exception as exc:
            try:
                failure_outputs = persist_failed_campaign_artifact(
                    campaign_plan=campaign_plan,
                    run_dirs=run_dirs,
                    run_details=details,
                    experiments_root=self.experiments_root,
                    error=exc,
                    execution_job=self._job_reference(parent_handle),
                )
                self._complete_experiment_job(
                    parent_handle,
                    experiment_id=failure_outputs.experiment_id,
                    experiment_dir=failure_outputs.experiment_dir,
                    bundle_path=failure_outputs.bundle_path,
                    run_details=details,
                    state="failed",
                    message="Campaign job failed; partial artifact was saved.",
                    error=exc,
                )
                failure_detail = self._build_experiment_detail(failure_outputs.experiment_dir)
            except Exception as persist_exc:
                self._job_registry().fail(parent_handle, persist_exc)
                raise HTTPException(
                    status_code=500,
                    detail={
                        "message": "Campaign failed, and the failed campaign artifact could not be saved.",
                        "error": str(exc),
                        "artifact_error": str(persist_exc),
                        "completed_run_ids": [summary["run_id"] for summary in summaries],
                    },
                ) from persist_exc
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Campaign failed; a failed campaign artifact was saved.",
                    "error": str(exc),
                    "experiment_id": failure_detail["summary"]["experiment_id"],
                    "run_ids": failure_detail["summary"]["run_ids"],
                    "bundle": failure_detail["urls"]["bundle"],
                    "report": failure_detail["urls"]["report"],
                },
            ) from exc

        try:
            comparison = build_run_comparison(details)
            artifact_outputs = persist_experiment_artifact(
                run_dirs=run_dirs,
                run_details=details,
                experiments_root=self.experiments_root,
                label=campaign_plan["label"],
                experiment_id=campaign_plan["id"],
                kind="campaign",
                execution_job=self._job_reference(parent_handle),
            )
            self._complete_experiment_job(
                parent_handle,
                experiment_id=artifact_outputs.experiment_id,
                experiment_dir=artifact_outputs.experiment_dir,
                bundle_path=artifact_outputs.bundle_path,
                run_details=details,
                message="Campaign job completed.",
            )
        except Exception as exc:
            self._job_registry().fail(parent_handle, exc)
            raise
        artifact = self._build_experiment_detail(artifact_outputs.experiment_dir)
        campaign_summary = {
            "id": campaign_plan["id"],
            "label": campaign_plan["label"],
            "strategy": campaign_plan["strategy"],
            "dimension_count": campaign_plan["dimension_count"],
            "planned_run_count": campaign_plan["planned_run_count"],
            "dimensions": campaign_plan["dimensions"],
            "run_ids": [summary["run_id"] for summary in summaries],
            "recommended_run_id": (comparison.get("decision") or {}).get("recommended_run_id"),
        }
        study_template = None
        if study_template_path is not None:
            study_template = self._record_campaign_study_last_run(
                study_template_path,
                campaign_summary=campaign_summary,
                comparison=comparison,
                artifact=artifact,
                run_count=len(summaries),
            )

        return {
            "campaign": campaign_summary,
            "runs": summaries,
            "comparison": comparison,
            "guide": self._build_campaign_study_guide(study_template_record, comparison),
            "artifact": artifact,
            "execution_job": artifact["execution_job"],
            "study_template": study_template,
        }

    def export_research_object(self, payload: ResearchObjectExportRequest) -> dict:
        research_object = dict(payload.research_object)
        markdown = str(research_object.get("markdown") or "").strip()
        if not markdown:
            raise HTTPException(status_code=400, detail="Research object markdown is required")

        file_name = safe_filename(
            str(research_object.get("fileName") or "qs-dmss-research-object.md"),
            default="qs-dmss-research-object.md",
            suffixes=(".md",),
        )
        export_id = create_experiment_id("research-object")
        scenario = research_object.get("scenario") or {}
        label = str(scenario.get("label") or research_object.get("runId") or export_id)
        export_dir = self._research_object_export_dir(export_id, create=True)
        markdown_path = export_dir / "research-object.md"
        source_json_path = export_dir / "research-object.json"
        parent_handle = self._start_parent_job(
            config={},
            source_name=file_name,
            experiment={
                "id": export_id,
                "kind": "research-object-export",
                "label": label,
            },
            labels=("research-object", "export"),
            metadata={
                "file_name": file_name,
                "run_id": research_object.get("runId"),
                "scenario": scenario,
                "campaign_study_available": bool(
                    (research_object.get("campaignStudy") or {}).get("available")
                ),
            },
            message="Local research-object export job started.",
        )

        try:
            export_provenance = (
                "\n## Export Provenance\n\n"
                f"Executor job: `{parent_handle.job_id}`\n\n"
                f"Backend: `{parent_handle.backend}`\n\n"
                f"Registry: `{parent_handle.status_uri}`\n"
            )
            persisted_markdown = f"{markdown}\n{export_provenance}\n"
            research_object["markdown"] = persisted_markdown
            research_object["export"] = {
                "id": export_id,
                "file_name": file_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            markdown_path.write_text(persisted_markdown, encoding="utf-8")
            source_json_path.write_text(
                json.dumps(research_object, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            registry = self._job_registry()
            registry.update(
                parent_handle,
                "collecting",
                message="Collecting research-object export artifacts.",
                progress=0.9,
                metadata={
                    "export_id": export_id,
                    "markdown_path": str(markdown_path),
                    "source_json_path": str(source_json_path),
                },
            )
            result = ExecutionJobResult(
                handle=ExecutionJobHandle(
                    job_id=parent_handle.job_id,
                    backend=parent_handle.backend,
                    state="succeeded",
                    status_uri=parent_handle.status_uri,
                ),
                state="succeeded",
                experiment_id=export_id,
                experiment_dir=export_dir,
                artifacts=(
                    ExecutionArtifact(
                        role="research_object",
                        path=markdown_path,
                        media_type="text/markdown",
                        label="Research object Markdown",
                    ),
                    ExecutionArtifact(
                        role="other",
                        path=source_json_path,
                        media_type="application/json",
                        label="Research object source JSON",
                    ),
                ),
            )
            registry.complete(
                parent_handle,
                result,
                message="Research-object export job completed.",
            )
        except Exception as exc:
            self._job_registry().fail(parent_handle, exc)
            raise

        job_detail = self._build_job_detail(self._get_job_record(parent_handle.job_id))
        export = {
            "id": export_id,
            "file_name": file_name,
            "markdown_path": str(markdown_path),
            "source_json_path": str(source_json_path),
            "download_url": f"/api/research-objects/{export_id}/download",
        }
        return {
            "research_object": research_object,
            "export": export,
            "execution_job": job_detail,
        }

    def bundle_path(self, run_id: str) -> Path:
        run_dir = self._get_run_dir(run_id)
        bundle_path = run_dir / "evidence_bundle.zip"
        if not bundle_path.exists():
            raise HTTPException(status_code=404, detail="Evidence bundle not found")
        return bundle_path

    def run_bundle_profile_path(self, run_id: str, profile_name: str) -> Path:
        profile = RUN_BUNDLE_PROFILES.get(profile_name)
        if profile is None:
            raise HTTPException(status_code=404, detail="Evidence bundle profile not found")
        run_dir = self._get_run_dir(run_id)
        safe_run_id = safe_filename(run_id, default="run")
        bundle_root = contained_path(self.output_root, "_derived_bundles")
        bundle_root.mkdir(parents=True, exist_ok=True)
        bundle_path = contained_path(
            bundle_root,
            f"{safe_run_id}-{safe_filename(profile_name, default='profile')}-bundle.zip",
        )
        if bundle_path.exists():
            return bundle_path

        included_files: list[str] = []
        missing_files: list[str] = []
        for relative_name in profile["files"]:
            candidate = contained_path(run_dir, relative_name)
            if candidate.exists() and candidate.is_file():
                included_files.append(relative_name)
            else:
                missing_files.append(relative_name)

        profile_record = {
            "schema_version": "1.0",
            "profile": profile_name,
            "title": profile["title"],
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "claim_boundary": profile["claim_boundary"],
            "included_files": included_files,
            "missing_optional_files": missing_files,
        }
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "bundle-profile.json",
                json.dumps(profile_record, indent=2, sort_keys=True) + "\n",
            )
            for relative_name in included_files:
                archive.write(contained_path(run_dir, relative_name), arcname=relative_name)
        return bundle_path

    def report_path(self, run_id: str) -> Path:
        run_dir = self._get_run_dir(run_id)
        report_path = run_dir / "report.html"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Run report not found")
        return report_path

    def experiment_bundle_path(self, experiment_id: str) -> Path:
        experiment_dir = self._get_experiment_dir(experiment_id)
        bundle_path = experiment_dir / "evidence_bundle.zip"
        if not bundle_path.exists():
            raise HTTPException(status_code=404, detail="Experiment bundle not found")
        return bundle_path

    def experiment_report_path(self, experiment_id: str) -> Path:
        experiment_dir = self._get_experiment_dir(experiment_id)
        report_path = experiment_dir / "report.html"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Experiment report not found")
        return report_path

    def experiment_workbook_path(self, experiment_id: str) -> Path:
        experiment_dir = self._get_experiment_dir(experiment_id)
        workbook_path = experiment_dir / "workbook.html"
        if not workbook_path.exists():
            raise HTTPException(status_code=404, detail="Experiment workbook not found")
        return workbook_path

    def research_object_markdown_path(self, export_id: str) -> tuple[Path, str]:
        export_dir = self._research_object_export_dir(export_id)
        metadata_path = export_dir / "research-object.json"
        markdown_path = export_dir / "research-object.md"
        if not metadata_path.exists() or not markdown_path.exists():
            raise HTTPException(status_code=404, detail="Research object export not found")
        metadata = self._read_json(metadata_path)
        export = metadata.get("export") or {}
        file_name = safe_filename(
            str(export.get("file_name") or "qs-dmss-research-object.md"),
            default="qs-dmss-research-object.md",
            suffixes=(".md",),
        )
        return markdown_path, file_name

    def showcase_markdown_path(self, scenario: str) -> Path:
        report_path = self._showcase_output_root(
            self._resolve_showcase_scenario(scenario).name
        ) / SHOWCASE_MARKDOWN_REPORT
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Showcase report not found")
        return report_path

    def showcase_json_path(self, scenario: str) -> Path:
        report_path = self._showcase_output_root(
            self._resolve_showcase_scenario(scenario).name
        ) / SHOWCASE_JSON_REPORT
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Showcase JSON report not found")
        return report_path

    def showcase_artifact_path(self, scenario: str, artifact_name: str) -> Path:
        scenario_name = self._resolve_showcase_scenario(scenario).name
        artifact_root = self._showcase_output_root(scenario_name) / "artifacts"
        artifact_path = contained_path(
            artifact_root,
            safe_filename(artifact_name, default="artifact"),
        )
        if not artifact_path.exists() or not artifact_path.is_file():
            raise HTTPException(status_code=404, detail="Showcase artifact not found")
        return artifact_path

    def index_path(self) -> Path:
        return self.static_root / "index.html"

    def static_asset_revision(self) -> str:
        """Return a stable revision for the browser assets referenced by the cockpit shell."""
        digest = hashlib.sha256()
        for asset_name in ("styles.css", "app.js"):
            asset_path = self.static_root / asset_name
            digest.update(asset_name.encode("utf-8"))
            digest.update(asset_path.read_bytes())
        return digest.hexdigest()[:12]

    def _list_run_dirs(self) -> list[Path]:
        if not self.output_root.exists():
            return []
        run_dirs = [
            path
            for path in self.output_root.iterdir()
            if path.is_dir() and (path / "run.json").exists()
        ]
        return sorted(run_dirs, key=lambda path: path.stat().st_mtime, reverse=True)

    def _list_experiment_dirs(self) -> list[Path]:
        if not self.experiments_root.exists():
            return []
        experiment_dirs = [
            path
            for path in self.experiments_root.iterdir()
            if path.is_dir() and (path / "experiment.json").exists()
        ]
        return sorted(experiment_dirs, key=lambda path: path.stat().st_mtime, reverse=True)

    def _safe_source_name(self, source_name: str) -> str:
        return safe_filename(
            source_name,
            default="cockpit.yaml",
            suffixes=(".yaml", ".yml"),
        )

    def _temp_source_path(self, temp_dir: Path, source_name: str) -> Path:
        return contained_path(temp_dir, self._safe_source_name(source_name))

    def _get_run_dir(self, run_id: str) -> Path:
        run_dir = (self.output_root / run_id).resolve()
        if run_dir.parent != self.output_root.resolve():
            raise HTTPException(status_code=404, detail="Run not found")
        if not run_dir.exists() or not (run_dir / "run.json").exists():
            raise HTTPException(status_code=404, detail="Run not found")
        return run_dir

    def _get_experiment_dir(self, experiment_id: str) -> Path:
        experiment_dir = (self.experiments_root / experiment_id).resolve()
        if experiment_dir.parent != self.experiments_root.resolve():
            raise HTTPException(status_code=404, detail="Experiment not found")
        if not experiment_dir.exists() or not (experiment_dir / "experiment.json").exists():
            raise HTTPException(status_code=404, detail="Experiment not found")
        return experiment_dir

    def _job_registry(self) -> LocalJobRegistry:
        return LocalJobRegistry(self.jobs_root)

    def _get_job_record(self, job_id: str) -> dict:
        try:
            return self._job_registry().get(job_id)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail="Execution job not found") from exc

    def _job_reference(self, handle: ExecutionJobHandle) -> dict[str, str | None]:
        return {
            "job_id": handle.job_id,
            "backend": handle.backend,
            "registry_path": handle.status_uri,
        }

    def _start_parent_job(
        self,
        *,
        config: dict[str, Any] | None,
        source_name: str,
        experiment: dict[str, Any],
        labels: tuple[str, ...],
        metadata: dict[str, Any],
        message: str,
    ) -> ExecutionJobHandle:
        registry = self._job_registry()
        handle = registry.create(
            ExecutionJobSpec(
                config=config or {},
                source_name=source_name,
                output_root=self.output_root,
                experiment=experiment,
                labels=labels,
                metadata=metadata,
            )
        )
        registry.update(handle, "running", message=message, progress=0.1)
        return handle

    def _child_job_ids_from_details(self, run_details: list[dict]) -> list[str]:
        child_job_ids: list[str] = []
        for detail in run_details:
            summary = self._build_execution_job_summary(
                detail.get("run_record", {}).get("execution_job")
            )
            if summary and summary.get("job_id"):
                child_job_ids.append(str(summary["job_id"]))
        return child_job_ids

    def _complete_experiment_job(
        self,
        handle: ExecutionJobHandle,
        *,
        experiment_id: str,
        experiment_dir: Path,
        bundle_path: Path,
        run_details: list[dict],
        state: JobState = "succeeded",
        message: str = "Experiment artifact job completed.",
        error: BaseException | str | None = None,
    ) -> dict:
        registry = self._job_registry()
        child_job_ids = self._child_job_ids_from_details(run_details)
        registry.update(
            handle,
            "collecting",
            message="Collecting experiment artifact outputs.",
            progress=0.9,
            metadata={
                "child_job_ids": child_job_ids,
                "experiment_id": experiment_id,
                "run_count": len(run_details),
            },
        )
        result = ExecutionJobResult(
            handle=ExecutionJobHandle(
                job_id=handle.job_id,
                backend=handle.backend,
                state=state,
                status_uri=handle.status_uri,
            ),
            state=state,
            experiment_id=experiment_id,
            experiment_dir=experiment_dir,
            artifacts=(
                ExecutionArtifact(
                    role="experiment_directory",
                    path=experiment_dir,
                    label="Experiment directory",
                ),
                ExecutionArtifact(
                    role="comparison",
                    path=experiment_dir / "comparison.json",
                    media_type="application/json",
                    label="Comparison data",
                ),
                ExecutionArtifact(
                    role="evidence_bundle",
                    path=bundle_path,
                    media_type="application/zip",
                    label="Experiment evidence bundle",
                ),
                ExecutionArtifact(
                    role="report",
                    path=experiment_dir / "report.html",
                    media_type="text/html",
                    label="Experiment report",
                ),
                ExecutionArtifact(
                    role="manifest",
                    path=experiment_dir / "manifest.sha256.json",
                    media_type="application/json",
                    label="Experiment manifest",
                ),
            ),
            metrics={"run_count": len(run_details), "child_job_count": len(child_job_ids)},
            error=str(error) if error else None,
        )
        registry.complete(handle, result, message=message)
        return self._build_job_detail(self._get_job_record(handle.job_id))

    def _missing_job_summary(self, reference: dict, message: str) -> dict:
        return {
            "available": False,
            "job_id": reference.get("job_id"),
            "backend": reference.get("backend"),
            "registry_path": reference.get("registry_path"),
            "state": "unavailable",
            "message": message,
            "created_at": None,
            "updated_at": None,
            "progress": None,
            "labels": [],
            "source_name": None,
            "run_id": None,
            "experiment_id": None,
            "metadata": {},
            "child_job_ids": [],
            "artifact_roles": [],
            "lifecycle_states": [],
            "url": (
                f"/api/jobs/{reference['job_id']}"
                if reference.get("job_id")
                else None
            ),
        }

    def _build_job_summary(self, record: dict) -> dict:
        spec = record.get("spec") or {}
        result = record.get("result") or {}
        artifacts = result.get("artifacts") or []
        lifecycle = record.get("lifecycle") or []
        metadata = {
            **(spec.get("metadata") or {}),
            **(record.get("metadata") or {}),
        }
        return {
            "available": True,
            "job_id": record["job_id"],
            "backend": record["backend"],
            "registry_path": str(self.jobs_root / record["job_id"] / "job.json"),
            "state": record["state"],
            "message": record.get("message", ""),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "progress": record.get("progress"),
            "labels": spec.get("labels") or [],
            "source_name": spec.get("source_name"),
            "run_id": result.get("run_id"),
            "experiment_id": result.get("experiment_id") or metadata.get("experiment_id"),
            "metadata": metadata,
            "child_job_ids": metadata.get("child_job_ids") or [],
            "artifact_roles": [
                artifact.get("role")
                for artifact in artifacts
                if artifact.get("role")
            ],
            "lifecycle_states": [
                event.get("state")
                for event in lifecycle
                if event.get("state")
            ],
            "url": f"/api/jobs/{record['job_id']}",
        }

    def _build_job_detail(self, record: dict) -> dict:
        return {
            "summary": self._build_job_summary(record),
            "spec": record.get("spec") or {},
            "lifecycle": record.get("lifecycle") or [],
            "result": record.get("result") or {},
            "record": record,
        }

    def _build_execution_job_summary(self, reference: dict | None) -> dict | None:
        if not isinstance(reference, dict) or not reference.get("job_id"):
            return None
        try:
            return self._build_job_summary(self._get_job_record(str(reference["job_id"])))
        except HTTPException:
            return self._missing_job_summary(
                reference,
                "Local job record is not available for this run.",
            )

    def _build_execution_job_detail(self, reference: dict | None) -> dict | None:
        if not isinstance(reference, dict) or not reference.get("job_id"):
            return None
        try:
            return self._build_job_detail(self._get_job_record(str(reference["job_id"])))
        except HTTPException:
            return {
                "summary": self._missing_job_summary(
                    reference,
                    "Local job record is not available for this run.",
                ),
                "spec": {},
                "lifecycle": [],
                "result": {},
                "record": None,
            }

    def _resolve_showcase_scenario(self, scenario: str):
        try:
            return resolve_showcase_scenario(scenario)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail="Showcase scenario not found") from exc

    def _showcase_output_root(self, scenario: str, *, create: bool = False) -> Path:
        showcases_root = self.output_root.resolve().parent / "showcases"
        output_root = contained_path(
            showcases_root,
            safe_filename(scenario, default=DEFAULT_SHOWCASE_NAME),
        )
        if create:
            output_root.mkdir(parents=True, exist_ok=True)
        return output_root

    def _research_objects_root(self, *, create: bool = False) -> Path:
        export_root = self.experiments_root / "research-objects"
        if create:
            export_root.mkdir(parents=True, exist_ok=True)
        return export_root

    def _research_object_export_dir(
        self,
        export_id: str,
        *,
        create: bool = False,
    ) -> Path:
        export_root = self._research_objects_root(create=create)
        export_dir = contained_path(
            export_root,
            safe_filename(export_id, default="research-object"),
        )
        if create:
            export_dir.mkdir(parents=True, exist_ok=False)
        if not export_dir.exists() or not export_dir.is_dir():
            raise HTTPException(status_code=404, detail="Research object export not found")
        return export_dir

    def _research_object_export_path(self, export_id: str) -> Path:
        export_path = self._research_object_export_dir(export_id) / "research-object.json"
        if not export_path.exists() or not export_path.is_file():
            raise HTTPException(status_code=404, detail="Research object export not found")
        return export_path

    def _build_research_object_export_detail(self, path: Path) -> dict:
        record = self._read_json(path)
        export = record.get("export") or {}
        scenario = record.get("scenario") or {}
        export_id = str(export.get("id") or path.parent.name)
        file_name = safe_filename(
            str(export.get("file_name") or "qs-dmss-research-object.md"),
            default="qs-dmss-research-object.md",
            suffixes=(".md",),
        )
        return {
            "summary": {
                "id": export_id,
                "file_name": file_name,
                "created_at": export.get("created_at"),
                "run_id": record.get("runId"),
                "scenario_label": scenario.get("label") or scenario.get("name"),
                "campaign_study_available": bool(
                    (record.get("campaignStudy") or {}).get("available")
                ),
            },
            "research_object": record,
            "urls": {
                "download": f"/api/research-objects/{export_id}/download",
            },
        }

    def _workspaces_root(self, *, create: bool = False) -> Path:
        workspace_root = self.experiments_root / "workspaces"
        if create:
            workspace_root.mkdir(parents=True, exist_ok=True)
        return workspace_root

    def _workspace_dir(self, workspace_id: str, *, create: bool = False) -> Path:
        workspace_root = self._workspaces_root(create=create)
        workspace_dir = contained_path(
            workspace_root,
            safe_filename(workspace_id, default="workspace"),
        )
        if create:
            workspace_dir.mkdir(parents=True, exist_ok=False)
        if not workspace_dir.exists() or not workspace_dir.is_dir():
            raise HTTPException(status_code=404, detail="Workspace export not found")
        return workspace_dir

    def _get_workspace_path(self, workspace_id: str) -> Path:
        workspace_path = self._workspace_dir(workspace_id) / "workspace.json"
        if not workspace_path.exists() or not workspace_path.is_file():
            raise HTTPException(status_code=404, detail="Workspace export not found")
        return workspace_path

    def _list_workspace_paths(self) -> list[Path]:
        workspace_root = self._workspaces_root()
        if not workspace_root.exists():
            return []
        return sorted(
            [
                path / "workspace.json"
                for path in workspace_root.iterdir()
                if path.is_dir() and (path / "workspace.json").is_file()
            ],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def _campaign_studies_root(self, *, create: bool = False) -> Path:
        studies_root = self.experiments_root / "campaign-studies"
        if create:
            studies_root.mkdir(parents=True, exist_ok=True)
        return studies_root

    def _packaged_campaign_studies_root(self) -> Path:
        return bundled_assets_root() / "campaign-studies"

    def _list_campaign_study_template_paths(self) -> list[Path]:
        studies_root = self._campaign_studies_root()
        if not studies_root.exists():
            return []
        return sorted(
            [
                path
                for path in studies_root.glob("*.json")
                if path.is_file()
            ],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def _list_packaged_campaign_study_template_paths(self) -> list[Path]:
        studies_root = self._packaged_campaign_studies_root()
        if not studies_root.exists():
            return []
        return sorted(
            [
                path
                for path in studies_root.glob("*.json")
                if path.is_file()
            ],
            key=lambda path: path.name,
        )

    def _get_campaign_study_template_path(self, template_id: str) -> Path:
        template_name = safe_filename(
            template_id,
            default="campaign-study",
            suffixes=(".json",),
        )
        local_path = contained_path(self._campaign_studies_root(), template_name)
        if local_path.exists() and local_path.is_file():
            return local_path

        packaged_root = self._packaged_campaign_studies_root()
        packaged_path = contained_path(packaged_root, template_name)
        if packaged_path.exists() and packaged_path.is_file():
            return packaged_path

        raise HTTPException(status_code=404, detail="Campaign study template not found")

    def _ensure_local_campaign_study_template_path(self, template_id: str) -> Path:
        template_name = safe_filename(
            template_id,
            default="campaign-study",
            suffixes=(".json",),
        )
        studies_root = self._campaign_studies_root(create=True)
        local_path = contained_path(studies_root, template_name)
        if local_path.exists() and local_path.is_file():
            return local_path

        source_path = self._get_campaign_study_template_path(template_id)
        record = self._read_json(source_path)
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        record.setdefault("created_at", now)
        record["updated_at"] = now
        if record.get("packaged"):
            record["installed_from_packaged_template"] = True
        local_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return local_path

    def _campaign_study_template_id(self, label: str) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stem = safe_filename(
            label.lower().replace(" ", "-"),
            default="campaign-study",
        )
        base_id = f"{stem}-{timestamp}"
        template_id = base_id
        index = 2
        studies_root = self._campaign_studies_root(create=True)
        while contained_path(studies_root, f"{template_id}.json").exists():
            template_id = f"{base_id}-{index}"
            index += 1
        return template_id

    def _normalize_campaign_study_template(self, template: dict[str, Any]) -> dict:
        if not isinstance(template, dict):
            raise ValueError("Campaign study template must be an object")
        raw_config = template.get("config")
        if not isinstance(raw_config, dict):
            raise ValueError("Campaign study template requires a config object")

        config = parse_config(raw_config).to_dict()
        campaign_plan = build_campaign_plan(config)
        objective = config.get("objective") or {}
        constraints = {"require_verification": True, **(config.get("constraints") or {})}
        ranking = config.get("ranking") or {}
        label = str(
            template.get("label")
            or campaign_plan["label"]
            or "Campaign Studio study template"
        ).strip()
        if not label:
            label = "Campaign Studio study template"
        description = str(
            template.get("description")
            or objective.get("summary")
            or "Reusable Campaign Studio study template."
        ).strip()
        source_config_name = self._safe_source_name(
            str(template.get("source_config_name") or "campaign-study.yaml")
        )
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        campaign = {
            "label": campaign_plan["label"],
            "strategy": campaign_plan["strategy"],
            "max_runs": config.get("campaign", {}).get(
                "max_runs",
                campaign_plan["planned_run_count"],
            ),
            "planned_run_count": campaign_plan["planned_run_count"],
            "dimension_count": campaign_plan["dimension_count"],
            "dimensions": campaign_plan["dimensions"],
        }
        scoring_contract = {
            "objective": objective,
            "constraints": constraints,
            "ranking": {
                "primary_metric_weight": ranking.get("primary_metric_weight"),
                "weights": ranking.get("weights", {}),
            },
            "planned_run_count": campaign_plan["planned_run_count"],
            "max_runs": campaign["max_runs"],
        }

        record: dict[str, Any] = {
            "schema_version": 1,
            "template_id": self._campaign_study_template_id(label),
            "label": label,
            "description": description,
            "created_at": now,
            "updated_at": now,
            "source_config_name": source_config_name,
            "campaign": campaign,
            "objective": objective,
            "constraints": constraints,
            "ranking": scoring_contract["ranking"],
            "scoring_contract": scoring_contract,
            "config": config,
        }
        for key in (
            "purpose",
            "expected_runtime",
            "metrics",
            "limitations",
            "non_claims",
            "interpretation",
        ):
            if key in template:
                record[key] = template[key]
        if template.get("packaged"):
            record["packaged"] = True
        if template.get("imported_from_template_id"):
            record["imported_from_template_id"] = str(template["imported_from_template_id"])
        if template.get("imported_from_workspace_id"):
            record["imported_from_workspace_id"] = str(template["imported_from_workspace_id"])
        return record

    def _record_campaign_study_last_run(
        self,
        path: Path,
        *,
        campaign_summary: dict,
        comparison: dict,
        artifact: dict,
        run_count: int,
    ) -> dict:
        record = self._read_json(path)
        decision = comparison.get("decision") or {}
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        last_run = {
            "ran_at": now,
            "status": "completed",
            "campaign_id": campaign_summary["id"],
            "campaign_label": campaign_summary["label"],
            "strategy": campaign_summary["strategy"],
            "planned_run_count": campaign_summary["planned_run_count"],
            "run_count": run_count,
            "run_ids": campaign_summary["run_ids"],
            "recommended_run_id": campaign_summary.get("recommended_run_id"),
            "decision_status": decision.get("status"),
            "recommended_score": decision.get("recommended_score"),
            "reason": decision.get("reason"),
            "experiment_id": artifact["summary"]["experiment_id"],
            "experiment_report_url": artifact["urls"]["report"],
            "experiment_bundle_url": artifact["urls"]["bundle"],
        }
        record["last_run"] = last_run
        record["updated_at"] = now
        path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return self._build_campaign_study_detail(path)

    def _campaign_study_urls(self, template_id: str) -> dict:
        return {
            "detail": f"/api/campaign-studies/{template_id}",
            "download": f"/api/campaign-studies/{template_id}/download",
        }

    def _build_campaign_study_summary(self, record: dict) -> dict:
        template_id = record["template_id"]
        campaign = record.get("campaign") or {}
        objective = record.get("objective") or {}
        packaged = bool(record.get("packaged"))
        return {
            "template_id": template_id,
            "label": record.get("label", template_id),
            "description": record.get("description", ""),
            "purpose": record.get("purpose"),
            "expected_runtime": record.get("expected_runtime"),
            "metrics": record.get("metrics") or [],
            "limitations": record.get("limitations") or [],
            "non_claims": record.get("non_claims") or [],
            "interpretation": record.get("interpretation") or {},
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "source_config_name": record.get("source_config_name"),
            "campaign_label": campaign.get("label"),
            "strategy": campaign.get("strategy"),
            "planned_run_count": campaign.get("planned_run_count"),
            "dimension_count": campaign.get("dimension_count"),
            "objective_name": objective.get("name"),
            "primary_metric": objective.get("primary_metric"),
            "goal": objective.get("goal"),
            "packaged": packaged,
            "origin": "packaged" if packaged else "local",
            "imported": bool(record.get("imported_from_template_id")),
            "imported_from_template_id": record.get("imported_from_template_id"),
            "exportable": True,
            "last_run": record.get("last_run"),
            "urls": self._campaign_study_urls(template_id),
        }

    def _build_campaign_study_detail(self, path: Path) -> dict:
        record = self._read_json(path)
        return {
            "summary": self._build_campaign_study_summary(record),
            "template": record,
            "urls": self._campaign_study_urls(record["template_id"]),
        }

    def _build_campaign_study_guide(
        self,
        record: dict | None,
        comparison: dict[str, Any],
    ) -> dict[str, Any]:
        interpretation = (record or {}).get("interpretation") or {}
        label = (record or {}).get("label") or "Campaign Studio study"
        rows = comparison.get("rows") or []
        ranges = comparison.get("ranges") or {}
        decision = comparison.get("decision") or {}
        shared = comparison.get("shared_experiment") or {}
        dimensions = shared.get("dimensions") or []
        changed_paths = ", ".join(
            str(dimension.get("path") or dimension.get("label"))
            for dimension in dimensions
        )
        if not changed_paths:
            changed_paths = "the configured campaign parameters"

        what_changed = list(interpretation.get("what_changed") or [])
        if rows:
            energy_span = ranges.get("energy_drift", {}).get("span")
            norm_span = ranges.get("norm_drift", {}).get("span")
            density_span = ranges.get("max_density", {}).get("span")
            if energy_span is not None:
                what_changed.append(f"Energy drift span across completed variants: {energy_span:.3e}.")
            if norm_span is not None:
                what_changed.append(f"Norm drift span across completed variants: {norm_span:.3e}.")
            if density_span is not None:
                what_changed.append(f"Max-density span across completed variants: {density_span:.3e}.")
        if decision.get("recommended_run_id"):
            what_changed.append(
                "The scoring contract recommends "
                f"{decision['recommended_run_id']} because: {decision.get('reason', 'no rationale recorded')}"
            )
        if not what_changed:
            what_changed.append(f"The campaign varies {changed_paths} and compares the resulting evidence rows.")

        return {
            "title": f"{label} guided interpretation",
            "plain_language_summary": interpretation.get(
                "summary",
                (
                    f"QS-DMSS ran a Campaign Studio study varying {changed_paths}. "
                    "Read the result as a reproducible parameter-study workflow, not a scientific verdict."
                ),
            ),
            "what_changed": what_changed,
            "metric_meanings": list(
                interpretation.get("metric_meanings")
                or [
                    "Energy and norm drift are stability-oriented diagnostics.",
                    "Max density is an output response to compare across variants.",
                    "Elapsed seconds keeps reviewer-facing runtime visible.",
                    "The recommendation is a scoring-contract result, not peer-reviewed validation.",
                ]
            ),
            "what_this_does_not_claim": list(
                interpretation.get("what_this_does_not_claim")
                or (record or {}).get("non_claims")
                or [
                    "It does not prove that one parameter value is scientifically correct.",
                    "It does not replace external validation or peer review.",
                ]
            ),
            "review_prompt": interpretation.get(
                "review_prompt",
                "A useful review comment can focus on whether the campaign evidence makes parameter behavior understandable.",
            ),
        }

    def _build_workspace_record(self, payload: WorkspaceExportRequest) -> dict:
        workspace_id = create_experiment_id("workspace")
        now = datetime.now(timezone.utc).isoformat()
        collaborators = self._normalize_workspace_collaborators(payload.collaborators)
        annotations = self._normalize_workspace_annotations(
            payload.annotations,
            collaborators,
        )
        warnings: list[dict] = []
        resources = {
            "runs": self._collect_workspace_resources(
                "run",
                self._dedupe_text_values(payload.run_ids),
                self._build_workspace_run_resource,
                warnings,
            ),
            "experiments": self._collect_workspace_resources(
                "experiment",
                self._dedupe_text_values(payload.experiment_ids),
                lambda experiment_id: self._build_experiment_detail(
                    self._get_experiment_dir(experiment_id)
                ),
                warnings,
            ),
            "campaign_study_templates": self._collect_workspace_resources(
                "campaign-study",
                self._dedupe_text_values(payload.campaign_study_template_ids),
                lambda template_id: self._build_campaign_study_detail(
                    self._get_campaign_study_template_path(template_id)
                ),
                warnings,
            ),
            "research_objects": self._collect_workspace_resources(
                "research-object",
                self._dedupe_text_values(payload.research_object_ids),
                lambda export_id: self._build_research_object_export_detail(
                    self._research_object_export_path(export_id)
                ),
                warnings,
            ),
        }
        job_summaries = self._workspace_job_summaries(resources)
        record = {
            "schema_version": 1,
            "workspace_id": workspace_id,
            "title": str(payload.title or "QS-DMSS workspace").strip()
            or "QS-DMSS workspace",
            "description": (
                str(payload.description).strip()
                if payload.description is not None
                else None
            ),
            "created_at": now,
            "updated_at": now,
            "collaborators": collaborators,
            "annotations": annotations,
            "resources": resources,
            "job_summaries": job_summaries,
            "warnings": warnings,
        }
        record["summary"] = self._workspace_resource_counts(
            resources,
            collaborators,
            annotations,
            job_summaries,
            warnings,
        )
        return record

    def _normalize_imported_workspace(self, workspace: dict[str, Any]) -> dict:
        if not isinstance(workspace, dict):
            raise ValueError("Workspace import requires a workspace object")
        record = json.loads(json.dumps(workspace))
        resources = record.get("resources") or {}
        if not isinstance(resources, dict):
            raise ValueError("Workspace resources must be an object")

        source_workspace_id = str(record.get("workspace_id") or "workspace")
        now = datetime.now(timezone.utc).isoformat()
        collaborators = self._normalize_workspace_collaborators(
            record.get("collaborators") or []
        )
        annotations = self._normalize_workspace_annotations(
            record.get("annotations") or [],
            collaborators,
        )
        job_summaries = self._workspace_job_summaries(resources)
        record["workspace_id"] = create_experiment_id("workspace")
        record["imported_from_workspace_id"] = source_workspace_id
        record["imported_at"] = now
        record["updated_at"] = now
        record["title"] = str(record.get("title") or "Imported QS-DMSS workspace").strip()
        record["description"] = record.get("description")
        record["collaborators"] = collaborators
        record["annotations"] = annotations
        record["resources"] = resources
        record["job_summaries"] = job_summaries
        record["warnings"] = record.get("warnings") or []
        record["summary"] = self._workspace_resource_counts(
            resources,
            collaborators,
            annotations,
            job_summaries,
            record["warnings"],
        )
        return record

    def _install_workspace_campaign_studies(self, record: dict) -> list[dict]:
        installed: list[dict] = []
        resources = record.get("resources") or {}
        templates = resources.get("campaign_study_templates") or []
        if not isinstance(templates, list):
            raise ValueError("Workspace campaign study templates must be a list")

        for item in templates:
            if not isinstance(item, dict):
                continue
            template = item.get("template")
            if not isinstance(template, dict):
                continue
            imported_template = dict(template)
            imported_from_template_id = imported_template.get("template_id")
            if imported_from_template_id:
                imported_template["imported_from_template_id"] = str(
                    imported_from_template_id
                )
            imported_template["imported_from_workspace_id"] = record["workspace_id"]
            imported_template.pop("packaged", None)
            detail = self.save_campaign_study_template(
                CampaignStudyTemplateRequest(template=imported_template),
            )
            installed.append(detail["summary"])
        return installed

    def _build_workspace_run_resource(self, run_id: str) -> dict:
        summary = self._build_run_summary(self._get_run_dir(run_id))
        return {
            "summary": summary,
            "urls": {
                "detail": f"/api/runs/{summary['run_id']}",
                "bundle": f"/api/runs/{summary['run_id']}/bundle",
                "report": f"/api/runs/{summary['run_id']}/report",
            },
        }

    def _collect_workspace_resources(
        self,
        resource_type: str,
        resource_ids: list[str],
        build_resource: Callable[[str], dict],
        warnings: list[dict],
    ) -> list[dict]:
        resources: list[dict] = []
        for resource_id in resource_ids:
            try:
                resources.append(build_resource(resource_id))
            except HTTPException as exc:
                if exc.status_code != 404:
                    raise
                warnings.append(
                    {
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "message": str(exc.detail),
                    }
                )
        return resources

    def _workspace_urls(self, workspace_id: str) -> dict:
        return {
            "detail": f"/api/workspaces/{workspace_id}",
            "download": f"/api/workspaces/{workspace_id}/download",
        }

    def _build_workspace_summary(self, path: Path) -> dict:
        record = self._read_json(path)
        workspace_id = str(record.get("workspace_id") or path.parent.name)
        resources = record.get("resources") or {}
        collaborators = record.get("collaborators") or []
        annotations = record.get("annotations") or []
        job_summaries = record.get("job_summaries") or []
        warnings = record.get("warnings") or []
        return {
            "workspace_id": workspace_id,
            "title": record.get("title") or workspace_id,
            "description": record.get("description"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "imported_from_workspace_id": record.get("imported_from_workspace_id"),
            **self._workspace_resource_counts(
                resources,
                collaborators,
                annotations,
                job_summaries,
                warnings,
            ),
            "urls": self._workspace_urls(workspace_id),
        }

    def _build_workspace_detail(self, path: Path) -> dict:
        record = self._read_json(path)
        workspace_id = str(record.get("workspace_id") or path.parent.name)
        return {
            "summary": self._build_workspace_summary(path),
            "workspace": record,
            "urls": self._workspace_urls(workspace_id),
        }

    def _workspace_resource_counts(
        self,
        resources: dict,
        collaborators: list[dict],
        annotations: list[dict],
        job_summaries: list[dict],
        warnings: list[dict],
    ) -> dict:
        return {
            "run_count": len(resources.get("runs") or []),
            "experiment_count": len(resources.get("experiments") or []),
            "campaign_study_template_count": len(
                resources.get("campaign_study_templates") or []
            ),
            "research_object_count": len(resources.get("research_objects") or []),
            "collaborator_count": len(collaborators),
            "annotation_count": len(annotations),
            "job_count": len(job_summaries),
            "warning_count": len(warnings),
        }

    def _workspace_job_summaries(self, resources: dict) -> list[dict]:
        job_summaries: dict[str, dict] = {}

        def add(summary: dict | None) -> None:
            if not isinstance(summary, dict) or not summary.get("job_id"):
                return
            job_summaries[str(summary["job_id"])] = summary

        for item in resources.get("runs") or []:
            add(((item.get("summary") or {}).get("execution_job")) if isinstance(item, dict) else None)
        for item in resources.get("experiments") or []:
            if not isinstance(item, dict):
                continue
            add((item.get("summary") or {}).get("execution_job"))
            add((item.get("execution_job") or {}).get("summary"))
        for item in resources.get("research_objects") or []:
            if not isinstance(item, dict):
                continue
            research_object = item.get("research_object") or {}
            if isinstance(research_object, dict):
                add((research_object.get("executionJob") or {}).get("summary"))
                add((research_object.get("execution_job") or {}).get("summary"))
        return list(job_summaries.values())

    def _normalize_workspace_collaborators(
        self,
        collaborators: list[dict[str, Any]],
    ) -> list[dict]:
        if not isinstance(collaborators, list):
            raise ValueError("Workspace collaborators must be a list")
        if not collaborators:
            return [
                {
                    "collaborator_id": "local-user",
                    "display_name": "Local QS-DMSS user",
                    "role": "owner",
                }
            ]

        normalized: list[dict] = []
        for index, raw in enumerate(collaborators, start=1):
            if not isinstance(raw, dict):
                raise ValueError("Workspace collaborator entries must be objects")
            display_name = str(raw.get("display_name") or raw.get("name") or "").strip()
            if not display_name:
                raise ValueError("Workspace collaborator display_name is required")
            collaborator_id = safe_filename(
                str(raw.get("collaborator_id") or raw.get("id") or display_name),
                default=f"collaborator-{index}",
            )
            collaborator = {
                "collaborator_id": collaborator_id,
                "display_name": display_name,
                "role": str(raw.get("role") or "reviewer").strip() or "reviewer",
            }
            for key in ("affiliation", "location_label", "contact", "orcid"):
                value = raw.get(key)
                if value is not None and str(value).strip():
                    collaborator[key] = str(value).strip()
            normalized.append(collaborator)
        return normalized

    def _normalize_workspace_annotations(
        self,
        annotations: list[dict[str, Any]],
        collaborators: list[dict],
    ) -> list[dict]:
        if not isinstance(annotations, list):
            raise ValueError("Workspace annotations must be a list")
        allowed_targets = {
            "workspace",
            "run",
            "experiment",
            "campaign-study",
            "research-object",
            "job",
        }
        collaborator_ids = {
            str(collaborator["collaborator_id"])
            for collaborator in collaborators
            if collaborator.get("collaborator_id")
        }
        now = datetime.now(timezone.utc).isoformat()
        normalized: list[dict] = []
        for index, raw in enumerate(annotations, start=1):
            if not isinstance(raw, dict):
                raise ValueError("Workspace annotation entries must be objects")
            text = str(raw.get("text") or raw.get("body") or "").strip()
            if not text:
                raise ValueError("Workspace annotation text is required")
            target_type = str(raw.get("target_type") or "workspace").strip()
            if target_type not in allowed_targets:
                raise ValueError(f"Unsupported workspace annotation target_type: {target_type}")
            annotation_id = safe_filename(
                str(raw.get("annotation_id") or raw.get("id") or f"annotation-{index}"),
                default=f"annotation-{index}",
            )
            annotation = {
                "annotation_id": annotation_id,
                "target_type": target_type,
                "target_id": str(raw.get("target_id") or "workspace").strip()
                or "workspace",
                "text": text,
                "created_at": str(raw.get("created_at") or now),
                "tags": [
                    str(tag).strip()
                    for tag in (raw.get("tags") or [])
                    if str(tag).strip()
                ],
            }
            author_id = raw.get("author_collaborator_id") or raw.get("author")
            if author_id is not None and str(author_id).strip():
                author = safe_filename(str(author_id), default="collaborator")
                annotation["author_collaborator_id"] = author
                annotation["author_registered"] = author in collaborator_ids
            normalized.append(annotation)
        return normalized

    def _dedupe_text_values(self, values: list[str]) -> list[str]:
        deduped: dict[str, None] = {}
        for value in values:
            text = str(value).strip()
            if text:
                deduped[text] = None
        return list(deduped)

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _format_grid_label(self, grid_shape: list[int] | tuple[int, int, int]) -> str:
        return " x ".join(str(value) for value in grid_shape)

    def _format_bytes(self, byte_count: int) -> str:
        units = ["B", "KB", "MB", "GB"]
        value = float(byte_count)
        unit_index = 0
        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1
        precision = 0 if unit_index == 0 else 2
        return f"{value:.{precision}f} {units[unit_index]}"

    def _evidence_categories(self, manifest: dict) -> list[dict]:
        buckets = {
            "State Snapshots": 0,
            "Diagnostics": 0,
            "Invariants": 0,
            "Metadata": 0,
        }
        for entry in manifest.get("files", []):
            path = entry["path"]
            if path.startswith("artifacts/"):
                buckets["State Snapshots"] += 1
            elif path in {"metrics.json", "energy.csv", "report.html"}:
                buckets["Diagnostics"] += 1
            elif path in {"environment.lock.json"}:
                buckets["Invariants"] += 1
            else:
                buckets["Metadata"] += 1

        tones = {
            "State Snapshots": "teal",
            "Diagnostics": "copper",
            "Invariants": "olive",
            "Metadata": "stone",
        }
        return [
            {"label": label, "count": count, "tone": tones[label]}
            for label, count in buckets.items()
            if count > 0
        ]

    def _build_showcase_summary(self, scenario: str) -> dict:
        selected = self._resolve_showcase_scenario(scenario)
        config = load_config(selected.config_path)
        metadata = showcase_scenario_metadata(selected.name)
        guided_variants = self._guided_comparison_variants(config.to_dict())
        return {
            "name": selected.name,
            "label": metadata["title"],
            "config_name": selected.config_path.name,
            "run_name": config.run.name,
            "grid_label": self._format_grid_label(config.engine.grid_shape),
            "steps": config.engine.num_steps,
            "description": (
                "Packaged simulation scenario that produces a run, "
                "verified evidence bundle, replay check, CSV/SVG artifacts, "
                "and a human-readable showcase report."
            ),
            "claim_boundary": (
                "Workflow demonstration only; not peer-reviewed scientific validation."
            ),
            "purpose": metadata["purpose"],
            "expected_runtime": metadata["expected_runtime"],
            "output_artifacts": metadata["output_artifacts"],
            "limitations": metadata["limitations"],
            "readiness_badges": metadata["readiness_badges"],
            "next_actions": metadata["next_actions"],
            "guided_comparison": {
                "label": "Packaged variant comparison",
                "strategy": "packaged-variants",
                "planned_run_count": len(guided_variants),
                "dimensions": self._guided_comparison_dimensions(),
                "variants": [
                    {
                        "slug": variant["slug"],
                        "label": variant["label"],
                        "description": variant["description"],
                    }
                    for variant in guided_variants
                ],
                "purpose": (
                    "Compare curated variants with a shared seed so the cockpit can explain "
                    "evidence deltas without requiring manual YAML edits."
                ),
            },
        }

    def _build_showcase_artifact_links(self, scenario: str, report: dict) -> list[dict]:
        links = []
        for key, value in report.get("artifacts", {}).items():
            artifact_name = Path(value).name
            kind = Path(artifact_name).suffix.lstrip(".") or "file"
            links.append(
                {
                    "key": key,
                    "label": key.replace("_", " ").title(),
                    "name": artifact_name,
                    "kind": kind,
                    "previewable": kind in {"csv", "svg"},
                    "url": f"/api/showcases/{scenario}/artifacts/{artifact_name}",
                }
            )
        return links

    def _guided_comparison_dimensions(self) -> list[dict[str, str]]:
        return [
            {
                "path": "initial.width",
                "label": "Initial packet width",
            },
            {
                "path": "engine.g_int",
                "label": "Interaction strength",
            },
        ]

    def _guided_comparison_variants(self, base_config: dict[str, Any]) -> list[dict[str, Any]]:
        base_width = float(base_config["initial"]["width"])
        base_interaction = float(base_config["engine"]["g_int"])
        wider_width = round(base_width * 1.27, 6)
        stronger_interaction = round(base_interaction * 1.5, 6)
        return [
            {
                "slug": "baseline",
                "label": "Baseline",
                "description": "The packaged canonical showcase settings.",
                "values": {
                    "initial.width": base_width,
                    "engine.g_int": base_interaction,
                },
            },
            {
                "slug": "wider-packet",
                "label": "Wider packet",
                "description": "A wider initial density packet with the same interaction strength.",
                "values": {
                    "initial.width": wider_width,
                    "engine.g_int": base_interaction,
                },
            },
            {
                "slug": "stronger-interaction",
                "label": "Stronger interaction",
                "description": "The baseline packet with a stronger self-interaction setting.",
                "values": {
                    "initial.width": base_width,
                    "engine.g_int": stronger_interaction,
                },
            },
        ]

    def _guided_comparison_config(
        self,
        base_config: dict[str, Any],
        values: dict[str, int | float],
    ) -> dict[str, Any]:
        return apply_parameter_values(
            base_config,
            [(path, value) for path, value in values.items()],
        )

    def _guided_comparison_context(
        self,
        *,
        experiment_id: str,
        label: str,
        dimensions: list[dict[str, str]],
        variant: dict[str, Any],
        ordinal: int,
        total_runs: int,
    ) -> dict[str, Any]:
        entries = [
            {
                "path": dimension["path"],
                "label": dimension["label"],
                "value": variant["values"][dimension["path"]],
                "value_label": format_parameter_value(variant["values"][dimension["path"]]),
            }
            for dimension in dimensions
        ]
        return {
            "id": experiment_id,
            "kind": "guided-comparison",
            "label": label,
            "strategy": "packaged-variants",
            "dimensions": dimensions,
            "dimension_count": len(dimensions),
            "parameter_path": None,
            "parameter_label": "Guided Variant",
            "parameter_value": None,
            "parameter_value_label": variant["label"],
            "variant": entries,
            "variant_label": variant["label"],
            "variant_note": variant["description"],
            "ordinal": ordinal,
            "total_runs": total_runs,
        }

    def _build_guided_comparison_guide(self, comparison: dict[str, Any]) -> dict[str, Any]:
        rows = comparison["rows"]
        highlights = comparison["highlights"]
        ranges = comparison["ranges"]
        decision = comparison.get("decision") or {}
        recommended_run_id = decision.get("recommended_run_id")
        recommended_row = next(
            (row for row in rows if row["run_id"] == recommended_run_id),
            None,
        )
        recommended_label = (
            recommended_row.get("variant_label") or recommended_row.get("parameter_value_label")
            if recommended_row
            else None
        )
        recommendation_sentence = (
            f"The current objective profile recommends the {recommended_label} variant "
            f"({recommended_run_id})."
            if recommended_run_id and recommended_label
            else "No objective-driven recommendation is available, so compare the evidence rows manually."
        )
        return {
            "title": "How the guided variants differ",
            "plain_language_summary": (
                "QS-DMSS ran the packaged showcase as a small guided comparison: the baseline, "
                "a wider initial density packet, and a stronger interaction variant. The variants "
                "use the same deterministic seed so the cockpit can focus attention on evidence "
                "differences rather than random setup changes."
            ),
            "what_changed": [
                f"Baseline run: {rows[0]['run_id']}. Each other row reports deltas against that baseline.",
                f"Energy drift span across variants: {ranges['energy_drift']['span']:.3e}.",
                f"Norm drift span across variants: {ranges['norm_drift']['span']:.3e}.",
                f"Max-density span across variants: {ranges['max_density']['span']:.3e}.",
                recommendation_sentence,
            ],
            "what_to_inspect": [
                f"Lowest absolute energy drift: {highlights['lowest_abs_energy_drift_run_id']}.",
                f"Lowest absolute norm drift: {highlights['lowest_abs_norm_drift_run_id']}.",
                f"Highest max density: {highlights['highest_max_density_run_id']}.",
                "Open the experiment report to inspect the comparison table, copied run evidence, and bundle manifest.",
            ],
            "what_this_does_not_claim": [
                "It does not prove one variant is scientifically correct or physically validated.",
                "It does not replace peer review, calibration, or domain-specific benchmark validation.",
                "It demonstrates the QS-DMSS workflow for comparing reproducible research objects.",
            ],
            "review_prompt": (
                "A useful review comment can focus on whether the comparison makes variant behavior "
                "understandable, whether the evidence deltas are enough, or which diagnostic should be added next."
            ),
        }

    def _build_run_summary(self, run_dir: Path) -> dict:
        run_record = self._read_json(run_dir / "run.json")
        metrics = self._read_json(run_dir / "metrics.json")
        config = load_config(run_dir / "config.yaml")
        experiment = run_record.get("experiment")
        bundle_path = run_dir / "evidence_bundle.zip"
        execution_job = self._build_execution_job_summary(
            run_record.get("execution_job"),
        )
        return {
            "run_id": run_record["run_id"],
            "name": run_record["name"],
            "config_name": run_record["source_config_name"],
            "seed": run_record["seed"],
            "grid_label": self._format_grid_label(config.engine.grid_shape),
            "steps": config.engine.num_steps,
            "status": run_record["status"],
            "finished_at": run_record["finished_at"],
            "elapsed_seconds": run_record["elapsed_seconds"],
            "config_digest": run_record["config_digest"],
            "energy_drift": metrics["energy_drift"],
            "norm_drift": metrics["norm_drift"],
            "bundle_size_bytes": bundle_path.stat().st_size,
            "bundle_size_label": self._format_bytes(bundle_path.stat().st_size),
            "bundle_sha256": _file_sha256(bundle_path),
            "bundle_filename": f"{run_record['run_id']}-evidence-bundle.zip",
            "experiment": experiment,
            "execution_job": execution_job,
        }

    def _build_run_detail(self, run_dir: Path) -> dict:
        run_record = self._read_json(run_dir / "run.json")
        metrics = self._read_json(run_dir / "metrics.json")
        manifest = self._read_json(run_dir / "manifest.sha256.json")
        config = load_config(run_dir / "config.yaml")
        verification = verify_run_path(run_dir)
        bundle_path = run_dir / "evidence_bundle.zip"
        decision = evaluate_run_decision(
            config,
            metrics,
            verification_success=verification.success,
        )
        execution_job = self._build_execution_job_detail(
            run_record.get("execution_job"),
        )

        urls = {
            "bundle": f"/api/runs/{run_record['run_id']}/bundle",
            "review_bundle": f"/api/runs/{run_record['run_id']}/review-bundle",
            "state_bundle": f"/api/runs/{run_record['run_id']}/state-bundle",
            "report": f"/api/runs/{run_record['run_id']}/report",
        }
        if execution_job and execution_job["summary"].get("job_id"):
            urls["job"] = f"/api/runs/{run_record['run_id']}/job"

        return {
            "summary": self._build_run_summary(run_dir),
            "config": config.to_dict(),
            "run_record": run_record,
            "execution_job": execution_job,
            "metrics": metrics,
            "latest_snapshot": metrics["history"][-1],
            "decision": decision,
            "verification": {
                "success": verification.success,
                "checked_files": verification.checked_files,
                "errors": verification.errors,
            },
            "evidence": {
                "file_count": len(manifest.get("files", [])),
                "bundle_size_bytes": bundle_path.stat().st_size,
                "bundle_size_label": self._format_bytes(bundle_path.stat().st_size),
                "bundle_sha256": _file_sha256(bundle_path),
                "bundle_filename": f"{run_record['run_id']}-evidence-bundle.zip",
                "categories": self._evidence_categories(manifest),
                "artifact_paths": [entry["path"] for entry in manifest.get("files", [])],
            },
            "urls": urls,
        }

    def _build_experiment_summary(self, experiment_dir: Path) -> dict:
        experiment_record = self._read_json(experiment_dir / "experiment.json")
        bundle_path = experiment_dir / "evidence_bundle.zip"
        execution_job = self._build_execution_job_summary(
            experiment_record.get("execution_job"),
        )
        return {
            "experiment_id": experiment_record["experiment_id"],
            "label": experiment_record["label"],
            "kind": experiment_record["kind"],
            "status": experiment_record.get("status", "completed"),
            "created_at": experiment_record["created_at"],
            "baseline_run_id": experiment_record["baseline_run_id"],
            "run_count": experiment_record["run_count"],
            "planned_run_count": experiment_record.get("planned_run_count"),
            "run_ids": experiment_record["run_ids"],
            "shared_experiment": experiment_record.get("shared_experiment"),
            "decision_available": bool((experiment_record.get("decision") or {}).get("available")),
            "decision_status": (experiment_record.get("decision") or {}).get("status"),
            "recommended_run_id": (experiment_record.get("decision") or {}).get("recommended_run_id"),
            "bundle_size_bytes": bundle_path.stat().st_size,
            "bundle_size_label": self._format_bytes(bundle_path.stat().st_size),
            "bundle_sha256": _file_sha256(bundle_path),
            "bundle_filename": f"{experiment_record['experiment_id']}-comparison-bundle.zip",
            "execution_job": execution_job,
        }

    def _build_experiment_detail(self, experiment_dir: Path) -> dict:
        experiment_record = self._read_json(experiment_dir / "experiment.json")
        comparison = self._read_json(experiment_dir / "comparison.json")
        manifest = self._read_json(experiment_dir / "manifest.sha256.json")
        execution_job = self._build_execution_job_detail(
            experiment_record.get("execution_job"),
        )
        urls = {
            "bundle": f"/api/experiments/{experiment_record['experiment_id']}/bundle",
            "report": f"/api/experiments/{experiment_record['experiment_id']}/report",
        }
        if (experiment_dir / "workbook.html").exists():
            urls["workbook"] = (
                f"/api/experiments/{experiment_record['experiment_id']}/workbook"
            )
            urls["workbook_download"] = (
                f"/api/experiments/{experiment_record['experiment_id']}/workbook/download"
            )
        if execution_job and execution_job["summary"].get("job_id"):
            urls["job"] = f"/api/jobs/{execution_job['summary']['job_id']}"
        return {
            "summary": self._build_experiment_summary(experiment_dir),
            "experiment_record": experiment_record,
            "execution_job": execution_job,
            "comparison": comparison,
            "decision": comparison.get("decision"),
            "evidence": {
                "file_count": len(manifest.get("files", [])),
                "bundle_sha256": _file_sha256(experiment_dir / "evidence_bundle.zip"),
                "bundle_filename": (
                    f"{experiment_record['experiment_id']}-comparison-bundle.zip"
                ),
                "artifact_paths": [entry["path"] for entry in manifest.get("files", [])],
            },
            "urls": urls,
        }


def create_app(
    repo_root: str | Path | None = None,
    output_root: str | Path | None = None,
    hosted_demo: bool | None = None,
) -> FastAPI:
    service = CockpitService.create(
        repo_root=repo_root,
        output_root=output_root,
        hosted_demo=hosted_demo,
    )

    app = FastAPI(
        title="QS-DMSS Studio Cockpit",
        summary=(
            "Local-first API and browser cockpit for deterministic runs and evidence bundles. "
            "Set QS_DMSS_HOSTED_DEMO=1 for the constrained public hosted demo."
        ),
    )
    app.state.hosted_demo_last_cleanup = 0.0
    app.state.hosted_demo_cleanup_lock = threading.Lock()

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        COCKPIT_LOGGER.error(
            "cockpit_request_failed method=%s path=%s exception_type=%s",
            request.method,
            request.url.path,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": GENERIC_COCKPIT_ERROR_DETAIL},
        )

    app.mount("/static", StaticFiles(directory=service.static_root), name="static")

    @app.middleware("http")
    async def crawler_policy_middleware(
        request: Request,
        call_next: Callable,
    ):
        response = await call_next(request)
        if request.url.path.startswith(NOINDEX_RESPONSE_PATHS):
            response.headers["X-Robots-Tag"] = (
                "noindex, nofollow, noarchive, nosnippet"
            )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        for name, value in BASELINE_SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response

    @app.middleware("http")
    async def hosted_demo_session_middleware(
        request: Request,
        call_next: Callable,
    ):
        if not service.hosted_demo.enabled:
            return await call_next(request)

        session_id = request.cookies.get(HOSTED_DEMO_COOKIE_NAME)
        if not _is_valid_hosted_demo_session_id(session_id):
            session_id = _new_hosted_demo_session_id()
        request.state.hosted_demo_session_id = session_id
        with app.state.hosted_demo_cleanup_lock:
            app.state.hosted_demo_last_cleanup = service.cleanup_hosted_sessions(
                now=time.time(),
                last_cleanup_at=app.state.hosted_demo_last_cleanup,
            )

        response = await call_next(request)
        response.set_cookie(
            HOSTED_DEMO_COOKIE_NAME,
            session_id,
            max_age=service.hosted_demo.ttl_seconds,
            httponly=True,
            samesite="lax",
        )
        return response

    def current_service(request: Request) -> CockpitService:
        if not service.hosted_demo.enabled:
            return service
        session_id = getattr(request.state, "hosted_demo_session_id", None)
        if not _is_valid_hosted_demo_session_id(session_id):
            session_id = _new_hosted_demo_session_id()
            request.state.hosted_demo_session_id = session_id
        return service.for_hosted_session(str(session_id))

    def hosted_demo_job_key(request: Request) -> str:
        session_id = getattr(request.state, "hosted_demo_session_id", "local")
        client_host = request.client.host if request.client else "unknown"
        return f"{session_id}:{client_host}"

    def run_hosted_job_guard(
        request: Request,
        active_service: CockpitService,
        action: Callable[[], dict],
    ) -> dict:
        if not active_service.hosted_demo.enabled:
            return action()

        key = hosted_demo_job_key(request)
        with _HOSTED_DEMO_ACTIVE_JOBS_LOCK:
            if key in _HOSTED_DEMO_ACTIVE_JOBS:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Hosted demo allows one active job per browser session. "
                        "Wait for the current run to finish before starting another."
                    ),
                )
            _HOSTED_DEMO_ACTIVE_JOBS.add(key)
        try:
            return action()
        finally:
            with _HOSTED_DEMO_ACTIVE_JOBS_LOCK:
                _HOSTED_DEMO_ACTIVE_JOBS.discard(key)

    def guarded_file_response(
        active_service: CockpitService,
        path: Path,
        *,
        media_type: str,
        filename: str | None = None,
    ) -> FileResponse:
        active_service.assert_hosted_download_allowed(path)
        return FileResponse(path, media_type=media_type, filename=filename)

    @app.get("/")
    def root() -> HTMLResponse:
        index_html = service.index_path().read_text(encoding="utf-8")
        rendered_index = index_html.replace(
            "__QS_DMSS_STATIC_REVISION__",
            service.static_asset_revision(),
        )
        return HTMLResponse(
            rendered_index,
            headers={
                "Cache-Control": "no-cache, max-age=0, must-revalidate",
                "Link": f"<{HOSTED_DEMO_PUBLIC_URL}>; rel=\"canonical\"",
            },
        )

    @app.get("/robots.txt", include_in_schema=False)
    def robots() -> PlainTextResponse:
        return PlainTextResponse(HOSTED_DEMO_ROBOTS)

    @app.get("/sitemap.xml", include_in_schema=False)
    def sitemap() -> Response:
        return Response(HOSTED_DEMO_SITEMAP, media_type="application/xml")

    @app.get("/api/health")
    def health(
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        session_id = getattr(request.state, "hosted_demo_session_id", None)
        return {
            "status": "ok",
            "version": __version__,
            "ui_contract": "research-command-center-v2",
            "deployment": public_deployment_provenance(),
            "release": {
                "version": __version__,
                "tag": f"v{__version__}",
                "latest_archived_release_tag": LATEST_ARCHIVED_RELEASE_TAG,
                "project_doi": PROJECT_DOI,
                "project_doi_url": f"https://doi.org/{PROJECT_DOI}",
                "archived_release_doi": RELEASE_DOI,
                "archived_release_doi_url": f"https://doi.org/{RELEASE_DOI}",
                "archived_release_record_url": RELEASE_RECORD_URL,
            },
            "capabilities": {
                "quantum_validation_snapshot": True,
                "quantum_validation_live": (
                    active_service.quantum_runtime_status()["live_execution"]
                ),
                "quantum_stack_available": (
                    active_service.quantum_runtime_status()["stack_available"]
                ),
                "client_sweep_preflight": True,
                "hosted_custom_compute": not active_service.hosted_demo.enabled,
            },
            "hosted_demo": active_service.hosted_demo_status(session_id),
        }

    @app.get("/api/configs")
    def configs(active_service: CockpitService = Depends(current_service)) -> dict:
        items = active_service.list_configs()
        return {
            "items": items,
            "default_name": items[0]["name"] if items else None,
        }

    @app.get("/api/sweeps/parameters")
    def sweep_parameters(active_service: CockpitService = Depends(current_service)) -> dict:
        return {"items": active_service.list_sweep_parameters()}

    @app.get("/api/showcases")
    def showcases(active_service: CockpitService = Depends(current_service)) -> dict:
        try:
            items = active_service.list_showcases()
            campaign_studio = active_service.campaign_studio_preview()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=GENERIC_COCKPIT_ERROR_DETAIL,
            ) from None
        return {
            "items": items,
            "default_name": DEFAULT_SHOWCASE_NAME,
            "campaign_studio": campaign_studio,
        }

    @app.get("/api/quantum-validation")
    def quantum_validation(
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        try:
            return active_service.quantum_validation_showcase()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=GENERIC_COCKPIT_ERROR_DETAIL,
            ) from None

    @app.get("/api/quantum-validation/runs/latest")
    def latest_quantum_validation_run(
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        try:
            return active_service.latest_quantum_validation_run()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=GENERIC_COCKPIT_ERROR_DETAIL,
            ) from None

    @app.post("/api/quantum-validation/runs")
    def run_quantum_validation(
        payload: QuantumValidationRunRequest,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        if not _QUANTUM_VALIDATION_ACTIVE_LOCK.acquire(blocking=False):
            raise HTTPException(
                status_code=409,
                detail="A local quantum validation run is already active.",
            )
        try:
            return active_service.run_quantum_validation(payload)
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=GENERIC_COCKPIT_ERROR_DETAIL,
            ) from None
        finally:
            _QUANTUM_VALIDATION_ACTIVE_LOCK.release()

    def quantum_validation_file_response(
        active_service: CockpitService,
        path: Path,
        artifact_key: str,
    ) -> FileResponse:
        if path.suffix.lower() == ".html":
            active_service.assert_hosted_download_allowed(path)
            return FileResponse(
                path,
                media_type="text/html",
                headers={
                    "Content-Security-Policy": (
                        "default-src 'none'; style-src 'unsafe-inline'; "
                        "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
                    ),
                    "X-Content-Type-Options": "nosniff",
                },
            )
        media_types = {
            "report": "application/json",
            "summary": "text/html",
            "markdown": "text/markdown",
            "matrix": "text/csv",
            "manifest": "application/json",
            "bundle": "application/zip",
        }
        return guarded_file_response(
            active_service,
            path,
            media_type=media_types.get(artifact_key, "application/octet-stream"),
            filename=path.name,
        )

    @app.get("/api/quantum-validation/files/{artifact_name}")
    def quantum_validation_artifact(
        artifact_name: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        path = active_service.quantum_validation_artifact_path(artifact_name)
        artifact_key = quantum_compilation_showcase_artifact_key(artifact_name)
        return quantum_validation_file_response(
            active_service,
            path,
            artifact_key,
        )

    @app.get(
        "/api/quantum-validation/runs/{run_id}/files/{artifact_name}"
    )
    def quantum_validation_run_artifact(
        run_id: str,
        artifact_name: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        path = active_service.quantum_validation_run_artifact_path(
            run_id,
            artifact_name,
        )
        try:
            artifact_key = quantum_compilation_showcase_artifact_key(artifact_name)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Quantum artifact not found") from exc
        return quantum_validation_file_response(
            active_service,
            path,
            artifact_key,
        )

    @app.post("/api/showcases/{scenario}/run")
    def launch_showcase(
        scenario: str,
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return run_hosted_job_guard(
            request,
            active_service,
            lambda: active_service.launch_showcase(scenario),
        )

    @app.post("/api/showcases/{scenario}/compare")
    def launch_showcase_comparison(
        scenario: str,
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return run_hosted_job_guard(
            request,
            active_service,
            lambda: active_service.launch_showcase_comparison(scenario),
        )

    @app.get("/api/showcases/{scenario}/report")
    def showcase_markdown_report(
        scenario: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        report_path = active_service.showcase_markdown_path(scenario)
        return guarded_file_response(
            active_service,
            report_path,
            media_type="text/markdown",
        )

    @app.get("/api/showcases/{scenario}/report.json")
    def showcase_json_report(
        scenario: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        report_path = active_service.showcase_json_path(scenario)
        return guarded_file_response(
            active_service,
            report_path,
            media_type="application/json",
        )

    @app.get("/api/showcases/{scenario}/artifacts/{artifact_name}")
    def showcase_artifact(
        scenario: str,
        artifact_name: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        artifact_path = active_service.showcase_artifact_path(scenario, artifact_name)
        media_type = "application/octet-stream"
        if artifact_path.suffix == ".svg":
            media_type = "image/svg+xml"
        elif artifact_path.suffix == ".csv":
            media_type = "text/csv"
        return guarded_file_response(
            active_service,
            artifact_path,
            media_type=media_type,
            filename=artifact_path.name,
        )

    @app.get("/api/runs")
    def runs(active_service: CockpitService = Depends(current_service)) -> dict:
        return {"items": active_service.list_runs()}

    @app.get("/api/runs/{run_id}")
    def run_detail(
        run_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.get_run_detail(run_id)

    @app.get("/api/runs/{run_id}/job")
    def run_job_detail(
        run_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.get_run_job_detail(run_id)

    @app.get("/api/jobs/{job_id}")
    def job_detail(
        job_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.get_job_detail(job_id)

    @app.post("/api/runs")
    def launch_run(
        payload: LaunchRunRequest,
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return run_hosted_job_guard(
            request,
            active_service,
            lambda: active_service.launch_run(payload),
        )

    @app.post("/api/compare")
    def compare_runs(
        payload: CompareRunsRequest,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.compare_runs(payload)

    @app.post("/api/experiments")
    def create_experiment(
        payload: CreateExperimentRequest,
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return run_hosted_job_guard(
            request,
            active_service,
            lambda: active_service.create_experiment(payload),
        )

    @app.get("/api/experiments")
    def experiments(active_service: CockpitService = Depends(current_service)) -> dict:
        return {"items": active_service.list_experiments()}

    @app.get("/api/experiments/{experiment_id}")
    def experiment_detail(
        experiment_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.get_experiment_detail(experiment_id)

    @app.get("/api/campaign-studies")
    def campaign_studies(active_service: CockpitService = Depends(current_service)) -> dict:
        return {"items": active_service.list_campaign_study_templates()}

    @app.post("/api/campaign-studies")
    def save_campaign_study(
        payload: CampaignStudyTemplateRequest,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.save_campaign_study_template(payload)

    @app.post("/api/campaign-studies/import")
    def import_campaign_study(
        payload: CampaignStudyTemplateRequest,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.import_campaign_study_template(payload)

    @app.get("/api/campaign-studies/{template_id}")
    def campaign_study_detail(
        template_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.get_campaign_study_template(template_id)

    @app.get("/api/campaign-studies/{template_id}/download")
    def campaign_study_download(
        template_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        template_path = active_service.campaign_study_template_path(template_id)
        return guarded_file_response(
            active_service,
            template_path,
            media_type="application/json",
            filename=template_path.name,
        )

    @app.post("/api/sweeps")
    def launch_sweep(
        payload: SweepRequest,
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return run_hosted_job_guard(
            request,
            active_service,
            lambda: active_service.launch_sweep(payload),
        )

    @app.post("/api/campaigns")
    def launch_campaign(
        payload: LaunchCampaignRequest,
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return run_hosted_job_guard(
            request,
            active_service,
            lambda: active_service.launch_campaign(payload),
        )

    @app.post("/api/research-objects/export")
    def export_research_object(
        payload: ResearchObjectExportRequest,
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return run_hosted_job_guard(
            request,
            active_service,
            lambda: active_service.export_research_object(payload),
        )

    @app.get("/api/research-objects/{export_id}/download")
    def research_object_download(
        export_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        markdown_path, file_name = active_service.research_object_markdown_path(export_id)
        return guarded_file_response(
            active_service,
            markdown_path,
            media_type="text/markdown",
            filename=file_name,
        )

    @app.get("/api/workspaces")
    def workspaces(active_service: CockpitService = Depends(current_service)) -> dict:
        return {"items": active_service.list_workspaces()}

    @app.post("/api/workspaces/export")
    def export_workspace(
        payload: WorkspaceExportRequest,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.export_workspace(payload)

    @app.post("/api/workspaces/import")
    def import_workspace(
        payload: WorkspaceImportRequest,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.import_workspace(payload)

    @app.get("/api/workspaces/{workspace_id}")
    def workspace_detail(
        workspace_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.get_workspace(workspace_id)

    @app.get("/api/workspaces/{workspace_id}/download")
    def workspace_download(
        workspace_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        workspace_path = active_service.workspace_path(workspace_id)
        return guarded_file_response(
            active_service,
            workspace_path,
            media_type="application/json",
            filename=workspace_path.name,
        )

    @app.post("/api/runs/{run_id}/verify")
    def verify_run(
        run_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return active_service.verify_run(run_id)

    @app.post("/api/runs/{run_id}/replay")
    def replay_run(
        run_id: str,
        request: Request,
        active_service: CockpitService = Depends(current_service),
    ) -> dict:
        return run_hosted_job_guard(
            request,
            active_service,
            lambda: active_service.replay_run(run_id),
        )

    @app.get("/api/runs/{run_id}/bundle")
    def bundle_download(
        run_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        bundle_path = active_service.bundle_path(run_id)
        return guarded_file_response(
            active_service,
            bundle_path,
            media_type="application/zip",
            filename=f"{safe_filename(run_id, default='run')}-evidence-bundle.zip",
        )

    @app.get("/api/runs/{run_id}/review-bundle")
    def review_bundle_download(
        run_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        bundle_path = active_service.run_bundle_profile_path(run_id, "review")
        return guarded_file_response(
            active_service,
            bundle_path,
            media_type="application/zip",
            filename=f"{safe_filename(run_id, default='run')}-review-bundle.zip",
        )

    @app.get("/api/runs/{run_id}/state-bundle")
    def state_bundle_download(
        run_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        bundle_path = active_service.run_bundle_profile_path(run_id, "state")
        return guarded_file_response(
            active_service,
            bundle_path,
            media_type="application/zip",
            filename=f"{safe_filename(run_id, default='run')}-state-bundle.zip",
        )

    @app.get("/api/runs/{run_id}/report")
    def run_report(
        run_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        report_path = active_service.report_path(run_id)
        return guarded_file_response(
            active_service,
            report_path,
            media_type="text/html",
        )

    @app.get("/api/experiments/{experiment_id}/bundle")
    def experiment_bundle_download(
        experiment_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        bundle_path = active_service.experiment_bundle_path(experiment_id)
        return guarded_file_response(
            active_service,
            bundle_path,
            media_type="application/zip",
            filename=(
                f"{safe_filename(experiment_id, default='experiment')}"
                "-comparison-bundle.zip"
            ),
        )

    @app.get("/api/experiments/{experiment_id}/report")
    def experiment_report(
        experiment_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        report_path = active_service.experiment_report_path(experiment_id)
        return guarded_file_response(
            active_service,
            report_path,
            media_type="text/html",
        )

    @app.get("/api/experiments/{experiment_id}/workbook")
    def experiment_workbook(
        experiment_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        workbook_path = active_service.experiment_workbook_path(experiment_id)
        return guarded_file_response(
            active_service,
            workbook_path,
            media_type="text/html",
        )

    @app.get("/api/experiments/{experiment_id}/workbook/download")
    def experiment_workbook_download(
        experiment_id: str,
        active_service: CockpitService = Depends(current_service),
    ) -> FileResponse:
        workbook_path = active_service.experiment_workbook_path(experiment_id)
        return guarded_file_response(
            active_service,
            workbook_path,
            media_type="text/html",
            filename=(
                f"{safe_filename(experiment_id, default='experiment')}"
                "-research-workbook.html"
            ),
        )

    return app
