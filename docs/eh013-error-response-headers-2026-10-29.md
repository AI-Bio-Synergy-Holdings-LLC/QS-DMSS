# EH-013: unhandled-error response headers

Baseline: `05b6a2256e6bf582b48596b990a80ffc157d86d3` (PR #219).
Scope: characterize, correct and qualify locally. No commit, PR, merge,
deployment, release or scientific admission is authorized.

## Characterization and correction

The original 93-case export characterization passes before production changes.
The new 37-case EH-013 suite initially reports 29 failures on absent response
headers and eight passing compatibility cases. Raw attempts remain under
`.tmp/eh013-header-correction-20261029/`; they are not scientific evidence.

The unhandled-exception handler is reached by Starlette's outer
`ServerErrorMiddleware`, after normal HTTP middleware has unwound. Its fresh,
sanitized JSON 500 therefore previously omitted the cockpit's response headers.
The correction shares the existing header-policy implementation between that
handler and normal middleware, without changing the policy values or precedence.

Security headers remain defaults, preserving route-specific report sandbox CSP.
`/api/` retains `Cache-Control: no-store`; the existing API/docs/redoc/OpenAPI
prefixes retain noindex directives. Non-API cache/index rules are not broadened.
No exception strings, internal paths or tracebacks enter the client JSON body.
The existing structured cockpit log retains method, path and exception type,
not exception text. This does not remove Uvicorn's independent server tracebacks.

Status/body contracts, download guards, content disposition/ranges/caps, session
generation/refresh and exception propagation remain unchanged. An outer 500
still does not set a hosted-session cookie. Existing missing-file behavior
remains local generic 500 versus hosted guarded 404. A response that has already
started is not replaced with a JSON 500 or a second response-start message.

The export suite's formerly header-deficient 500 assertions are updated to the
approved header correction, while preserving exact error status and detail.
The historical characterization receipts and previous qualification document
remain unchanged.

## Qualification

- Fresh full Linux Python 3.12.15 quantum-enabled suite: **1,793 passed,
  7 skipped, 91.95% aggregate statement coverage**, passing the unchanged 88%
  floor. No new skip, coverage exclusion or threshold change is introduced.
- Native Windows Python 3.14.3: **502 passed** across cockpit API, all five
  artifact-delivery groups, EH-013 and report security; a separate **62 passed**
  covers sessions, workspaces and campaigns. Python 3.14 remains supplemental,
  not an expansion of the supported Python matrix or a full native quantum run.
- Installed-wheel Linux Python 3.12.15: **564 passed**, checkout import paths
  disabled and imports verified under the disposable wheel environment's
  site-packages. Its dependency closure comes from the existing ordinary QA
  image, not a newly resolved or frozen research lock.
- Native Windows source, installed Linux wheel and the freshly built Docker
  runtime pass real loopback HTTP checks in local and hosted modes. These cover
  fresh protected 500s, authored 409s, report CSP, actual missing/directory AI
  downloads, cookie continuity, server survival and incomplete started streams.
  The unmodified Dockerfile produces a healthy non-root `qsdmss` runtime with
  network `none`, no published ports and installed API bytes matching source.
- Ruff, medium-or-higher Bandit, compilation, dependency consistency, Twine,
  wheel/sdist membership and current CI archive assertions pass. The ordinary
  environment audit covers **92 distributions**, and the Docker runtime has
  **18 distributions** (17 audited non-project pins), with no known advisories
  reported. These inventories are not new hash-complete dependency locks.
- All **14 JavaScript syntax checks**, **113 JavaScript regressions**, demo
  benchmark validation, frozen-registry integrity, six-file read-only discovery
  parity and social-card source parity pass. Numerical evidence is not regenerated.
- The complete ordered API/OpenAPI is structurally identical: **61 route entries
  and 56 documented paths**. AST comparison confirms the header-policy statements
  are unchanged and the remainder of production implementation is unchanged.
- Static-site/release-document contracts: **41 passed** after the qualification
  record was drafted; final documentation is checked again during closeout.

The initial full Linux attempt is retained as **incomplete**, including its
synthetic-preflight failure. Pytest could import from the source tree, but the
preflight's child interpreter could not import `qs_dmss`; its retained worker log
reports `ModuleNotFoundError`. This was a disposable QA bootstrap error, not a
CERN source correction. The attempt was stopped without erasing outputs. A fresh
container installs the candidate wheel before rerunning the full suite, with
distinct output paths and no changes to research code, tests or limits.

The fresh full suite passes after that bootstrap correction. The earlier
incomplete attempt and its original failure outputs remain intact. The full-suite
snapshot predates the final documentation receipt; production and test bytes are
bound separately against the snapshot. Final package receipts retain the updated
documentation without presenting preparation artifacts as a published release.

Remote Python 3.10–3.13, CodeQL, dependency review and owner/Copilot review are
separate later gates; local qualification does not claim those gates or public
deployment. EH-013 is locally mitigated, not administratively closed or shipped.

## Preservation

Retained CERN wheels, protocols, frozen evidence/environments/locks, inactive
drafts, approved media and scientific statuses are outside this change. Ordinary
QA runs use new output paths, not the constrained research corpora. No research
allocation, cap or budget is changed. EDRS/v3 remain **DEFERRED, HOLD**;
scientific validation remains `NOT_ESTABLISHED` and independent human review
remains `PENDING`. Unit-test simulator fixtures are not new scientific evidence,
real-data pilot execution or admission. No provider call, deployment, publication
or outreach is performed.

The scoped before/after comparison covers **46,760 protected entries**: tracked
and retained files, frozen environment configuration/RECORD anchors and historical
reparse metadata, not every frozen environment binary. Only the authorized API,
export-test and debt-register paths may differ. The new regression module and
this receipt are separately scoped additions. Both retained CERN wheel identities
and the original untracked allocation-draft identity must remain unchanged.
