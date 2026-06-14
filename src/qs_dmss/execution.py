"""Internal execution contracts for future distributed QS-DMSS runs.

This module intentionally defines shape, not behavior. The current product
continues to execute through the local runner; future executors can implement
this protocol without changing the evidence-bundle contract.
"""

from __future__ import annotations

import json
import uuid
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

ArtifactRole = Literal[
    "request_bundle",
    "run_directory",
    "experiment_directory",
    "evidence_bundle",
    "report",
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

    def create(self, spec: ExecutionJobSpec, *, backend: str = "local") -> ExecutionJobHandle:
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        job_id = f"job-{_job_timestamp()}-{uuid.uuid4().hex[:8]}"
        job_dir = self._job_dir(job_id, create=True)
        record_path = job_dir / "job.json"
        handle = ExecutionJobHandle(
            job_id=job_id,
            backend=backend,
            state="submitted",
            status_uri=str(record_path),
        )
        now = _utc_now()
        record = {
            "schema_version": 1,
            "job_id": job_id,
            "backend": backend,
            "state": "submitted",
            "created_at": now,
            "updated_at": now,
            "progress": 0.0,
            "message": "Job accepted by local registry.",
            "handle": _json_safe(handle),
            "spec": _json_safe(spec),
            "lifecycle": [
                {
                    "state": "submitted",
                    "at": now,
                    "message": "Job accepted by local registry.",
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

    def _job_dir(self, job_id: str, *, create: bool = False) -> Path:
        if not job_id.startswith("job-") or any(separator in job_id for separator in ("/", "\\")):
            raise ValueError(f"Invalid job id: {job_id}")
        job_dir = (self.jobs_root / job_id).resolve()
        if job_dir.parent != self.jobs_root.resolve():
            raise ValueError(f"Job path escapes registry root: {job_id}")
        if create:
            job_dir.mkdir(parents=True, exist_ok=False)
        return job_dir

    def _job_record_path(self, job_id: str) -> Path:
        record_path = self._job_dir(job_id) / "job.json"
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
