# Fractal SSFM Independent Review Target — v0.13.2

Status: **maintainer baseline complete; independent technical review pending**.

This document pins the current public review target for the experimental
`numpy_fractal_ssfm` backend. It accompanies the machine-readable
[`review-evidence/fractal-ssfm-v0.13.2.json`](review-evidence/fractal-ssfm-v0.13.2.json)
snapshot and the public discussion in
[issue #105](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105).

The maintainer-run baseline below demonstrates that the published command is
reproducible on one clean environment. It is not independent review,
peer-reviewed physical validation, exact fractal-boundary PDE validation, or
evidence for direct atomic-void modeling.

## Pinned Release Identity

- Version: `0.13.2`
- Git tag: `v0.13.2`
- Source commit: `7a063eb91af6c50e483c2d062bf6cee0daf709e4`
- Wheel SHA-256:
  `6f22876fa625681aa72b96d99e14de92cfd5cfae870fc53d9d41673ebf82416f`
- Wheel:
  <https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/download/v0.13.2/qs_dmss-0.13.2-py3-none-any.whl>

## Clean-Environment Reproduction

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/download/v0.13.2/qs_dmss-0.13.2-py3-none-any.whl
qs-dmss validation fractal-ssfm --output-root fractal-ssfm-validation
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/download/v0.13.2/qs_dmss-0.13.2-py3-none-any.whl
qs-dmss validation fractal-ssfm --output-root fractal-ssfm-validation
```

Reviewers should inspect both generated reports:

- `fractal-ssfm-validation/fractal-ssfm-validation.json`
- `fractal-ssfm-validation/fractal-ssfm-validation.md`

## Maintainer Baseline

The exact release wheel was run on 2026-07-17 using Python 3.12.13, NumPy
2.5.1, Windows 11, and AMD64 hardware.

| Signal | Observed result |
| --- | --- |
| Overall harness status | PASS |
| Estimated Strang order | `2.005689879706288` |
| Coarse-to-medium relative L2 error | `2.3381067931267736e-05` |
| Medium-to-fine relative L2 error | `5.822259094138076e-06` |
| Fuzzy-potential relative norm error | `0.0` at tolerance `1e-9` |
| Fuzzy-potential posture | `phase_only_fuzzy_potential` |
| Soft-mask posture | `nonconservative_exploratory` |
| Hard-mask posture | `nonconservative_exploratory` |
| `spectral_leakage` / `aliasing_ratio` | Diagnostics-only; excluded from decision ranking |

The second-order estimate is a self-convergence signal, not comparison with an
analytic solution, independently implemented solver, or empirical physical
reference. The norm result is a bounded software observation for this fixed
configuration, not a general conservation proof.

## Focused Review Questions

A reviewer need answer only one question, but should state the basis for the
answer and identify any blocking follow-up.

1. Is the self-convergence design and observed second-order estimate a
   sufficient first numerical gate? What analytic or external reference should
   be required next?
2. Is the fuzzy-potential norm-conservation test and `1e-9` tolerance
   defensible for this split-step formulation?
3. Do the soft-mask and hard-mask labels clearly prevent amplitude projection
   from being mistaken for conservative evolution?
4. Should `spectral_leakage` and `aliasing_ratio` remain diagnostics-only? What
   definitions and acceptance envelopes would be required before decision use?
5. Does the public claim boundary adequately distinguish software validation
   from physical-model validation?

## Gate Closure

The gate remains open until:

- at least one person independent of the maintainer leaves a substantive public
  technical review on issue #105;
- every finding is classified as accepted, actioned, deferred with rationale,
  or rejected with rationale;
- blocking numerical or claim-boundary findings are resolved before promoting
  the backend beyond experimental status; and
- `spectral_leakage` and `aliasing_ratio` remain outside decision ranking until
  their semantics and thresholds have been independently reviewed and tested.

Security or reliability patches may proceed while this gate is open. New
feature-release preparation should wait for a recorded gate disposition.
