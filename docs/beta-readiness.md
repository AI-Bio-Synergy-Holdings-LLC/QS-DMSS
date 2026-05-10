# Beta Readiness

This document records the gate used to move QS-DMSS from
`Development Status :: 3 - Alpha` to `Development Status :: 4 - Beta` on PyPI.

The intended beta claim is narrow:

> QS-DMSS is beta for reproducible package/evidence workflows; it is not
> peer-reviewed scientific validation.

## Current Decision

- Current release target: `v0.3.0` / `0.3.0`
- Current PyPI classifier target: `Development Status :: 4 - Beta`
- Promotion basis: `v0.1.5` passed the beta-readiness gate
- Current Zenodo concept DOI: `10.5281/zenodo.20074924`
- Latest archived release DOI: `10.5281/zenodo.20112923`

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
- Citation metadata points to the latest archived release DOI.
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
