# Wolfram cross-tool supplement v1

This assessment supplements, and does not replace, the
[original pilot packet](review-evidence/falsification-pilot-v1.md). The original
packet correctly records that Wolfram was unavailable at its execution time.
The user subsequently activated the local kernel, which reported Wolfram 15.0.1.

The [execution plan](../research/falsification/wolfram-plan-v1.json) is committed
before Wolfram numerical measurements. It adds no new scientific acceptance
thresholds: the 72 FFT cases, 15 small-graph cases and two evolution cases retain
the original protocol's bounds and source pin. Comparing stored candidate data
against a separately generated reference is intentional; Wolfram receives the
protocol and execution plan, **not** production operators or trajectories.

The Wolfram reference constructs the cell complex by recursively translating
three copies of the preceding complex; rational cell weights and a degree-minus-
adjacency matrix supply the declared mass and stiffness. This differs from the
production midpoint subdivision and the Python reference's address-word assembly.
It still implements the same declared modeling convention, not an independently
established physical law.

[Eigensystem](https://reference.wolfram.com/language/ref/Eigensystem.html) supplies
the generalized spectrum at 60-digit working precision. Complete mass-weighted
eigenspace projectors are compared, not individual eigenvectors. Linear evolution
uses [MatrixExp](https://reference.wolfram.com/language/ref/MatrixExp.html).
Nonlinear evolution uses [NDSolveValue](https://reference.wolfram.com/language/ref/NDSolveValue.html)
on explicit real/imaginary components at 40 and 60 digits, with accuracy/precision
goals 20 and 30 and maximum step T/64. Reference precision-refinement and agreement
with the stored SciPy reference must each meet the original 1e-11 bound.
High-precision internal refinement error is measured before export; JSON arrays
are exported as machine numbers for comparison with the candidate float64 data.

The script is restricted to the fixed small cases, 120 seconds and 512 MiB of
additional evaluation memory. Missing or malformed rows and tool failures are
inconclusive, not passes. Any actual disagreement must be retained. Runtime or
script corrections are documented without changing thresholds or hiding attempts.

This is cross-tool corroboration by the same AI-assisted authoring workflow.
It is not independent human scientific review, proof of universal correctness,
continuum convergence or physical calibration. Scientific status remains
NOT_ESTABLISHED and human disposition PENDING under issue #183. No application,
release, hosted execution, AI or public-challenge UI change is implied.
