"""Internal execution contracts for future distributed QS-DMSS runs.

This module intentionally defines shape, not behavior. The current product
continues to execute through the local runner; future executors can implement
this protocol without changing the evidence-bundle contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
