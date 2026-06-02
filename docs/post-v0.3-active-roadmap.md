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

- Package: `qs-dmss==0.4.0`
- GitHub release target: `v0.4.0`
- Latest archived release DOI before `v0.4.0`: `10.5281/zenodo.20112923`
- Review hub:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37`
- Reviewer opt-in discussion:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44`

Use `v0.4.0` for external review after publication because it makes the
canonical simulation showcase installable from PyPI. Avoid package churn for
documentation-only visibility work after this release.

## Current Active Slice

The next build slice is reviewer-confidence work around a canonical simulation
showcase:

- add one packaged scenario that highlights the actual simulated field output;
- generate reviewer-readable CSV tables, SVG plots, and a summary report;
- verify and replay the showcase run through the normal evidence path;
- make generated evidence bundles and replay outputs faster to inspect;
- route community feedback into focused issues instead of broad private notes;
- refine the research/JOSS framing so current claims and non-claims stay clear.

This is intentionally not a new scientific-validation claim. It is a stronger
software-review, simulation-inspection, and evidence-audit path for the current reference
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

- fold reviewer feedback from the canonical simulation showcase into scenario
  naming, plots, and report wording;
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
