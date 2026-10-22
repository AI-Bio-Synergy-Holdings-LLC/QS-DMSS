# PR #208 — descendant marker and fresh qualification

Date: 2026-10-21, America/Mexico_City. Base: `b155705a5c850e8111c8454dc0ca145a76a4d557`.
This AI-assisted engineering record is not owner approval or independent
scientific review. Earlier packets, failures and qualification records remain
unchanged; none is relabeled as this run.

## Test-only correction

The descendant itself creates and closes an empty `ready` marker before its
seven-second sleep. Both parent cases (immediate exit and continued execution)
must observe that marker in their exclusive test root. A timeout before the
descendant starts can no longer falsely satisfy the regression. The original
0.5-second supervised timeout and under-three-second teardown assertion remain.
No runtime, production, protocol, dependency-lock or scientific code changed.

Two deliberate no-descendant negative controls fail specifically at the marker
assertion. Both real marker cases passed on the locked Windows and Linux
runtimes, and also in the broader Windows test run.

## Unchanged-cap preflight and retained packet

The test-only edit adds exactly 71 retained source bytes. The complete 19-file
source plan, compact index and four reserved 16 KiB environment slots occupy
**262,144 / 262,144 bytes**. There is **zero source headroom**; further active
source growth must preflight and HOLD rather than silently increasing a cap.
No required source, result, check or receipt was removed or shortened.

The new, exclusive serial synthetic root passed on its first execution:
`.local/cern-dimuon-pr208-descendant-marker-20261021/rehearsal-01/`.
All 63 files were counted; every inventoried hash and all 19 active-source
matches were verified. Its **8,347,874 / 27,262,976 bytes** are allocated as:

| Input | Wheel | Windows | Linux | Source | Comparison | Logs | Integrity |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,388,970 | 788,263 | 2,845,200 | 2,845,196 | 262,144 | 11,097 | 196,608 | 10,396 |

Source-index SHA-256:
`c2ef2586e33948f2a32d42012595ce040a35851889863424fb11e7e9a462bb16`.
Inventory SHA-256:
`a5109a3248d75bdfb23d4f6c12545ba5e37335c994db4e8996e79565f704f4e6`.
The inventory counts itself but does not claim to hash itself. Engineering
test/build files and runtime caches remain outside the bounded evidence root,
as in the existing protocol; no aggregate delivery archive was introduced.

## Fresh Windows/Linux qualification: PASS

- Locked CPython 3.12.15 / NumPy 2.5.4 installed-wheel regressions: Windows
  **270 passed, two existing symlink-privilege skips**; Linux **272 passed**.
- Serial Windows → Linux → comparison → refusal controls:
  `SYNTHETIC_REHEARSAL_PASSED`. Windows 19.973333 s; Linux 31.507530 s, within
  the unchanged 300-second native-stage deadlines, with no worker retry.
- Both original synthetic 20,000-row evidence bundles verified; 19,996 selected
  rows on both systems met the unchanged scalar/Decimal comparison criteria.
  This is not the CERN snapshot or its known numerical result.
- Ruff/format, medium-or-higher Bandit, registry/discovery, 113 Node tests,
  JavaScript syntax, social-card integrity and whitespace checks passed.
  Both frozen dependency locks report zero known vulnerabilities.
- All 15 protected hashes matched before execution. Both earlier successful
  packet inventories/contents and the previous failed rehearsal packet were
  checked and retained. The old launch-stall HOLD root was not reused.

## Broader local engineering gate: HOLD

The additional Windows CPython 3.14.3 full-suite attempt is retained separately:
**1,174 passed, 25 skipped, five failed; 91.72% core coverage**, above the
unchanged 88% coverage threshold. This is not an all-green full-suite result.
All five failures were `PermissionError: [WinError 5]` at file/directory
rename or replacement in otherwise unrelated campaign/robustness paths:

- `test_cli_campaigns_run_demo`: `job.json.tmp` replacement.
- `test_recorded_resolution_loops_preserve_isolation_and_error_contracts`
  (`real_symlink-analyses-analysis.json` and `real_symlink-analyses-source`):
  publishing a pending robustness directory, before reaching the symlink check.
- `test_discovery_streams_at_most_ceiling_plus_one_without_reading_or_deleting`
  (`5000-analyses`): publishing a pending robustness directory.
- `test_analysis_listing_isolates_invalid_compact_summaries`
  (`field11-value11`): publishing a pending robustness directory.

The root cause of those access denials is not established. No production fix,
security-setting change, skip, tolerance change or test retry was applied to
turn that failure record green. The broader local gate remains HOLD pending a
separate diagnosis/disposition; passing bounded CERN helpers does not waive it.
The complete log, JUnit and coverage reports remain under
`.local/cern-dimuon-pr208-descendant-marker-20261021/` with prefix `marker-`.

## Preservation and authority

Both approved wheel files, criteria, dependency locks, budgets, frozen evidence
and historical records remain unchanged. Actual CERN qualification stays
`NOT_EXECUTED`; `pilot_execution_ready=false`; scientific validation remains
`NOT_ESTABLISHED`; independent review and human disposition remain `PENDING`;
AI advice remains null. No actual CERN input was read or mounted.

No new review request, ready transition, merge, pilot, deployment, publication
or release is authorized or performed. Review threads remain unchanged. The
bounded qualification PASS and the separate broader engineering HOLD must not
be collapsed into a single approval or validation status.
