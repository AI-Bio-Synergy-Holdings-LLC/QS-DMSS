# CERN Dimuon Evidence Lab — local pilot

This **experimental, CLI-first educational external-data workflow** is included
in the v0.15.0 engineering-beta preparation, not in the published v0.14.0 wheel.
Preparation is not publication or real-data numerical reconciliation. No new
cockpit/portal route, solver, AI setting or hosted execution is introduced.
It does not replace the frozen scientific evidence or assessment under
[#183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183).

## Researcher workflow

Obtain a local copy of `Jpsimumu.csv` from
[CERN Open Data record 5203](https://opendata.cern.ch/record/5203), review its
terms and record its SHA-256. The CLI never downloads anything. Use a qualified
source/installed-candidate build, not an unmodified published wheel. The output
parent must exist; the final directory must not exist, even if empty.

```console
qs-dmss external-data dimuon --input Jpsimumu.csv --input-kind cms-record-5203 --output dimuon-baseline --expected-sha256 FULL_64_LOWERCASE_HEX
qs-dmss external-data verify dimuon-baseline/dimuon-evidence.zip
qs-dmss external-data verify dimuon-baseline/dimuon-evidence.zip --recompute
```

`--expected-sha256` is optional but recommended. `--source-commit` and
`--candidate-wheel-sha256` retain optional caller-declared implementation
identities; these assertions are not independently verified. Retain the actual
wheel separately. The receipt records Python, NumPy, QS-DMSS metadata and the
actual relevant module-byte hashes. The core version alone cannot identify
the exact implementation.

The frozen numerical-reconciliation protocol still identifies source `c158c3b`
and its separately approved 0.14.0 candidate wheel. New 0.15.0 artifacts are not
substitutes for that wheel, and the identity checker must continue refusing such
substitution. Real-data qualification remains `NOT_EXECUTED`; EDRS/v3 remain
deferred, HOLD. Neither releasing software nor successful integrity verification
changes scientific status.

For a narrower saved analysis, use a **new** output directory and add
`--mass-min 2.8 --mass-max 3.4 --pt-min 1 --bins 30`. No profile is overwritten
and no recommendation or score is optimized. Open `report.html` locally for the
mass histogram, cut flow, exclusions, exact profile, provenance and limitations.
Every figure has an exact table alternative, without JavaScript, fonts/CDNs,
hover-only content or network dependencies. Desktop and mobile have separate
chart layouts; ordinary disclosure controls are keyboard accessible.
The exact-count table uses round-trip representations of retained float edges,
including narrow analysis windows; display formatting does not change binning.

Original synthetic fixtures in the same closed format require
`--input-kind synthetic`. Their reports conspicuously say
`SYNTHETIC_NOT_COLLISION_DATA`; they must not be presented as CMS observations.
The installed-wheel acceptance smoke is
`.github/scripts/external_dimuon_smoke.py --output-root NEW_DIRECTORY`.

All commands emit JSON. Exit 0 means workflow/integrity success, not scientific
approval. Empty selections produce `COMPLETED_NO_SELECTED_EVENTS`, a zero-count
histogram and null descriptive statistics. Authored failures return 1;
argparse usage errors return 2. No numerical/scientific pass badge is assigned.

## Exact source contract and identity

Record 5203 is Thomas McCauley's *J/psi to two muons from 2011*, an educational
subset of CMS DoubleMu 2011: 20,000 selected events, published in 2019. The
provider explicitly says it is **not suitable for a full physics analysis**.
Reference metadata was checked on 2026-10-20:

- `Jpsimumu.csv`: 2,639,302 bytes, `adler32:214e4077`.
- File version: `0afc5f87-176f-4b4b-855b-5bd568dc1b3d`.
- Maintainer-observed SHA-256 of the bounded HTTPS retrieval on 2026-10-20:
  `95bf87f7c14758b445d9cb76bc0111affc1ce70831453dde34f687310685e59f`.
  This is a retained-byte identity, not a provider-signed digest.
- License: CC0-1.0; no DOI is asserted for this record.
- Neither CMS nor CERN endorses this derived work.

The exact ASCII header (case and order significant) is:

```text
Run,Event,type1,E1,px1,py1,pz1,pt1,eta1,phi1,Q1,type2,E2,px2,py2,pz2,pt2,eta2,phi2,Q2
```

The different teaching-repository CSV with `Type1`/`Type2` and an additional `M`
column is intentionally **not** silently accepted. No notebook code or teaching
materials are imported. This implementation uses its own analytic fixtures.

CMS-kind admission requires the pinned provider size, Adler-32 and row count,
plus the maintainer-observed snapshot SHA-256.
Every admitted snapshot gets its own SHA-256. Size/Adler-32 agreement is **not
cryptographic authentication**, and input kind is caller-declared. A caller's
SHA-256 checks exact local bytes, not independent provenance. Provider metadata
changes require a separately reviewed profile change, not automatic refresh.

## Analysis convention `cms-dimuon-four-vector-v1`

In natural units `c=1`, energy, momentum and reconstructed mass use GeV:

```text
m_squared = (E1 + E2)^2 - (px1 + px2)^2 - (py1 + py2)^2 - (pz1 + pz2)^2
mass = sqrt(m_squared)
```

Numeric data are finite float64. Values must have absolute magnitude ≤1e6;
energy is positive, pt nonnegative, charge ±1 and muon type G/T. Run/event IDs
are 1–19 decimal digits within signed 64-bit range. Bad numeric/category rows
are excluded with a first-failure reason; malformed file structure fails
admission. Rows are neither imputed nor silently omitted from accounting.

Only negative mass-squared values within
`64 * float64_epsilon * max(E_sum_squared + p_sum_squared, 1)` are clamped to
zero; materially negative values are rejected and counted. This is a floating-
point cancellation policy, **not** a detector/rounding uncertainty model.

Sequential source cuts are reapplied: both `abs(eta) < 2.4`, at least one G
muon, opposite charges, then `2 < recomputed mass < 5`. Rounded CSV values can
move events near a source boundary; those exclusions remain visible. Additional
analysis cuts are both `pt >= pt_min`, then strict `mass_min < mass < mass_max`.
The analysis mass window must remain within [2,5] GeV. pt minimum is 0–10,000
GeV, and bins are 1–100 (default 60). These are explicit profile controls, not a
search for a preferred peak.

The histogram is unweighted counts, left-closed bins with the final bin
right-closed. Strict selection excludes the analysis endpoints before binning.
Descriptive mean/population standard deviation are not fit parameters or
uncertainty estimates. No event weights, cross sections, acceptance/efficiency
corrections, significance, background fit or luminosity inference are supplied.

## Resource, filesystem and failure-retention policy

This new workflow has its own bounds; existing diagnostic-pack, historical
semantic-checker and frozen evidence policies are **not** changed:

| Resource | Ceiling |
| --- | ---: |
| Local CSV snapshot | 4 MiB |
| Data rows | 25,000 |
| Physical line / cell | 4,096 / 128 bytes |
| Histogram bins | 100 |
| All noninput records including integrity manifest | 256 KiB |
| Receipt | 16 KiB |
| Stored evidence ZIP | 4.5 MiB |
| Completed retained output (records plus ZIP) | 10 MiB |

Reads check size before allocation and read at most ceiling+1 bytes. Only
literal regular files are admitted; links/reparse paths, URL inputs, multiline
cells, control characters, wrong/duplicate/reordered headers and extra columns
are refused. Input and output paths containing parent-traversal (`..`)
components are refused before normalization, even if normalization would remain
inside a trusted directory. Parents are also checked for links/reparse points.
Descriptor and path identities/size/mtime are rechecked around the bounded read. These checks
are not descriptor-anchored isolation from a hostile process concurrently
replacing output parents. Use a trusted local directory. Limits bound admitted
work and retained bytes; they are not OS-enforced RSS/time/concurrency limits.

The new directory and bounded `receipt.json` are reserved **before** reading or
parsing. Admitted-size raw input bytes are retained as `input.csv` even when
CSV/schema/hash admission subsequently fails. Oversized or unreadable sources
are not copied. Refusal, source drift, analysis/export failure and interruption
leave a failed receipt (stage and authored reason) and partial output. Arbitrary
exception text and unbounded logs are not retained. Storage failure can prevent
receipt finalization; an initial/partial receipt remains when possible. Do not
reuse or delete failed evidence to retry: select a new output directory.

## Evidence and verification boundary

The stored, unencrypted ZIP has exactly seven flat members:

```text
input.csv
analysis.json
profile.json
source.json
report.html
receipt.json
manifest.sha256.json
```

The manifest (`qs-dmss-external-dimuon/v1-integrity`) hashes the six other
members and their byte sizes; no self-referential manifest/ZIP hash is used.
The command returns the ZIP SHA-256. The receipt is mutable only during active
execution/finalization; the workflow never changes a completed directory.
Filesystem permissions do not make these records tamper-proof.

`verify` checks bounded archive/member sizes, exact entry set, duplicate names,
stored/unencrypted policy, CRCs, strict JSON manifest and file hashes, closed
profile, input identity consistency and pilot statuses. It never extracts
archive paths, opens HTML, imports content or calls a solver. It does not claim
full result-schema validation. `--recompute` additionally re-admits the embedded
CSV and compares the source record and complete numerical analysis against the
**current** installed implementation. Cross-environment numeric differences
are a mismatch to investigate, not a reason to retune limits silently.

Neither mode authenticates an author: an attacker can replace records and their
manifest together. Neither establishes independent scientific review. All
results retain scientific status `NOT_ESTABLISHED`, independent review/human
disposition `PENDING` and AI advice `null`. Historical numerical statuses,
candidate artifacts, review media and #183 remain unchanged. The graph backend
stays experimental, CPU/local-only; hosted graph execution and AI stay disabled.

## Qualification and explicit non-goals

`tests/test_external_dimuon.py` covers analytic scalar/vectorized agreement,
boundary selections, material-negative versus roundoff mass, invalid-row
accounting, empty results, maximum/over-limit inputs, immutable exports,
failure retention, source drift, symlinks where supported, manifest/archive
tampering, strict JSON, safe HTML and CLI round trips. CI adds installed-wheel
synthetic import/analysis/recomputation to the supported Python 3.10–3.13 matrix.
Synthetic acceptance is **not** qualification of the full provider payload.

The 2026-10-20 local acceptance also exercised the exact provider snapshot
identified above through a separately installed candidate wheel: 20,000 input
rows, 19,997 selected (one eta-cut and two recomputed mass-window exclusions),
with integrity verification and current-implementation recomputation matching.
The full raw snapshot and every exclusion remain represented in the retained
bundle; these counts do not establish detector or physical validity. Local
qualification data, wheels and receipts stay under ignored `.local/cern-dimuon-*`
directories and are not packaged as scientific reference evidence.

Initial local engineering qualification on Windows/Python 3.14.3 (supplementary, not
the supported remote matrix) finished with **989 passed, 26 skipped, 91.70%
coverage**; the focused pilot suite had **82 passed, one skipped**. The skipped
pilot test requires host symlink-creation privileges; a separate reparse-point
regression runs without those privileges. Ruff, medium-or-higher Bandit,
compilation, 113 JavaScript regressions, frozen-registry/discovery checks,
wheel/sdist content checks and Twine passed. The isolated installed-wheel
environment's final dependency audit reported no known vulnerabilities.

That initial code-qualified, unpublished wheel SHA-256 is
`72e9280b61c4b02b93c7ed61f43d613ffbd8f3166fbacb4124dd730045fed780`;
its retained relevant module hashes match the workspace implementation.
Desktop 1280×720 and mobile 360×800/390×844 browser QA found no final overflow or
console errors; keyboard disclosure opened the 60-bin table with its header.
Physical mobile hardware and assistive-technology testing remain separate.

Do not erase qualification caveats: earlier complete runs encountered
intermittent Windows `WinError 5` while replacing **existing cockpit/campaign**
`job.json` records (`tests/test_cli_campaigns.py` and `tests/test_cockpit_api.py`).
Both affected tests subsequently passed individually and the final whole suite
passed, but this does not establish that the unrelated file-lock issue is fixed.
The original shared development environment's audit also reported four known
vulnerabilities across `certifi 2026.6.17` and `urllib3 2.7.0`; that environment
was not silently upgraded. These are separate maintenance findings, not a claim
that all environments are security-clean. The initial local pass preceded PR
#206; its original remote checks subsequently passed. Neither a local nor a
remote engineering pass establishes scientific approval or release authority.

### PR #206 correction qualification — 2026-10-20

Four review findings are corrected without changing the analysis convention,
resource ceilings, frozen evidence or scientific statuses: oversized integer
thresholds and malformed UTF-8 archive names now produce authored JSON refusals;
exact interval labels retain float precision; and parent traversal is refused
before path normalization for both input and output.

The 20 added regression cases failed before the corrections and passed after
them. Final Windows/Python 3.14.3 qualification finished with **1,009 passed,
26 skipped, 91.71% coverage**; the focused pilot suite had **102 passed, one
skipped**. Ruff, medium-or-higher Bandit, compilation, 113 JavaScript regressions,
registry/discovery checks, wheel/sdist build and Twine passed. The isolated
installed-wheel dependency audit reported no known vulnerabilities; the shared
environment caveat above remains unchanged.

The corrected, code-qualified unpublished wheel SHA-256 is
`b8434593e6b34abda2536e0c5752e5ade253d76a083537a34fb84d3b6b70974e`.
Installed-wheel synthetic acceptance and exact-provider recomputation passed;
the provider analysis is unchanged from the initial retained result. The
malformed-archive regressions also returned JSON refusals through the installed
CLI. Final desktop 1280×720 and mobile 360×800 browser checks confirmed 60
distinct narrow-window interval labels, no horizontal overflow or console
errors, and keyboard access to the exact table. Physical-device and
assistive-technology testing were not performed. Updated remote qualification
is required for the correction commit before resolving its review findings.

Out of scope: network downloader, ROOT/NanoAOD, general dataset registry,
executable packs, campaign scores, graph/quantum/AI execution, portal/cockpit UI,
public challenge promotion, release publication and deployment.
