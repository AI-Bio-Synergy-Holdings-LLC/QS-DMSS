# Beta Readiness Gate

This gate defines what must be true before QS-DMSS moves from
`Development Status :: 3 - Alpha` to `Development Status :: 4 - Beta` on PyPI.

The intended beta claim is narrow:

> QS-DMSS is beta for reproducible package/evidence workflows; it is not
> peer-reviewed scientific validation.

## Current Decision

- Current published release: `v0.1.5` / `0.1.5`
- Current PyPI classifier: `Development Status :: 3 - Alpha`
- Target promotion release: `v0.2.0`
- Target promotion classifier: `Development Status :: 4 - Beta`
- Current Zenodo concept DOI: `10.5281/zenodo.20074924`
- Latest archived release DOI: `10.5281/zenodo.20076871`

Do not publish the beta classifier until this gate is green on `main` and the
release owner explicitly approves the `v0.2.0` promotion.

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

## Required Evidence Before Promotion

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

Once this gate is satisfied, the `v0.2.0` promotion PR should make only the
classifier and release-alignment changes needed for beta:

- Bump `pyproject.toml` and `qs_dmss.__version__` to `0.2.0`.
- Change the PyPI classifier to `Development Status :: 4 - Beta`.
- Update release docs and issue templates from `0.1.5` to `0.2.0`.
- Preserve the public language: beta for reproducible package/evidence
  workflows, not peer-reviewed scientific validation.
- Cut `v0.2.0`, let Zenodo archive it, and publish through Trusted Publishing.

Avoid adding new features in the beta promotion PR. The point of the promotion
is to change the maturity signal only after the release surface is already
proven.
