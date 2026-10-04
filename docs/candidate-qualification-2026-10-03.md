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
