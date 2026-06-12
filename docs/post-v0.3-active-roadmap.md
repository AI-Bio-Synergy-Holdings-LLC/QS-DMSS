# Active Builder Roadmap

This file remains at the older roadmap path so existing links do not break, but
the strategy has moved beyond a review-sprint posture.

The current QS-DMSS direction is:

```text
run simulations -> inspect evidence -> compare campaigns -> publish reproducible artifacts
```

The stable public package is `qs-dmss==0.7.0`. The latest archived release DOI
is `v0.7.0` / `10.5281/zenodo.20671389`.

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

## Current Active Slice: Campaign Studio Template Library

Lab Mode and Campaign Studio now make QS-DMSS feel meaningfully different from
a generic open simulator. The current product-polish slice should make saved
campaign designs feel like reusable research assets, not only JSON behind a
dropdown.

The target user flow is:

```text
choose scenario -> edit campaign -> save study template -> inspect card -> rerun/import/export -> compose research object
```

The current implementation should focus on the local cockpit and existing
showcase/campaign/evidence spine:

- save edited Campaign Studio grids and decision profiles as local templates;
- display templates as visible cards with objective, metric, plan, source, and portability metadata;
- reopen and rerun saved campaign templates from the cockpit;
- record last-run provenance, recommendation, report, and bundle links after execution;
- import/export template JSON so another user can reproduce the campaign design;
- attach scoring contract, campaign metadata, and recommendation rationale to
  exported research objects;
- keep releases paused unless a meaningful product/runtime milestone lands.

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
