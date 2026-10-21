# CERN dimuon helper review and environment-lock preparation

Date: 2026-10-20. Baseline: `c158c3ba3f81cadf7d11bdfcab3441c8d99be851`
plus the existing uncommitted source-only qualification helpers. No merge,
deployment or release is included. This is AI-assisted engineering review,
not owner approval or independent human scientific assessment.

**Disposition: helper admission HOLD.** Environment locking completed, but
two independently reproducible early-stop retention defects remain. The
approved core wheel is unchanged; neither finding establishes a numerical
defect in that wheel or a conclusion about actual CERN data.

## Findings requiring a separate correction pass

### HR-001 — counterexample limit drops earlier exclusions (P1)

In `research/cern_dimuon_qualification/comparison.py`, the return at the
33-counterexample limit (lines 146–155 in this reviewed snapshot) omits the
`exclusions` accumulated before the limit. A purely synthetic 34-row probe
containing one eta-excluded row followed by 33 selected rows with injected
candidate-mass disagreements returns HOLD with 33 counterexamples but no
exclusion collection. The earlier exclusion is therefore absent from the
returned partial evidence even though it was already calculated.

Required correction: retain both collections, the triggering record, processed
row count and an explicit incomplete outcome on every detail-limit return.
Do not increase the 33-record guards or any byte allowance. Add mixed-stream
regressions, not only an all-selected counterexample-limit test.

### HR-002 — exclusion limit skips the triggering disagreement (P1)

The 33-exclusion return (lines 120–129) occurs before the current row's
`reasons` are appended to `failures`. A purely synthetic 33-row excluded input,
with an injected first-failure disagreement on row 33, returns all 33
exclusions but zero counterexamples. The triggering disagreement is omitted.

Required correction: preserve the current row's disagreement before stopping,
and retain all earlier exclusions/counterexamples. If a bounded result cannot
retain them, refuse safely with the bounded trigger and incomplete state;
never silently discard it or loosen criteria. Add a combined trigger-limit
regression. No implementation correction was made during this review.

Both probes reproduced under the earlier isolated Python 3.14 environment and
both newly locked native CPython 3.12.15 environments. Their original synthetic
inputs, injected views and returned partial outputs are retained in the
review workspace. Expected review findings are not disguised as passing
scientific tests. The existing synthetic preflight remains a valid record of
its narrower controls, not proof that these cases passed.

## Reviewed boundaries

All eight Python helper modules and the protocol were read and their exact
identities recorded in `environments/v1/verification.json`. Review covered
closed-format parsing, independent Decimal/scalar reference arithmetic,
array/source correspondence, fixed tolerances and boundary-HOLD behavior,
wheel/Git identity, exclusive writes, byte accounting, padded failure receipts,
supervised fixed synthetic workers and the absence of a pilot entry point.

Existing protections remain useful: the reference imports no QS-DMSS or NumPy;
the candidate does not relabel CMS bytes synthetic; source-byte disagreements
are refused; scientific fields are checked; failure roots are not retried or
deleted; and negative timeout/overflow/drift controls have retained receipts.
None of these protections excuses the two partial-result losses.

The current preflight does not consume the new lock manifest and correctly
continues to report pilot readiness false. Any future measurement runner must
verify/retain actual environment identity against the frozen manifests before
opening the dataset. No such runner was implemented here. Trusted local
storage is still required; these helpers are not hostile-process/RSS isolation.

## Environment locks and executed checks

The [data-only lock pack](../../research/cern_dimuon_qualification/environments/v1/README.md)
pins CPython **3.12.15** on Windows x86-64 and Linux x86-64, and NumPy
**2.5.4** on both. Every dependency is version- and wheel-hash-pinned; common
versions match exactly. Windows has 24 installed packages, Linux 23; only
Windows-specific `colorama` differs. The approved QS-DMSS hash is part of both
locks, so an ordinary published 0.14.0 wheel cannot be substituted.

- Offline native installs, dependency closure and `pip check`: passed.
- All 103 installed QS-DMSS package files matched the approved wheel on both
  platforms. The same approved wheel hash remains unchanged.
- Windows synthetic regressions: **162 passed, 2 permission-related skips**.
- Linux synthetic regressions: **164 passed**. One non-failing pytest cache
  warning came from the deliberately read-only source mount, not a test error.
- Both frozen package sets: **zero known vulnerabilities** in the observed
  strict dependency audits. This is not an OS-image vulnerability audit or a
  claim that unrelated existing environments are vulnerability-free.
- Ruff check/format and medium-or-higher Bandit: passed.
- Both targeted synthetic retention probes: confirmed the findings above.

The NumPy wheels and compiler/BLAS builds are necessarily platform-specific;
their observed configurations are retained. Identical NumPy versions do not
replace cross-platform numerical reconciliation.

The source-distribution manifest gained only a source-only `.txt`/`.md`
inclusion for the lock pack; its previous local changes are preserved.
The helpers, protocol bytes, approved/original wheels, earlier receipts,
frozen evidence and scientific statuses were not changed. No actual CERN
snapshot was opened, mounted in Linux, imported or analyzed.

## Next gate

Seek approval for one focused correction of HR-001/HR-002 with mixed-limit
regressions and bounded evidence accounting, then re-review the resulting
helper identities alongside the locked environments. This review does not
authorize that correction or the pilot. Numerical qualification remains
`NOT_EXECUTED`; scientific validation `NOT_ESTABLISHED`; independent scientific
review and human disposition `PENDING`. No deployment or publication occurred.
