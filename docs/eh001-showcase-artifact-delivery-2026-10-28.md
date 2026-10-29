# EH-001: showcase-artifact delivery boundary

Date: 2026-10-28. Baseline: `16dca7b863a2f4c473c555bbbb8c0960d5fb0311`.
This records local implementation/qualification, not commit/PR preparation,
merge, deployment, release, scientific admission or independent assessment.

## Characterization and extraction

Before production edits, **85 characterization cases passed** for:

- `/api/showcases/{scenario}/report`
- `/api/showcases/{scenario}/report.json`
- `/api/showcases/{scenario}/artifacts/{artifact_name}`

Synthetic fixtures cover Markdown and noncanonical JSON report bytes, SVG, CSV,
binary, uppercase-suffix and HTML-file attachment behavior. Contracts include
exact media types/download names, no-store/noindex/security headers, local and
hosted behavior, inclusive caps, session isolation, missing outputs without
generation, range/unsatisfiable-range responses, dependency overrides, guard
ordering, sanitized failures and complete ordered route/OpenAPI identity.

Existing scenario aliases and artifact-basename normalization, including the
default artifact name, remain characterized behavior. They are not changed into
new strict rejection rules or presented as a new security policy. These fixtures
show that normalized aliases resolve inside the expected artifact directory.

The three registrations move to
[`showcase_artifact_routes.py`](../src/qs_dmss/cockpit/showcase_artifact_routes.py)
at their original ordered position, using a structural service protocol and
injected file-response guard without importing `api.py` back into the module.
AST comparison confirms identical handler bodies/decorators except for the
injected dependency and service annotation. The complete route/OpenAPI snapshots
remain identical: **61 entries, 56 documented paths**, SHA-256
`8b86ad035fcffc32b601c6047f327f8012f27bd5bd6b85e868a2f024ef5c257d`.

`create_app` and `CockpitService` remain compatibility entry points. Artifact
lookup/normalization, generation, caching, session selection, execution,
serialization and security/download policies remain in their previous owners.
The distinct quantum-validation delivery policy is outside this increment.
`api.py` decreases from 3,006 to **2,968 lines**; `CockpitService` still spans
**1,836 lines**. EH-001 remains open.

## Local qualification

Raw QA is retained under `.tmp/eh001-showcase-artifact-delivery-20261028/`.

- Native Windows Python 3.14.3 focused gate: **283 passed**.
- Full Linux Python 3.12.15 quantum-enabled suite: **1,543 passed, 7 skipped,
  91.79% aggregate statement coverage**, passing the unchanged 88% floor.
  New module: 90% coverage, with all handlers covered and three protocol-stub
  bodies unexecuted. No coverage-padding calls or exclusions were introduced.
- Installed-wheel gate: **263 passed**, with checkout imports disabled and both
  API/delivery imports verified under the wheel environment's `site-packages`.
  This isolated wheel environment inherits the existing disposable QA image's
  dependencies; it is not an independently resolved dependency closure.
- Real installed-wheel loopback HTTP acceptance passes across all three routes
  and seven content representations: exact bytes/media/download behavior,
  200/206/416 responses, separate cookie jars and peer/base-output denial.
  Only synthetic files are served; no showcase computation is needed.
- Wheel/sdist builds, Twine and current CI archive-content assertions pass.
  Exact new source/test membership is checked; local retention trees,
  unapproved admission drafts and portal MP4 files are excluded.
- Ruff, configured medium-or-higher Bandit, isolated package/test compilation,
  all 14 tracked JavaScript syntax
  checks and **113 JavaScript tests** pass. Base and installed-wheel dependency
  consistency pass; the ordinary 92-package environment audit reports no known
  vulnerabilities. No dependency declarations or frozen locks change.
- Registry and discovery checks pass without regeneration: three challenges,
  89 candidate cases and 89 retained cross-tool comparisons remain unchanged.
- The unmodified Dockerfile builds successfully. The local image runs as
  non-root `qsdmss`, becomes healthy and passes real HTTP checks for all three
  routes/seven content representations, including ranges, exact security/media
  behavior and session isolation. Network is `none`, with no published ports.
  The separately inventoried 18 installed runtime distributions pass dependency
  consistency and a pinned-inventory advisory audit with no known vulnerabilities.
  This inventory is QA evidence, not a new frozen lock or reproducibility policy.
  An interrupted NumPy transfer was automatically resumed within the original
  build; the successful build and warning history remain retained. No dependency,
  network-mode or recipe change was needed.

No full native Windows quantum suite was rerun; its existing Rustworkx
application-control restriction is neither fixed nor bypassed. Python 3.14 is
supplemental evidence, not newly supported. Remote Python 3.10–3.13, candidate
wheel, Docker/security and owner/review gates remain separate later requirements;
this local pass does not authorize a commit, PR or protected merge.

## Preservation and boundaries

Approved wheels, frozen evidence, historical QA, inactive drafts, media,
protocols, locks/environments, caps and scientific statuses are outside the
change scope. QA distributions are unpublished engineering artifacts, not
replacements for either retained CERN wheel or changes to a candidate pin.

A scoped before/after comparison checks **46,751 protected entries** with no
unexpected changes; only the authorized tracked API/debt-register edits differ.
The new module, tests and this record are additional uncommitted files. Both
retained CERN wheel hashes and the existing untracked allocation draft remain
unchanged.

The preservation comparison checks tracked/retained files and frozen environment
configuration/RECORD anchors. Historical reparse fixtures are compared as metadata,
not followed; this does not claim to hash every frozen environment binary.
The pre-existing allocation draft remains untracked and unadmitted. Frozen
environments and inactive drafts are not executed by this pass.

EDRS/v3 remain **DEFERRED, HOLD**. Scientific validation remains
`NOT_ESTABLISHED`; independent review and human dispositions remain `PENDING`.
Hosted graph execution and AI policy are unchanged. No commit, PR, merge,
deployment, release, publication, outreach or research pilot is performed.
