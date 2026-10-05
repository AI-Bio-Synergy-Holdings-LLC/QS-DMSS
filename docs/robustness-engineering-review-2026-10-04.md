# Recommendation robustness: pre-re-review engineering assessment

Review date: 2026-10-04, America/Mexico_City. This is an AI-assisted engineering
assessment and qualification record, not owner approval, an independent human
scientific assessment or a guarantee that another reviewer will find no issues.

## Scope and baseline

PR #197 remains draft. Clean main is
`fd38ef5e922ce968709ddc153ff0e9f31652ba4a`; this focused correction starts from
`5a5e96502f259399c24c1f9d886e7e19dcf77621` on
`codex/recommendation-robustness`. The single prior completed Copilot review
`5407668568` identified non-string display metadata reaching SVG `.slice()`
after Save was enabled. The owner authorized one display/render-state correction,
qualification and one re-review, with this engineering assessment first.

Product changes are confined to `static/robustness.js`. API routes, Python
implementation, schemas, scoring, resource limits and persistence formats are
unchanged. The new tests and installed-wheel/Docker smoke protect that boundary.
No release, deployment, hosted compute/AI activation or scientific-status change
is included. Candidate metadata remains 0.13.2, not published-release identity.

## End-to-end boundary review

The analysis/scoring modules, isolated cockpit service, UI island, shared path
and HTML-security helpers, integration points, packaging and CI contracts were
reviewed alongside the complete local test suite. The following are engineering
invariants, not stronger security or scientific claims:

| Boundary | Assessed contract and evidence |
| --- | --- |
| Recorded source → analysis | Captured metrics/identities agree with manifest-backed comparison data; optional display fields remain raw. Nine new API compatibility cases exercise source, preview, save, reopen and ZIP export. |
| Scoring | Existing goals, normalization, primary bonus, qualifications, six-decimal scores and tie breaks remain characterized. The bounded grid preserves every profile; fallback wins are not qualified wins or probabilities. |
| Admission/resources | Finite profiles, Unicode/JSON-tree checks, nesting, row/grid/file/bundle/discovery ceilings remain enforced. Missing storage, permissions, loop errors and unrelated runtime errors retain their distinct contracts. |
| Storage | Exact reserved-root identities are checked before writes; allocation retries collisions, stages saves and atomically publishes. Regression tests retain cleanup and immutable-save contracts. This is not descriptor-anchored TOCTOU isolation. |
| Read/reopen/export | Saved source and complete bundle integrity checks remain in place; discovery isolates bad summaries and intentionally does not verify every artifact. Hashes are not authenticity, malicious-replacement prevention or scientific approval. |
| UI concurrency | Existing source/preview/save/list generations and duplicate-save guards are retained. All actual-callback race/error tests pass. Editor preparation and rendering now precede committing an actionable result. |
| Label/text rendering | One display-only nonblank-string fallback is used everywhere. Hostile strings stay literal via text nodes; non-string labels fall back to a name/run ID without rewriting evidence. |
| Rendering failure | Save/download are disabled before rendering; exceptions clear partial state/output and permit explicit recovery. A failed saved editor cannot replace the active source or expose incomplete controls. |
| Hosted/compute boundary | Hosted robustness access remains denied. The island calls only recorded-source/analysis endpoints, not solvers or AI. Hosted graph and AI settings are unchanged. |
| Reports/security | Same-origin framing is limited to report/workbook previews; cockpit/API/download denial remains. Fixed current/legacy script hashes and bounded style admission do not enable arbitrary inline scripts. Existing CSP tests remain part of the full suite. |
| Distribution | Static revision hashing covers the island; package data and source-distribution rules retain code/tests/docs. New smoke flag `raw_display_fields_preserved` checks accepted raw fields and scoring fidelity in installed-wheel/Docker environments. |

## Regression qualification

The new actual-source Node contracts were red before the product fix:
**12 failures / 25 passes**. Afterward all **37 pass**. Fourteen label cases
render actual SVG/table code at desktop/mobile widths, preserve analysis data,
and cover strings, meaningful spaces, blank/whitespace, null, object, array,
number, boolean, missing fields and hostile Unicode. Additional cases check
render-time action gating, preview/saved failures and recovery, prevention of
Save after failed rendering, and saved-editor/source isolation.

The nine new Python compatibility cases pass. The full local quantum-enabled
CPython 3.12.14 suite passes **736 tests / 25 Windows symlink-privilege skips /
90.95% coverage**, retaining the 88% gate. Isolated offline no-project Python
3.10.20 and 3.11.15 each pass **352 robustness/core tests / 25 privilege skips**.
Ruff, configured medium-or-higher Bandit, dependency compatibility, a fresh-cache
audit with no known vulnerabilities, compilation, JS syntax, baseline benchmark
and challenge-registry/discovery consistency pass. Source-development smoke
passes all existing flags and the new raw-display compatibility flag.

Real OS loop cases unavailable to this Windows account must execute on Linux.
Latest-head remote matrix, all-OS installed wheels, Docker, security and dependency
gates must be checked before the single Copilot re-review. Exact commit, artifact
hashes and remote results are recorded on PR #197 after completion, avoiding
self-referential artifact identities in the packaged source record.

## Rendered acceptance and retained evidence

An owned ephemeral loopback service uses fresh isolated campaign evidence and
manifest-consistent in-memory label variants, not fabricated browser responses.
Playwright/Chromium at 1440×1000 and 375×900 exercises object, array, numeric,
boolean, whitespace and hostile-Unicode metadata. Six real keyboard saves,
read-only reopens and UI ZIP downloads pass; download hashes and retained raw
comparison/analysis fields match. Programmatic duplicate clicks issue no second
save. Original 29 corpus files and the healthy source fingerprint are unchanged.

A deliberate one-shot DOM chart failure follows an actual successful preview:
partial output/actions fail closed and keyboard update recovers. Actual stale-pin
409 and tampered-manifest 400 responses block Save and recover. The completed
acceptance run has zero page/unexpected console errors, four deliberate HTTP
error entries and no page-wide overflow. No solver or AI request occurs.

The completed run adds six analyses (count 6→12). Earlier QA attempts retained
five saves before a synchronization/HTML `open`-attribute assertion problem;
all generated QA evidence is preserved. QA corrections also respect the explicit
ZIP root prefix and the existing rejection of a grid that removes every positive
weight; they are not product changes or suppressed failures. The workflow pass
additionally checks live profile redraw, tracking a nonrecommended candidate,
17-point grid, explicit qualification fallback, invalid-profile Save denial,
recovery and named/focusable table regions, without more saves.

Scripts, screenshots, downloads and hash checks are retained under ignored
`output/playwright/label-render-e2e/`; source-smoke evidence is under ignored
`.tmp/label-render-source-smoke/`. No screenshot CSS or CSP was injected. Owned
QA processes are stopped after acceptance; user services/browser are not changed.

## Disposition and honest limits

The confirmed label/render-state defect is corrected within the authorized
scope. No further high-confidence blocking implementation defect was identified
by this bounded assessment; a fresh reviewer can still identify omissions.
Review comments, including summary-only previously missed findings, must be
assessed after the one re-review, not inferred from workflow success.

Separate debt remains: the Windows fresh-wheel Application Control restriction
(WinError 4551; no retry/bypass), hidden discovery-only busy-state polish,
pre-existing low-severity security diagnostics, architecture/supply-chain decisions
in the engineering-health register and independent scientific assessment under
#183. None is represented as resolved here. Keep PR #197 draft pending fresh
owner review and explicit readiness/protected-merge authorization.
