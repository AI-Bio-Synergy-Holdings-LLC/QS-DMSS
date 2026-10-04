# Development-candidate qualification — 2026-10-03

This is engineering evidence, not publication authorization or independent
scientific approval. No tag, version bump, PyPI upload or production deploy was
performed. The roadmap target is v0.14.0; current metadata remains 0.13.2.

## Exact baseline before the pilot

Clean local/remote main:
`fd38ef5e922ce968709ddc153ff0e9f31652ba4a`.

Fresh Windows environment: CPython 3.12.14, NumPy 2.5.3, FastAPI 0.142.2,
Starlette 1.7.0, Pydantic 2.13.5, Qiskit 2.5.2, Aer 0.17.2. Development/audit
extras and the bounded falsification requirements were installed. The runtime's
initial pip 25.0.1 was updated to 26.2.1 before the clean dependency audit.

Before source edits: **352 passed, 90.32% coverage** (88% gate). Ruff, Bandit
medium-or-higher, pip-audit, baseline benchmark, challenge-registry/discovery
consistency, wheel/sdist build and Twine passed. The isolated installed wheel
passed run/verify/replay, campaign, showcase, cockpit and experimental graph
smoke checks. Docker Python 3.12 build and run-demo/verification passed.

Locally built, unpublished baseline artifacts (not published v0.13.2 artifacts):

- Wheel SHA-256: `e5eb016d1a5480b0ba47b00b3a53e883306d5d5548e9ef18038ae8af4fb9c0b9`.
- Sdist SHA-256: `8aa4cc96f021b8b57582abfc321cb1092ada4cfab2b20aca14a8aaf6e096c58b`.

The artifacts are retained in the implementation worktree's ignored
`.tmp/baseline-dist/`, identified by these hashes. Rebuilds may have different
archive timestamps; a version string alone is not candidate identity.

## Recommendation-robustness pilot qualification

**393 passed, 90.61% coverage** with quantum extras. New pure analysis has 100%
statement coverage; isolated cockpit service has 92%. Ruff, Bandit and dependency
audit passed. Wheel/sdist and Twine passed. Fresh-installed candidate smoke now
also checks the pilot's original-score agreement, save/reopen/export, unchanged
source fingerprint and hosted denial. A Docker-installed candidate passed the
same recorded-campaign smoke.

Browser: Playwright CLI / Chromium, 1440×1000 desktop and 375×900 mobile.
The dedicated Browser plugin/skill was not available in this session.
Rendered assertions passed for a changed recommendation, actual SVG redraw,
save/reopen/bundle download, keyboard weights, invalid-profile save denial,
literal rendering of an HTML-like hostile label, overlapping-refresh protection,
unavailable-source save denial, mobile bounds and collapsible controls.
Browser console: zero errors/warnings after repairing generated
report CSP. Screenshots are retained outside the repository in the temporary
`qs-dmss-robustness-qa` directory, not distributed as package evidence.

Security correction: generated HTML report/workbook previews admit same-origin
framing only, hash-bound inline stylesheet blocks and one fixed core-owned
workbook tab script. They do not authorize arbitrary inline scripts or
`unsafe-inline`. The cockpit, JSON, static assets and downloads retain framing
denial. Existing evidence files are not rewritten.

Representative repeatable commands:

```powershell
python -m pytest -q --cov=qs_dmss --cov-fail-under=88 --cov-report=term
python -m ruff check src tests .github/scripts research site/build_portal.py
python -m bandit -r src --severity-level medium --confidence-level medium -q
python -m pip_audit --local
python research/challenges/validate_registry.py
python research/challenges/build_discovery.py --check
node --check src/qs_dmss/cockpit/static/robustness.js
python -m build --sdist --wheel
python -m twine check dist/*
python .github/scripts/fresh_install_smoke.py --source candidate-wheel --wheel-path dist
```

## External state and remaining gates

### Review follow-up

Owner approval was recorded for initial pilot commit `1b18269`. Copilot then
identified three bounded issues: non-object decisions in recorded JSON,
whole-list failure from one corrupted saved analysis, and an inline workbook
print handler blocked by CSP. A single follow-up batch fixes them and adds nine
regression cases. **402 tests passed, 90.65% coverage** locally with quantum
extras; the cockpit robustness service now has 93% statement coverage.

New workbooks bind print through the fixed core-owned script. The prior tab
script hash remains authorized for historical workbooks; arbitrary handlers,
`unsafe-inline` and `unsafe-hashes` remain blocked. Historical artifacts are
not rewritten (use the browser's print command for their legacy print control).
Chromium desktop/mobile checks verified click/keyboard print invocation using
a print spy, new/legacy tabs and mobile bounds. The native print dialog/PDF
save was not automated; a pre-existing standalone `/favicon.ico` 404 is
unrelated to CSP or the action. These changes require requalification and
refreshed owner approval of the revised head, not approval inherited from
`1b18269`.

The first follow-up remote matrix exposed a Python 3.10/3.11 compatibility
failure in the unreadable-artifact regression: older `pathlib.glob` performs
an existence/stat check while enumerating literal child names, outside the
per-artifact exception boundary. Listing now enumerates immediate entries and
checks each `analysis.json` inside that boundary. The regression was retained,
not weakened. The full Windows CPython 3.12 suite again passed **402 tests,
90.65% coverage**, with Ruff and Bandit clean. All 28 isolated cockpit
robustness tests also passed on a fresh Windows CPython 3.11.15 runtime.
Latest-head remote matrix and
Docker qualification remain required; the failed first follow-up is not a pass.

That compatibility head (`6c7a75a`) subsequently passed its complete remote
Python 3.10–3.13/quantum matrix, Docker, cross-platform candidate-wheel smoke,
CodeQL, Code Quality and dependency/policy/metadata gates.

The next Copilot pass confirmed the first three fixes and identified explicit
malformed convention values and unnamed, unfocusable scrollable table regions.
Explicit conventions now require a non-empty string; only an absent field uses
the legacy fallback. Both table regions are named and keyboard-focusable.
Chromium desktop/mobile checks passed Tab reachability and native arrow-key
horizontal scrolling, with no page-wide overflow or runtime/console errors.
The source/qualification suite passed **410 tests, 90.66% coverage**, with Ruff
and Bandit clean. Eight new regression cases cover malformed conventions and
complete recorded scoring-component agreement.

The suggested change to `RankingConfig` iteration order was not adopted:
actual run records are serialized with sorted keys before campaign scoring.
The unchanged real-campaign HTTP equality test passes with canonical order;
the added complete-positive-weight regression demonstrates that the proposed
in-memory default order changes the recorded component list. This is an
evidence-backed review disposition, not a bypass of an unresolved failing test.
Latest-head remote gates and refreshed owner review are still required after
these additional changes.

Owner approval was subsequently recorded on `c7ce7a4`. The completed Copilot
review identified one new fresh-install defect: listing saved analyses before
the first save raised `FileNotFoundError` and returned HTTP 400. The focused
correction catches missing storage only and returns `{"items": []}` without
creating evidence storage. Permission errors and non-directory storage retain
their sanitized error contract; hosted access remains denied. Five regression
cases cover absent experiment/analysis roots, an empty existing root and the
two storage-error classes. The pre-fix run reproduced both absent-root failures.
All 40 cockpit robustness tests pass after correction, and the full local
quantum-enabled suite passes **415 tests, 90.66% coverage**. The five new cases
also pass on fresh Windows CPython 3.10.20 and 3.11.15. Ruff, Bandit, compilation
and a fresh-cache installed-dependency audit pass (no known vulnerabilities).
Installed-wheel/Docker smoke now checks the empty collection before campaign
execution and before the first save, then discovery of the saved artifact.
Latest-head remote requalification and renewed owner approval are required;
the approval on `c7ce7a4` is not inherited by this corrective commit.

The empty-storage head (`11e33f9`) passed all remote gates, with **415 tests,
90.62% coverage** in the Python 3.13 quantum job. Its completed Copilot review
confirmed that correction but identified a captured-metric type gap in its
previously-missed summary: Python permits `true == 1.0` and `false == 0.0`.
The owner separately authorized this focused correction and requalification.
Both comparison and captured values now require a non-boolean integer or float
before numeric equality is considered. Numeric representation compatibility,
finite/resource limits, scoring order and scientific boundaries are unchanged.

The regression batch has 28 malformed-capture cases across all four metrics
(true, false, null, numeric string, array, object and missing), plus 16 equal
integer/float compatibility cases. Fixtures retain valid manifests and bundles,
so invalid types cannot hide behind an unrelated integrity failure. Before the
fix, the eight boolean cases failed because source admission did not reject
them; the other 36 cases passed. After the fix, all 84 cockpit robustness tests
pass, including authored HTTP 400 responses for source/preview/save and no
analysis storage creation on rejection. The 44 added cases also pass on fresh
Windows CPython 3.10.20 and 3.11.15. The full local quantum-enabled suite passes
**459 tests, 90.69% coverage**. Ruff, Bandit, compilation and fresh-cache
installed-dependency audit pass (no known vulnerabilities). Latest-head remote
matrix, installed-wheel/Docker qualification and completed review remain
required; neither old approval nor an automated workflow's success is a clean
scientific or owner approval of the revised head.

The captured-metric head (`716e3c8`) passed all remote gates with **459 tests,
90.62% coverage** in the quantum job. Its completed Copilot summary identified
two additional previously-missed concerns, separately authorized as one batch:
full bundle/source reads during summary listing, and uncaught invalid UTF-8
in report style-hash generation. Listing now reads only the manifest and
`analysis.json`, checks identity/summary fields, retains newest-first ordering
and the 200-item cap, and labels each item `analysis_json_only`. Direct
open/export still checks retained sources and the entire bundle. The UI explains
the distinction beside the selector and attaches an accessible description.
Malformed reports keep their original bytes and baseline style allowlist;
no artifact style hashes are admitted when strict UTF-8 decoding fails.
Fixed core-owned script hashes and same-origin-only framing remain unchanged.

Eighteen added cases cover 1/3/201-item listings with exactly two bounded reads
per returned item, invalid summaries, damaged/missing source/bundle rejection
on HTTP open/export, three malformed UTF-8 sequences and the actual run-report,
experiment-report and workbook HTTP routes. The initial 15-case pre-fix batch
had **12 failures, 3 passes**, reproducing both findings. After correction, all
104 report-security/cockpit-robustness cases pass. The complete local suite
passes **477 tests, 90.68% coverage** with quantum extras; Ruff, Bandit,
compilation and fresh-cache dependency audit pass. All 18 additions also pass
on fresh Windows CPython 3.10.20 and 3.11.15. Installed-wheel/Docker smoke
explicitly checks the summary scope and malformed-preview fallback.

Rendered QA: Playwright CLI 0.1.22/Chromium at 1440x1000 and 375x900 on a
dedicated temporary localhost service (not user ports or production).
The dedicated Browser skill was unavailable. Run Lab -> saved selector ->
reopened analysis passed; the download control remained visible, the description
was visible and correctly associated, native selector focus worked, and there
was no page-wide overflow or console warning/error. Screenshots were inspected
and retained outside tracked source. No layout redesign was performed.
Latest-head remote qualification and one completed Copilot review remain
required; no merge, deployment, release or scientific approval is implied.

The summary/report head (`3557561`) subsequently passed all automated remote
gates with **477 tests, 90.64% coverage** in the quantum job. Its completed
Copilot summary no longer flags either corrected issue but identifies a new
previously-missed resource concern: the 4 MiB report-read bound did not bound
the generated CSP value. Read-only function-level fixtures produced 14,156,157
CSP bytes from repeated style blocks and 221,565 bytes from 4,096 distinct
styles. Those measurements alone did not test server/proxy rejection.

The owner separately authorized a bounded correction. Style hashes are now
deduplicated in first-seen order and admitted only within an **8 KiB complete
CSP-value budget**, including baseline directives and the fixed current/legacy
workbook-script hashes. A lazy style iterator stops on budget overflow and
omits all artifact hashes rather than admitting a partial list. An already
oversized trusted baseline is preserved without adding artifact hashes; no
baseline directives or core script hashes are removed. Report bytes, scientific
code, UI implementation and historical evidence remain unchanged.

Thirteen added cases cover stable deduplication, an exact 4 MiB repeated-style
fixture, early stopping on distinct hashes, one-byte-below/at/above budget
boundaries, oversized trusted-baseline preservation and actual HTTP delivery
through all three report/workbook routes. Before correction, **11 failed and
2 passed**. Afterward all **21 report-security tests** pass on Windows CPython
3.10.20, 3.11.15 and 3.12.14. The full quantum-enabled local suite passes
**490 tests, 90.72% coverage**; the CSP helper has 100% statement coverage.
Ruff, Bandit, compilation, fresh-cache dependency audit (no known vulnerabilities),
baseline benchmark and registry/discovery consistency checks pass. The same
stress fixtures now yield **435 CSP bytes / 1 style hash** for repetitions and
**381 bytes / 0 artifact hashes** for distinct-style overflow. Installed-wheel
and Docker smoke explicitly check both deduplication and budget fallback.

Compatibility QA used Playwright CLI 0.1.22/Chromium at 1440x1000 and 375x900 on
a dedicated temporary port 8104. The Browser mention was visible, but the
dedicated Browser skill/runtime was not exposed in the session. A retained
campaign workbook rendered with its original styles; Overview -> Variant
matrix -> Overview changed the visible tab panel, and Print invoked the fixed
script through a spy. The native print dialog/PDF export was not automated.
The actual workbook response was HTTP 200 with a 435-byte CSP and SAMEORIGIN
framing. Screenshots were inspected and retained outside source. There was no
page-wide overflow, error overlay or CSP/script error. The sole console error
was the previously known standalone `/favicon.ico` 404, not a clean zero-error
claim. Latest-head remote gates, one completed re-review and fresh owner
approval remain required; there is no readiness, merge or release authorization.

### Bounded retained-artifact and parser follow-up

The CSP-budget head (`9e63957`) passed its remote matrix, Docker, cross-platform
installed-wheel and security gates (**490 passed, 90.68%** in the quantum job).
Its completed Copilot review nevertheless identified four new concerns, including
three in the previously-missed summary. The owner explicitly authorized one
batch and a **4096-entry discovery ceiling**, without historical deletion.

Retained manifests, hash files and ZIPs now use child containment checks. Load
and HTTP export share a verified, bounded ZIP snapshot; HTTP serves those exact
bytes rather than reopening a mutable path after verification. The compatibility
path accessor returns a resolved contained path and is not used for HTTP delivery.
Streaming `os.scandir` bounds discovery to 4097 consumed entries and at most
4096 stored candidates before stats, reads or sorting. Every immediate entry
counts, including non-artifacts and `_pending`. Overflow returns an explicit
HTTP 400, never a partial latest list; direct known-ID access remains available.
Missing roots, root storage failures, ordering, 200-candidate selection and
individual-record isolation retain their documented contracts. This also avoids
older Python's literal-child glob/stat failure and eager `iterdir` enumeration.

Style extraction now uses forward-only, quote-aware opening-tag and closing-tag
scans. Unclosed markup scans its remaining suffix once and admits no artifact
hashes, including any earlier valid styles. Exact CSS, newline normalization,
deduplication order, core-script hashes and the complete 8 KiB CSP budget remain
unchanged. No HTML, historical evidence or scientific implementation is rewritten.

The 28 additional cases cover simulated and real symlink escapes, a bundle
changed after verification but before response creation, unreadable campaign
discovery, 4096/4097/5000-entry scan instrumentation for both collections,
ordering/caps, quoted attributes, malformed suffix fallback, one closing search
for 4000 unclosed openings, full 4 MiB malformed inputs and all three preview
HTTP routes. The initial focused red test run had **15 failed, 5 passed and
4 skipped**, including tests for the not-yet-implemented helpers. After correction,
the full Windows CPython 3.12.14 quantum-enabled suite passes **514 tests,
4 skipped, 90.76% coverage**. CSP helper statement coverage is 100%. All
**141 targeted tests pass, 4 skipped** on CPython 3.10.20 and 3.11.15 as well.
The four real-symlink cases are skipped because this Windows host denies symlink
creation (WinError 1314); simulated containment tests pass. Linux CI must execute
the real-link cases; no Windows privilege or OS policy change was attempted.

Ruff, Bandit medium-or-higher, compilation, fresh-cache dependency audit (no known
vulnerabilities), baseline benchmark, registry/discovery checks and JavaScript
syntax pass. Installed-wheel/Docker smoke additionally asserts verified ZIP
snapshot identity and unclosed-style fallback. Latest-head artifact checks,
remote requalification and one completed re-review are recorded in the PR after
commit; older gates are not inherited by this head. The previously observed local
fresh-wheel console-launcher block (WinError 4551) remains unresolved and was not
bypassed with an alternate launcher. No new rendered-browser pass is claimed for
this server-only batch; valid generated workbook/report HTTP contracts are tested.
Fresh owner review and explicit readiness/merge authorization remain required.
PR stays draft; no merge, deployment, release or hosted capability activation.

### Source-bundle streamed-byte ceiling — 2026-10-04

The four-finding head (`e47b82c`) passed every automated remote gate, including
**518 tests, no skips, 90.72% coverage** in Linux quantum CI and actual symlink
regressions. Its single completed Copilot re-review no longer flagged those four
issues but identified a medium concern under **Previously missed**, despite
"Findings: None": the source ZIP size check preceded an unbounded read-to-EOF
hash loop. A bounded read-only simulation reproduced acceptance with an 8-byte
injected ceiling, 4-byte reported stat and 12 bytes consumed. Retained evidence
was unchanged. This was not a physical file-growth or production load experiment.

The owner separately authorized the focused guard and requalification. Hashing
now counts streamed bytes, requests at most the remaining allowance plus one
overflow-detection byte (and never more than 1 MiB per read), rejects overflow
before updating the digest, and closes the stream through its context manager.
The initial stat remains a fast rejection only. The declared 64 MiB ceiling,
authored source-limit HTTP 400, valid hashes/fingerprints, scoring and original
artifacts remain unchanged. This is a per-read resource bound, not a concurrent
traffic limit or guarantee of coherent snapshots under arbitrary local mutation.

Fifteen added cases cover one-byte-below/at/above 8-byte, multichunk and actual
64 MiB boundaries, underreported stat, bounded never-ending short reads, fast
oversize rejection without opening, valid short-read hash/pin/preview/save
compatibility and source/preview/save HTTP rejection before persistence. The
pre-fix run had **13 failures, 2 passes**. After correction all 15 pass on
Windows CPython 3.10.20, 3.11.15 and 3.12.14. Full local quantum qualification:
**529 passed, 4 skipped, 90.81% coverage**; the four pre-existing real-symlink
skips reflect this host's unavailable privilege, not a new streaming-test skip.

Ruff, Bandit medium-or-higher, compilation, fresh-cache dependency audit (no known
vulnerabilities), baseline benchmark, registry/discovery consistency and JavaScript
syntax pass. The source-development campaign smoke also passes save/reopen/export,
original-score agreement, hosted denial and the new in-memory growth check
(`source_bundle_stream_limit_enforced: true`), with its generated evidence retained.
Installed-wheel/Docker smoke now performs the same growth check and confirms the
real campaign fingerprint is unchanged afterward. No new local installed-wheel
pass is claimed: the previously observed Windows console-launcher policy block
remains unresolved and was not bypassed. No UI, numerical, scientific-status,
dependency or production changes were made. Latest-head artifact checks, remote
gates and one completed re-review are recorded in the PR after commit. Fresh
owner review and explicit readiness/protected-merge authority remain required.

### Compact discovery summaries and aggregate response ceiling — 2026-10-04

Automated gates passed on source `fb9bad2`, including **533 remote quantum tests,
90.77% coverage**, installed-wheel OS matrix and Docker. The completed review
still identified a high listing-payload resource concern: per-file limits did
not bound the nested values copied into up to 200 response items. Small read-only
in-memory probes reproduced that retention mechanism, not a maximum-load or
production failure. The owner separately authorized this focused correction and
the accompanying non-blocking import-style cleanup, not merge or publication.

Campaign selector summaries now require small scalar fields: labels up to 512
characters, non-boolean integer run counts 0–64, and nullable timestamp strings
up to 64 characters. Missing/empty labels retain the ID fallback; missing dates
remain null. Saved summaries project source label and optional validated
experiment ID, source fingerprint and legacy flag. Full hash/convention maps and
unknown nested provenance remain in the original record and direct open/export,
not the discovery response. Label-only historical summaries remain compatible.
Invalid shape, size, Unicode and over-nested JSON records are individually
isolated. No stored artifact, manifest or bundle is rewritten.

Both full response envelopes have a **1 MiB compact UTF-8 JSON ceiling** including
commas and escaping. Accounting is incremental, before item retention; overflow
propagates as an authored HTTP 400 instead of hiding the error or returning a
partial latest-items list, and later metadata reads stop. Existing ordering,
200-candidate selection, 4096-entry scan limit, two-file saved-summary checks,
integrity-scope labeling and full direct-access verification remain unchanged.
This is not concurrent-traffic control or a new aggregate metadata-I/O ceiling.
The 512/64-character bounds are not scientific/date-format validation.

Fifty-eight added cases cover malformed scalar shapes, booleans/floats, field
boundaries, invalid surrogates, missing-field compatibility, compact projection
with 1 MiB of unknown provenance, complete direct open/export, full serialized
response boundaries and exact HTTP Content-Length, empty envelopes, early-stop
reads, 200 max-length escaped summaries and deeply nested JSON. The initial
49-case pre-fix batch produced **41 failures, 8 passes**. After correction all
77 listing cases pass on Windows CPython **3.10.20, 3.11.15 and 3.12.14**. The
200-item HTTP responses measured **743,828 campaign bytes** and **833,611 saved
analysis bytes**; these are serialized sizes, not peak-memory/load benchmarks.

Full local quantum-enabled suite: **587 passed, 4 skipped, 90.87% coverage**. The
four pre-existing real-symlink skips are the Windows privilege limitation and
must execute on Linux CI. Ruff, Bandit medium-or-higher, compilation, fresh-cache
installed-dependency audit (no known vulnerabilities), baseline benchmark,
scientific registry/discovery consistency and JavaScript syntax pass. The smoke
script uses one module import style and checks compact projection, invalid
scalar isolation and the aggregate response ceiling without altering the real
campaign, adding `compact_listing_response_limits_enforced: true` to installed
wheel/Docker qualification. Its source-development run also retains score/hash,
reopen/export, snapshot, streaming-ceiling, CSP and hosted-denial checks.

The local fresh-wheel console-launcher policy block remains unresolved; it was
not retried through an alternate launcher or OS-policy change. No current local
fresh-wheel or new browser-rendered pass is claimed. This server-only correction
changes neither numerical/UI implementation, dependencies, hosted graph/AI,
scientific status, version nor production settings. Build/archive checks and
latest-head remote gates plus one completed re-review are recorded in the PR
after commit. Fresh owner review and explicit readiness/protected-merge authority
remain required; draft, deployment and release holds remain.

### Campaign discovery identity admission — 2026-10-04

Source `4a1fcbd` passed its automated remote gates, including **591 remote quantum
tests, no skips, 90.83% coverage** and cross-platform installed-wheel/Docker smoke.
Its one completed Copilot re-review resolved the previous high listing-resource
finding but identified a medium identity mismatch under **Previously missed**,
despite "Findings: None": copied campaign directories could be advertised under
their directory ID although the retained record used another ID and direct open
rejected it. A read-only probe confirmed that behavior without changing evidence.
The owner separately authorized this focused correction and requalification.

Discovery now requires exact equality between recorded and directory experiment
IDs before constructing a summary. Missing, non-string and mismatched IDs are
skipped, not repaired or migrated. Direct source/preview/save retain their existing
authored identity HTTP 400 and full integrity checks. Healthy ordering, the
first-200 candidate-read cap, metadata-only discovery, response/scan budgets,
scoring and original hashes are unchanged. Skipped records are not backfilled
from older candidates; discovery is still not full artifact verification.

Sixteen added cases cover fourteen missing/malformed/mismatched identities in
integrity-valid copied test artifacts, exact HTTP failures before persistence,
unchanged original/copy bytes and fingerprints, ordered 200-read admission and
the complete healthy discovery/open/preview/save/reopen/export workflow. After
correcting a new test fixture to mirror production's canonical persisted-profile
order, the authoritative pre-fix run was **15 failed, 1 passed**; no production
scoring change was made. All 16 pass on Windows CPython **3.10.20, 3.11.15 and
3.12.14** after the identity guard.

Full local quantum-enabled qualification: **603 passed, 4 skipped, 90.87%
coverage** (88% gate). Ruff, Bandit medium-or-higher, compilation, a fresh-cache
installed-dependency audit (no known vulnerabilities), the baseline benchmark,
scientific registry/discovery consistency and JavaScript syntax all pass.

The source-development campaign smoke preserves its real campaign while injecting
null and mismatched IDs in memory; installed-wheel/Docker smoke uses the same
check and emits `source_listing_identity_enforced: true`. No new local fresh-wheel
pass or browser-rendered pass is claimed. The existing Windows console-launcher
Application Control block and four real-symlink privilege skips remain documented;
neither is bypassed. No UI, solver, dependency, version, hosted graph/AI,
scientific-status, production or release change is included. Current-head archive
identity, remote gates and the single completed re-review are recorded in the PR
after commit. Fresh owner review and explicit readiness/protected-merge authority
remain required; draft, deployment and release holds remain.

### Sibling artifact identity and failure-state corrections — 2026-10-04

Source `cde9bac` passed all remote gates, including **607 quantum tests, no skips,
90.83% coverage** and cross-platform installed-wheel/Docker smoke. Its one
completed Copilot review (5407137876) nevertheless recommended changes: a high
sibling-alias identity concern and three previously-missed medium findings
(recursive JSON HTTP 500, successful-save/list-refresh failure, and failed-reopen
busy state). Read-only probes reproduced these mechanisms; the owner separately
authorized one focused four-finding batch, not readiness, merge or publication.

Resolved artifact leaves now match the requested ID exactly, in addition to
parent containment. Sibling aliases are filtered before the 200-candidate window
and direct access returns the existing HTTP 404. All entries still count toward
the 4096-entry scan ceiling. Router error normalization includes `RecursionError`
in the existing sanitized HTTP 400, without leaking paths or parser messages.
Successful returned saves keep their ID/download and disabled Save control when
selector refresh fails; genuine POST rejection remains retryable. Failed reopen
clears busy and labels the previous result without permitting save/download.
Generation guards preserve newer requests. This is not network idempotency.

Twenty-five Python cases cover both collections' virtual/real sibling aliases,
200-alias candidate-window instrumentation, and 8192-level / 16,396-byte JSON
across five source metadata files and source/preview/save/open/export paths.
Evidence hashes/bytes and healthy contracts are retained. The authoritative
pre-fix batch had **23 failures, 2 Windows symlink skips**; after correction it
passes **23 tests, 2 skips** on CPython 3.10.20, 3.11.15 and 3.12.14. New built-in
Node tests execute the actual UI callbacks under a minimal DOM/I/O shim: the
initial 11 cases had **3 failures, 8 passes**, and the final 12 pass on Node
26.3.0, including an additional post-save display-error guard. CI runs these
dependency-free contracts on Node 22 in every supported Python matrix job; the
sdist explicitly retains the CJS test. These are not rendered-layout tests.

Full local quantum-enabled qualification: **626 passed, 6 skipped, 90.87%
coverage** (88% gate). The six real-symlink skips are Windows WinError 1314
(four existing, two new), not skipped JSON or UI-state tests; Linux must execute
them. Ruff, Bandit medium-or-higher, compilation, fresh-cache dependency audit
(no known vulnerabilities), benchmark, registry/discovery and JavaScript syntax
pass. Source-development smoke additionally emits
`artifact_alias_identity_enforced: true` and `recursive_json_errors_sanitized:
true`, alongside unchanged score, fingerprint, export/snapshot, resource, CSP
and hosted-denial checks. Latest-head archive and remote evidence is recorded
in the PR after commit; older gates are not inherited by the new head.

Rendered acceptance used cached Playwright CLI 0.1.22/Chromium on an isolated
ephemeral loopback service at desktop 1440x1000 and mobile 375x900. Native
keyboard save/reopen, real successful saves followed by injected listing HTTP
400, no duplicate POST on retry, downloaded bundle SHA-256, prior-chart retention,
busy clearing, overlapping-request generation guards, recovery and unchanged
source fingerprints pass. Exactly two new QA analyses are retained in the
isolated corpus; user/production evidence was not used. Mobile page width is
375 px, with component bounds 43–332 px. The acceptance run had no page errors
or unexpected console errors; its six HTTP 400 entries were deliberate injected
failures. Four original component screenshots were inspected and retained under
ignored `output/playwright/followup-guards/`; sticky navigation appears in the
long scrolling captures. A separate attempt to hide that chrome for two extra
captures generated two expected HTTP 400 and four CSP style-block errors: the
policy correctly blocked screenshot-only injected CSS. Those captures are not
claimed as chrome-free, and that attempt does not make the whole console log
error-free. No security policy was weakened. The owned browser/service stopped.

No solver/scoring, dependency, version, scientific-status, production or hosted
graph/AI change is included. The local fresh-wheel Application Control block
(WinError 4551) remains unresolved and was not bypassed; no fresh local installed
wheel pass is claimed. One completed latest-head re-review and fresh owner
review plus explicit readiness/protected-merge authority remain required.
PR stays draft; deployment and release holds remain.

The first remote qualification of this batch (`e53cde9`) exposed a fixture
portability error, not a passing gate: standard Linux/macOS CPython 3.12/3.13
parsed the 8192-level fixture and reached other authored validation errors,
where the bundled Windows runtime raised `RecursionError`. Python 3.12/3.13
tests and fresh-wheel smoke failed; Docker was consequently skipped. Tests and
installed smoke now inject the parser exception deterministically only for the
exact malformed fixture, preserving healthy JSON reads and the exact sanitized
HTTP 400 assertion. The production fix is unchanged. These are parser-exception
contract tests, not a universal JSON depth limit or cross-platform native-parser
reproduction claim. Revised-head qualification is required from scratch.

The portable 25-case batch again passes **23 tests, 2 Windows symlink skips**
in isolated offline CPython 3.10.20/3.11.15 and existing 3.12.14 environments;
the unchanged 12 Node callback contracts and source-development smoke pass.
The full local quantum suite was rerun: **626 passed, 6 Windows symlink skips,
90.90% coverage**, with the 88% gate retained. Production source bytes did not
change during this fixture-only follow-up.
Initial project-scoped UV attempts failed with access denied rather than
switching the active 3.12 interpreter, but partially removed development
dependencies; the subsequent build check exposed the damage. The environment
was repaired through normal package reinstallation, without OS-policy changes
or a console-launcher bypass, and must pass fresh dependency/build/test checks.
Successful compatibility runs explicitly use `--no-project --isolated` and
do not manage this worktree's development environment.
Reinstallation completed with 86 compatible installed packages and a fresh-cache
audit reporting no known vulnerabilities. Auxiliary `charset-normalizer` moved
from 3.5.1 to 3.5.2 and `rpds-py` from 2026.6.3 to 2026.9.1; core numerical/
quantum versions remained as recorded above. Ruff, Bandit, compilation and the
source-development smoke pass after repair. No regenerated console launcher was
executed; this remains source-environment qualification, not a fresh-wheel pass.

Main CI, Python 3.10–3.13 matrix, Docker, CodeQL, Code Quality, policy, Pages and
production auto-deploy verifier were successful on the pinned baseline. The
latest scheduled quality/security checks also succeeded on that commit. The
pilot still requires **its own** remote matrix, Docker, security/dependency
checks, owner/Copilot review, protected merge and post-merge verification.
Local CPython 3.12 results do not substitute for the supported remote matrix.

Hosted `/api/health` returned `ok`, metadata 0.13.2 and Render main `fd38ef5…`.
Hosted custom compute, live quantum and AI advisory drafts remain disabled.
The independent scientific-review gate [#183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183)
remains open. Registry evidence still says `NOT_ESTABLISHED` / `PENDING`.

Release preparation must settle candidate version/notes/public metadata and
retain the scientific and legal limitations. This pilot does not close EH-011,
EH-012 or the controlled-restart publication gate. The next feature increment
is one schema-validated data-only diagnostics pack, not executable plugins or
hosted graph/AI expansion.

## Admission-validation follow-up (2026-10-04)

Owner authorization covered one focused batch for the two findings in Copilot
review `5407263942`: unsafe full-tree JSON rendering and incomplete recorded
profiles. It did not authorize readiness, merge, deployment or publication.

Metadata now has a pre-decoder 64-container nesting ceiling, with quoted/escaped
brackets excluded, and a depth-bounded full-tree UTF-8/finite-number check.
Unknown/unused fields are checked too. Profiles use the request schema plus
explicit editor-required recorded sections; validation never dumps normalized
defaults over original evidence or changes persisted weight order. Empty
constraints, optional prose, partial weights, valid astral Unicode, standard
byte encodings and integer/float representations remain compatible. A rejected
source also clears its matching busy state while hiding editor/results and
keeping save/download blocked; stale-request guards are preserved.

The 55-case Python batch was red before implementation (**50 failed, 5 passed**)
and subsequently passed. Two Node source-rejection contracts were added; the
new busy-state case was red before its narrow UI fix. All **14 Node contracts**
now pass. Full local quantum-enabled qualification on the existing CPython
3.12.14 source environment: **681 passed, 6 Windows symlink-privilege skips,
90.93% coverage**, retaining the 88% gate. Isolated, offline, no-project Python
3.10.20 and 3.11.15 runs each passed **297 tests, 6 privilege skips** across
robustness core/API tests without managing the existing development environment.
Ruff, the configured medium-or-higher Bandit gate, compilation, JavaScript syntax,
baseline benchmark, registry/discovery consistency, dependency compatibility
(86 packages) and fresh-cache audit (no known vulnerabilities) pass. An additional
unfiltered Bandit diagnostic reported four existing low-severity findings in
quantum-request metadata and the fixed git-provenance subprocess; these are not
new findings in this batch or a claim of zero security debt.

Source-development smoke passed original-score preservation, immutable save/
reopen/export and hosted denial; it now emits `unsafe_json_tree_rejected`,
`recorded_profile_admission_enforced` and `json_nesting_policy_enforced` for
remote installed-wheel/Docker checks. Its generated campaign/analysis are kept
under ignored `.tmp/admission-validation-source-smoke/`.

Rendered Playwright/Chromium QA at 1440x1000 and 375x900 used an owned ephemeral
loopback service with integrity-consistent in-memory metadata, not browser-made
responses or mutated artifact files. Empty profile, missing ranking, lone
surrogate and NaN each returned real HTTP 400, exposed a plain-text error,
cleared busy state, hid editor/results, blocked save/download and recovered
through keyboard refresh. Eight deliberate HTTP 400 console entries and zero
unexpected console/page errors occurred in the successful run. Healthy saved
analyses reopened/exported; retained bundle SHA-256 remained
`5de11936636e982752baf3c02b2404904dba6b06eb5e9f2a91d97c7327395ec7`.
All **51 corpus files remained byte-identical**, with no solver, AI or artifact
write. An initial QA assertion used an obsolete 29-file corpus count and failed
despite `unchanged=true`; corrected QA compares the captured baseline count and
passed on rerun. Screenshots/scripts remain under ignored
`output/playwright/admission-validation/`; no screenshot CSS or CSP changes.
The owned browser and service were stopped; user ports/browser were untouched.

Revised-head remote matrix, packaging, Docker, security/dependency checks and
one completed Copilot re-review remain required. The local fresh-wheel
Application Control restriction (WinError 4551) was not retried or bypassed.
No dependency, version, scoring, production configuration or scientific-status
change is included. PR #197 remains draft; fresh owner review and explicit
protected readiness/merge authority are required on the revised head.

## Storage identity and saved-list concurrency follow-up (2026-10-04)

Owner authorization covers one focused batch following Copilot review
`5407348262`: the reserved storage-root alias finding, the related staging-root
identity variant, and saved-list response ordering. PR #197 remains draft; no
readiness, merge, deployment or publication is authorized by this batch.

Both `_robustness` and `_pending` must resolve to their exact expected parent and
leaf before the first `mkdir`. Sibling, nested same-leaf, outside-root and loop
identities fail closed under the existing sanitized HTTP 400 contract. Missing
literal storage remains compatible; invalid staging blocks writes but does not
disable healthy saved list/load/export. The safeguard checks resolved identities
at access time; it does not claim descriptor-anchored protection from adversarial
concurrent filesystem replacement. No retained artifact is repaired in place.

Saved-list refreshes now use a separate monotonic generation. Stale successes
cannot replace the newer selector and stale failures cannot replace successful
save status/download. The latest failure still propagates to the existing warning
path. Scoring, routes, persistence formats, solver and AI boundaries are unchanged.

The ten new Python cases were red before implementation (**8 failures, 2 Windows
privilege skips**) and four new actual-callback Node races were also red. The
focused storage/missing-directory compatibility checks pass (**13 passed,
2 privilege skips**), and all **18 Node callback contracts** pass. The full
quantum-enabled source environment on CPython 3.12.14 passes **689 tests,
8 Windows symlink-privilege skips, 90.94% coverage**, retaining the 88% gate.
Isolated offline no-project CPython 3.10.20 and 3.11.15 robustness/core runs each
pass **305 tests, 8 privilege skips**, without managing the worktree environment.
Ruff, configured Bandit, compilation, JavaScript syntax, baseline benchmark,
registry/discovery consistency, 86-package compatibility and a fresh-cache audit
with no known vulnerabilities pass. Existing low-severity security debt and the
fresh-wheel Windows Application Control limitation are not asserted resolved.

The source-development smoke preserves original scores and immutable saves,
reopen/export and hosted denial. Virtual storage/staging redirects are rejected
before any writer, with healthy staging-independent reads preserved. It emits
`storage_root_identity_enforced` and
`staging_root_identity_enforced_before_writes` for installed-wheel/Docker gates.
Generated evidence is isolated under ignored `.tmp/storage-concurrency-source-smoke/`.

Rendered Playwright/Chromium acceptance passes at 1440x1000 and 375x900. An actual
pre-save GET response is fetched and held until a newer post-save GET completes;
its delayed success or deliberate transport failure cannot change the newer
selector, status or download. Four keyboard saves return real HTTP 200, reopen
successfully and download with matching bundle hashes. Zero page/unexpected
console errors, two deliberate transport-error entries and no page-wide overflow
occurred. All 29 captured original corpus files and the campaign fingerprint are
unchanged. The completed run adds four analyses (count 4 to 8); an initial QA
attempt added three, then lost keyboard focus during core initialization before
its fourth POST. The QA synchronization was corrected; all seven generated QA
saves remain retained, alongside the initial source-smoke analysis. Scripts,
hashes and unmodified-CSS screenshots are retained under ignored
`output/playwright/storage-concurrency/`. No solver or AI request is involved.

Revised-head remote qualification is recorded in the PR after completion.
Remote Linux must exercise the real-symlink cases that
cannot run with this Windows account's privileges. One completed Copilot re-review
is required after automated gates; fresh owner review and explicit readiness/
protected-merge authority are still required for the revised head.
