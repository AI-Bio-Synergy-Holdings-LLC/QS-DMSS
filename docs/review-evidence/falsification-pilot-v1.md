# Falsification pilot v1: retained candidate evidence

**Outcome: NOT_FALSIFIED_WITHIN_SCOPE. Scientific validation: NOT_ESTABLISHED.**

The [89-case evidence packet](falsification-pilot-v1.zip) contains per-case results,
raw matrices/projectors/complex trajectories, negative controls, environment and
command receipts, and the exact protocol/reference/runner files. Its SHA-256 is
`17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4`.
It is a data/reference archive, not a published QS-DMSS release.

| Identity | Value |
| --- | --- |
| Target source | `48d7ab5d10da189caddbcad1dd6622e58d204940` |
| Protocol committed before measurements | `5fe19ed857a253caa0cb91ffc1a4d18904cc07e3` |
| Runner implementation commit | `1422891` |
| Candidate wheel SHA-256 | `1c269bb96cec6e262fe19292ee4b290450df14d3b80e4f2924c278caeee5cb2f` |
| Execution | Fresh isolated installed-wheel environment, Windows, Python 3.14.3, NumPy 2.5.1, SciPy 1.18.0 |
| Diagnostic conventions | `fft_cell_measure_v2`, `graph_mass_stiffness_v1`, `whole_eigenvalue_cluster_v1` |
| Human scientific disposition | PENDING; no reviewer approval asserted |
| AI assistance | Codex-assisted protocol, reference, runner and report; maintainer-origin evidence |

The source archive and candidate wheel are retained in the local assessment
artifacts. The packet contains their hashes and the build receipt, not the wheel.
External reviewers can rebuild the pinned source and bind their own wheel hash;
bit-identical wheel reconstruction is not claimed. The runner verifies installed
package bytes against the supplied wheel before computing measurements.

## Observed numerical bounds

| Exercise | Observed result | Preregistered bound |
| --- | --- | --- |
| 72 analytic FFT cases | Maximum scaled energy error `5.976e-16`; norm error `4.441e-16` | `5e-12`; `5e-13` |
| 15 independently assembled graph cases | Matrix error `1.799e-16`; spectrum error `5.311e-16` | `5e-13`; `1e-11` |
| Complete eigenspace projectors / tail power | Maximum errors `6.026e-15` / `5.551e-17` | `1e-10` / `1e-11` |
| Dirichlet evolution | Finest trajectory error `9.411e-8`; observed orders `2.0014, 2.0003, 2.0001` | `1e-5`; `[1.7,2.3]` |
| Neumann evolution | Finest trajectory error `9.234e-8`; observed orders `2.0009, 2.0002, 2.0001` | `1e-5`; `[1.7,2.3]` |
| Reference refinement agreement | Maximum `2.935e-12` | `1e-11` |
| Linear propagation / norm drift | Maximum errors `9.777e-16` / `3.376e-14` | `1e-11` / `1e-11` |

All seeded negative controls were rejected where applicable. The phase-perturbed
control retained norm while producing about `0.09996` trajectory error, illustrating
why norm preservation does not establish trajectory accuracy. No candidate
counterexample was found in these fixed cases; this is not an exhaustive search.

## Attempts, omissions and required human decisions

The protocol and thresholds were not changed after measurements. Development
regressions preceded the installed-wheel exercise and used the same cases.
The first Python 3.12.14 / SciPy 1.18.1 candidate attempt stalled during a native
SciPy import before computation; no numerical result was produced. The successful
retry changed the environment, not the wheel, cases or acceptance criteria.
See the [attempt record](../../research/falsification/README.md#attempt-record).

WolframScript reported an activation/license problem. **No Wolfram result was
obtained**, and cross-tool Wolfram assessment remains NOT_EXECUTED. Neither the
license restriction nor the Python import problem is evidence about model validity.

Issue [#183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183)
remains the active gate. Human review must assess model applicability, cell measure,
length scaling, boundary conventions, continuum convergence and physical calibration.
The FFT and graph models remain distinct. The published v0.13.2 review packet is
unchanged. No release, hosted execution, AI enablement or public challenge UI is
authorized by these results.
