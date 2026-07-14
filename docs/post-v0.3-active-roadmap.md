# Active Builder Roadmap

This file remains at the older roadmap path so existing links do not break, but
the strategy has moved beyond a review-sprint posture.

The current QS-DMSS direction is:

```text
run simulations -> inspect evidence -> compare campaigns -> publish reproducible artifacts
```

The current GitHub, Zenodo, and PyPI release is `v0.13.1`; its archived DOI is
`10.5281/zenodo.21348597`.

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

## Current Active Slice: v0.13.1 Research-Grade Review Conversion

Lab Mode and Campaign Studio now make QS-DMSS feel meaningfully different from
a generic open simulator. `v0.9.0` shipped the dry-run Slurm review target, and
`v0.13.0` makes the experimental Fractal/Quadrant SSFM validation harness live
inside Studio, including redrawable topology and attribution figures, the
Research Runbook, and a contextual Evidence Assistant. The released GitHub
wheel also retains the public reference-data provenance calibration sandbox,
Conceptual Reference Map links, and job-registry path hardening. PyPI remains
on `v0.13.1` while the research and provenance gates are reviewed.

The target user flow is:

```text
pip install -> run fractal SSFM validation or reference-data calibration -> inspect JSON/Markdown/evidence output -> comment on issue #105 or related provenance issues
```

The current implementation should focus on review conversion after publication,
not another immediate feature release:

- route numerical-methods, nonlinear-waves, spectral-methods, and
  scientific-Python reviewers to
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105`;
- ask for one public comment on Strang refinement, fuzzy-potential norm
  conservation, non-conservative mask labels, or diagnostics-only status;
- use the `v0.13.1` GitHub release wheel as the stable public review baseline
  while the validation and provenance gates are reviewed;
- keep GPU expansion, real HPC submission, and decision-metric UI paused until
  the review target receives substantive technical feedback or exposes a
  blocker.

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
