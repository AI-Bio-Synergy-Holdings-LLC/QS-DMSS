# CERN numerical reconciliation — approved protocol, preflight-only implementation

The owner approved protocol `CERN-DIMUON-NR-001` revision 1, its criteria and
26 MiB evidence-root budget on 2026-10-20. Implementation and **synthetic
preflight only** are authorized. The actual CERN comparison remains
`NOT_EXECUTED`; there is no pilot execution command or dataset input option.
Approval of this implementation must not be inferred from protocol approval.

The machine-readable contract is
[`protocol-v1.json`](../research/cern_dimuon_qualification/protocol-v1.json).
Its canonical semantic hash is checked before controls; raw retained-byte
hashes are recorded separately so LF/CRLF presentation is not confused with
changed criteria. This is integrity checking, not a signature.

## Fixed scope and independence

- Candidate source: `c158c3ba3f81cadf7d11bdfcab3441c8d99be851`.
- Qualified unpublished wheel SHA-256:
  `6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60`
  (owner-approved artifact-pin correction described below).
- Future source CSV SHA-256:
  `95bf87f7c14758b445d9cb76bc0111affc1ce70831453dde34f687310685e59f`;
  2,639,302 bytes from CERN record 5203. Preflight does not read this CSV.
- One profile: 60 unweighted bins, strict `2 < mass < 5 GeV`, both `pt >= 0`,
  unchanged source cuts and float64 roundoff policy.
- Prior knowledge is disclosed: 20,000 input rows, 19,997 selected, one eta-cut
  and two mass-window exclusions. Those observations are not a blinded result
  or an instruction to force agreement.

`reference.py` uses its own parser, scalar binary64 arithmetic, Decimal
80-/120-digit arithmetic from original tokens, and independent counting. It
imports neither QS-DMSS nor NumPy. Decimal arithmetic explicitly uses
`ROUND_HALF_EVEN`; ambient caller precision/rounding cannot select the criteria.

`candidate.py` is a separate adapter using the unchanged candidate. It checks
array-to-source-row correspondence and analyzes diagnostic row views of the
already admitted snapshot, reconciling those views to the full result. These
views are **not independently admitted CMS datasets** and are not relabelled
synthetic. Unexpected admission exclusions cause HOLD rather than inferred row
identities; invalid admission behavior is exercised separately with original
synthetic controls. Wheel identity checks compare raw module bytes, including
the core CLI, against both the imported implementation and pinned Git objects.

The independent implementation is AI-assisted maintainer work, not an
independent human scientific review. No external reviewer or approval is
implied. Owner review remains a separate gate.

## Fixed acceptance criteria

- Identity, row accounting, first-failure decisions, selection and counts must
  agree exactly. No tolerance-based reclassification.
- Histogram endpoints must be exact and edges strictly increasing; interior
  edges must be within one binary64 ULP of independently derived rational
  edges. Independent counting uses the retained edges only after that check.
  Differences at ideal rational edges are also flagged, not hidden.
- Selected squared masses must differ from the Decimal reference by no more
  than `64 * 2**(-52) * max(E_sum**2 + p_sum_squared, 1 GeV**2)`.
- Summary differences must not exceed `1e-10 GeV + 1e-12 * abs(reference)`
  against both scalar binary64 and Decimal120 summaries.
- Decimal80/120 values must agree to 50 significant digits with identical
  decisions. Precision or bin/selection-boundary disagreements produce HOLD.
- No precision escalation, tolerance retuning, source replacement or selective
  automatic retry. These are engineering criteria, not detector uncertainties
  or rigorous forward-error guarantees.

Helpers retain source-order intermediate digests, summaries, exclusion tokens
and counterexamples, not a complete per-row intermediate dump. At 33 detailed
counterexamples or exclusions, comparison stops with HOLD, retains the trigger
and marks results incomplete. This conservative guard does not increase the
approved byte limits or allow silently omitted findings.

## Retention and supervision

| Evidence-root allocation | Ceiling |
| --- | ---: |
| Shared CSV / wheel | 4 / 1 MiB |
| Windows / Linux production output | 10 / 10 MiB |
| Helper, protocol and environment records | 256 KiB |
| Comparison records and reports | 512 KiB |
| Logs and failure receipts | 192 KiB |
| Integrity accounting | 64 KiB |
| Total | **26 MiB** |

Production's 4.5 MiB ZIP, 10 MiB output and other existing per-run ceilings
remain unchanged. The new aggregate allowance does not amend historical
semantic-checker budgets. No aggregate archive or upload is produced.

Before any controls, the store allocates all 192 KiB of logs/receipts: five
pairs of 8 KiB start/final slots, four 24 KiB log slots and a 16 KiB emergency
slot. Padding counts as retained bytes. STARTED receipts are never overwritten;
only their separately reserved active final slots are updated. New files use
exclusive creation. Partial, staging and transport copies count against their
bucket and total; links/reparse points, hard links, traversal and unallocated
files are refused. The final inventory includes its own size but not its own
hash, avoiding a self-referential digest.

Four fixed synthetic workers test normal comparison, a supervised timeout,
log overflow and drift of a disposable fixture copy. They run serially with
a maximum 300-second timeout (the negative timeout control uses one second).
An overflow records the observed triggering byte and incomplete-output flag,
terminates the worker and never claims complete capture. There is no general
command runner, OS/RSS sandbox, hostile-process isolation or automatic retry.
Workers are reviewed no-child controls; teardown has a bounded grace period.

Interpreter/dependency installations and caches are outside the file-byte
evidence-root allowance, not silently counted as evidence; interpreter and
dependency locations are recorded. Logical file bytes, not filesystem block
overhead, are counted. Trusted local storage is required. Storage/power failure
can prevent finalization; reserved start/partial records are retained where
possible. Never delete a failed root to retry.

## Authorized preflight

From this source checkout, with the existing candidate available:

```console
python -B -m research.cern_dimuon_qualification.preflight --output NEW_LOCAL_DIRECTORY --candidate-wheel QUALIFIED_WHEEL_PATH
```

This copies/hash-checks helpers and the wheel and executes only built-in
synthetic controls. It does not open CERN data, generate Windows/Linux CERN
outputs, download datasets, invoke graph/quantum/AI code, modify production or
start/deploy any service. Omitting the wheel leaves identity `NOT_CHECKED`;
synthetic control success does not satisfy that gate. The CLI rejects
`--input`, `--execute` and `--pilot`.

`PREFLIGHT_PASSED` describes only these controls. `qualification_outcome` stays
`NOT_EXECUTED`, `pilot_execution_ready` stays false, scientific status stays
`NOT_ESTABLISHED`, and independent review/human disposition stay `PENDING`.
The current host has CPython 3.14, so its synthetic preflight is supplementary,
not the approved two-platform CPython 3.12 measurement.

### Retained preflight finding — 2026-10-20

The first retained preflight stopped **before workers or numerical controls**
at the literal-path guard: an imported editable-package path traversed a
Windows junction. Its initial/final receipts and source snapshot remain under
the ignored `.local/cern-dimuon-qualification-preflight-20261020/` root. This
failed attempt is not rewritten after helper corrections.

Trusted imported-code introspection now resolves its own module location,
as production's existing implementation-identity check does. Caller-controlled
wheel, input and output paths are not given that exception.

Separate read-only byte inspection found that the qualified wheel's
`qs_dmss/cli.py` (985 CRLF sequences) and `qs_dmss/__init__.py` (5 CRLF
sequences) match the current imported files but not the LF-only pinned Git
blobs. The inspected external-data modules match Git exactly. This is an
artifact/source-byte identity limitation, not an observed numerical defect.
The helper intentionally refuses raw-byte disagreement; no newline conversion,
replacement wheel, declared hash change or second retained preflight was
performed. Synthetic regression tests cover this exact LF/CRLF refusal.

**Artifact-identity gate remains HOLD.** A separate owner decision is needed
between a newly qualified commit-built candidate with a new identity, or an
explicit protocol amendment admitting a documented checkout-byte mapping with
both raw identities retained. Neither is authorized by this implementation pass.
Synthetic helper-test success does not clear this gate or execute the pilot.

## Local implementation qualification — 2026-10-20

Final Windows/CPython 3.14.3 regression qualification: **1,060 passed,
27 skipped, 91.71% core-package coverage**. This coverage measures `qs_dmss`,
not the source-only research helpers. The focused new-helper plus existing
dimuon suite passed **153 tests with two privilege-dependent skips**; the
new-helper subset has **51 passed and one skipped**. Synthetic controls include
mass/cut/bin boundaries, Decimal context independence, fixed thresholds,
protocol drift, exact wheel/Git byte refusal, row mapping, byte-ledger closure,
partial storage failure, source drift, timeout and log overflow. Ruff and the
medium-or-higher Bandit scan passed.

Read-only accounting of the retained failed attempt found **247,027 bytes in
27 files**, including all 192 KiB of reserved log/receipt slots. Its input,
wheel and Windows/Linux output buckets are empty. No second retained preflight
was run. The failed snapshot is preserved; later synthetic unit tests used
separate temporary test roots and do not replace that attempt.

Production `src/`, portal/media, published metadata, scientific registry,
protocol and both frozen evidence ZIPs were verified unchanged. No production
wheel was rebuilt, and no commit, push, PR, deployment, release or outreach was
performed. Changes are limited to research helpers, their tests and guidance,
plus a source-distribution manifest entry so the helper tests retain their
source dependencies. These helpers do not enter the installed wheel.

Future execution still requires separately authorized measurement, owner
review of the helper identities, frozen CPython 3.12 Windows/Linux dependency
manifests with identical NumPy versions, and the complete acceptance checklist.
Frozen graph/FFT packets, historical numerical statuses, media and #183 remain
unchanged. No new release, UI, hosted execution or scientific promotion follows
from this work. CERN's educational sample is not a full physics-analysis dataset.

## Owner-approved candidate-pin correction — 2026-10-20

The preceding findings and qualification counts describe the earlier retained
attempts; they are historical records, not results of the corrected preflight.
The owner separately approved the new wheel identity and authorized only its
candidate-pin correction and synthetic preflight. Actual pilot execution,
deployment and publication remain unauthorized.

The artifact-only rebuild from exact `c158c3b` Git blob bytes produced the
788,263-byte wheel with SHA-256
`6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60`.
All 103 packaged source/assets matched pinned Git bytes, and an identical
repeat-build hash, installed-wheel synthetic acceptance, 102 passing dimuon
regressions (one Windows privilege skip), strict metadata checks and clean
dedicated-environment audits were recorded. This is bounded Windows CPython
3.14.3 artifact qualification, not the future two-platform numerical gate.

The original 790,386-byte wheel, SHA-256
`b8434593e6b34abda2536e0c5752e5ade253d76a083537a34fb84d3b6b70974e`,
and its historical qualification records remain unchanged. The rebuild's
approval-pending receipts also remain unchanged; the later owner authorization
is recorded separately rather than rewriting them.

Only `candidate_wheel_sha256` changes in protocol revision 1. Its canonical
semantic digest correspondingly changes from
`dcafaf97bd99c43749261b15a9aab66cd47ed1631e911aa24fbf1f220f82449d` to
`afb3e2abca46794f71170599865e51d938c5cff50e7c939d3cad3f52e0b91266`.
All other protocol fields, including criteria, budgets, execution restrictions
and scientific statuses, remain identical. The original protocol bytes are
retained with the pin-correction record and in the first failed preflight.
This pin amendment is not a new numerical-criteria revision or signature.

Use the isolated environment containing the approved installed wheel, not the
CRLF-converted editable checkout, for its exact module/Git identity check.
The corrected synthetic preflight must use a new output root; it must not
rewrite or restart any earlier attempt. No actual CERN snapshot is admitted.

### Corrected synthetic preflight result — 2026-10-20

One new retained invocation with the approved installed wheel returned
`PREFLIGHT_PASSED`. Nine candidate module byte identities matched both the
wheel and pinned Git objects. The three-row original synthetic comparison
matched; the negative controls retained the expected `TIMEOUT`, `LOG_LIMIT`
(including the observed overflow byte) and `SOURCE_DRIFT` refusals. Those
expected control refusals are not CERN experiment results or scientific
counterexamples. No actual CERN CSV was opened or analyzed.

The new root is
`.local/cern-dimuon-qualification-preflight-approved-candidate-20261020/`.
Its closed integrity ledger covers **1,102,612 bytes in 33 files**, including
the 788,263-byte wheel, all 192 KiB reserved log/receipt slots and the ledger
itself. Its inventory SHA-256 is
`ac9e7b771768885f0c807bd4a5661589c239c4c38290e8b3202659fabbb2d9d0`.
All buckets remain below their unchanged ceilings; input and Windows/Linux
production-output buckets are empty. The original failed root is unchanged.
The source snapshot predates this result appendix; its own exact source
identities remain recorded rather than being retroactively replaced.

Pin-correction regressions passed **156 tests with two Windows
symlink-permission skips**. Ruff checks and the medium-or-higher Bandit scan
passed. Only the protocol's wheel field and corresponding helper pins changed;
criteria, budgets, historical artifacts, frozen scientific evidence and
scientific statuses are unchanged.

`qualification_outcome` remains `NOT_EXECUTED`; `pilot_execution_ready` remains
false. Remaining gates are reviewed helper identities, frozen CPython 3.12
Windows/Linux dependency manifests with identical NumPy versions, and separate
owner execution authorization. No commit, push, deployment or release follows
from this synthetic preflight.
