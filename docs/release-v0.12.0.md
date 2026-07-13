# QS-DMSS v0.12.0 Release Notes

QS-DMSS v0.12.0 is the simulator-first quantum-readiness milestone. It turns
the experimental Fractal SSFM circuit lane into a reviewable evidence workflow
without adding a quantum-provider integration or changing the classical solver
authority.

## Highlights

- Adds a bounded `4 x 4` Fractal SSFM quantum-readiness sidecar that compares
  one linear, phase-only fuzzy-potential Strang step with the NumPy reference.
- Adds a provider-neutral QPU request bundle with circuit artifacts, topology
  and basis declarations, state-preparation/routing costs, checksums, and an
  explicit non-submission policy.
- Adds a 12-row compilation validation matrix over generic linear, ring, and
  fully connected five-qubit targets at optimization levels `0` through `3`.
- Separates reference-exact and bounded-approximation semantic classes and
  reports depth, CX count, routing overhead, component attribution, and Pareto
  representatives.
- Adds the accepted Commercial Sustainability and Licensing Boundary decision
  while preserving the Apache-2.0 public core and distributions.

## Install And Run

Install the published package with the optional local quantum simulator stack:

```powershell
python -m pip install --upgrade "qs-dmss[quantum]==0.12.0"
```

Generate the three review artifacts:

```powershell
qs-dmss quantum validate-fractal --output-root quantum-sidecar-validation
qs-dmss quantum prepare-qpu-request --output-root qpu-request-bundle
qs-dmss quantum validate-compilation --output-root quantum-compilation-validation
```

Each path emits structured JSON, a human-readable review surface, checksums,
and a ZIP evidence object. The compilation harness also emits a CSV matrix and
per-target OpenQASM/QPY artifacts.

## Execution And Spending Boundary

This release has:

- no provider integration or provider submission;
- no provider credentials or credential lookup;
- no remote quantum API calls;
- no QPU execution or job polling;
- no physical-device calibration claim;
- zero authorized spend (`$0.00`).

The QPU request is a local, provider-neutral review bundle. `submitted` is
`false`, `never_submit` is `true`, and the compilation harness uses only local
ideal simulators and generic target models.

## Scientific Claim Boundary

QS-DMSS remains beta for reproducible package/evidence workflows. The quantum
artifacts validate a small circuit encoding and logical-to-target compilation
semantics within declared tolerances. They do not demonstrate quantum
advantage, hardware fidelity, calibrated-noise performance, nonlinear
Schrodinger-Poisson feedback on a QPU, production-scale quantum simulation, or
peer-reviewed scientific validation of the Fractal SSFM model.

The classical NumPy Fractal SSFM implementation remains the reference
authority. Scientific review of the underlying solver lane remains routed
through issue #105.

## License And Maturity

- Package license: `Apache-2.0`
- PyPI classifier: `Development Status :: 4 - Beta`
- Public-core and hosted-service rights remain separated by the accepted
  Commercial Sustainability and Licensing Boundary decision.

No research-only, noncommercial, provider-restricted, or proprietary terms are
added to the public package.

## Release Gate

Before tagging `v0.12.0`:

```powershell
python -m pytest -q
node --check src/qs_dmss/cockpit/static/app.js
python -m build --sdist --wheel
python -m twine check dist/*
```

Also install the generated wheel and source distribution into separate clean
environments with the `quantum` extra and run all three commands above. Confirm
that every evidence object verifies and records no credentials, no remote API,
no submission, no QPU use, and `$0.00` authorized spend.

After publication, run the cross-platform Fresh Install Smoke workflow against
PyPI `0.12.0` and the `v0.12.0` GitHub release wheel.

## Release Preparation Validation

Validated locally on 2026-07-12 with Python 3.13, Qiskit 2.5.0, and Qiskit Aer
0.17.2:

- full repository suite: `107 passed`;
- wheel and source distribution built successfully;
- both artifacts passed `twine check`;
- both artifacts preserved `Apache-2.0`, the Beta classifier, `NOTICE`, the
  packaged quantum profile, this release record, and the licensing decision;
- wheel and source distribution were installed into separate clean virtual
  environments with the declared `quantum` extra;
- all three packaged quantum commands passed from each environment;
- both compilation reports contained the expected 12-row matrix;
- every policy assertion confirmed no credentials, remote API, submission, QPU
  use, or authorized spend.

This validation record does not publish, tag, upload, or execute the release on
a quantum provider.

## Citation Status

- Project DOI: `10.5281/zenodo.20074924`
- Latest archived release at release preparation: `v0.11.0` /
  `10.5281/zenodo.21319023`

After Zenodo archives `v0.12.0`, update `CITATION.cff`, `README.md`,
`codemeta.json`, citation docs, and the GitHub release notes with the newly
minted version DOI. Do not delay package validation while waiting for that
metadata-only follow-up.
