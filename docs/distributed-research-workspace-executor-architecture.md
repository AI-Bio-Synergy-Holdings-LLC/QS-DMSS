# Distributed Research Workspace + Executor Architecture

Status: architecture sketch, not shipped distributed execution.

QS-DMSS is currently strongest as a local, evidence-first simulation lab. The
next larger platform direction is possible, but it should preserve that local
trust model: users should still be able to run, inspect, verify, replay, bundle,
and cite a study without a hosted service.

This document defines the next architecture seam for collaboration and HPC
connectors without turning the current product into a premature cloud platform.

## Goal

Add a path toward multiple researchers, locations, and compute backends while
keeping every simulation study portable as a research object.

The product loop becomes:

```text
design study -> submit job -> collect artifacts -> verify evidence -> discuss/export research object
```

## Current Baseline

The merged public product is local-first:

- FastAPI cockpit and static UI served on `127.0.0.1` by default.
- Filesystem-backed runs under `runs/`.
- Filesystem-backed experiments and study templates under `experiments/`.
- Synchronous local execution through the current Python runner.
- Evidence bundles, manifests, reports, replay commands, and campaign
  comparison artifacts.
- No user accounts, database, remote scheduler, credential store, or live
  collaboration channel.

That is a good foundation. The distributed design should wrap this model rather
than replace it.

## Collaboration Object Model

A collaboration suite should begin with portable workspace objects, not live
multi-user editing.

Recommended first objects:

- `ResearchWorkspace`: a named container for study templates, runs,
  experiments, research-object exports, annotations, and provenance.
- `CollaboratorRef`: display identity, affiliation, optional location label,
  and role used for provenance.
- `StudyTemplate`: existing Campaign Studio template plus owner, version,
  source, import/export status, and last-run provenance.
- `ExecutionJob`: a submitted run, replay, sweep, or campaign with job state,
  backend, scheduler ID, requesting collaborator, and linked artifacts.
- `Annotation`: lightweight comment attached to a run, metric, artifact,
  campaign recommendation, or export section.
- `ResearchObjectExport`: Markdown/HTML/report surface with citation block,
  evidence status, job provenance, and collaborator metadata.

The first collaboration version can be local and file-backed:

```text
experiments/
  workspaces/
    <workspace_id>/
      workspace.json
```

This supports asynchronous collaboration by export/import or Git-backed sharing
before introducing accounts or a server database. The current local
implementation embeds collaborators, annotations, selected run and experiment
summaries, Campaign Studio study templates, research-object references, and job
summaries in `workspace.json`; copied binary evidence payloads can be layered on
later as a bundle format.

Current local API:

- `GET /api/workspaces`
- `GET /api/workspaces/{workspace_id}`
- `GET /api/workspaces/{workspace_id}/download`
- `POST /api/workspaces/export`
- `POST /api/workspaces/import`

Importing a workspace preserves the source workspace ID and installs included
Campaign Studio study templates as local templates so another researcher can
reopen, edit, rerun, and export the study design.

## Executor Contract

Executors should be responsible for compute placement, not evidence semantics.
QS-DMSS should keep the same artifact expectations whether the work ran locally,
over SSH, or through Slurm.

Internal interface sketch:

```python
from qs_dmss.execution import (
    ExecutionJobHandle,
    ExecutionJobResult,
    ExecutionJobSpec,
    ExecutionJobStatus,
    ExecutorCapabilities,
)


class Executor:
    @property
    def capabilities(self) -> ExecutorCapabilities: ...
    def submit(self, spec: ExecutionJobSpec) -> ExecutionJobHandle: ...
    def status(self, handle: ExecutionJobHandle) -> ExecutionJobStatus: ...
    def collect(self, handle: ExecutionJobHandle) -> ExecutionJobResult: ...
```

The first implementation should be `LocalExecutor`, a thin adapter over the
existing runner. That proves the seam without changing behavior. Remote
executors should come after local parity is tested.

## Local Executor Implementation

The first implementation slice keeps execution synchronous and local while
recording job lifecycle metadata by default.

Local runs now follow this shape:

```text
ExecutionJobSpec -> LocalExecutor -> local runner -> evidence bundle
                              \-> jobs/<job_id>/job.json
```

The local job record is a file-backed lifecycle record with:

- submitted config and source name;
- labels such as `run`, `replay`, `campaign`, or `guided-comparison`;
- state transitions from `submitted` to `running` to `collecting` to
  `succeeded`;
- returned artifact roles such as run directory, evidence bundle, report,
  metrics, and manifest;
- failure metadata if a local run raises before completion.

Each generated `run.json` includes an `execution_job` reference with the local
job ID, backend, and registry path. The evidence bundle remains the trusted
research object; the registry is a local coordination layer for later
collaboration and HPC work.

## Job Lifecycle

Use one lifecycle vocabulary for local and remote execution:

```text
draft -> submitted -> queued -> running -> collecting -> succeeded
                                  -> failed
                                  -> cancelled
```

Important state boundaries:

- `draft`: study design exists but no executor has accepted it.
- `submitted`: QS-DMSS handed the job spec to an executor.
- `queued`: a scheduler or remote queue accepted the job.
- `running`: compute has started.
- `collecting`: QS-DMSS is copying or verifying returned artifacts.
- `succeeded`: manifest, report, metrics, and bundle are available.
- `failed`: error, logs, and partial artifacts should be preserved.
- `cancelled`: user or scheduler cancelled the job.

## Artifact Return Path

Every executor should return artifacts through the same roles:

- request bundle: config, job spec, workspace metadata, and environment notes;
- stdout/stderr logs;
- run directory or experiment directory;
- `metrics.json`;
- `manifest.sha256.json`;
- `report.html`;
- `evidence_bundle.zip`;
- scheduler metadata when applicable.

Remote collection should never trust files blindly. Collected artifacts should
be placed under a contained local workspace path, then verified with the same
manifest and config-digest checks the local product already uses.

## HPC Connector Path

HPC support is feasible, but should be layered in dry-run form before real
scheduler submission.

Recommended connector sequence:

1. `LocalExecutor`: current behavior behind the executor contract.
2. `DryRunExecutor`: writes the exact job spec and scheduler script but does not
   submit it.
3. `SlurmExecutor`: `sbatch`, `squeue`, `sacct`, artifact staging, and collection.
4. `PbsExecutor` or `LsfExecutor`: only after Slurm proves the contract.
5. `SshExecutor`: for single remote workstation/lab server workflows.

Each connector should answer:

- How is the config packaged?
- Where does stdout/stderr go?
- How is the run directory staged back?
- Which scheduler state maps to QS-DMSS job state?
- What credentials are required, and where are they kept?
- How are partial failures preserved as evidence?

## Security Boundaries

Distributed execution adds real risk. The default QS-DMSS posture should remain
safe and local.

Guardrails:

- Keep local-only cockpit as the default.
- Do not store SSH keys, API tokens, or scheduler credentials in study templates.
- Treat imported workspaces and artifact bundles as untrusted until verified.
- Use path containment for every collected file.
- Restrict remote job scripts to generated, reviewable templates.
- Prefer scheduler profiles by name over arbitrary shell snippets.
- Record collaborator, backend, scheduler ID, and collection time in job
  provenance.
- Preserve failed job artifacts and logs without exposing Python tracebacks in
  public UI surfaces.
- Add authentication and authorization before any shared server mode is exposed
  beyond localhost.

## Non-Goals For The First Slice

- No hosted QS-DMSS service.
- No real-time collaborative editing.
- No remote credential manager.
- No production-scale solver claim.
- No direct arbitrary shell execution from the cockpit.
- No scheduler-specific connector until the local executor seam exists.

## Recommended Build Slices

1. Complete: add this architecture and internal interface sketch.
2. Complete: implement `LocalExecutor` as the default cockpit/CLI execution
   adapter with file-backed job records for local runs and replay runs.
3. Complete: expose local job records in the cockpit/API as run and
   campaign-variant provenance.
4. Complete: add campaign-level and research-object-export job records where
   the job represents a multi-run artifact or persisted publication export
   rather than one simulation run.
5. Complete: add workspace export/import with collaborators and annotations.
6. Next: add `DryRunSlurmExecutor` that produces a reviewable batch script and request
   bundle without submission.
7. Add real Slurm submit/status/collect behind an explicit opt-in profile.

## Success Standard

The distributed layer is successful when a collaborator can receive a workspace
or collected HPC artifact, verify the evidence bundle, understand who ran what,
replay locally when feasible, and cite/export the result without trusting an
opaque remote service.
