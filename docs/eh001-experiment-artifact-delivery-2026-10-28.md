# EH-001: experiment-artifact delivery boundary

Date: 2026-10-28. Baseline: `680eab694370e7ec4fa85eab4f08429fba25442a`.
This is local implementation/qualification evidence, not a commit, PR, merge,
deployment, release, scientific admission or independent assessment.

## Characterization and extraction

Before production edits, **57 HTTP characterization cases passed** for:

- `/api/experiments/{experiment_id}/bundle`
- `/api/experiments/{experiment_id}/report`
- `/api/experiments/{experiment_id}/workbook`
- `/api/experiments/{experiment_id}/workbook/download`

The contracts cover exact status/error bodies, byte preservation, content types,
download names, local/hosted modes, session isolation, inclusive hosted caps,
range/unsatisfiable-range behavior, report/workbook preview versus attachment
security headers, dependency overrides, guard ordering and sanitized failures.

Only registration is moved into
[`experiment_artifact_routes.py`](../src/qs_dmss/cockpit/experiment_artifact_routes.py).
Direct registration retains its original ordered position. A structural service
protocol and injected response guard avoid a circular import of `api.py`.
`create_app` and all `CockpitService` compatibility methods remain available.
Session selection, artifact lookup, file assembly, download limits, report CSP
generation, experiment execution and serialization remain in their prior owners.

An AST comparison confirms identical handler bodies/decorators except for the
injected dependency and structural service annotation. The complete ordered
route/OpenAPI snapshots are identical: **61 entries, 56 documented paths**,
SHA-256 `8b86ad035fcffc32b601c6047f327f8012f27bd5bd6b85e868a2f024ef5c257d`.
`api.py` decreases from 3,058 to 3,006 lines. EH-001 remains open.

## Local qualification

Retained QA: `.tmp/eh001-experiment-artifact-delivery-20261028/`.

- Native Windows Python 3.14.3 focused gate: **198 passed**.
- Full Linux Python 3.12.15 quantum-enabled gate: **1,458 passed, 7 skipped,
  91.72% aggregate statement coverage**, passing the unchanged 88% floor.
  The new delivery module has 90% coverage: all handler statements are covered;
  its three protocol-stub bodies are unexecuted. No coverage-padding calls or
  exclusions were added.
- Isolated installed-wheel gate: **178 passed** with checkout imports disabled.
  The fresh wheel environment inherits the existing disposable QA image's
  dependencies, but both API/delivery imports resolve to its own `site-packages`.
  This is not an independently resolved dependency closure.
- Real installed-wheel loopback HTTP checks pass for all four routes, partial
  responses, separate cookie jars, peer/base artifact denial and distinct
  preview/download security. Only synthetic experiment files are served.
- Wheel/sdist build, Twine metadata and current CI archive-content assertions
  pass. Exact new source/test membership is checked; local retention trees,
  unapproved admission drafts and portal MP4 files are excluded.
- The rebuilt local Docker image runs as non-root `qsdmss`, becomes healthy,
  and returns HTTP 200 with the expected security headers. The installed
  delivery module is present; hosted custom compute and AI remain disabled.
  Its network is `none` and no ports are published. This is local QA, not a
  production deployment.
- Ruff, configured medium-or-higher Bandit, Python parsing, all 14 tracked
  JavaScript syntax checks and **113 JavaScript tests** pass.
- The ordinary Windows environment audit covers **92 packages with no known
  vulnerabilities**. Its separate msgpack correction is already qualified;
  no dependency declarations or frozen locks change in this increment.
- Registry integrity and generated discovery checks pass without regeneration:
  three challenges, 89 candidate cases and 89 retained cross-tool comparisons.

No full native Windows quantum gate was rerun; the existing Rustworkx
application-control restriction is neither fixed nor bypassed here. Python 3.14
is supplemental evidence, not an expansion of the supported Python matrix.
Remote Python 3.10–3.13, CodeQL, packaging/Docker and owner/review gates remain
required before any separately authorized protected merge.

## Preservation and boundaries

Frozen evidence, approved wheels, historical QA, inactive drafts, protocols,
locks, media, caps and scientific statuses are outside this extraction.
QA-built distributions are unpublished engineering artifacts, not replacements
for either retained CERN wheel or changes to a candidate pin.

A scoped before/after comparison checks **46,748 protected entries** and finds
no unexpected changes. Only the authorized tracked API and debt-register edits
differ; the new module, tests and this record are additional uncommitted files.
Both retained CERN wheel hashes and the pre-existing untracked allocation draft
are unchanged. The inventory hashes tracked/retained files and frozen environment
configuration/RECORD anchors; historical reparse fixtures are compared as metadata,
not followed. It does not claim to hash every frozen environment binary, and no
frozen environment is executed or modified.

EDRS/v3 remain **DEFERRED, HOLD**. Scientific validation remains
`NOT_ESTABLISHED`; independent review and human dispositions remain `PENDING`.
Hosted graph execution and AI policy are unchanged. No commit, PR, merge,
deployment, release, outreach or pilot execution is authorized by this record.
