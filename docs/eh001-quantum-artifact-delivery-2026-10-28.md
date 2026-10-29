# EH-001: quantum-validation artifact-delivery boundary

Date: 2026-10-28. Baseline: `c2c7b0814892e2d14725ab68201cf64a182cf271`.
This is local engineering characterization, extraction and qualification only.
It does not authorize commit, PR, merge, deployment, release, pilot admission or
scientific approval.

## Characterization before extraction

**120 cases passed against the unchanged production implementation** for:

- `/api/quantum-validation/files/{artifact_name}`
- `/api/quantum-validation/runs/{run_id}/files/{artifact_name}`

All new fixtures are synthetic. They cover the six allowlisted artifact formats
and their key/filename aliases; exact bytes, media types and attachment names;
local and hosted behavior; inclusive hosted caps; hosted denial of local-run
files; ranges and unsatisfiable ranges; missing files/directories; strict alias
and run-ID errors; dependency overrides; resolver/key/guard ordering; sanitized
unexpected failures; GET-only behavior; ordered routes and OpenAPI.

The first characterization run had **118 passes and two test failures**: its
expectation incorrectly applied the inline HTML preview CSP to an unsatisfiable
range response. Starlette emits a separate 416 error response with the baseline
CSP. Only the assertion was corrected, then all 120 cases passed before any
production edit. Both runs are retained. No production policy was changed to
make the tests pass.

Characterization also preserves existing details rather than silently changing
them: an unknown local-run lookup may create an empty `quantum-validations/`
directory, and unexpected key-resolver `ValueError` handling differs between the
two handlers. Synthetic overrides exercise that exception contract without
making invalid real artifacts newly downloadable.

## Extracted boundary

The two registrations move to
[`quantum_artifact_routes.py`](../src/qs_dmss/cockpit/quantum_artifact_routes.py)
at their original ordered position. A structural service protocol, the existing
service dependency, and injected response/key callbacks avoid a reverse import
from the extracted module into `api.py`.

The distinct `quantum_validation_file_response` remains in its original
application owner. Inline HTML retains its restrictive script-free preview CSP;
other formats retain their existing guarded attachments. No response policy is
consolidated or weakened. `CockpitService`, path resolution/allowlists, download
caps, runtime/status endpoints, POST execution, active-run locking, generation,
freshness/lineage, caching and serialization are unchanged.

AST comparison confirms identical handler bodies/decorators except for the
injected service annotation/dependency and confirms no other production AST
changes. The complete ordered API/OpenAPI shape is identical: **61 route entries,
56 documented paths**, SHA-256
`8b86ad035fcffc32b601c6047f327f8012f27bd5bd6b85e868a2f024ef5c257d`.
`api.py` decreases from 2,968 to **2,941 lines**; `CockpitService` remains
**1,836 lines**. EH-001 is not closed by this extraction.

## Local qualification

Raw QA is retained under `.tmp/eh001-quantum-artifact-delivery-20261028/`.

- Native Windows Python 3.14.3: **347 delivery/session tests plus two existing
  quantum API regressions pass**. The latter use a fake validator, not a live
  harness run. Python 3.14 is supplemental, not a newly supported interpreter.
- Full Linux Python 3.12.15 quantum-enabled suite: **1,663 passed, 7 skipped,
  91.88% aggregate statement coverage**, above the unchanged 88% floor.
  New module: **91.67%**, with every handler statement covered and only the two
  protocol-stub bodies unexecuted. No coverage padding or exclusions were added.
- Installed-wheel regression gate: **349 passed**, with checkout import paths
  disabled. Real loopback HTTP acceptance covers both routes, six formats, both
  aliases, exact bytes/media/attachment/security behavior, 200/206/416 responses,
  inclusive hosted caps and denial of hosted local-run access. API/module imports
  are verified under the new wheel environment's `site-packages`.
- That disposable wheel environment inherits the existing QA image's dependency
  closure; it is not a newly resolved independent lock. It does not modify or
  execute frozen CERN environments.
- Wheel/sdist builds, Twine and the current CI archive-content assertions pass.
  New module/test membership and exact source bytes are checked. Unapproved
  admission drafts, local retention trees and portal MP4 files are excluded.
- The unmodified Dockerfile builds. The image runs as non-root `qsdmss`, becomes
  healthy, and passes the same real HTTP checks from installed package imports.
  Local QA containers use network `none`, no published ports, and synthetic
  temporary files. Hosted custom compute, hosted AI and hosted live quantum
  execution remain disabled.
- Ruff, configured medium-or-higher Bandit, package/test compilation, all
  **14 JavaScript syntax checks** and **113 JavaScript tests** pass.
- Dependency consistency/advisory checks pass: **92 distributions** in the
  ordinary environment and **18** in the Docker runtime inventory, with no known
  vulnerabilities. The latter is an inventory audit, not a new frozen lock;
  pip-audit's warning about non-hash-complete inventory pins is retained.
- Demo benchmark validation, registry integrity and read-only discovery parity
  checks pass. The three challenges, 89 candidate cases and 89 retained
  cross-tool comparisons are unchanged; these checks are not new calculations
  or scientific approval.

The existing native Windows Rustworkx application-control limitation was not
bypassed or claimed fixed. No full native Windows quantum gate was rerun.
Supported remote Python 3.10–3.13, installed-wheel, Docker/security and owner/review
gates remain separate requirements for any later authorized PR.

## Preservation and limits

Both approved CERN wheels, frozen evidence, historical QA, environments/locks,
inactive drafts, protocols, caps, approved media and scientific statuses remain
outside the change scope. QA distributions are unpublished engineering artifacts,
not replacements for retained wheels, candidate pins or scientific evidence.

The scoped preservation check covers **46,754 protected entries**: tracked files,
retained local records, frozen-environment configuration/RECORD anchors and
historical reparse metadata. It does not claim to hash every frozen environment
binary. Only the authorized tracked API/debt-register edits differ; the new
module, test and this record are additional uncommitted files. The existing
allocation draft remains untracked and unadmitted.

EDRS/v3 remain **DEFERRED, HOLD**. Scientific validation remains
`NOT_ESTABLISHED`; independent review and human dispositions remain `PENDING`.
The new delivery fixtures invoke no harness. The full regression suite retains
its ordinary simulator/unit-test calculations in isolated QA; their outputs are
not new scientific evidence. No application-initiated live validation run,
CERN/EDRS pilot, QPU/provider call, evidence regeneration, commit, PR, merge,
deployment, release, publication or outreach is performed by this increment.
