# Recommendation robustness explorer (local pilot)

This is a recorded-result consumer of Campaign Studio, not a new solver or a
scientific-validation badge. No version is published by this change. The installed
metadata still says `0.13.2`; development-candidate identity must additionally use
the source commit or wheel hash. Published v0.13.2 does not contain this feature.

## Researcher workflow

1. Run a Campaign Studio study or select a completed campaign in Studies.
2. In Run Lab, open **Recommendation robustness explorer** and select that campaign.
3. Track any configuration, not just the original recommendation. Change the
   primary metric/direction, target, base weights, additional primary-metric weight,
   or qualification constraints. Changes re-score the recorded results.
4. Choose one base weight to vary over a 17-point grid from zero to a chosen maximum.
   Inspect current ranks, scores, constraint failures and every sampled outcome.
5. Save the analysis, download its bundle, and reopen it read-only. Original
   campaign files, scores, manifests and bundles are never rewritten.

The exact current profile and **every** sampled profile are retained. A sampled
winner count is a count over this explicit grid, not a probability, confidence
interval, global sensitivity result or proof of optimality. A campaign with no
qualified configuration retains the existing clearly labeled fallback; fallback
wins do not count as qualified wins.

## Scoring and provenance

- `campaign_minmax_weighted_v1`: the existing decision service transforms each
  metric according to its goal and normalizes across all recorded candidates.
  Constant metrics score 1. Primary-metric weight is added to that metric's base
  weight. Qualified candidates rank first; the existing six-decimal score and
  primary-objective/failure-count/runtime/run-ID tie breaks remain unchanged.
- `one_weight_grid_v1`: changes one **base** weight at a time. The primary-metric
  bonus, other weights, goal, target and constraints remain fixed. JSON profile
  weights use canonical key order to survive saved-profile round trips.
- Used comparison/experiment metadata and captured `metrics.json`/`run.json`
  are checked against the original campaign SHA-256 manifest. Comparison values
  and identities must agree with those captures. The original bundle hash is
  pinned, but this is not a fresh verification of every solver artifact.
- Each run's energy convention is recorded. Mixed conventions are rejected.
  All-legacy campaigns remain readable with an explicit `legacy/unspecified`
  warning; no old evidence is migrated or reinterpreted as corrected energy.
- Verification qualification uses the state **recorded at campaign creation**.
  It is not independent scientific review or a fresh replay.
- Source fingerprint covers the campaign identity, exact metadata/bundle hashes
  and energy conventions. Opening, previewing and saving use an optimistic pin;
  changed source evidence returns HTTP 409 and requires reopening the campaign.
- Saved analyses retain the exact source bytes used, original manifest, source
  hashes, normalized profiles, scoring/analysis conventions, Python/platform,
  core metadata version and implementation-module hashes. The full original
  bundle is hash-referenced, not duplicated. Preserve it separately for full
  solver-artifact reproduction. An analysis bundle has its own manifest and hash.

Hashes detect unintended changes, not authorship or malicious replacement of a
file and its manifest together. Numerical preference analysis, AI advice (`null`)
and independent scientific assessment (`not_established`) are separate fields.

Runtime is environment-dependent, not an intrinsic configuration performance
estimate. Terminal peak density is a researcher-selected response objective,
not physical correctness. A score advantage depends on the included candidate
set and does not establish temporal/spatial convergence.

## Engineering boundary and limits

`decision.py` exposes an explicit-profile scoring seam without changing existing
campaign routes or payloads. `robustness.py` owns validation and pure sensitivity
calculations. `cockpit/robustness.py` owns a separate router/persistence service;
`static/robustness.js` and `.css` own the rendering island. The shared cockpit
only registers the router and emits an experiment-selection event.

No new runtime dependency, executable plugin, entry point, provider, model call
or solver invocation is added. Hosted mode exposes an unavailable state and
denies analysis access/mutations. Hosted graph execution and AI remain unchanged.

Limits: 2–64 candidates, 2–41 distinct finite sampled weights, weights 0–10000,
finite metrics/targets/constraints bounded to magnitude 1e12, 2 MiB per metadata
file/derived analysis, 16 MiB total used source metadata, 64 MiB source bundle,
4096 manifest entries and 200 listed campaigns/analyses. A grid that removes
every positive weight is rejected, not silently omitted.

Routes under `/api/robustness`: `GET /sources`, `GET /sources/{experiment_id}`,
`POST /preview`, `POST /analyses`, `GET /analyses`, `GET /analyses/{analysis_id}`,
and `GET /analyses/{analysis_id}/bundle`. Request models forbid unknown keys;
OpenAPI documents the finite profile/grid contract. Artifacts are separate under
`experiments/_robustness/`. There is no update/delete route for saved analyses.

## Rendering design and acceptance

One native SVG horizontal ranking chart, at most 64 bars, paired with exact HTML
tables. An extra D3 dependency is unnecessary for this bounded linear encoding;
geometry, source normalization and interaction state are separate. Container
resizing recomputes label lanes and row heights rather than shrinking desktop
text. At mobile portrait widths (375 px), the insight/chart precede collapsed
scoring controls. Inputs/buttons have at least 44 px targets; values and caveats
are visible without hover, drag or animation. Keyboard/native input paths and
screen-reader table fallback remain available. No sensors or live streams.

Acceptance requires:

- Original-profile ranks/scores and campaign payload/order contracts match.
- Preference changes redraw the chart and change recommendations when warranted.
- Every configuration is inspectable, including constraint failures and ties.
- Invalid/stale profiles cannot be saved; previous valid results are labeled.
- Save/reopen/export preserves exact profiles and hashes without altering originals.
- Tampering, mixed conventions, path escapes, oversized input and hosted calls fail closed.
- Desktop/mobile, keyboard controls, safe text rendering, empty/error states and
  zero new browser errors pass rendered QA.

Generated report/workbook previews allow only same-origin framing; the cockpit
and other surfaces retain framing denial. This repairs the pre-existing conflict
between report iframes and blanket anti-framing headers, not a cross-origin embed
feature.

## Next increment: data-only add-on admission

After this pilot's protected review and researcher feedback, prove a closed,
schema-validated diagnostic-pack contract with one bounded analytic-reference
pack. Do not introduce general executable extension loading first.

The manifest must declare pack ID/type/version, supported core-version range,
required diagnostic conventions, dependencies (including an explicit empty list),
SPDX license and attribution, resource ceilings, evidence-schema version,
content hashes, built-in diagnostic identifiers and executable acceptance tests
owned by the core test harness. Reject unknown actions, path escapes, incompatible
core/conventions, invalid licenses and budget excess. Data-pack installation must
not import Python or run commands from its contents. Scenario and report packs
can use the same admission envelope later.

An optional Wolfram reference adapter is a separate reviewed execution boundary:
opt-in availability/license checks, explicit commands, environment and retained
results. Cross-tool agreement does not substitute for human scientific assessment.

Deferred: multidimensional weight/constraint sweeps, uncertainty distributions,
Pareto surfaces, statistically defensible runtime benchmarking, pack import UI,
executable backend/provider extensions, hosted execution and release publication.
