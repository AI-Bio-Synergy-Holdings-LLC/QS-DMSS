from pathlib import Path

from qs_dmss.execution import (
    CollaboratorRef,
    ExecutionArtifact,
    ExecutionJobHandle,
    ExecutionJobResult,
    ExecutionJobSpec,
    ExecutionJobStatus,
    ExecutorCapabilities,
    LocalJobRegistry,
    ResearchWorkspaceRef,
)


def test_execution_job_spec_captures_workspace_and_requester() -> None:
    workspace = ResearchWorkspaceRef(
        workspace_id="workspace-self-interaction",
        title="Self-Interaction Collaboration Workspace",
        storage_uri="file://experiments/workspaces/workspace-self-interaction",
        owner="AI Bio Synergy Holdings LLC",
    )
    requester = CollaboratorRef(
        collaborator_id="researcher-1",
        display_name="Researcher One",
        affiliation="Example Lab",
        location_label="remote",
    )

    spec = ExecutionJobSpec(
        config={"run": {"name": "demo"}},
        source_name="self-interaction.yaml",
        workspace=workspace,
        requested_by=requester,
        output_root=Path("runs"),
        labels=("self-interaction", "campaign"),
        metadata={"study_template_id": "self-interaction-sweep"},
    )

    assert spec.workspace == workspace
    assert spec.requested_by == requester
    assert spec.labels == ("self-interaction", "campaign")
    assert spec.metadata["study_template_id"] == "self-interaction-sweep"


def test_execution_result_links_artifacts_to_job_handle() -> None:
    handle = ExecutionJobHandle(
        job_id="job-001",
        backend="local",
        state="submitted",
    )
    status = ExecutionJobStatus(
        job_id=handle.job_id,
        backend=handle.backend,
        state="running",
        progress=0.5,
    )
    artifact = ExecutionArtifact(
        role="evidence_bundle",
        path=Path("runs/demo/evidence_bundle.zip"),
        sha256="abc123",
        media_type="application/zip",
        label="Evidence bundle",
    )
    result = ExecutionJobResult(
        handle=handle,
        state="succeeded",
        run_id="demo-run",
        run_dir=Path("runs/demo"),
        artifacts=(artifact,),
        metrics={"energy_drift": 0.01},
    )

    assert status.state == "running"
    assert result.handle.job_id == "job-001"
    assert result.artifacts[0].role == "evidence_bundle"
    assert result.metrics == {"energy_drift": 0.01}


def test_executor_capabilities_describe_scheduler_without_credentials() -> None:
    capabilities = ExecutorCapabilities(
        backend="slurm",
        supports_campaigns=True,
        supports_cancellation=True,
        requires_credentials=True,
        scheduler="slurm",
        notes=("dry-run first",),
    )

    assert capabilities.backend == "slurm"
    assert capabilities.supports_campaigns is True
    assert capabilities.requires_credentials is True
    assert capabilities.notes == ("dry-run first",)


def test_local_job_registry_records_lifecycle(tmp_path: Path) -> None:
    registry = LocalJobRegistry(tmp_path / "jobs")
    spec = ExecutionJobSpec(
        config={"run": {"name": "demo"}},
        source_name="demo.yaml",
        output_root=tmp_path / "runs",
        labels=("run",),
    )

    handle = registry.create(spec)
    running = registry.update(
        handle,
        "running",
        message="Running locally.",
        progress=0.5,
    )
    result = ExecutionJobResult(
        handle=handle,
        state="succeeded",
        run_id="demo-run",
        run_dir=tmp_path / "runs" / "demo-run",
        artifacts=(
            ExecutionArtifact(
                role="evidence_bundle",
                path=tmp_path / "runs" / "demo-run" / "evidence_bundle.zip",
            ),
        ),
    )
    registry.complete(handle, result)

    record = registry.get(handle.job_id)
    assert running.state == "running"
    assert record["state"] == "succeeded"
    assert record["spec"]["source_name"] == "demo.yaml"
    assert record["spec"]["output_root"] == str(tmp_path / "runs")
    assert record["result"]["run_id"] == "demo-run"
    assert [event["state"] for event in record["lifecycle"]] == [
        "submitted",
        "running",
        "succeeded",
    ]
