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
  and identities must agree with those captures. Both compared and captured
  metrics must be numeric, not booleans; equal integer/float representations
  remain compatible. The original bundle hash is pinned, but this is not a fresh
  verification of every solver artifact.
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
4096 manifest entries, a 4096-entry discovery scan ceiling per root, and 200
listed campaigns/analyses. A grid that removes
every positive weight is rejected, not silently omitted.

The source ZIP ceiling is enforced while hashing, not only by an initial size
check. Reads are at most 1 MiB and never exceed the remaining allowance plus
one overflow-detection byte. A source growing past 64 MiB is rejected with the
existing authored HTTP 400 before preview or persistence; the stream is closed.
Valid bundle hashes, source fingerprints and scoring remain unchanged. This
bounds one source read, not concurrent request load or malicious replacement
of a file and its manifest together.

Routes under `/api/robustness`: `GET /sources`, `GET /sources/{experiment_id}`,
`POST /preview`, `POST /analyses`, `GET /analyses`, `GET /analyses/{analysis_id}`,
and `GET /analyses/{analysis_id}/bundle`. Request models forbid unknown keys;
OpenAPI documents the finite profile/grid contract. Artifacts are separate under
`experiments/_robustness/`. There is no update/delete route for saved analyses.

Before the first save, `GET /analyses` returns HTTP 200 with `{"items": []}`
without creating storage. An existing empty collection has the same response.
Root permission/storage errors are not treated as empty data; they retain the
sanitized HTTP 400 response. Listing verifies each `analysis.json` against its
manifest, checks identity/summary fields and labels items with
`integrity_scope: analysis_json_only`. It reads only those two bounded metadata
files per item (up to 200), not retained source or bundle bytes. Invalid summaries
are skipped; a listed item is not a claim of full artifact integrity. Direct
open/export still verifies all retained source and the complete bundle, failing
closed if either is missing, corrupted or exceeds limits. The selector explains
this distinction and links it as an accessible description. Hosted listing
remains denied. Original saved files are not rewritten or given new summary files.

Both discovery responses have a **1 MiB complete compact UTF-8 JSON ceiling**.
Accounting includes the response envelope, commas, Unicode and JSON escaping;
overflow stops before retaining the next item and returns an authored HTTP 400,
not a misleading partial latest-items list. No later metadata records are read
after overflow. This is a per-response bound, not concurrent traffic control or
a limit on total metadata I/O across all 200 candidates.

Campaign summaries retain their four selector fields: safe experiment ID, a
non-empty string label of at most 512 characters, a non-boolean integer run count
between 0 and 64, and a timestamp string of at most 64 characters or `null`.
The recorded experiment ID must exactly match its directory ID. Missing,
non-string and mismatched IDs are excluded from discovery without rewriting
evidence or relaxing direct-access identity/integrity checks. Invalid candidates
still count toward the first-200 metadata selection cap; discovery does not read
older records to backfill them. Listing is not full artifact verification and
does not guarantee that every listed record can subsequently be opened.
Missing/null/empty labels still fall back to the ID; missing timestamps remain
`null`. Nested objects, invalid Unicode text and oversized scalar summaries are
isolated without hiding healthy candidates. Timestamp length/type constraints
are not a claim of date-format validation. Excessively nested JSON is isolated.

Saved summaries retain analysis ID, timestamp, profile hash and integrity scope,
but their `source` is deliberately compact: required label and, when present,
safe experiment ID, SHA-256 source fingerprint and boolean legacy-convention
flag. Historical label-only summaries remain discoverable. Other source keys,
including full hash/convention maps and unknown nested data, are not copied into
the list. **Direct open/export retains all original provenance and full integrity
checks**; no saved record, manifest or ZIP is migrated or rewritten. Selector
behavior and existing discovery ordering/candidate caps remain unchanged.

Discovery streams immediate filesystem entries, counting **all** entries
(including non-artifacts and `_pending`) before artifact stats, reads or sorting.
It consumes at most 4097 entries to detect overflow. A root above the 4096-entry
ceiling returns an explicit HTTP 400, not a potentially misleading partial
latest-200 list. Missing roots remain empty, genuine root storage failures remain
errors, and unreadable individual records are isolated on Python 3.10–3.13.
Below the ceiling, campaign lexicographic-descending and analysis mtime-descending
ordering and the 200-candidate selection cap remain unchanged. No historical
artifact is deleted; direct access to a known ID remains available beyond the
discovery ceiling. Use a deliberately smaller evidence root for discovery.

Every retained child read, including the manifest, bundle hash and ZIP, resolves
within its artifact directory. HTTP exports serve the exact bounded ZIP byte
snapshot whose hash was checked, so replacing the original path after verification
cannot change the download. Normal ZIP response bytes, media type, attachment
name, content length and baseline security headers are preserved. The local
`bundle()` path accessor remains for compatibility but is not used for HTTP
delivery; callers requiring verified bytes should use `bundle_snapshot()`.

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

New workbook print controls are bound by the hash-authorized core script, not
inline handler attributes. A separate fixed legacy tab-script hash preserves
historical tab behavior without rewriting evidence or enabling `unsafe-inline`
or `unsafe-hashes`. Use the browser print command for historical workbooks whose
old inline print control remains intentionally blocked.

Invalid UTF-8 report/workbook bytes are served unchanged with artifact inline
styles blocked, matching oversized-preview behavior. Strict decoding is used
only to authorize exact style hashes; replacement decoding does not broaden CSP.
Fixed core-owned script hashes, same-origin framing and other baseline headers
remain unchanged. No report bytes or historical evidence are repaired in place.

Report-derived style hashes are deduplicated in first-seen order. Their admission
is bounded by an **8 KiB complete CSP-value budget**, including baseline
directives and the fixed current/legacy workbook-script hashes. Style blocks are
iterated rather than collected in an unbounded hash list. If the next unique
hash would exceed the budget, iteration stops and **all** artifact style hashes
are omitted, not a partial set. The original report bytes and baseline policy
are preserved. A trusted baseline already exceeding the budget is not weakened
or truncated; it receives no artifact style hashes. The application's current
baseline plus fixed hashes is below the budget. This is a value-size admission
limit, not a guarantee about every proxy's total-header limits.

Style extraction uses forward-only opening-tag, quote-aware attribute and closing
tag scans rather than a lazy whole-block regex. An unclosed opening/content scans
its remaining suffix once and omits all artifact style hashes. Exact valid CSS,
newline normalization, stable hash order, fixed scripts and CSP budgets remain
unchanged. This is a narrow style-admission scanner, not general HTML sanitization;
the report bytes are still served unchanged under the restricted baseline CSP.

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
