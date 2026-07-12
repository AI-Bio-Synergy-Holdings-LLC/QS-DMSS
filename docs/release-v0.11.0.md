# QS-DMSS v0.11.0 Release Notes

QS-DMSS v0.11.0 is the Hosted Studio and scientific workspace milestone. It
aligns the downloadable Python package with the public demonstration at
`app.qs-dmss.studio` while preserving the stronger persistence and
configuration capabilities of a local install.

## Highlights

- Adds a constrained hosted-demo mode with packaged scenarios, session-scoped
  temporary outputs, runtime and artifact caps, and no arbitrary config or
  workspace uploads.
- Adds a progressive Lab Mode path: run the showcase, compare real variants,
  inspect evidence, and compose a publication-oriented research object.
- Expands scientific run detail with metric summaries, provenance, evidence
  status, richer SVG figures, and clearer interpretation/non-claim guidance.
- Adds polished comparison reports and a portable HTML research workbook with
  supporting visuals, parameter tables, metric deltas, recommendation context,
  artifact identities, and citation guidance.
- Improves WCAG 2.2-oriented navigation, focus visibility, responsive reflow,
  long-running status feedback, disabled-control semantics, and report layout.
- Adds Studio SEO/discovery metadata, Google and Bing verification assets, and
  a canonical link from `qs-dmss.studio` to the hosted application.

## Install And Run

```powershell
python -m pip install --upgrade qs-dmss==0.11.0
qs-dmss cockpit
```

Then open the local cockpit URL printed by the command. The local package uses
the same cockpit application as the hosted demo, without hosted-demo session
TTL, packaged-input restrictions, or temporary-output policy.

The constrained public experience remains available at:

```text
https://app.qs-dmss.studio
```

## Hosted And Local Boundary

The public hosted service allows packaged Lab Mode scenarios, guided
comparison, the packaged self-interaction study, evidence checks, workbooks,
and research-object exports. It restricts arbitrary paths, uploaded workspaces,
custom campaign launches, and large jobs. Hosted outputs are temporary.

A local install supports persistent outputs, local configuration editing,
workspace and study-template portability, and the complete local cockpit/API
surface. Neither mode submits real Slurm jobs; scheduler support remains a
reviewable dry-run request-bundle path only.

## Scientific Claim Boundary

QS-DMSS remains beta software for reproducible package/evidence workflows. It
does not claim peer-reviewed scientific validation, production cosmology
readiness, public-data calibration of the model, GPU-first performance, exact
fractal-boundary PDE solving, or real HPC scheduler submission.

The Fractal/Quadrant SSFM lane remains validation-gated. Its mask geometries and
spectral diagnostics are exploratory and must not be presented as validated
decision metrics without external technical review.

## Validation Gate

Before tagging `v0.11.0`:

```powershell
python -m pytest -q
node --check src/qs_dmss/cockpit/static/app.js
python -m build --sdist --wheel
python -m twine check dist/*
```

Also run a wheel-installed local cockpit smoke and the Docker hosted-demo smoke.
After publication, run the cross-platform Fresh Install Smoke workflow against
PyPI `0.11.0` and the `v0.11.0` GitHub release wheel.

## Citation Status

- Project DOI: `10.5281/zenodo.20074924`
- v0.11.0 release DOI: `10.5281/zenodo.21319023`
- Previous archived release: `v0.10.1` / `10.5281/zenodo.21270512`

The release DOI is recorded in `CITATION.cff`, `README.md`, `codemeta.json`,
citation docs, and public release notes.
