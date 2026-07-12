# Fractal/Quadrant SSFM Validation Spine

Status: experimental backend validation spine, not peer-reviewed physical validation.

QS-DMSS now has an opt-in nonlinear wave backend for quadrant-partitioned fuzzy fractal effective potentials. The first implementation is deliberately CPU-testable through `backend: numpy_fractal_ssfm`; `backend: cupy_fractal_ssfm` uses the same solver contract and is reserved for CUDA/CuPy environments.

The existing `backend: numpy` Schrodinger-Poisson reference path remains the default.

This page describes the installable validation gate included in the current
`v0.11.0` package baseline.
Reviewers should run this harness from the published package or an editable
source checkout and leave technical feedback on
[issue #105](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105).
GPU expansion, further release prep, and decision-metric UI for
`spectral_leakage` / `aliasing_ratio` remain paused behind that review gate.

## Governing Model

The backend evolves a 2-D wavefunction embedded in the existing QS-DMSS `grid_shape=[nx, ny, 1]` convention:

```text
i d_t psi = -(1 / 2m) Laplacian(psi) + V_f(x,y) psi + g(x,y)|psi|^2 psi
```

The quadrant-dependent nonlinear coefficient is:

```text
g(x,y) = g_0 * sum_q gamma_q Q_q(x,y) M_f(x,y)
```

where `Q_q` are quadrant masks and `M_f` is a fuzzy fractal occupancy field in `[0, 1]`.

The default geometry is a real-valued fuzzy potential:

```text
V_f(x,y) = V_0 * (1 - M_f(x,y))
```

## Geometry Modes

| Mode | Meaning | Conservation posture |
| --- | --- | --- |
| `fuzzy_potential` | Geometry enters as a real-valued phase potential. | Scientific default; phase-only geometry does not directly remove amplitude. |
| `soft_mask` | Applies `sqrt(M_f)` amplitude projection. | Exploratory and non-conservative. |
| `hard_mask` | Applies binary projection at `M_f >= 0.5`. | Exploratory and non-conservative. |

## Evidence Contract

Fractal SSFM runs use the same QS-DMSS run ledger and evidence bundle path as the existing reference solver:

- `metrics.json`
- `energy.csv`
- `run.json`
- `report.html`
- `manifest.sha256.json`
- `evidence_bundle.zip`
- `artifacts/final_density.npy`
- `artifacts/final_state.npz`

Additional backend diagnostics are nested under `metrics.diagnostics` and may also be surfaced as top-level evidence fields. They are not currently exposed as decision metrics in Campaign Studio.

Diagnostics include:

- `geometry_mode`
- `conservation_mode`
- `nonconservative_reasons`
- `relative_norm_error`
- `spectral_leakage`
- `aliasing_ratio`
- `quadrant_gamma`
- `mask_mean`, `mask_min`, `mask_max`
- `claim_boundary`

## Claim Boundary

This backend is an experimental pseudo-spectral nonlinear wave backend on a rectangular periodic grid. It is not exact fractal-boundary PDE solving, peer-reviewed physical validation, or direct atomic-void modeling.

The defensible public statement is:

> QS-DMSS includes an experimental nonlinear wave backend for quadrant-partitioned fuzzy fractal effective potentials, evidence-bundled and validation-gated.

## Usage

CPU reference smoke:

```bash
qs-dmss run configs/fractal_quadrant_ssfm.yaml
```

Validation harness:

```bash
python -m pip install -e .[dev]
qs-dmss validation fractal-ssfm
```

The harness writes generated configs and evidence-backed runs under
`fractal-ssfm-validation/`, plus two reviewer-facing reports:

- `fractal-ssfm-validation/fractal-ssfm-validation.json`
- `fractal-ssfm-validation/fractal-ssfm-validation.md`

Optional CUDA/CuPy path:

```bash
python -m pip install "qs-dmss[gpu]"
```

Then switch the sample config backend to:

```yaml
engine:
  backend: cupy_fractal_ssfm
```

## Validation Expectations

Before promoting this backend beyond experimental status, QS-DMSS should retain:

- Existing NumPy demo behavior unchanged.
- Parser and JSON schema agreement for `geometry` and `spectral`.
- Clean missing-CuPy failure when `backend: cupy_fractal_ssfm` is selected without CuPy.
- Evidence bundle, manifest, report, verify, and replay compatibility.
- Norm-conservation diagnostics for `geometry.mode: fuzzy_potential` when `spectral.dealias_fraction: null`.
- Explicit non-conservative labels for `soft_mask`, `hard_mask`, and de-alias filtering.
- Dedicated harness output for Strang refinement checks, fuzzy-potential norm conservation, and fuzzy/soft/hard geometry comparison.
