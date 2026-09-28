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

## Observed execution: 2026-09-28 UTC

The plan was committed as `463e87e836188a94a39395aa7ec796ce95709a0c` before
measurements. Wolfram 15.0.1 on Windows x86-64 completed all 89 reference cases.
The comparison returned **NOT_FALSIFIED_WITHIN_SCOPE** for every case, with no
failed or inconclusive cases. These are reference comparisons against the
preserved installed-candidate measurements, not a new execution of the candidate.

| Comparison | Largest observed error | Registered limit |
| --- | ---: | ---: |
| Analytic FFT energy | 5.98e-16 | 5e-12 |
| Graph mass/stiffness | 1.80e-16 | 5e-13 |
| Generalized spectrum | 6.00e-16 | 1e-11 |
| Complete eigenspace projector | 6.26e-15 | 1e-10 |
| Reconstructed candidate tail power | 5.55e-17 | 1e-11 |
| Linear evolution vs MatrixExp | 8.24e-16 | 1e-11 |
| Internal Wolfram precision refinement | 5.99e-13 | 1e-11 |
| Wolfram vs stored SciPy trajectory | 6.38e-13 | 1e-11 |
| Finest candidate trajectory vs Wolfram | 9.42e-8 | 1e-5 |

Observed temporal orders span 2.000058 to 2.001384 (required interval 1.7–2.3).
Reference disagreement remains well below the candidate error, so refinement is
resolved under the original separation rule. Norm conservation is reported
separately and is not used as a substitute for trajectory accuracy.

Topology is compared against the original independently assembled arrays, whose
exact agreement with the candidate topology is recorded in the immutable packet.
Tail power is reconstructed from retained **candidate** complete projectors using
the independently specified initial state; the supplement does not claim to
invoke the production tail method again. The original packet retains that direct
method check and its seeded negative controls.

The [retained supplement](review-evidence/wolfram-falsification-v1.zip) includes
raw Wolfram data, exact executed scripts and inputs, comparison results, execution
logs, and a per-file SHA-256 manifest. Its SHA-256 is
`fbdaa5c21a680f1d0a04be477c852ca1fedaddb2dae0f58be12b9256900e75b7`.
It binds to the original packet hash
`17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4`
and candidate wheel hash
`1c269bb96cec6e262fe19292ee4b290450df14d3b80e4f2924c278caeee5cb2f`.
Hashes establish byte identity, not authorship or scientific correctness.

## Attempt and correction record

1. The original pilot could not execute Wolfram because activation was blocked.
   That historical packet and its `NOT_EXECUTED` record remain unchanged.
2. After user activation, the first reference-script attempt had an unmatched
   bracket. WolframScript printed a syntax error but returned process code zero;
   no result file existed, so this is **not** accepted as successful execution.
   Its log is retained as `prior-attempt-01.log` in the supplement.
3. The bracket was corrected; the second reference attempt produced all cases
   without diagnostic messages. The receipt records 0.5222758 seconds of kernel
   evaluation (excluding process/kernel startup), under the 120-second bound.
4. Comparator fault injection then exposed an overflow trap: `max(finite, NaN)`
   could conceal a failed matrix comparison. Explicit finite checks now preserve
   such cases as FAIL with a strict-JSON nonfinite marker. The Wolfram data were
   not rerun or changed. The final comparison used the same reference bytes.

No case, tolerance, scientific claim, production algorithm, or historical evidence
was changed in response to results. Offline CI tests check packet integrity,
reference/data boundaries, missing/duplicate/malformed cases, finite counterexamples,
overflow, incomplete clusters, inconclusive refinement and non-overwrite behavior.
Those tests replay the retained data; CI does **not** run a licensed Wolfram kernel.
