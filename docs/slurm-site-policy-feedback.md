# Slurm Site-Policy Feedback Packet

This packet is for HPC administrators, research software engineers, and
research computing reviewers who can sanity-check the QS-DMSS dry-run Slurm
request bundle before any real scheduler connector is built.

QS-DMSS does **not** submit scheduler jobs today. The current Slurm path is a
review-only generator that writes local artifacts for inspection.

## What To Review

Run:

```bash
qs-dmss executors slurm-dry-run configs/demo.yaml --request-root dry-run-jobs --job-name qs-demo
```

The command creates:

```text
dry-run-jobs/
  job-<timestamp>-<id>/
    job.json
    request-bundle/
      README.md
      config.yaml
      request-bundle.json
      slurm-job.sh
```

Important guarantees:

- `job.json` remains in state `draft`.
- `request-bundle.json` records `submission_policy.submitted=false`.
- `request-bundle.json` records `submission_policy.never_submit=true`.
- `slurm-job.sh` contains `#SBATCH` directives and a `qs-dmss run` command.
- The dry-run command does not call `sbatch`, `squeue`, `sacct`, SSH, or any
  remote scheduler command.

## Review Questions

Please review the generated `request-bundle/` directory and answer any of the
questions below that match your site expertise.

### Scheduler Directives

- Are the generated `#SBATCH` directives acceptable as a neutral starting point?
- Which directives should be required, forbidden, or site-specific?
- Should `partition`, `account`, `qos`, memory, CPU, node, and time fields be
  profile-driven rather than user-entered each time?
- Are job names, stdout paths, and stderr paths formatted in a site-friendly way?

### Environment Setup

- Should QS-DMSS assume `python -m pip install qs-dmss`, a module load, a
  virtual environment, a container image, or a site-managed environment?
- Should `slurm-job.sh` avoid `module load` entirely unless a site profile
  provides it?
- Are there required prologue/epilogue patterns that should be represented in a
  review bundle before real submission?

### Filesystem And Artifact Flow

- Where should input configs be staged before submission?
- Where should run outputs, logs, evidence bundles, and reports be written?
- What path patterns should be rejected to avoid writing outside approved
  scratch/project directories?
- Should the eventual connector copy artifacts back, leave them in place, or
  record pointers to site storage?

### Accounting And State Mapping

- Which Slurm states should map to QS-DMSS states such as `queued`, `running`,
  `succeeded`, `failed`, `cancelled`, or `collecting`?
- Which scheduler identifiers and accounting fields are safe and useful to
  store in QS-DMSS job provenance?
- Which failure artifacts should always be preserved?

### Security And Policy Boundaries

- Does the bundle accidentally imply arbitrary shell execution?
- Are there shell quoting, path containment, or environment assumptions that
  should be tightened?
- What credential, SSH, or scheduler-access rules must be documented before any
  submit/status/collect connector exists?
- Should real submission require an explicit named site profile plus a manual
  confirmation step?

## Feedback Format

The most useful feedback is small and specific. A good review comment can be as
simple as:

```text
Site type: university Slurm cluster
Reviewed: slurm-job.sh and request-bundle.json
Blocker: account must be required; jobs without --account are rejected.
Recommendation: make account part of a named site profile, not a free-text CLI
field.
```

Please avoid sharing secrets, private hostnames, internal usernames, scheduler
tokens, unpublished allocation IDs, or private filesystem paths. Generalized
examples are better than exact site-sensitive values.

## What This Feedback Unlocks

This review does not imply real HPC submission support is ready. It helps decide
whether the next implementation slice should be:

- a named scheduler-profile model,
- stricter path and directive validation,
- a richer request-bundle manifest,
- a local-only manual submission guide,
- or a real `SlurmExecutor` prototype behind explicit opt-in controls.

Real `sbatch` / `squeue` / `sacct` support should wait until this dry-run shape
has been reviewed against at least one real site policy.
