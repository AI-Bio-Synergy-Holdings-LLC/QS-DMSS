"""Internal execution contracts for future distributed QS-DMSS runs.

This module intentionally defines shape, not behavior. The current product
continues to execute through the local runner; future executors can implement
this protocol without changing the evidence-bundle contract.
"""

from __future__ import annotations

import json
import re
import uuid
from hashlib import sha256
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Protocol

JobState = Literal[
    "draft",
    "submitted",
    "queued",
    "running",
    "collecting",
    "succeeded",
    "failed",
    "cancelled",
    "unknown",
]

_JOB_ID_PATTERN = re.compile(r"\Ajob-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}\Z")

ArtifactRole = Literal[
    "request_bundle",
    "run_directory",
    "experiment_directory",
    "comparison",
    "evidence_bundle",
    "report",
    "research_object",
    "metrics",
    "manifest",
    "stdout",
    "stderr",
    "other",
]


@dataclass(frozen=True)
class ResearchWorkspaceRef:
    """Stable identity for a shared research workspace."""

    workspace_id: str
    title: str
    storage_uri: str | None = None
    owner: str | None = None


@dataclass(frozen=True)
class CollaboratorRef:
    """Minimal collaborator identity for provenance and audit trails."""

    collaborator_id: str
    display_name: str
    affiliation: str | None = None
    location_label: str | None = None


@dataclass(frozen=True)
class ExecutionArtifact:
    """Artifact returned by an executor and attached to a research object."""

    role: ArtifactRole
    path: Path | None = None
    uri: str | None = None
    sha256: str | None = None
    media_type: str | None = None
    label: str | None = None


@dataclass(frozen=True)
class ExecutionJobSpec:
    """Portable request for a run or campaign execution backend."""

    config: dict[str, Any]
    source_name: str
    workspace: ResearchWorkspaceRef | None = None
    requested_by: CollaboratorRef | None = None
    output_root: Path | None = None
    experiment: dict[str, Any] | None = None
    labels: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionJobHandle:
    """Opaque handle returned after an executor accepts a job."""

    job_id: str
    backend: str
    state: JobState = "submitted"
    remote_id: str | None = None
    status_uri: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionJobStatus:
    """Current lifecycle state for a submitted job."""

    job_id: str
    backend: str
    state: JobState
    message: str = ""
    progress: float | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionJobResult:
    """Collected result once a job reaches a terminal state."""

    handle: ExecutionJobHandle
    state: JobState
    run_id: str | None = None
    experiment_id: str | None = None
    run_dir: Path | None = None
    experiment_dir: Path | None = None
    artifacts: tuple[ExecutionArtifact, ...] = ()
    metrics: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True)
class ExecutorCapabilities:
    """Backend traits the cockpit can use before submitting work."""

    backend: str
    supports_campaigns: bool = False
    supports_replay: bool = False
    supports_cancellation: bool = False
    supports_artifact_collection: bool = True
    requires_credentials: bool = False
    scheduler: str | None = None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SlurmDryRunOptions:
    """Review-only Slurm script settings for a generated request bundle."""

    job_name: str = "qs-dmss-dry-run"
    time_limit: str = "00:10:00"
    nodes: int = 1
    ntasks: int = 1
    cpus_per_task: int = 1
    memory: str = "2G"
    partition: str | None = None
    account: str | None = None
    qos: str | None = None
    output_name: str = "slurm-%j.out"
    error_name: str = "slurm-%j.err"
    python_module: str | None = None
    qs_dmss_command: str = "qs-dmss"
    output_root: str = "runs"


class Executor(Protocol):
    """Protocol for local, remote, or HPC-backed execution backends."""

    @property
    def capabilities(self) -> ExecutorCapabilities:
        """Return backend traits and scheduler constraints."""

    def submit(self, spec: ExecutionJobSpec) -> ExecutionJobHandle:
        """Accept a job spec and return a stable handle."""

    def status(self, handle: ExecutionJobHandle) -> ExecutionJobStatus:
        """Return the latest known job status."""

    def collect(self, handle: ExecutionJobHandle) -> ExecutionJobResult:
        """Collect terminal artifacts into the QS-DMSS evidence model."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


class LocalJobRegistry:
    """File-backed registry for local executor job lifecycle records."""

    def __init__(self, jobs_root: str | Path):
        self.jobs_root = Path(jobs_root).resolve()

    @classmethod
    def for_output_root(cls, output_root: str | Path) -> "LocalJobRegistry":
        return cls(Path(output_root).resolve().parent / "jobs")

    def create(
        self,
        spec: ExecutionJobSpec,
        *,
        backend: str = "local",
        state: JobState = "submitted",
        message: str | None = None,
    ) -> ExecutionJobHandle:
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        job_id = f"job-{_job_timestamp()}-{uuid.uuid4().hex[:8]}"
        job_dir = self._create_job_dir(job_id)
        record_path = job_dir / "job.json"
        handle = ExecutionJobHandle(
            job_id=job_id,
            backend=backend,
            state=state,
            status_uri=str(record_path),
        )
        now = _utc_now()
        status_message = message or "Job accepted by local registry."
        record = {
            "schema_version": 1,
            "job_id": job_id,
            "backend": backend,
            "state": state,
            "created_at": now,
            "updated_at": now,
            "progress": 0.0,
            "message": status_message,
            "handle": _json_safe(handle),
            "spec": _json_safe(spec),
            "lifecycle": [
                {
                    "state": state,
                    "at": now,
                    "message": status_message,
                }
            ],
            "result": None,
        }
        self._write_record(record_path, record)
        return handle

    def get(self, job_id: str) -> dict[str, Any]:
        return self._read_record(self._job_record_path(job_id))

    def status(self, handle: ExecutionJobHandle) -> ExecutionJobStatus:
        record = self.get(handle.job_id)
        return ExecutionJobStatus(
            job_id=record["job_id"],
            backend=record["backend"],
            state=record["state"],
            message=record.get("message", ""),
            progress=record.get("progress"),
            updated_at=record.get("updated_at"),
            metadata=record.get("metadata", {}),
        )

    def update(
        self,
        handle: ExecutionJobHandle,
        state: JobState,
        *,
        message: str = "",
        progress: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionJobStatus:
        record_path = self._job_record_path(handle.job_id)
        record = self._read_record(record_path)
        now = _utc_now()
        record["state"] = state
        record["updated_at"] = now
        record["message"] = message
        if progress is not None:
            record["progress"] = progress
        if metadata:
            record["metadata"] = {
                **record.get("metadata", {}),
                **_json_safe(metadata),
            }
        record.setdefault("lifecycle", []).append(
            {
                "state": state,
                "at": now,
                "message": message,
            }
        )
        self._write_record(record_path, record)
        return self.status(handle)

    def complete(
        self,
        handle: ExecutionJobHandle,
        result: ExecutionJobResult,
        *,
        message: str = "Job completed successfully.",
    ) -> ExecutionJobResult:
        record_path = self._job_record_path(handle.job_id)
        record = self._read_record(record_path)
        now = _utc_now()
        record["state"] = result.state
        record["updated_at"] = now
        record["progress"] = 1.0
        record["message"] = message
        record["result"] = _json_safe(result)
        record.setdefault("lifecycle", []).append(
            {
                "state": result.state,
                "at": now,
                "message": message,
            }
        )
        self._write_record(record_path, record)
        return result

    def record_result(
        self,
        handle: ExecutionJobHandle,
        result: ExecutionJobResult,
        *,
        message: str = "",
        progress: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionJobResult:
        record_path = self._job_record_path(handle.job_id)
        record = self._read_record(record_path)
        now = _utc_now()
        record["updated_at"] = now
        if message:
            record["message"] = message
        if progress is not None:
            record["progress"] = progress
        if metadata:
            record["metadata"] = {
                **record.get("metadata", {}),
                **_json_safe(metadata),
            }
        record["result"] = _json_safe(result)
        self._write_record(record_path, record)
        return result

    def fail(
        self,
        handle: ExecutionJobHandle,
        error: BaseException | str,
        *,
        message: str = "Job failed.",
    ) -> ExecutionJobStatus:
        error_text = str(error)
        return self.update(
            handle,
            "failed",
            message=message,
            metadata={"error": error_text},
        )

    def _validate_job_id(self, job_id: str) -> str:
        if not _JOB_ID_PATTERN.fullmatch(job_id):
            raise ValueError(f"Invalid job id: {job_id}")
        return job_id

    def _create_job_dir(self, job_id: str) -> Path:
        safe_job_id = self._validate_job_id(job_id)
        jobs_root = self.jobs_root.resolve()
        job_dir = jobs_root.joinpath(safe_job_id).resolve()
        try:
            job_dir.relative_to(jobs_root)
        except ValueError as exc:
            raise ValueError(f"Job path escapes registry root: {job_id}") from exc
        job_dir.mkdir(parents=True, exist_ok=False)
        return job_dir

    def _existing_job_dir(self, job_id: str) -> Path:
        safe_job_id = self._validate_job_id(job_id)
        jobs_root = self.jobs_root.resolve()
        if not jobs_root.exists():
            raise FileNotFoundError(f"Job registry not found: {jobs_root}")
        for candidate in jobs_root.iterdir():
            if candidate.is_dir() and candidate.name == safe_job_id:
                job_dir = candidate.resolve()
                try:
                    job_dir.relative_to(jobs_root)
                except ValueError as exc:
                    raise ValueError(f"Job path escapes registry root: {job_id}") from exc
                return job_dir
        raise FileNotFoundError(f"Job record not found: {job_id}")

    def _job_record_path(self, job_id: str) -> Path:
        record_path = self._existing_job_dir(job_id) / "job.json"
        if not record_path.exists():
            raise FileNotFoundError(f"Job record not found: {record_path}")
        return record_path

    def _read_record(self, record_path: Path) -> dict[str, Any]:
        return json.loads(record_path.read_text(encoding="utf-8"))

    def _write_record(self, record_path: Path, record: dict[str, Any]) -> None:
        temp_path = record_path.with_suffix(".json.tmp")
        temp_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temp_path.replace(record_path)


class DryRunSlurmExecutor:
    """Generate reviewable Slurm request artifacts without submitting a job."""

    backend = "dry-run-slurm"

    def __init__(
        self,
        registry: LocalJobRegistry,
        *,
        options: SlurmDryRunOptions | None = None,
    ):
        self.registry = registry
        self.options = options or SlurmDryRunOptions()

    @property
    def capabilities(self) -> ExecutorCapabilities:
        return ExecutorCapabilities(
            backend=self.backend,
            supports_campaigns=True,
            supports_replay=False,
            supports_cancellation=False,
            supports_artifact_collection=True,
            requires_credentials=False,
            scheduler="slurm",
            notes=(
                "Dry-run only: writes request bundle and Slurm script; never calls sbatch.",
                "Generated artifacts must be reviewed before manual scheduler submission.",
            ),
        )

    def submit(self, spec: ExecutionJobSpec) -> ExecutionJobHandle:
        handle = self.registry.create(
            spec,
            backend=self.capabilities.backend,
            state="draft",
            message="Dry-run Slurm request bundle created; no scheduler submission performed.",
        )
        request_dir = Path(handle.status_uri or "").resolve().parent / "request-bundle"
        artifacts = self._write_request_bundle(handle, spec, request_dir)
        result = ExecutionJobResult(
            handle=ExecutionJobHandle(
                job_id=handle.job_id,
                backend=handle.backend,
                state="draft",
                status_uri=handle.status_uri,
            ),
            state="draft",
            experiment_id=(spec.experiment or {}).get("id"),
            artifacts=artifacts,
        )
        self.registry.record_result(
            handle,
            result,
            message="Dry-run Slurm request bundle is ready for review.",
            progress=1.0,
            metadata={
                "scheduler": "slurm",
                "submission_policy": "never_submit",
                "manual_submit_command": "sbatch slurm-job.sh",
                "request_bundle_dir": str(request_dir),
                "artifact_paths": [
                    str(artifact.path)
                    for artifact in artifacts
                    if artifact.path is not None
                ],
            },
        )
        return handle

    def status(self, handle: ExecutionJobHandle) -> ExecutionJobStatus:
        return self.registry.status(handle)

    def collect(self, handle: ExecutionJobHandle) -> ExecutionJobResult:
        record = self.registry.get(handle.job_id)
        result = record.get("result") or {}
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
            state=record["state"],
            experiment_id=result.get("experiment_id"),
            artifacts=artifacts,
            error=result.get("error"),
        )

    def _write_request_bundle(
        self,
        handle: ExecutionJobHandle,
        spec: ExecutionJobSpec,
        request_dir: Path,
    ) -> tuple[ExecutionArtifact, ...]:
        request_dir.mkdir(parents=True, exist_ok=False)
        config_path = self._write_config_source(spec, request_dir)
        script_path = request_dir / "slurm-job.sh"
        readme_path = request_dir / "README.md"
        request_path = request_dir / "request-bundle.json"

        script_path.write_text(
            self._render_slurm_script(config_path.name),
            encoding="utf-8",
        )
        readme_path.write_text(
            self._render_request_readme(handle, spec, config_path.name),
            encoding="utf-8",
        )
        request_payload = self._request_bundle_payload(
            handle,
            spec,
            request_dir=request_dir,
            config_path=config_path,
            script_path=script_path,
            readme_path=readme_path,
        )
        request_path.write_text(
            json.dumps(request_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        return (
            ExecutionArtifact(
                role="request_bundle",
                path=request_path,
                sha256=_file_sha256(request_path),
                media_type="application/json",
                label="Slurm dry-run request bundle",
            ),
            ExecutionArtifact(
                role="other",
                path=script_path,
                sha256=_file_sha256(script_path),
                media_type="text/x-shellscript",
                label="Reviewable Slurm batch script",
            ),
            ExecutionArtifact(
                role="other",
                path=config_path,
                sha256=_file_sha256(config_path),
                media_type=_media_type_for_config(config_path),
                label="Copied QS-DMSS config",
            ),
            ExecutionArtifact(
                role="other",
                path=readme_path,
                sha256=_file_sha256(readme_path),
                media_type="text/markdown",
                label="Dry-run review instructions",
            ),
        )

    def _write_config_source(self, spec: ExecutionJobSpec, request_dir: Path) -> Path:
        source_config_path = spec.metadata.get("source_config_path")
        if source_config_path:
            source_path = Path(str(source_config_path)).resolve()
            if source_path.exists() and source_path.is_file():
                suffix = source_path.suffix if source_path.suffix else ".yaml"
                target_path = request_dir / f"config{suffix}"
                target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
                return target_path

        target_path = request_dir / "config.json"
        target_path.write_text(
            json.dumps(spec.config, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target_path

    def _request_bundle_payload(
        self,
        handle: ExecutionJobHandle,
        spec: ExecutionJobSpec,
        *,
        request_dir: Path,
        config_path: Path,
        script_path: Path,
        readme_path: Path,
    ) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "created_at": _utc_now(),
            "job_id": handle.job_id,
            "backend": self.capabilities.backend,
            "scheduler": "slurm",
            "state": "draft",
            "submission_policy": {
                "submitted": False,
                "never_submit": True,
                "manual_review_required": True,
                "manual_submit_command": "sbatch slurm-job.sh",
            },
            "capabilities": _json_safe(self.capabilities),
            "slurm_options": _json_safe(self.options),
            "request_dir": str(request_dir),
            "spec": _json_safe(spec),
            "artifacts": [
                self._artifact_manifest_entry(config_path, "config"),
                self._artifact_manifest_entry(script_path, "slurm_script"),
                self._artifact_manifest_entry(readme_path, "review_readme"),
            ],
            "security_notes": [
                "This dry-run artifact does not submit to Slurm or contact a remote host.",
                "Review scheduler directives, module loads, environment assumptions, and output paths before manual use.",
                "Do not add credentials, SSH keys, tokens, or private scheduler settings to this bundle.",
            ],
        }

    def _artifact_manifest_entry(self, path: Path, role: str) -> dict[str, str]:
        return {
            "role": role,
            "path": path.name,
            "sha256": _file_sha256(path),
        }

    def _render_slurm_script(self, config_name: str) -> str:
        options = self.options
        directives = [
            "#!/usr/bin/env bash",
            "# QS-DMSS Slurm dry-run script. Review before manual submission.",
            "# This file was generated without calling sbatch.",
            f"#SBATCH --job-name={_shell_safe_directive(options.job_name)}",
            f"#SBATCH --time={_shell_safe_directive(options.time_limit)}",
            f"#SBATCH --nodes={options.nodes}",
            f"#SBATCH --ntasks={options.ntasks}",
            f"#SBATCH --cpus-per-task={options.cpus_per_task}",
            f"#SBATCH --mem={_shell_safe_directive(options.memory)}",
            f"#SBATCH --output={_shell_safe_directive(options.output_name)}",
            f"#SBATCH --error={_shell_safe_directive(options.error_name)}",
        ]
        if options.partition:
            directives.append(f"#SBATCH --partition={_shell_safe_directive(options.partition)}")
        if options.account:
            directives.append(f"#SBATCH --account={_shell_safe_directive(options.account)}")
        if options.qos:
            directives.append(f"#SBATCH --qos={_shell_safe_directive(options.qos)}")

        lines = [
            *directives,
            "",
            "set -euo pipefail",
            "",
            "echo \"QS-DMSS dry-run Slurm script starting at $(date -u +%Y-%m-%dT%H:%M:%SZ)\"",
            "echo \"Working directory: ${SLURM_SUBMIT_DIR:-$(pwd)}\"",
        ]
        if options.python_module:
            lines.extend(
                [
                    f"module load {_shell_safe_directive(options.python_module)}",
                    "",
                ]
            )
        lines.extend(
            [
                f"{_shell_quote(options.qs_dmss_command)} run {_shell_quote(config_name)} --output-root {_shell_quote(options.output_root)}",
                "echo \"QS-DMSS dry-run Slurm script completed at $(date -u +%Y-%m-%dT%H:%M:%SZ)\"",
                "",
            ]
        )
        return "\n".join(lines)

    def _render_request_readme(
        self,
        handle: ExecutionJobHandle,
        spec: ExecutionJobSpec,
        config_name: str,
    ) -> str:
        labels = ", ".join(spec.labels) if spec.labels else "none"
        return (
            "# QS-DMSS Slurm Dry-Run Request Bundle\n\n"
            "This directory is review material only. QS-DMSS did not submit a "
            "scheduler job, contact Slurm, or run remote commands.\n\n"
            f"- Job ID: `{handle.job_id}`\n"
            f"- Backend: `{self.capabilities.backend}`\n"
            f"- Scheduler: `slurm`\n"
            f"- State: `draft`\n"
            f"- Source config: `{config_name}`\n"
            f"- Labels: `{labels}`\n\n"
            "Review checklist:\n\n"
            "1. Inspect `request-bundle.json` for config, workspace, requester, and metadata.\n"
            "2. Inspect `slurm-job.sh` for scheduler directives and environment assumptions.\n"
            "3. Confirm no credentials, SSH keys, tokens, or private scheduler settings are present.\n"
            "4. If appropriate, copy the bundle to the target environment and submit manually with `sbatch slurm-job.sh`.\n"
            "5. Return generated QS-DMSS run artifacts through the normal evidence verification path.\n"
        )


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _media_type_for_config(path: Path) -> str:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return "application/x-yaml"
    if path.suffix.lower() == ".json":
        return "application/json"
    return "text/plain"


def _shell_safe_directive(value: str) -> str:
    return "".join(character for character in str(value) if character not in "\r\n").strip()


def _shell_quote(value: str) -> str:
    text = str(value)
    if not text:
        return "''"
    if all(character.isalnum() or character in "._/-" for character in text):
        return text
    return "'" + text.replace("'", "'\"'\"'") + "'"
