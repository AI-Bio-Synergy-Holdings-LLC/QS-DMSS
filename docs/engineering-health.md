# Engineering Health and Debt Register

Last full sweep: 2026-07-28

This register separates measured engineering health from work that needs a
larger architectural, operational, scientific, or legal decision. It is not a
release-readiness approval and does not expand the project's scientific claim.

## Verified baseline

- Baseline commit: `2c28c7f89f365a88e49ee2bccb263bb929ed12b2`
  (`origin/main` at the start of the sweep).
- Worktree state: clean before the sweep.
- Python validation: 135 tests passed on Python 3.14.3.
- Measured statement coverage: 89.77% (reported as 90%).
- Lowest material module coverage: `experiment.py` 80%, `cli.py` 82%,
  `ai.py` 83%, and `paths.py` 83%. The eight-line cockpit server entry point
  had no direct coverage.
- Dependency audit: no known vulnerabilities in the resolved local
  environment.
- Direct runtime, development HTTP-client, and quantum-extra dependencies
  declare permissive MIT, BSD, Apache-2.0, or compatible bundled license
  expressions; no direct copyleft conflict was identified. This is an
  engineering inventory, not a legal opinion.
- Source audit: no medium- or high-severity Bandit findings. Four low-severity
  findings were reviewed; three describe the fixed-argument `git rev-parse`
  provenance probe and one is a false positive on a Boolean policy field.
- GitHub security posture: zero open CodeQL, Dependabot, or secret-scanning
  alerts at the time of the sweep.
- Upstream automation: CI, CodeQL, dependency graph, Pages, and production
  provenance checks were green for the baseline commit.
- Public deployment: portal and app both reported version `0.13.2`, Render
  provenance for the baseline commit, and the required response headers.
- Documentation integrity: all 65 tracked Markdown files had resolvable local
  file links.
- Post-mitigation gate: 139 tests passed and the enforced coverage floor passed
  at 89.73%.

## Mitigations in this sweep

- Corrected the supported security line and current quantum/JOSS/distribution
  documentation from `v0.12.x` to `v0.13.x` / `v0.13.2`.
- Aligned CodeMeta runtime requirements with package metadata.
- Synchronized the top-level public run schema with the wheel's runtime schema;
  the former had omitted the Fractal SSFM backends, geometry, and spectral
  fields.
- Added repository-owned Ruff rules, an 88% quantum-enabled coverage floor on
  Python 3.13, a dependency audit, and a medium-or-higher source-security gate.
- Added weekly dependency update monitoring for Python, GitHub Actions, and the
  Docker base image.
- Added a pull-request dependency review that blocks moderate-or-higher
  vulnerabilities introduced by dependency changes.
- Expanded production provenance verification from `site/**` changes to every
  push on `main`.
- Added regression checks for supported-version drift, CodeMeta dependency and
  package-asset drift, Markdown link integrity, and production-verification
  scope.

## EH-001 incremental extraction progress

The first compatibility-preserving EH-001 increment starts from merged commit
`b2e7f164123c339ccc148ca881ebe69659ceb2e2` and isolates run and experiment
artifact access in `CockpitArtifactService`.

- Added characterization coverage for traversal rejection, exact HTTP error
  contracts, profile-bundle contents, and marker-bounded directory ordering
  before moving the implementation.
- Preserved every existing `CockpitService` method and API route as a delegating
  compatibility surface.
- Reduced `cockpit/api.py` from 4,548 to 4,435 lines and the
  `CockpitService` class span from 3,252 to 3,174 lines.
- The extracted service has maintainability index 32.57 (A), average
  cyclomatic complexity 3.55 (A), and maximum method complexity 7 (B).
- Verified the extracted module at 98% statement coverage; the complete local
  gate passed with 143 tests and 89.93% aggregate coverage.

EH-001 remains open. Workspace and campaign orchestration, AI evidence-context
assembly, transport registration, and response serialization still require
separate characterization-first increments.

## Prioritized debt register

| ID | Priority | Area | Evidence and risk | Decision / completion gate |
| --- | --- | --- | --- | --- |
| EH-001 | P0 | Cockpit architecture | The first artifact/path service is extracted, but `src/qs_dmss/cockpit/api.py` remains 4,435 lines, `CockpitService` spans 3,174 lines, and `build_ai_evidence_context` retains cyclomatic complexity 39. Changes still have a broad regression radius. | Continue one characterization-first boundary per PR: workspace services, campaign services, AI evidence context, transport registration, and serialization. Preserve API and evidence contracts before each move. |
| EH-002 | P0 | CLI architecture | `cli.main` has cyclomatic complexity 83 and owns routing for unrelated command families. | Replace the monolithic dispatcher with command-family handlers or registered subcommands without changing the public CLI. |
| EH-003 | P1 | Frontend architecture | The cockpit uses single assets of 6,909 JavaScript lines, 6,663 CSS lines, and 2,187 HTML lines with no module-level test boundary. Browser behavior is covered mostly through static assertions and API tests. | Choose a no-build ES-module split or a maintained frontend toolchain; add focused browser acceptance tests before restructuring. |
| EH-004 | P1 | Evidence/report architecture | `evidence/bundle.py`, `showcase.py`, and `experiment.py` combine calculation, rendering, persistence, and archive assembly. Their maintainability indices are low, and report changes can affect signed evidence contents. | Define stable evidence schemas and golden artifact tests before separating renderers from persistence and calculations. |
| EH-005 | P1 | Reproducible dependencies | Runtime dependencies use minimum ranges and the container builds from mutable image tags. This is appropriate for a library compatibility surface but insufficient for byte-for-byte service rebuilds. | Decide whether to maintain separate tested constraints for hosted deployments and whether Docker bases/actions must be digest/SHA pinned. Keep library metadata permissive unless compatibility policy changes. |
| EH-006 | P1 | Coverage depth | Aggregate coverage is healthy, but the server entry point is 0% and important failure branches in experiments, AI provider integration, path handling, and evidence verification remain uncovered. | Add process-level cockpit startup/shutdown coverage and targeted negative-path tests; do not inflate coverage with low-value line-only tests. |
| EH-007 | P1 | Operational observability | Production provenance and headers are tested, but New Relic alert configuration and Render settings are external dashboard state rather than repository-controlled configuration. | Decide which alert policies, destinations, SLOs, and deployment settings can be represented as reviewed infrastructure-as-code without storing secrets. |
| EH-010 | P1 | Merge governance | Main protection requires the Python matrix, Docker smoke, and CodeQL, but not the quantum-sidecar or candidate-wheel workflows. It does not require signed commits or a human approval, and administrators are not subject to the rule. | Decide the release and ordinary-merge approval policy, then require the appropriate quantum/fresh-install checks, human review, signatures, and administrator enforcement without making external contribution impractical. |
| EH-008 | P2 | Supply-chain automation | Dependabot now monitors declared ecosystems, but third-party Actions still use mutable major-version tags. | Pin Actions to reviewed commit SHAs and define a routine for Dependabot SHA refreshes. |
| EH-009 | P2 | Python support | Package metadata permits Python 3.14 and the local sweep passed there, while CI/classifiers stop at 3.13. | Add 3.14 to CI and classifiers after the release team decides it is a supported rather than incidental interpreter. |
| EH-011 | Decision gate | Scientific review | The Fractal SSFM independent-review gate remains open; engineering tests cannot establish physical validity or independent human scientific review. | Keep issue #105 open until corrected external methodology, exact release reproduction evidence, and defensible scientific interpretations are accepted. |
| EH-012 | Decision gate | Paper/legal metadata | `paper/paper.md` intentionally contains unresolved authorship, affiliation, AI-disclosure, impact, funding, and acknowledgement placeholders. | Require accountable human authorship and qualified legal/scholarly review before submission; do not infer or auto-fill these fields. |

## Maintenance cadence

- Review dependency and container update PRs weekly.
- Re-run this sweep before each release-preparation PR.
- Update this register only from measured evidence; retain historical release
  documents as historical records.
- Treat P0/P1 decomposition work as separate PR series with explicit API and
  evidence-schema compatibility gates.
