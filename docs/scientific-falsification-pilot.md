# Scientific falsification pilot v1

This is a bounded numerical challenge, not scientific approval, a release, or a
public challenge launch. The graph backend remains experimental, CPU-only and
local-only. Rectangular Fractal SSFM and the finite graph are different models;
agreement between their outputs is not an acceptance criterion.

## Gate and historical evidence

Issue [#183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183)
is the active human scientific-review gate. Issue #105 is a closed historical
record; its administrative closure is not evidence of scientific approval. The
published v0.13.2 packet, schema, wheel hash and validator remain unchanged.
That packet predates the FFT diagnostic correction and graph admission.

This pilot targets source commit `48d7ab5d10da189caddbcad1dd6622e58d204940`.
The candidate still reports package version 0.13.2 but is **not** the published
v0.13.2 wheel. Source commit, candidate wheel SHA-256, installed-file agreement,
protocol SHA-256, reference-script hashes and environment identify each run.
Do not replace historical energy evidence with corrected results.

## Prospective acceptance contract

[`protocol-v1.json`](../research/falsification/protocol-v1.json) is committed
before executing the pilot. Its first commit is the preregistration record, not
an assertion of external preregistration or independent authorship. Subsequent
changes to cases or tolerances require a new protocol ID and an explicit reason;
do not tune thresholds after seeing results. Implementation corrections and
failed attempts must be retained and disclosed separately.

The parameter grid is fixed in the protocol. It contains 72 FFT cases, 15 graph
cases (level-zero Dirichlet is undefined and excluded), and two evolution cases.
Scaled scalar/matrix errors use `norm(actual-reference) / max(1,norm(reference))`.
Projectors use the Frobenius norm. Trajectory errors use the mass-weighted L2
norm relative to the initial norm, with complex phase retained, at every saved
time. Potential and nonlinear fields are independently assembled.

| Exercise | Reference and acceptance | Deliberately defective control |
| --- | --- | --- |
| FFT energy | Unit-norm analytic plane wave, `E=sum((2*pi*n/L)^2)/(2*m)`. Both CPU FFT backends; non-unit domains, multiple masses and rectangular grids. Energy error <= 5e-12; norm error <= 5e-13. | Omit the cell measure, reproducing the old kinetic diagnostic defect. |
| Graph operator | Address-word construction of small cells, rational cell masses and an edge-incidence quadratic form. Compare coordinates/order, edges, boundary restriction, mass/stiffness, generalized spectra and complete mass-weighted eigenspace projectors. Matrix error <= 5e-13, spectrum <= 1e-11, projector <= 1e-10, tail power <= 1e-11. | Replace cell masses by uniform weights; use the induced-subgraph Laplacian instead of Dirichlet principal restriction. |
| Evolution | Independently assembled generator; matrix exponential for the linear substep and adaptive DOP853 for nonlinear trajectories. Two reference tolerances must agree within 1e-11. Linear error <= 1e-11, finest trajectory error <= 1e-5, norm error <= 1e-11, observed refinement order in [1.7,2.3]. | A phase-perturbed trajectory preserves norm but must fail the trajectory test. |

Refinement is **INCONCLUSIVE**, not passed, when errors are below the 1e-12
resolution floor or within 100 times the reference disagreement. Reference
integration failures are inconclusive; measured threshold violations are
**FAIL**. Non-finite results cannot pass. Passing all required comparisons means
**NOT_FALSIFIED_WITHIN_SCOPE**, not verified physics. Negative controls must be
rejected to demonstrate that the checks can detect their declared defects.

The known legacy FFT error is a seeded control, not a new defect in this candidate.
Record genuine counterexamples and failures without silently fixing production
algorithms in this PR. Human disposition stays `PENDING` until a named reviewer
actually assesses the evidence. AI-assisted authoring is disclosed in every report.

## Reference independence and limitations

The reference module must not import QS-DMSS. It constructs the operator from
the declared finite-model specification, not from exported production matrices.
SciPy's [generalized eigensolver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.eigh.html)
and [DOP853 integration](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
provide alternate numerical routes. NumPy and SciPy can share BLAS/LAPACK and
hardware, so this is not completely independent implementation infrastructure.
Independent assembly does not establish that the shared modeling convention is
physically appropriate. Length^-2 scaling, cell measure, continuum convergence,
domain applicability, and empirical calibration remain unresolved scientific gates.

Wolfram is an optional additional cross-tool reference, not a runtime dependency
or a replacement for human review. If unavailable or unlicensed, record
`NOT_EXECUTED` and the reason. Never convert unavailable execution to a PASS.
Wolfram results, if later added, must use an independently assembled small graph,
not merely import the QS-DMSS operator, and receive their own hashed receipt.

## Execution and evidence

The repository-only pilot runner and reference live under `research/falsification`.
Install the separate research requirements in an isolated candidate environment;
they are not application dependencies. Run from outside the checkout so that the
candidate wheel, not an editable installation, supplies QS-DMSS. The runner checks
installed package bytes against the supplied wheel and refuses a mismatched build.
The source pin and trusted local build receipt bind that wheel to the target commit;
the hash alone is not a cryptographic attestation of its source.

The packet retains per-case measurements, reference matrices/projectors, complex
trajectories, protocol and script copies, command/environment receipts, hashes,
limitations and pending human dispositions. Output directories must be new; no
historical packet is overwritten. CI regression runs exercise the same cases but
are not substitutes for the commit-pinned installed-candidate receipt.

After this pilot is reviewed, a separate proposal may expose challenge packets,
counterexamples and human finding dispositions in the studio and Evidence Assistant.
This PR does not change the UI, hosted compute, AI settings, or release version.

The first installed-candidate [result and retained packet](review-evidence/falsification-pilot-v1.md)
are available for human review. Their bounded outcome does not close issue #183.

A separately preregistered [Wolfram cross-tool supplement](wolfram-falsification-supplement.md)
now provides independently assembled Wolfram references for the same cases.
It preserves the original packet and its historical execution status. Its bounded
agreement adds numerical evidence, not independent human scientific approval.
