# Beta Readiness

This document records the gate used to move QS-DMSS from
`Development Status :: 3 - Alpha` to `Development Status :: 4 - Beta` on PyPI.

The intended beta claim is narrow:

> QS-DMSS is beta for reproducible package/evidence workflows; it is not
> peer-reviewed scientific validation.

## Current Decision

- Current release target: `v0.12.0` / `0.12.0`
- Current PyPI classifier target: `Development Status :: 4 - Beta`
- Promotion basis: `v0.1.5` passed the beta-readiness gate
- Current Zenodo concept DOI: `10.5281/zenodo.20074924`
- Latest archived release DOI: `10.5281/zenodo.21329711`
- `v0.12.0` release DOI: `10.5281/zenodo.21329711`
- `v0.11.0` release DOI: `10.5281/zenodo.21319023`
- `v0.8.0` release DOI: `10.5281/zenodo.20673804`
- `v0.7.0` release DOI: `10.5281/zenodo.20671389`
- `v0.6.1` release DOI: `10.5281/zenodo.20631860`
- `v0.6.0` release DOI: `10.5281/zenodo.20618884`
- `v0.5.0` release DOI: `10.5281/zenodo.20617028`

The beta classifier is only appropriate for the narrow package/evidence surface
defined below.

## Beta-Stable Surface

The beta promise applies to these user-facing workflows:

- Installing `qs-dmss` from PyPI into a fresh virtual environment.
- Installing the GitHub release wheel into a fresh virtual environment.
- Running `qs-dmss run-demo` from an installed package.
- Running `qs-dmss campaigns run-demo` from an installed package.
- Producing run outputs under caller-controlled `runs/` paths.
- Producing campaign outputs under caller-controlled `experiments/` paths.
- Verifying generated evidence bundles with `qs-dmss verify`.
- Replaying a generated run with `qs-dmss replay`.
- Running `qs-dmss benchmarks validate --scenario demo-baseline` from the
  packaged benchmark validation spine.
- Starting the local cockpit and using Lab Mode for guided interpretation,
  Evidence Explorer previews, and guided comparison of packaged variants.
- Using Campaign Studio to inspect packaged scenario metadata, edit the
  parameter grid, edit the decision profile, preview the scoring contract, and
  launch an objective-driven campaign through the cockpit.
- Publishing traceable wheel and sdist artifacts through GitHub releases and
  PyPI Trusted Publishing.
- Keeping package metadata, release assets, and citation metadata aligned.

## Beta Non-Goals

The beta label does not claim:

- Peer-reviewed scientific validation.
- Production scientific conclusions from the bundled demo configuration.
- Numerical accuracy guarantees beyond deterministic smoke and regression
  coverage.
- Stability of internal Python module APIs.
- Hosted service availability.
- GPU, distributed, or high-performance backend support.
- Long-term stability for experimental cockpit UI details.
- Compatibility with arbitrary user-defined physical models.

## Required Evidence

- Main CI is green across Python 3.10 through 3.13.
- CodeQL has no open high-severity alerts.
- Docker smoke passes.
- Release artifacts pass `twine check`.
- Fresh install smoke passes on Linux, macOS, and Windows for:
  - PyPI install path.
  - GitHub release wheel install path.
- Reviewer quickstart includes Windows PowerShell and Linux/macOS Bash paths.
- Reviewer quickstart includes expected output examples for the demo and
  campaign demo.
- Reviewer quickstart includes a reproducibility review checklist.
- Citation metadata points to the latest available archived release DOI until a
  new release-specific DOI is minted.
- PyPI project URLs include the repository, issues, reviewer quickstart,
  circulation funnel, beta readiness gate, PyPI, and DOI links.

## Promotion Patch

The `v0.2.0` promotion made only the classifier and release-alignment changes
needed for beta.

The `v0.3.0` promotion adds the benchmark-validation release surface:

- Bumps `pyproject.toml` and `qs_dmss.__version__` to `0.3.0`.
- Keeps the PyPI classifier at `Development Status :: 4 - Beta`.
- Ships packaged benchmark scenarios, expected metric envelopes, and
  `qs-dmss benchmarks validate`.
- Updates release docs and issue templates to `0.3.0`.
- Preserve the public language: beta for reproducible package/evidence
  workflows, not peer-reviewed scientific validation.
- Cut `v0.3.0`, let Zenodo archive it, and publish through Trusted Publishing.

Avoid expanding the scientific claim in the benchmark-validation promotion.
The point of `v0.3.0` is to make the benchmark evidence workflow installable,
not to claim peer-reviewed scientific validation.

The `v0.5.0` product milestone adds the Lab Mode release surface:

- Keeps the PyPI classifier at `Development Status :: 4 - Beta`.
- Ships guided interpretation, Evidence Explorer previews, and guided
  comparison through the local cockpit.
- Preserves the same claim boundary: beta for reproducible package/evidence
  workflows, not peer-reviewed scientific validation.

The `v0.6.0` product milestone adds the Publication Export Composer:

- Keeps the PyPI classifier at `Development Status :: 4 - Beta`.
- Lets Lab Mode compose a reviewer-facing research object with scenario,
  metrics, evidence status, replay instructions, artifact links, citation/DOI
  metadata, and a Markdown export.
- Keeps the same claim boundary: beta for reproducible package/evidence
  workflows, not peer-reviewed scientific validation.

The `v0.7.0` product milestone adds Campaign Studio configurability:

- Keeps the PyPI classifier at `Development Status :: 4 - Beta`.

The `v0.8.0` release target adds the Campaign Studio Template Library polish
and a clean public code-scanning posture:

- Keeps the PyPI classifier at `Development Status :: 4 - Beta`.
- Shows saved study templates as reusable research-asset cards with objective,
  metric, run-plan, source, import/export, and last-run provenance metadata.
- Uses the latest available archived DOI until the next release-specific DOI is minted.
- Ships Scenario Library metadata, editable Campaign Studio parameter grids,
  editable decision profiles, and scoring-contract preview in the local
  cockpit.
- Keeps using the existing campaign/evidence/recommendation pipeline rather
  than expanding the scientific claim.
- Keeps the same claim boundary: beta for reproducible package/evidence
  workflows, not peer-reviewed scientific validation.
