# EH-001: run-artifact delivery boundary

Date: 2026-10-27 (local). Baseline: `ec6453d49e7c41363dad0bf3e82a16c351552f33`.
This records local qualification performed before commit/PR preparation, not
merge, deployment, release, admission, or independent scientific approval.

## Scope and characterization

Before production edits, 43 HTTP characterization cases passed against the
existing `create_app` implementation. They cover these four GET routes:

- `/api/runs/{run_id}/bundle`
- `/api/runs/{run_id}/review-bundle`
- `/api/runs/{run_id}/state-bundle`
- `/api/runs/{run_id}/report`

The characterized contracts include status and error bodies, content types,
download names, byte delivery, range/unsatisfiable-range responses, security
headers, inclusive hosted download ceilings, session isolation, dependency
overrides, guard ordering, ZIP member ordering, optional graph artifacts,
lazy generation, cache reuse, and sanitized unexpected failures.

The handlers now live in
[`artifact_routes.py`](../src/qs_dmss/cockpit/artifact_routes.py), registered
directly at their original position through an injected service dependency
and file-response guard. A small structural service protocol avoids importing
`api.py` back into the extracted module. `create_app` and `CockpitService`
remain compatible public entry points.

Session selection, hosted limits, security middleware, report CSP generation,
artifact lookup/assembly, experiments, serialization, and execution remain in
their existing owners. In particular, profile generation still precedes the
download guard, and an existing cached profile is still reused without source
freshness invalidation. Those are preserved behaviors, not newly endorsed
resource/freshness policies.

An initial included-router implementation changed route introspection under
the installed FastAPI version. Characterization caught it; direct registration
preserves the full ordered route table and OpenAPI instead. Both before/after
JSON snapshots have SHA-256
`8b86ad035fcffc32b601c6047f327f8012f27bd5bd6b85e868a2f024ef5c257d`
(61 route entries, 56 documented paths).

## Qualification

QA outputs are retained separately under
`.tmp/eh001-artifact-delivery-20261027/`. Failed/intermediate attempts remain
there and are not represented as successful qualification.

- Windows Python 3.14.3 focused delivery/service/report-security gate:
  **79 passed**.
- Full Linux Python 3.12.15 quantum-enabled gate: **1,359 passed, 7 skipped,
  91.70% aggregate coverage**. The new delivery module has **100% statement
  coverage**; the enforced 88% floor passes.
- Full Windows Python 3.14.3 gate: **1,335 passed, 27 skipped, 4 failed**. The
  four quantum failures encounter the existing native Rustworkx DLL
  application-control restriction. This is not a green full Windows result;
  application control is not bypassed and coverage is not waived (87.44%, below
  the 88% floor).
- Isolated installed-wheel delivery/service gate: **47 passed**; imports resolve
  to `site-packages`, with checkout import paths disabled.
- Installed-wheel loopback HTTP acceptance passes for all four GET routes and
  partial requests, including content types, no-store/noindex, nosniff and the
  distinct report-preview framing policy. Only synthetic files are served.
- Installed-wheel `demo-baseline` benchmark and dependency consistency pass.
- Ruff, medium-or-higher Bandit, Python compilation and JavaScript syntax pass;
  **113 JavaScript tests pass**. Registry integrity and discovery checks pass
  without changing scientific statuses or regenerating frozen evidence.
- QA wheel/source archive build and Twine metadata checks pass. Archive checks
  confirm the new module/test membership and exclusion of local retention
  trees, unapproved allocation drafts and portal MP4 media.
- The installed base-runtime closure (16 pinned distributions) has **no known
  vulnerabilities** in the recorded audit. This does not certify all optional
  environments or future dependency resolutions.
- The broader Windows tooling audit is **not clean**: `msgpack 1.2.1` is flagged
  as `CVE-2026-114613` / `GHSA-j586-36cw-2gc2`, with reported fix `1.2.3`.
  Its local dependency chain is `pip_audit -> CacheControl -> msgpack`; it is
  absent from the installed base runtime closure. No dependency or lock changes
  are bundled into this compatibility extraction.

The supported remote Python 3.10-3.13, CodeQL, packaging/Docker and review gates
remain PR requirements. No remote qualification is claimed by this local
record; remote results must be checked against the PR's exact head commit.

## Preserved artifacts and boundaries

Both retained CERN wheels remain byte-identical:

- Approved rebuilt wheel:
  `6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60`.
- Original wheel:
  `b8434593e6b34abda2536e0c5752e5ade253d76a083537a34fb84d3b6b70974e`.

The pre-existing untracked `source-allocation-v3-r2.json` remains at
`0b0be1b9f10c15c8603b7de790416f94a832120e1a3aa2cea993c00d5544fc26`.
No research protocol, budget, lock, approved media, evidence or inactive draft
is edited. Ordinary repository QA outputs are not CERN/EDRS protocol records.
EDRS and v3 remain deferred and **HOLD**. Scientific validation remains
`NOT_ESTABLISHED`; independent review remains `PENDING`. Hosted graph execution
and AI policy are unchanged.

## Separate follow-ups, not changes in this increment

1. The existing hosted-session generator can emit a leading/trailing hyphen
   from `token_urlsafe(18)`, while its validator requires equality with
   `safe_filename`, which strips boundary hyphens. A retained failed delivery
   attempt observed a trailing-hyphen session replaced on its next request.
   New delivery fixtures therefore use a deterministic valid session cookie
   scoped to the TestClient host. Correcting and characterizing session-ID
   generation is a separate small behavior-changing task.
2. Remediate and re-audit the local tooling-only `msgpack` advisory separately;
   do not infer that an audit-tool dependency is a deployed runtime dependency.
3. EH-001 stays open for the remaining transport and serialization boundaries.
   Profile-generation resource bounding/cache freshness require separate
   decisions rather than silent changes during route extraction.

The local qualification pass performed no staging, commit, push, PR, merge,
deployment, release or scientific admission. Subsequent owner-authorized
commit/PR preparation does not authorize merge, deployment or release.
