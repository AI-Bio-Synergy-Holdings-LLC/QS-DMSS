# QS-DMSS v0.10.1 Release Notes

QS-DMSS v0.10.1 is a public-trust patch release. It keeps the v0.10.0
reference-data provenance and Fractal/Quadrant SSFM validation workflows
installable from PyPI while adding job-registry path hardening, package
metadata alignment, and a public Conceptual Reference Map.

This release does not add new scientific claims or feature scope.

## Highlights

- Hardens local job-registry path handling for run, campaign, and dry-run Slurm
  provenance records.
- Adds regression coverage that rejects path-like job IDs while preserving
  generated local job records and dry-run Slurm request bundles.
- Adds a public Conceptual Reference Map that labels references by role:
  conceptual physics context, numerical-method precedent, public source-data
  provenance, research-object infrastructure, and future comparison targets.
- Updates package-facing metadata to use `AI-Bio Synergy Holdings LLC`, the
  Studio front door, and the Conceptual Reference Map project URL.
- Refreshes current-baseline docs, reviewer quickstarts, Studio copy, cockpit
  citation metadata, and release policy to `v0.10.1`.

## Quickstart

Install the release:

```powershell
python -m pip install --upgrade qs-dmss==0.10.1
```

Run the public evidence workflows:

```powershell
qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss validation fractal-ssfm
qs-dmss data calibration run --output-root reference-data-calibration
```

Inspect the reference map:

```text
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/conceptual-reference-map.md
```

## Security And Trust

GitHub CodeQL opened high-severity `py/path-injection` alerts against the local
job registry path flow after the v0.10.0 public-surface updates. v0.10.1
hardens the registry boundary:

- externally supplied job IDs must match the generated
  `job-YYYYMMDDTHHMMSSZ-xxxxxxxx` shape;
- existing jobs are resolved by matching a direct child directory of the local
  `jobs_root`;
- path-like, absolute, nested, or legacy loose job IDs are rejected;
- dry-run Slurm request bundles remain generated under
  `jobs/<job_id>/request-bundle`;
- no Slurm scheduler submission is performed.

## Claim Boundary

QS-DMSS remains beta for reproducible package/evidence workflows. This release
does not claim peer-reviewed scientific validation, public-data calibration of
the QS-DMSS model, production cosmology readiness, GPU-first performance, or
real HPC scheduler submission support.

The Conceptual Reference Map is a transparency layer. It makes citation roles
auditable; it is not an endorsement or external validation claim.

## Validation Gate

Before tagging `v0.10.1`, validate:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --check src/qs_dmss/cockpit/static/app.js
.\.venv\Scripts\python.exe -m build --sdist --wheel
.\.venv\Scripts\python.exe -m twine check dist/*
```

After publication, run a fresh install smoke against PyPI `qs-dmss==0.10.1`
and the GitHub release wheel from `v0.10.1`.

## Citation Status

- Project DOI: `10.5281/zenodo.20074924`
- `v0.10.1` release DOI: `10.5281/zenodo.21270512`
- Previous archived release DOI: `10.5281/zenodo.20693736`
