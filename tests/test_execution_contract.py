import json
from pathlib import Path

import pytest

from qs_dmss.execution import (
    CollaboratorRef,
    DryRunSlurmExecutor,
    ExecutionArtifact,
    ExecutionJobHandle,
    ExecutionJobResult,
    ExecutionJobSpec,
    ExecutionJobStatus,
    ExecutorCapabilities,
    LocalJobRegistry,
    ResearchWorkspaceRef,
    SlurmDryRunOptions,
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


def test_local_job_registry_rejects_path_like_job_ids(tmp_path: Path) -> None:
    registry = LocalJobRegistry(tmp_path / "jobs")
    spec = ExecutionJobSpec(config={"run": {"name": "demo"}}, source_name="demo.yaml")
    handle = registry.create(spec)

    assert registry.get(handle.job_id)["job_id"] == handle.job_id
    for job_id in (
        "../job-20260101T000000Z-12345678",
        r"..\job-20260101T000000Z-12345678",
        "/tmp/job-20260101T000000Z-12345678",
        "job-20260101T000000Z-12345678/child",
        "job-001",
    ):
        with pytest.raises(ValueError):
            registry.get(job_id)


def test_dry_run_slurm_executor_emits_reviewable_request_bundle(tmp_path: Path) -> None:
    config_path = tmp_path / "self-interaction.yaml"
    config_path.write_text(
        "run:\n  name: self-interaction\n  seed: 7\n",
        encoding="utf-8",
    )
    registry = LocalJobRegistry(tmp_path / "jobs")
    executor = DryRunSlurmExecutor(
        registry,
        options=SlurmDryRunOptions(
            job_name="qs-self-interaction",
            partition="debug",
            account="science",
            time_limit="00:05:00",
            cpus_per_task=2,
            memory="4G",
            output_root="hpc-runs",
        ),
    )
    spec = ExecutionJobSpec(
        config={"run": {"name": "self-interaction", "seed": 7}},
        source_name=config_path.name,
        output_root=Path("hpc-runs"),
        labels=("dry-run", "slurm"),
        metadata={"source_config_path": str(config_path)},
    )

    handle = executor.submit(spec)
    status = executor.status(handle)
    result = executor.collect(handle)
    record = registry.get(handle.job_id)
    request_dir = tmp_path / "jobs" / handle.job_id / "request-bundle"
    request_bundle_path = request_dir / "request-bundle.json"
    script_path = request_dir / "slurm-job.sh"
    copied_config_path = request_dir / "config.yaml"

    assert handle.backend == "dry-run-slurm"
    assert handle.state == "draft"
    assert status.state == "draft"
    assert record["state"] == "draft"
    assert record["backend"] == "dry-run-slurm"
    assert record["metadata"]["submission_policy"] == "never_submit"
    assert record["result"]["state"] == "draft"
    assert [event["state"] for event in record["lifecycle"]] == ["draft"]
    assert request_bundle_path.exists()
    assert script_path.exists()
    assert copied_config_path.read_text(encoding="utf-8") == config_path.read_text(
        encoding="utf-8",
    )

    request_bundle = json.loads(request_bundle_path.read_text(encoding="utf-8"))
    assert request_bundle["submission_policy"]["submitted"] is False
    assert request_bundle["submission_policy"]["never_submit"] is True
    assert request_bundle["slurm_options"]["partition"] == "debug"
    assert request_bundle["slurm_options"]["account"] == "science"
    assert request_bundle["spec"]["metadata"]["source_config_path"] == str(config_path)
    assert {artifact["role"] for artifact in request_bundle["artifacts"]} == {
        "config",
        "slurm_script",
        "review_readme",
    }

    script = script_path.read_text(encoding="utf-8")
    assert "#SBATCH --partition=debug" in script
    assert "#SBATCH --account=science" in script
    assert "qs-dmss run config.yaml --output-root hpc-runs" in script
    assert not any(line.strip().startswith("sbatch") for line in script.splitlines())

    assert {
        artifact.role for artifact in result.artifacts
    } == {"request_bundle", "other"}
    assert all(artifact.sha256 for artifact in result.artifacts)
