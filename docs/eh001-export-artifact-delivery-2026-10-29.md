# EH-001: remaining-export artifact delivery

Date: 2026-10-29. Baseline: `8f1c061285cf74aeba9058a9496311ccd9b6e0ff`.
Scope: local characterization, registration-only extraction and qualification.
No commit, PR, merge, deployment, release or scientific admission is authorized.

## Characterized and extracted boundary

The four GET handlers are:

- `/api/ai/drafts/{interaction_id}/bundle`
- `/api/campaign-studies/{template_id}/download`
- `/api/research-objects/{export_id}/download`
- `/api/workspaces/{workspace_id}/download`

**85 cases passed before production extraction.** An expanded **93-case suite**
also passes against an exact, unmodified baseline archive and the extracted
implementation. New inputs are synthetic persisted files, not retained evidence
or regenerated provider/scientific results. Downloads remain available for
session-owned persisted advisory bundles without enabling an AI provider.

Characterization covers exact bytes/media/download names, noncanonical JSON,
Markdown attachment rather than HTML execution, metadata-derived filenames,
campaign local precedence/packaged fallback, existing ID normalization, strict
AI IDs, hosted session/base-output isolation, inclusive caps, ranges, methods,
dependency overrides, lookup/guard ordering, sanitized failures and exact errors.

[`export_artifact_routes.py`](../src/qs_dmss/cockpit/export_artifact_routes.py)
uses four explicit registration functions at the original four positions. A
single insertion of all four routes would change ordering and is not used.
Structural service and response-guard dependencies avoid a reverse import into
`api.py`. Public `create_app` and `CockpitService` entry points remain intact.

AST comparison confirms identical handler bodies/decorators except for the
injected service annotation/dependency, with no other production AST changes.
Service implementations, response/security policy, generation, persistence,
serialization, provider execution, POST handlers and locks are unchanged.
The ordered API/OpenAPI is identical: **61 route entries, 56 documented paths**,
SHA-256 `8b86ad035fcffc32b601c6047f327f8012f27bd5bd6b85e868a2f024ef5c257d`.
`api.py` decreases from 2,941 to **2,900 lines**; `CockpitService` remains
**1,836 lines**. The remaining file-download registrations are now isolated;
EH-001 still includes non-download transport and serialization debt.

## Pre-existing finding: unhandled-500 response headers

The initial characterization had **82 passes and three failed header assertions**.
The unchanged outer exception handler returns sanitized JSON without the normal
baseline security, cache-control and noindex headers. This occurs for unexpected
lookup errors and some `FileResponse` failures. Error bodies remain sanitized;
no new data-disclosure or script-execution claim is made.

Tests now explicitly preserve this observed contract instead of changing policy
inside extraction. Real installed-wheel and Docker HTTP checks independently
confirm it. The gap is recorded as **EH-013**, not represented as repaired or as
successful error-response security hardening. A separate focused correction is
recommended before any deployment/release decision.

Existing missing-path handling is also mode-dependent: local missing AI bundle
files reach the generic 500; hosted missing paths are rejected by the existing
guard with a protected 404 (`Artifact not found`). Existing directories can still
reach 500s in either mode. Research-object and other service-level errors retain
their own exact contracts. No status/error normalization is bundled here.

The first HTTP helper wrongly expected the local missing-file result in both
modes. Initial attempts, wire diagnostics and helper source are retained. A first
eight-case expansion also had two incorrect directory expectations on both
baseline and candidate; only QA expectations were corrected before the final
93-case pass. Production policy was not modified to satisfy these tests.

## Local qualification

Raw QA is under `.tmp/eh001-export-artifact-delivery-20261029/`.

- Native Windows Python 3.14.3 focused gate: **460 passed**. Python 3.14 remains
  supplemental; the known Windows Rustworkx application-control limitation was
  not bypassed or claimed fixed, and no full native quantum suite was rerun.
- Final Linux Python 3.12.15 quantum-enabled suite: **1,756 passed, 7 skipped,
  91.95% aggregate statement coverage**, passing the unchanged 88% floor.
  New module: **89.19%**, with all handler statements covered and only the four
  protocol-stub bodies unexecuted. No coverage padding or exclusions were added.
- Installed-wheel gate: **460 passed**, checkout import paths disabled. Real
  loopback HTTP covers all four routes, exact attachments and headers on normal
  responses, 200/206/416, session isolation, inclusive caps and existing error
  behavior. Imports are verified under the new wheel environment's site-packages.
  The disposable wheel environment inherits the existing QA image's dependency
  closure; it is not a newly resolved independent lock.
- The unmodified Dockerfile builds. Its non-root `qsdmss` image becomes healthy
  and passes the same installed-package real HTTP cases with network `none` and
  no published ports. Hosted custom compute, AI and live quantum execution remain
  disabled. Synthetic fixture creation is not a production deployment.
- Ruff, configured medium-or-higher Bandit, compilation, all **14 JavaScript
  syntax checks** and **113 JavaScript tests** pass. Passing source scans do not
  negate the separately recorded response-header finding.
- Wheel/sdist, Twine and current CI archive assertions pass. The added module
  and test are included; unapproved admission drafts, retained local trees and
  portal MP4 are excluded. Final artifact/source bindings are recorded separately.
- Dependency consistency/audits pass: ordinary environment **92 distributions**,
  Docker runtime inventory **18**, no known vulnerabilities. Inventory pins are
  not a new frozen lock; pip-audit's non-hash-complete inventory warning is retained.
- Demo benchmark validation, frozen registry integrity and read-only discovery
  parity pass without regeneration or scientific-status promotion.

The first full Linux run, before the additional eight regressions, passed
**1,748 tests, 7 skips, 91.92% coverage**; it is not represented as covering the
later test revision. The final source snapshot and results are retained separately.
The closeout wheel's member bytes match the installed/tested wheel; final source
and test hashes are bound to the expanded Linux snapshot. Remote Python 3.10–3.13,
installed-wheel, Docker/security and owner/review gates remain separate later
requirements, not completed by this local qualification.

## Preservation and boundaries

The protection scope includes tracked files, retained records, frozen-environment
configuration/RECORD anchors and historical reparse metadata, not every frozen
environment binary. Only the authorized API/debt-register tracked edits may
differ; new module/tests and this document are uncommitted additions. Historical
QA, failed attempts and original drafts are retained rather than overwritten.
The scoped comparison checks **46,757 protected entries**, with no unexpected
changes. Both retained CERN wheel hashes and the untracked allocation-draft hash
remain unchanged.

Both retained CERN wheels, frozen evidence, environments/locks, inactive drafts,
protocols, caps, approved media and scientific statuses remain outside scope.
The original allocation draft remains untracked and unadmitted. Ordinary QA
artifacts live outside the research retention corpora; no cap is raised or moved.

EDRS/v3 remain **DEFERRED, HOLD**. Scientific validation remains
`NOT_ESTABLISHED`; independent review/human dispositions remain `PENDING`.
The full regression suite retains ordinary isolated simulator/unit-test work;
those outputs are not replacement scientific evidence or CERN/EDRS execution.
No provider call, pilot/admission, evidence regeneration, commit, PR, merge,
deployment, release, publication or outreach is performed.
