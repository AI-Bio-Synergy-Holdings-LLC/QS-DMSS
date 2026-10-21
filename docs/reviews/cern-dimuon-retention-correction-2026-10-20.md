# HR-001/HR-002 focused correction and re-review

Date: 2026-10-20. Baseline: `c158c3b` plus the existing source-only
qualification work. Scope: early-stop evidence retention, regression tests
and AI-assisted engineering re-review. No pilot, merge, deployment or release
is included; no independent scientific or owner approval is implied.

**Engineering disposition: HR-001 and HR-002 corrected and verified; no
additional findings in the reviewed scope.** Owner review of the corrected
helper identities and separate execution authorization remain outstanding.
Numerical qualification remains `NOT_EXECUTED`; pilot readiness remains false.

## Exact correction

Only `comparison.py` and its existing helper regression-test file changed.
Both collections for the current row are now assembled before checking the
unchanged 33-exclusion / 33-counterexample guards. Either partial HOLD return
contains exclusions, counterexamples, the triggering record, processed-row
count and `complete: false`.

- HR-001: reaching the counterexample guard no longer omits earlier exclusions.
- HR-002: reaching the exclusion guard no longer skips the current row's
  disagreement. Earlier disagreements remain retained as well.
- When both guards are reached on the same row, both collections are retained
  and the existing exclusion-limit reason takes precedence.
- Evaluation still stops at the first triggering row. Neither collection
  exceeds 33 entries; the 4 KiB counterexample-record guard is unchanged.

Numerical calculations, tolerances, selection/bin decisions, complete-result
aggregation, the protocol and every allocation ceiling are unchanged. The
source-only helper is not part of either wheel; no wheel was rebuilt.

## Regression and re-review evidence

Before the correction, the new 14-case early-stop matrix produced **12
failures and two passing controls** against the preserved old helper. That
red result is retained rather than replaced by the later passing result.

Sixteen new parameterized tests cover minimal/maximum-length cells, earlier
exclusions, triggering disagreements, earlier plus triggering disagreements,
simultaneous guards, interleaved streams, either guard occurring first, and
unchanged below-limit complete-result behavior. They check exact retained row
identities, input-view immutability, stopping position, scientific fields,
record-byte limits and persistence through the closed byte ledger.

Locked native CPython **3.12.15**, NumPy **2.5.4** results:

- Windows: **178 passed, two symlink-permission skips**.
- Linux: **180 passed**, no warnings. The pinned Docker environment ran offline
  with no CERN dataset mounted; only selected helper/test inputs were mounted.
- Original HR-001/HR-002 probes: both missing-record findings absent on both
  platforms; the original pre-correction probe receipts remain unchanged.
- All 103 installed QS-DMSS package files still matched the approved wheel on
  both platforms. Runtime/package versions matched the frozen locks exactly.
- Ruff check/format, medium-or-higher Bandit and whitespace checks passed.

Re-review also compared old/new complete results for **64 original synthetic
below-limit cases**; every result matched exactly. Fourteen retained partial
results checked the corrected boundaries. The largest serialized partial
result was **107,550 bytes**, below the unchanged **524,288-byte** comparison
bucket. A closed original-synthetic retention root, including its input,
reserved log/receipt slots and self-counted integrity ledger, occupied
**380,740 bytes**. No limit was increased or record silently dropped.

The original sources are retained in `source-before.zip`; red/green test
reports, original/fixed probes, source snapshots, all 14 synthetic input/output
pairs and the closed maximum-detail ledger are retained under
`.local/cern-dimuon-retention-correction-20261020/`. Those newly generated
fixtures are explicitly original synthetic engineering tests, not recovered
historical evidence or CERN experiment results.

## Preservation and status boundaries

The [original review](cern-dimuon-helper-review-2026-10-20.md), its HOLD
dispositions, frozen `environments/v1/verification.json`, both preflight roots
and earlier evidence remain byte-identical. The later additive
`environments/v1/retention-rereview-20261020.json` records the corrected helper
identities and links the historical review without rewriting it.

Both original and approved wheels, the protocol/criteria, dependency locks,
production code, scientific registry, historical numerical statuses and frozen
scientific packets are unchanged. No actual CERN snapshot was opened or
analyzed. Scientific validation remains `NOT_ESTABLISHED`; independent review
and human scientific disposition remain `PENDING`; AI advice remains null.

No new pilot entry point or automatic environment-lock enforcement was added.
Any future authorized measurement must verify and retain its actual native
environment against the existing locks before opening the dataset. This
bounded engineering correction does not promote scientific claims or authorize
execution, deployment, publication or outreach.
