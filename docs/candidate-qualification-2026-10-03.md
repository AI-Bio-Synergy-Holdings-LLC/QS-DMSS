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
