# Active Builder Roadmap

This file remains at the older roadmap path so existing links do not break, but
the strategy has moved beyond a review-sprint posture.

The current QS-DMSS direction is:

```text
run simulations -> inspect evidence -> compare campaigns -> publish reproducible artifacts
```

The current public baseline is `qs-dmss==0.9.0`, archived by Zenodo as
`v0.9.0` / `10.5281/zenodo.20693736`.

## Strategic Shift

The earlier v0.3/v0.4 work made QS-DMSS installable, citable, reproducible, and
reviewable. The next phase should make it compelling to build and fund.

That means:

- fewer broad "please review" asks;
- more concrete build lanes;
- fewer documentation-only release loops;
- more simulation-lab product work;
- clearer funding milestones tied to public artifacts.

The full strategy now lives in:

- [product-vision.md](product-vision.md)
- [contributor-roadmap.md](contributor-roadmap.md)
- [funding-roadmap.md](funding-roadmap.md)

## Current Active Slice: Self-Interaction Study Template

Lab Mode and Campaign Studio now make QS-DMSS feel meaningfully different from
a generic open simulator. `v0.9.0` has shipped the dry-run Slurm review target,
and `v0.8.0` shipped the Campaign Studio Template
Library polish, and PR #90 clarified the scientific scope and tangible-utility
lane. The current slice turns that positioning into a packaged runnable study.

The target user flow is:

```text
select Self-Interaction Sweep -> run engine.g_int campaign -> inspect guidance -> export research object
```

The current implementation should focus on the local cockpit and existing
showcase/campaign/evidence spine:

- ship a packaged `Self-Interaction Sweep` Campaign Studio template focused on
  `engine.g_int`;
- show purpose, expected runtime, metrics, limitations, and non-claims in the
  template library before a user edits YAML;
- run the packaged template through the existing campaign/recommendation
  pipeline without writing inside installed package assets;
- record local last-run provenance, recommendation, report, and bundle links
  after execution;
- attach the scoring contract, campaign metadata, guided interpretation, and
  recommendation rationale to exported research objects;
- keep package releases paused until the template feels like a meaningful
  `v0.9.0` product milestone.

## Builder Board Tracks

Public builder board:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/57`

The public issue board should consolidate around seven ambitious but concrete
tracks:

1. Lab Mode cockpit flow.
2. Scenario library and scenario metadata.
3. Evidence Explorer.
4. Publication-grade report export.
5. Campaign Studio.
6. Numerical validation scenarios.
7. Release and infrastructure reliability.

Each track should have a small first task and a larger destination. The goal is
to give contributors and sponsors a visible path into meaningful work.

## Maintainer Cadence

Maintainer updates should now emphasize product momentum:

- short progress updates on the builder board;
- focused PRs that advance one track;
- issue comments that move stale review requests into build opportunities;
- package releases only when a meaningful product or runtime milestone lands.

## Non-Goals For This Track

This roadmap does not claim:

- peer-reviewed scientific validation;
- production cosmology or astrophysics readiness;
- GPU, distributed, or high-performance backend support;
- stable internal Python APIs;
- a need to publish a new package for every documentation update.

The purpose is to make QS-DMSS worth building with: a reproducible simulation
lab where outputs are inspectable, replayable, comparable, and publishable.
