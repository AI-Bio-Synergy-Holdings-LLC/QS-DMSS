# QS-DMSS v0.13.0 Release Candidate

## Status

This document is release preparation, not a publication announcement. The
current published package and archived Zenodo release remain `v0.12.0`.
`v0.13.0` has no release DOI until the tagged GitHub release is archived by
Zenodo.

## What Changes

- The local-first cockpit now runs the quantum validation harness live and
  redraws topology and attribution figures from the resulting evidence.
- Every topology and optimization row is available for comparison; a
  recommendation is highlighted rather than used as a constraint.
- Lab Mode has a Research Runbook that makes the research sequence visible:
  define scope, execute, inspect evidence, verify/replay, and communicate.
- The contextual Evidence Assistant explains the selected scenario, run,
  evidence bundle, verification, replay, comparison, or export record without
  acting as a generic chatbot or creating evidence.
- Cockpit and site metadata separate the source build from the latest archived
  DOI so readers never mistake an unarchived build for a citable release.

## Claim Boundary

QS-DMSS remains beta software for reproducible package and evidence workflows;
it is not peer-reviewed scientific validation. Quantum validation remains
simulator-first and provider-neutral: no provider credentials, remote API calls,
QPU execution, job submission, or authorized spend are included.

## Release Gates

Before `v0.13.0` is published:

1. Merge PR #154, then PR #155, through green `main` CI.
2. Confirm CodeQL reanalysis closes alert #20 on `main`.
3. Build the source distribution and wheel from the clean merge commit; run
   `twine check` and a fresh-install smoke test.
4. Tag `v0.13.0`, create the GitHub release, and attach the approved artifacts.
5. Wait for Zenodo to archive the GitHub release, then update the exact release
   DOI in citation metadata, the cockpit, and the public Studio site.
6. Use the Trusted Publishing workflow to publish those same assets to PyPI.
7. Confirm GitHub Pages and the Render service have deployed `main` and report
   healthy `/api/health` responses.

## Citation During Preparation

Use the stable QS-DMSS project concept DOI during preparation:

```text
10.5281/zenodo.20074924
```

For the current archived baseline, use the exact v0.12.0 DOI:

```text
10.5281/zenodo.21329711
```
