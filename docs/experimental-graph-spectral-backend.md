# Experimental CPU graph-spectral backend

This is an additive, local-only research backend. `numpy`, `numpy_fractal_ssfm`,
`cupy_fractal_ssfm`, their geometry/spectral configuration, and quantum-sidecar
profiles remain supported without changes. No additional runtime dependency is
required. Execution is available through the CLI or explicit local API config,
not the rectangular Run Setup selector. The public demo cannot execute this backend.

## Run and inspect

Use the published `v0.14.0` package or a separately qualified source build; the
historical v0.13.2 wheel does not contain this backend. It remains experimental,
CPU-only and local-only, not an independently validated scientific model. Issue
#183 remains open. Installing the current package does not reproduce the frozen,
commit-pinned challenge packets; follow their exact source and hash instructions.

```powershell
$graphConfig = python -c "from importlib.resources import files; print(files('qs_dmss.assets').joinpath('configs/sierpinski_graph_spectral.yaml'))"
qs-dmss run $graphConfig --output-root graph-runs
qs-dmss verify graph-runs/<run-id>
qs-dmss replay graph-runs/<run-id> --output-root graph-replays
```

This resolves the installed package's bundled config; it does not assume that a
`configs/` checkout directory exists in the current working directory. Substitute
the generated run ID for `<run-id>` when verifying and replaying.

The config opts into `fractal_graph_spectral` and a `fractal_graph` section. Omitted
`engine.grid_shape` is derived as `[active_vertices, 1, 1]` for compatibility with
existing configuration records only. It does **not** describe rectangular geometry.
Explicit shapes must contain integers (not booleans/floats) and match that count.
The state/density arrays have shape `[active_vertices]`. The evidence report labels
the domain; the manifest includes `artifacts/graph_operator.npz` with stiffness,
mass weights, vertex/edge ordering, boundary IDs, node fields, and spectrum. The
full vertex index space and active index space are distinguished by their names.
The existing run, verify, replay, campaign and report mechanisms are reused.
Rectangular showcase spatial plots and quantum encoding are not graph adapters.
The current Run Setup form forces a NumPy configuration and drops non-rectangular
sections; graph configs are therefore withheld from its catalog on both local and
hosted instances. A future graph-aware form is separate work, not part of admission.

## Numerical conventions and claim boundary

The finite Sierpinski graph uses cell-incidence mass weights and stiffness scaling
`(5/3)^level / box_size^2`. Dirichlet boundary vertices are removed by principal
restriction; Neumann retains them. Domain scaling and embedded-coordinate quadrant
fields are declared modeling conventions, not independently reviewed physical laws.

Evolution uses the symmetric mass-weighted generalized eigenproblem and a complete
CPU eigensystem for the linear propagator. Only that linear substep is exact up to
eigensolver/roundoff error. Potential/nonlinear composition is second-order Strang
splitting with finite timestep error. Norm preservation is not trajectory accuracy,
continuum convergence, physical calibration, or quantum advantage.

Energy uses `graph_mass_stiffness_v1` (not the FFT convention). The spectral-tail
cutoff starts at `floor(tail_fraction * vertex_count)` and moves down to include
the **entire** eigenvalue cluster containing that index. Clusters join adjacent gaps
within `64 * eps * N * spectral_radius`. A fraction of 1 selects no modes. The
effective start, cutoff eigenvalue, and tolerance are saved, making the selected
subspace explicit. Power is invariant to rotations/permutations within that cluster;
individual exported eigenvectors are not canonical research observables.
The operator archive stores full and active integer lattice coordinates. A requested
number of exported mode columns may split a cluster; `exported_eigenmode_count`
and `eigenmode_export_policy` record that limitation. Reconstruct complete spectral
projectors from the saved stiffness and mass for basis-invariant comparisons.

Roundoff-scale eigenvalues are classified as zero; materially negative eigenvalues
raise errors. Multilevel reports separate nullity/absolute nullspace residual from
ordered positive-eigenvalue percentage changes. Indices are not claims of physical
mode correspondence across levels. Stabilization is not a continuum proof.

## Enforced resource policy

- Maximum level 5 (366 full vertices); Dirichlet requires level >= 1.
- Preflight before graph construction and all validation levels, including direct APIs.
- Dense-memory estimate `16 * full_vertices^2 * 8 + 1024 * full_vertices` <= 64 MiB.
  This conservative admission estimate is not an OS-enforced peak-memory guarantee.
- At most 10,000 steps and `2 * active_vertices^2 * steps <= 100,000,000`.
- At most six distinct validation levels, none above the run level; at most 366
  exported/validation modes. Domain scale is bounded to `[1e-6, 1e6]`.
- GPU requests are rejected. No optional CuPy import occurs for graph runs.
- Non-representable evolution/diagnostics and a zero initial mass-weighted norm
  fail explicitly before state, report, manifest or evidence-bundle persistence.
  A failed execution may retain its job record/config for troubleshooting.

These are per-run limits, not a concurrency scheduler. Larger models require a
separate sparse/operator design and measured memory/runtime review.

## Provenance and remaining gates

Adapted from the user-supplied graph patch, SHA-256
`d6cd497def8383374e0e35f784176f8156f90702901ddceb02714282de72c6d0`.
Only the graph algorithms were ported; its stale packaging, deleted backends, GPU
path, replacement tests and broad exactness claims were not adopted. New tests are
separate from the existing fractal validation suite.

The FFT energy correction is a separate preceding change; historical evidence must
not be overwritten. See [diagnostic migration](fft-energy-diagnostic-correction.md).
Independent human scientific review, length-scaling interpretation, continuum
convergence and scientific promotion remain separate gates. Inclusion in the
published package does not enable hosted execution or establish scientific approval.

### Admission checklist (not scientific approval)

- JSON Schema and parser must agree at every level, boundary, shape and step-work
  limit, including omitted default fields. Both shipped schemas are synchronized.
- Keep the supported Python matrix, security/dependency review, packaging, Docker,
  legacy solver/quantum tests and human engineering review green before merge.
- The cross-platform installed-wheel smoke executes, verifies and replays the
  packaged graph config outside the checkout, checks its operator archive, and
  confirms selector omission and hosted replay rejection. Publication does not
  enable the hosted backend or turn these checks into scientific validation.
- Independent human scientific review must assess the finite-cell measure,
  boundary restriction, length scaling, quadrant fields, temporal refinement,
  multilevel interpretation and domain applicability before scientific promotion.
- Source-bundle provenance is recorded above; the owner must confirm the supplied
  code's provenance/licensing before admission. No independent legal assessment
  is implied by the engineering tests.
- Concurrent-run scheduling, sparse solvers, larger graphs, spatial UI adapters
  and any quantum mapping require separate designs. None is admitted by this PR.
