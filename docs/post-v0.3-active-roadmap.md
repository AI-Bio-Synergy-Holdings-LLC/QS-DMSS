# Post-v0.3.0 Active Roadmap

This roadmap keeps the next QS-DMSS development arc visible while `v0.3.0`
remains the stable public review baseline.

QS-DMSS is beta for reproducible package/evidence workflows; it is not
peer-reviewed scientific validation. The active post-v0.3.0 work should make
that beta baseline easier to review, harder to misinterpret, and more useful
for contributors who want a concrete place to help.

Public roadmap issue:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/49`

## Stable Review Baseline

- Package: `qs-dmss==0.3.0`
- GitHub release: `v0.3.0`
- Release DOI: `10.5281/zenodo.20112923`
- Review hub:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37`
- Reviewer opt-in discussion:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44`

Use `v0.3.0` for external review unless a public blocker requires a patch
release. Avoid package churn for documentation-only visibility work.

## Current Active Slice

The next build slice is reviewer-confidence work around the validation spine:

- clarify benchmark scenario purpose, expected envelopes, and failure meaning;
- make generated evidence bundles and replay outputs faster to inspect;
- improve the reviewer path from PyPI install to evidence verification;
- route community feedback into focused issues instead of broad private notes;
- refine the research/JOSS framing so current claims and non-claims stay clear.

This is intentionally not a new scientific-validation claim. It is a stronger
software-review and evidence-audit path for the current reference
implementation.

## Public Review Goals

The immediate goal is three public review comments:

- one install/reproducibility comment on issue `#39`;
- one evidence/benchmark-validation comment on issue `#40`;
- one scientific/JOSS-framing comment on issue `#41`.

A short pass/fail comment is enough to move the project forward. The highest
value signal is public evidence that an external reader could install, run, or
critique the project from the published artifacts.

## Maintainer Cadence

Maintainer updates should be small and public:

- weekly or event-driven comments on issue `#49`;
- review-sprint status updates on issue `#37` or discussion `#44`;
- focused follow-up issues for concrete reviewer blockers;
- no new package release unless a blocker affects the public adoption path.

## What Comes After Review Feedback

If reviewers confirm the current path is understandable, the next engineering
work should deepen the validation spine rather than broaden the product:

- add clearer benchmark comparison notes;
- document when metric-envelope updates are acceptable;
- expose reviewer-friendly summaries for benchmark and replay evidence;
- improve paper/JOSS readiness from actual reviewer questions;
- keep PyPI, Zenodo, and GitHub metadata synchronized only when a meaningful
  release is justified.

## Non-Goals For This Track

This active roadmap does not claim:

- peer-reviewed scientific validation;
- production cosmology or astrophysics readiness;
- GPU, distributed, or high-performance backend support;
- stable internal Python APIs;
- a commitment to release every documentation update as a package version.

The purpose is visible, disciplined momentum: stable enough for review, active
enough that onlookers can see where the originator and contributors are moving
next.
