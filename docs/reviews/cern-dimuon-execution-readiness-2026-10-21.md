# CERN execution-readiness qualification — 2026-10-21 UTC

Scope: one source-only, synthetic-only readiness increment after #207, based
on `8e0c073aed7cd9f82cac40a1d8e66d42881a271b`. AI-assisted implementation and
self-review are not owner approval or independent scientific assessment.

## Implemented boundary

- Exact live runtime/package admission before fixture access and again after
  analysis: CPython 3.12.15, NumPy 2.5.4, frozen Windows/Linux dependencies,
  wheel hashes and installed original members, excluding regenerated RECORD.
- Fixed serial Windows → Linux → comparison → refusal-control sequence;
  exclusive worker claims, no arbitrary command/data option or automatic retry.
- Offline digest-pinned Linux image, fresh isolated environment, minimal mounts,
  no network, bounded scratch storage and verified container teardown.
- Reserved before/after environment slots, complete active source/lock/test/guide
  snapshot, unchanged byte caps, failure receipts and retained partial outputs.
  The original log-limit/timeout receipt is preserved on coordinator failure.

The Linux image contains no Git. The controller retains a nine-module identity
map checked against the pinned Git objects and approved wheel; Linux checks
imports against that map and wheel. Windows additionally repeats the Git check.
This is disclosed provenance, not an independent Linux Git verification or an
OS/BLAS attestation. See the [execution guide](../cern-dimuon-execution-readiness.md).

## Qualification

- Complete final regression suite: **1,162 passed, 27 skipped; 91.71% core
  coverage**, exceeding the unchanged 88% gate.
- Approved installed-wheel, locked Python 3.12 native regressions: Windows
  **255 passed, 2 skipped** (host symlink privileges); Linux **257 passed**.
  Includes 48 new readiness regressions and real child-process timeout,
  overflow, drift and refusal controls on both platforms.
- Ruff/format, medium-or-higher Bandit, registry/discovery checks, 113 Node
  tests, JavaScript syntax, social-card integrity, whitespace and compilation
  of 121 Python files passed. Both frozen dependency-lock audits reported
  zero known vulnerabilities; this is not an audit of every host application.
- Three retained synthetic rehearsals passed during implementation. The final
  source-identical rehearsal processed the original built-in 20,000-row fixture
  with 19,996 selected rows on both platforms, verified both bundles, and met
  the existing scalar/Decimal comparison criteria. It did not open CERN data.
  Windows took 14.22 s; Linux took 19.48 s, each within the unchanged 300 s bound.

Final packet identity and accounting (logical retained file bytes):

| Bucket | Bytes | Unchanged cap |
| --- | ---: | ---: |
| Input | 1,388,970 | 4,194,304 |
| Wheel | 788,263 | 1,048,576 |
| Windows | 2,845,200 | 10,485,760 |
| Linux | 2,845,196 | 10,485,760 |
| Sources, locks and environment reservations | 259,101 | 262,144 |
| Comparisons | 11,143 | 524,288 |
| Logs and reserved failure slots | 196,608 | 196,608 |
| Integrity | 10,213 | 65,536 |
| Total | **8,344,694** | **27,262,976** |

- Source-index SHA-256:
  `469baa3e648a6722ade75e1b33afde61a9b556874e210e3798bc1f024db22ae9`.
- Inventory SHA-256:
  `d3452c9016d0f87261ca363044d68919edfe776b2c9af1e71bb61187439da946`.
- All 62 retained files were counted; every inventoried hash was verified,
  and all 18 active source files matched the proposed checkout. Empty exclusive
  claim directories do not contain payload bytes. The inventory counts itself
  but does not claim to hash itself.
- Interpreter/dependency caches and separate engineering test/build logs are
  identified prerequisites/qualification records outside this evidence root,
  not omitted result copies. Historical records and interim failures remain
  local under `.local/cern-dimuon-execution-readiness-20261021/`.

Interim findings were corrected without raising limits: fixed temporary paths
were replaced by exclusive temporary creation; the provisional source-size test
was replaced by the coordinator's exact encoded ledger, rather than an estimated
index allowance. The initial failing test/scan logs were retained. The final
source cap has only 3,043 bytes of headroom; further growth must refuse before
workers start, not silently relax the approved budget.

## Preservation and disposition

All 15 baseline preservation checks, including both wheels, frozen evidence,
protocol, locks and historical review records, matched. The approved unpublished
wheel remains `6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60`;
the original remains
`b8434593e6b34abda2536e0c5752e5ade253d76a083537a34fb84d3b6b70974e`.

No production module, scientific criterion, public UI, licensing or release
version changed. Actual qualification is `NOT_EXECUTED`; pilot execution ready
is false; scientific validation is `NOT_ESTABLISHED`; independent review and
human disposition remain `PENDING`; AI advice is null. #183 is unaffected.
No pilot, deployment or release was performed. Remote qualification and owner
review of this PR remain separate gates; merge is not authorized by this record.
