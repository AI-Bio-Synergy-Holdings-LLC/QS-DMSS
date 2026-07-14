# QS-DMSS v0.13.0 Release

## Status

`v0.13.0` was released from merge commit
`7321d126c184863c50e32c6d0c5b9d71674fcdb7` on 2026-07-14. The GitHub release
contains the validated wheel and source distribution, and Zenodo archived the
release as [10.5281/zenodo.21348257](https://doi.org/10.5281/zenodo.21348257).
The exact artifacts were published on PyPI as `qs-dmss==0.13.0` through the
repository's Trusted Publishing workflow.

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

## Completed Release Gates

1. PRs #154 and #155 merged through green `main` CI.
2. CodeQL reanalysis fixed alert #20; no open main-branch code-scanning alerts remain.
3. The source distribution and wheel built from the clean merge commit and passed
   `twine check`; fresh-install, quantum-sidecar, and Docker-smoke checks passed.
4. GitHub release `v0.13.0` was created with the approved artifacts.
5. Zenodo archived the release as `10.5281/zenodo.21348257`.
6. GitHub Pages and the Render service deployed `main`; `/api/health` reports
   `v0.13.0`.
7. The guarded `Publish to PyPI` workflow validated the exact release assets and
   published both files through GitHub OIDC / PyPI Trusted Publishing.

## Citation

Use this version DOI when citing the exact v0.13.0 release:

```text
10.5281/zenodo.21348257
```

Use the stable project concept DOI for project-level citation:

```text
10.5281/zenodo.20074924
```
