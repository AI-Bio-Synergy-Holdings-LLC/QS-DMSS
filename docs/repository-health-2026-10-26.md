# Repository engineering-health sweep — 2026-10-26

## Scope and baseline

This is a bounded engineering survey and repair record, not a guarantee that
the repository has no undiscovered defects, a release approval, or scientific
validation. Historical evidence, approved wheels, inactive drafts and their
HOLD/deferred statuses are outside the repair scope.

- Starting `main` and freshly fetched `origin/main` both identified
  `a977d60b3dc04e05bfe29f171b4524ca5138d8ba` (PR #211).
- The checkout was not completely clean: `.local/` retention material and
  `research/cern_dimuon_qualification/admission/contracts/source-allocation-v3-r2.json`
  were already untracked. Neither was admitted or changed by this sweep.
- Repairs are on `codex/engineering-health-20261026`. No commit, push, PR,
  merge, deployment or publication is part of this record.
- GitHub reported no open PRs and zero open code-scanning, Dependabot or
  secret-scanning alerts at inspection time. This is an observed alert state,
  not proof of absence of vulnerabilities.
- Baseline main CI passed Python 3.10–3.13, quantum-sidecar and Docker jobs
  in [run 39870686205](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/actions/runs/39870686205).
  CodeQL, Code Quality and organization-policy runs also passed. Production
  verification was intentionally cancelled for the approved no-deployment
  merge; it must not be reported as a successful deployment check.

## Confirmed findings and repairs

| Finding | Evidence | Local correction |
| --- | --- | --- |
| Ambiguous recorded robustness JSON | Duplicate object members silently used the last value, including escaped-equivalent keys. | Reject duplicate decoded keys at every object level; route-level regressions cover source, preview, save, reopen, export and listing behavior. |
| Invalid Unicode evidence keys | The dimuon decoder checked dictionary values but accepted escaped lone-surrogate keys. | Validate keys and values with the existing UTF-8 and nesting policy; test root/nested invalid keys and valid Unicode round trips. |
| Demo output escaped the working directory | Two existing tests failed when their temporary working directories were nested inside a checkout. Repository discovery redirected output to the ancestor repository. | Both demo CLI entry points explicitly default to the current directory's `runs/`; preserve explicit roots and non-demo campaign behavior. Add nested-repository regressions. |
| Unreviewed source-archive member | A real baseline sdist included the existing untracked `source-allocation-v3-r2.json` via a recursive manifest rule. | Allow only the four reviewed admission-contract JSON files. Assert the exact member set in CI and regression tests. Preserve the local draft unchanged. |
| Overbroad Docker context and retention ignore | The context exclusion list did not cover `.local/`, `.tmp/` or general credential files. | Default-deny Docker context with explicit build inputs, plus bytecode/environment exclusions; ignore the whole local-retention directory in Git. No retained files were deleted. |
| Sticky navigation obscured nested Lab anchors | Mobile evidence navigation placed its heading beneath the sticky rail because the scroll-offset rule only covered section/details elements. | Apply the existing offset to the two nested Lab targets and add a selector/anchor regression. |
| Documentation check traversed hidden retention trees | The link test used recursive globbing and only excluded hidden paths after visiting them. The Docker bind-mount run stalled in filesystem traversal. | Prune hidden directories before descent, preserving the public-document scan; a guarded-scandir regression fails if a hidden directory is entered. |
| Stale ordinary development environment | Installed editable metadata said 0.13.2 while source declared 0.14.0; the build prerequisites were missing. Seven advisory records affected certifi, filelock and urllib3. | Refresh only the ordinary `.venv`, install build prerequisites, and reinstall the current editable package without changing runtime requirement ranges or frozen locks. |

The refreshed ordinary environment uses certifi 2026.10.23, filelock 4.2.4
and urllib3 2.8.0. Dependency audit and `pip check` pass. A newly created
wheel-smoke environment initially inherited pip 25.3 from Python's bundled
bootstrap; upgrading that disposable environment to pip 26.2.2 cleared its
audit as well. Neither environment is a frozen CERN qualification environment.

## Qualification

- Native Windows Python 3.14.3 final full suite: **1,279 passed, 27 skipped**, with
  **91.70% statement coverage** against the enforced 88% floor. The baseline
  had two failures, 1,256 passes and 27 skips. Python 3.14 remains supplemental
  evidence, not an addition to the supported Python 3.10–3.13 matrix.
- Fresh Linux Python 3.12.15 quantum-enabled full suite: **1,299 passed,
  seven skipped**, **91.66% coverage**, 117.25 seconds. The platform-dependent
  skips remain skips, not passes.
- Focused repair suite: **472 passed, 26 skipped**.
- JavaScript state, research-object and graph-explorer tests: **113 passed**.
- Configured Ruff and medium-or-higher/medium-confidence Bandit gates pass.
  All tracked JavaScript syntax checks pass.
- Static parsing: 137 Python files, 41 JSON files (duplicate-key checking),
  38 YAML files and one TOML file parsed without errors.
- Wheel and sdist build and Twine checks pass. The complete CI archive-content
  assertions pass against the actual built files: 111 wheel members and 389
  sdist members in the closeout build, including the public Docker/ignore
  fixtures needed by the new packaging regressions; no portal MP4, `.local/`, `.tmp/` or unreviewed admission
  contract in the inspected archives.
- Fresh installed-wheel checks run outside the checkout pass: synthetic
  dimuon import/analysis/recomputation/retention, data-only diagnostics pack,
  and robustness source/preview/save/reopen/export/resource/error contracts.
- Installed quantum-extra checks pass for the sidecar and all 12 compilation
  rows. Execution-policy assertions confirm local simulators, no credential
  reads, no remote API, no submission and zero authorized QPU cost. These are
  engineering smoke results, not physical-validation claims.
- The rebuilt Docker image starts as `qsdmss`, becomes healthy, serves HTTP
  200 and supplies the expected baseline response-security headers.
- An isolated local cockpit completed a packaged run, manifest verification
  and deterministic replay. Chromium checks at 1440×1000 and 390×844 showed
  correct application identity, readable workflow/evidence content, no page
  horizontal overflow and no console warnings/errors. The mobile navigation
  remains intentionally horizontally scrollable. This is not a new physical
  iPhone/VoiceOver certification or an exhaustive accessibility audit.
- Registry and discovery consistency checks preserve three challenges,
  89 candidate cases and 89 cross-tool comparisons, with scientific status
  `NOT_ESTABLISHED` and independent review `PENDING`.
- A before/after byte-count and SHA-256 comparison of 629 protected local
  records, drafts and the two retained wheels found no differences.

Local QA outputs are retained in `.tmp/engineering-health-20261026/` and
browser captures in the user's temporary directory. The baseline sdist in
`before-dist/` is a rejected audit artifact because it contains the local
draft; it must never be published. Rebuilt artifacts are also QA-only, not
authorized replacements for either approved historical wheel. No inactive
EDRS/C32/v3 launcher, pilot or qualification attempt was executed.

The first Linux full-suite attempt was interrupted after 967 passes and two
skips at 833.99 seconds, while the old documentation traversal waited on the
Windows bind mount (`p9_client_rpc`). It is an incomplete run, not a passing
gate. After the pruning correction, the Windows governance suite completed
11 tests in 0.20 seconds. Linux closeout uses a 7,633,920-byte source snapshot
containing current tracked working-tree files plus this audit record, extracted
on container-native storage; it does not copy `.local/`, environments or the
untracked admission draft. Both original test outcomes remain part of this
record rather than being replaced by a successful retry.

## Public and origin posture

Read-only HTTPS checks returned 200 for both public surfaces. The portal
reported v0.14.0 at `719acb823a8914786f2a7ce065566fd340d6314a`; the app reported
v0.14.0 at `c158c3ba3f81cadf7d11bdfcab3441c8d99be851`. Both supplied CSP,
frame protection, nosniff, Referrer-Policy and HSTS. Hosted AI, live quantum
execution and custom compute remained disabled. These older deployment pins
are consistent with the subsequent no-deployment work; neither is represented
as deployed current main. No Render configuration was changed.

Origin does not contain these uncommitted repairs. Its passing baseline
workflows cannot qualify a later repair branch. A focused protected PR must
pass the supported Python matrix, packaging/installed-wheel and Docker gates,
CodeQL, dependency review, policy checks and owner review before a merge can
be considered. Deployment, if desired, requires its own scope decision.

## Prioritized remaining debt

| Priority | Next decision/work | Boundary |
| --- | --- | --- |
| P1 | Review and remotely qualify these repairs, especially archive membership and parser compatibility. | No automatic merge, deployment or release. Preserve untracked/frozen materials. |
| P1 | Address EH-010 branch-governance gap: administrators can bypass protection and zero approving reviews are required. | Owner/organization policy decision; no unilateral protection changes. |
| P0 architectural debt | Continue EH-001/EH-002 incremental extraction of the cockpit API and CLI. | Existing register priority is unchanged. Characterize contracts first; no large decomposition in this security/quality patch. |
| P1 | Continue EH-003 rendering-boundary extraction and EH-006 direct server-entry-point/error-branch coverage. | Runtime/browser smoke reduces uncertainty but does not erase the remaining coverage gaps or skips. |
| P1/P2 | Resolve EH-005 reproducible dependency/container policy and EH-008 immutable Action pins. | Existing priorities remain P1/P2 respectively. Passing audits are point-in-time; frozen evidence locks must not be silently rewritten. |
| P1 | Reconcile intended production revision and EH-007 observability checks after the no-deployment series. | Public health checks do not certify private alert delivery or a new deployment. |
| Separate gate | Scientific assessment under #183 and the existing licensing/legal decisions. | No change to scientific approval, evidence interpretation or release scope. |

EDRS and v3 remain deferred and HOLD. Resolving ordinary engineering findings
does not admit either path or close the independent scientific-review gate.
