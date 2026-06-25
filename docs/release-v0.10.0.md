# QS-DMSS v0.10.0 Release Notes

QS-DMSS v0.10.0 is the public reference-data provenance and validation-spine
milestone. It makes the Fractal/Quadrant SSFM validation harness and the
public reference-data calibration sandbox installable from PyPI as evidence
workflows rather than source-only review targets.

## Highlights

- Adds `qs-dmss validation fractal-ssfm` as the installable validation harness
  for the experimental NumPy Fractal/Quadrant SSFM backend.
- Adds `qs-dmss data sources list` and `qs-dmss data sources inspect <source>`
  for packaged public source-lane records.
- Adds `qs-dmss data calibration run` to materialize metadata-only source
  manifests, a tiny calibration fixture, user-cache checksums, Markdown/JSON
  reports, config metadata, and an evidence ZIP.
- Packages official source records for Planck Legacy Archive, DESI DR1, SDSS
  DR19, and Gaia DR3.
- Keeps public dataset handling provenance-first: QS-DMSS does not bundle,
  mirror, redistribute, or fine-tune against provider datasets.
- Keeps Fractal/Quadrant SSFM diagnostics scoped as a validation spine:
  `spectral_leakage` and `aliasing_ratio` remain diagnostics-only, not decision
  ranking metrics.

## Quickstart

Install the release:

```powershell
python -m pip install --upgrade qs-dmss==0.10.0
```

Inspect public reference-data source lanes:

```powershell
qs-dmss data sources list
qs-dmss data sources inspect planck-legacy
```

Run the calibration sandbox:

```powershell
qs-dmss data calibration run --output-root reference-data-calibration
```

Run the Fractal/Quadrant SSFM validation harness:

```powershell
qs-dmss validation fractal-ssfm
```

## Claim Boundary

QS-DMSS remains beta for reproducible package/evidence workflows. This release
does not claim peer-reviewed scientific validation, validated physical
conclusions from bundled scenarios, public-data calibration of the QS-DMSS
model, GPU-first performance, or production HPC submission support.

The reference-data workflow is a provenance and calibration sandbox. It records
source URLs, access dates, citations, transform metadata, cache checksums, and
evidence bundles. It does not download or mirror provider datasets.

The Fractal/Quadrant SSFM workflow is an experimental validation spine. GPU
expansion and decision-metric UI for `spectral_leakage` / `aliasing_ratio`
should wait until issue #105 receives substantive technical feedback.

## Validation Gate

Before tagging `v0.10.0`, validate:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --check src/qs_dmss/cockpit/static/app.js
.\.venv\Scripts\python.exe -m build --sdist --wheel
.\.venv\Scripts\python.exe -m twine check dist/*
```

After publication, run a fresh install smoke against PyPI `qs-dmss==0.10.0`
and the GitHub release wheel from `v0.10.0`.

## Citation Status

- Project DOI: `10.5281/zenodo.20074924`
- Latest archived release DOI before `v0.10.0`: `10.5281/zenodo.20693736`
- `v0.10.0` release DOI: pending Zenodo archive

After Zenodo archives `v0.10.0`, open a tiny DOI metadata PR updating
CITATION.cff, README citation text, Codemeta, and citation docs.
