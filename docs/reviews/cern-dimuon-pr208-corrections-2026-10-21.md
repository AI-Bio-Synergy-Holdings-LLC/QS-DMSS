# PR #208 — six-finding correction qualification, 2026-10-21 UTC

Base: `689e313a50f26c4b6b70b098e1c7215165e5fcde`. This AI-assisted engineering
correction does not constitute owner approval or independent scientific review.
The [original qualification](cern-dimuon-execution-readiness-2026-10-21.md) and
all its retained packets remain historical and unchanged.

## Findings and regressions

| Existing comment | Correction and coverage |
| --- | --- |
| [4333596023](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/pull/208#discussion_r4333596023) | Shared process backend: Windows Job Object with a pre-spawn gate, POSIX session/process group, nonblocking raw-pipe polling, no reader thread. Descendant-held stdout is tested with both a running and an already-exited parent. |
| [4333596079](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/pull/208#discussion_r4333596079) | New empty startup bytecode prefixes plus explicit `-B` for workers/bootstrap. Admission checks the actual startup prefix and rejects missing flags, prefix drift or populated caches. A timestamp-valid stale-cache regression proves the old cache loads without the prefix and verified source loads with it. |
| [4333596106](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/pull/208#discussion_r4333596106) | One Docker connection-environment snapshot for inspect/create/start/remove/absence verification; Python sanitization remains separate. The integration regression covers DOCKER_HOST, DOCKER_CONTEXT and DOCKER_CONFIG and POSIX container cache paths from Windows. |
| [4333596147](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/pull/208#discussion_r4333596147) | One full rescan after an enumerated file disappears, discarding the incomplete count. Repeated disappearance HOLDs; directory-enumeration/permission failures still refuse immediately. Both rescan outcomes and all earlier enumeration regressions pass; no deadline is reset. |
| [4333596164](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/pull/208#discussion_r4333596164) | Stage HOLD retains primary reason, overflow byte, log usage and elapsed time, adding cleanup_failure separately. Four combined TIMEOUT/LOG_LIMIT × cleanup-returncode/cleanup-timeout cases pass. |
| [4333596184](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/pull/208#discussion_r4333596184) | Supervisor HOLD is attempted before independent best-effort stage recovery and inventory. Torn JSON, missing stage slots and stage-write refusal retain supervisor HOLD and a complete failure inventory when readable. |

Legacy synthetic controls now share the bounded backend rather than retaining
the same buffered-pipe defect. Their existing result fields and refusal reasons
are preserved, with an additional cleanup diagnostic. Test-fixture/JSON-read
duplication was extracted without removing cases: the legacy file retains all
39 test functions and 133 assertions. There are 15 new regression cases, 63
readiness cases total. No scientific algorithm or production module changed.

## Unchanged-cap preflight

All 19 active helper/protocol/lock/test/guide files are retained in raw form.
The compact JSON index retains every field and hash; no aggregate archive,
source omission, receipt truncation or new allocation was introduced.
Four 16 KiB environment reservations remain intact. Source records require
**261,910 / 262,144 bytes**, leaving only **234 bytes**. Any further growth must
preflight again and HOLD if it cannot fit; no cap may silently increase.
Interim capacity refusals occurred before worker execution.

The corrected synthetic packet contains **63 files / 8,347,640 bytes**, below
the unchanged 27,262,976-byte total. Logical bucket bytes:

| Input | Wheel | Windows | Linux | Source | Comparison | Logs | Integrity |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,388,970 | 788,263 | 2,845,200 | 2,845,196 | 261,910 | 11,097 | 196,608 | 10,396 |

Source-index SHA-256:
`c852b66d42af490919842341a9943d5233f22b3a87c08008950dfd66a9e00951`.
Inventory SHA-256:
`9abe14eefa0a83ece8cfae2aca25d1f70470134dfc3e0211d7cca68267e7414c`.
Every inventoried hash and active-source match was verified. The inventory
counts itself but does not claim to hash itself; empty directories contain no
payload. Runtime/dependency caches and separate engineering test/build records
are explicitly outside this evidence root, not hidden result copies.

## Qualification and preservation

- Full suite: **1,177 passed, 27 skipped; 91.74% core coverage**, above the
  unchanged 88% gate.
- Locked CPython 3.12.15 / NumPy 2.5.4 installed-wheel regressions: Windows
  **270 passed, two host-symlink skips**; Linux **272 passed**.
- Corrected serial synthetic rehearsal passed on its first new root: Windows
  15.78 s, Linux 27.20 s; unchanged 300 s deadlines. Both 20,000-row bundles
  verified, with 19,996 selected rows, using unchanged scalar/Decimal criteria.
- Ruff/format, medium-or-higher Bandit, registry/discovery, 113 Node tests,
  JavaScript syntax, social-card integrity, whitespace and compilation of 122
  Python files passed. Both frozen dependency-lock audits report zero known
  vulnerabilities; this does not characterize every host application.
- All 15 baseline preservation hashes match. The original 62-file rehearsal
  inventory and its contents were also checked without modification. An initial
  full-suite launcher refused an existing temporary path; it was preserved and
  a distinct path used, with no worker/root retry.

Receipts are local under `.local/cern-dimuon-pr208-corrections-20261021/`.
Both wheels, criteria, budgets, frozen evidence and scientific statuses remain
unchanged. Actual qualification is `NOT_EXECUTED`, pilot ready false, scientific
validation `NOT_ESTABLISHED`, independent review/human disposition `PENDING`,
AI advice null. No CERN data, new review request, merge, pilot, deployment or
release is authorized or performed. Remote qualification and separate owner
review remain required; resolving verified engineering threads is not approval
of scientific claims or authorization to merge.

## Final retention refinement — qualification HOLD

The successful results above describe correction commit `6628edd4282b238f794884cd1f9f56c2e1696b0e`,
not the subsequent refinement. The refinement gives process-tree cleanup its
own `tree_cleanup_failure` field so Docker's `cleanup_failure` cannot replace
it; the four combined-failure cases now assert preservation of both facts.
Four automatic Code Quality comments are also addressed with an explicit
`import ctypes.wintypes as W` (not an uninitialized `C.wintypes` attribute) and
comments explaining intentionally best-effort handlers. No policy or algorithm
changed. The complete current source plan is **262,073 / 262,144 bytes**, with
**71 bytes** spare, including the unchanged four 16 KiB environment slots.

Final qualification remains **HOLD**, not passed. The distinct retained root
`.local/cern-dimuon-pr208-corrections-final-20261021/` contains the interrupted
full-suite log and a synthetic rehearsal that retained supervisor HOLD before
either native stage ran. A separate readiness diagnostic stopped at the first
normal subprocess control: 22 passed, one failed; the 20-second control retained
TIMEOUT, zero log bytes and no cleanup failure. Independent minimal Python and
Git child-launch probes also timed out, so local launch behavior must be
restored and final bytes qualified on new, exclusive roots. No timeout, test,
budget or acceptance criterion was relaxed to make this attempt pass.

The final-attempt static checks and both frozen-lock audits completed, but do
not replace the interrupted full/native qualification. All 15 protected hashes
and both previous successful packet inventories/contents were rechecked and
remain unchanged. The final refinement is not represented as having the earlier
packet's hashes or passing results. Review findings remain open pending final
verification. No new Copilot review, merge, pilot, deployment or release occurred.
