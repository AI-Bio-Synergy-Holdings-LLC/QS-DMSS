# Scientific challenges and reviewer intake

These are **open requests for falsification and human assessment**, not validation
badges. The [registry](../research/challenges/registry-v1.json) describes three
bounded challenges from the merged numerical pilot. The active scientific-review
gate is [#183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183).
Closed #105 is historical context; administrative closure is not scientific approval.

## Three independent status dimensions

| Challenge | Numerical evidence | Engineering review of pilot #194 | Independent scientific assessment |
| --- | --- | --- | --- |
| SC-FFT-001 — FFT kinetic-energy normalization | 72 candidate cases, not falsified within scope | Owner approved implementation/evidence packaging | Pending; scientific validity not established |
| SC-GRAPH-001 — finite graph operators and subspaces | 15 candidate cases, not falsified within scope | Owner approved implementation/evidence packaging | Pending; scientific validity not established |
| SC-EVOLUTION-001 — evolution accuracy and refinement | 2 candidate cases, not falsified within scope | Owner approved implementation/evidence packaging | Pending; scientific validity not established |

Wolfram comparisons cover the **same 89 candidate cases**, not 89 additional
independent experiments. Wolfram supplied independently assembled reference
operators/trajectories and compared preserved candidate measurements; it did not
rerun the candidate. Both reference implementations were authored through the
same AI-assisted maintainer workflow. Owner engineering approval does not count
as independent scientific review. Agreement between tools does not establish
physical applicability or continuum convergence.

## Choose a challenge

- **SC-FFT-001:** scrutinize cell measure, normalization, units and the analytic
  plane-wave expectation. The claim covers zero potential/coupling on the fixed
  periodic 2-D/3-D grids, not arbitrary states or physical calibration.
- **SC-GRAPH-001:** prioritize finite-cell mass measure, Dirichlet principal
  restriction versus an induced-subgraph Laplacian, length scaling, and multilevel
  interpretation. Compare complete degenerate eigenspaces; individual eigenvector
  differences can be a basis choice rather than a counterexample.
- **SC-EVOLUTION-001:** scrutinize the specified finite-model initial-value
  problems, reference separation and temporal order. Norm conservation alone is
  not trajectory accuracy. Long-time stability and continuum claims remain open.

The registry records the claim, source commit, diagnostic conventions, case count,
acceptance limits, pointers into both packets, limitations and unresolved questions
for each ID. Full grids, reference tolerances, controls and interpretation rules
remain in the [unchanged protocol](../research/falsification/protocol-v1.json).
Evolution also uses the graph matrix bound for its independently assembled fields.

Per-case numerical values and environments are retained, not paraphrased into a
new score: read `results.json` in the [original packet](review-evidence/falsification-pilot-v1.zip)
and [Wolfram supplement](review-evidence/wolfram-falsification-v1.zip). Human-readable
summaries are in [the original result](review-evidence/falsification-pilot-v1.md)
and [the supplement](wolfram-falsification-supplement.md). The original report's
Wolfram `NOT_EXECUTED` status describes its earlier attempt; the later supplement
records successful execution. Neither original packet is rewritten.

## Identify the correct evidence track

| Track | Source identity | How to obtain it |
| --- | --- | --- |
| Published v0.13.2 baseline | `7a063eb91af6c50e483c2d062bf6cee0daf709e4` | PyPI `qs-dmss==0.13.2` or matching GitHub release wheel |
| Development challenge candidate | `48d7ab5d10da189caddbcad1dd6622e58d204940` | Rebuild this exact source commit and retain a new build receipt |
| Reviewed pilot/reference tooling and packets | `a5f72e614dc7d38e72ffe3f4b752aace0bb408b4` | Merged PR #194; packet URLs in the registry are pinned to this commit |

The candidate also reports package version 0.13.2, but it is **not** the published
wheel. Installing from PyPI does not reproduce the corrected FFT/graph candidate.
Source commit, wheel hash, environment and diagnostic conventions—not version
alone—identify the review target. The original candidate wheel is retained locally;
the public packets contain its hash and build receipt, not that wheel. Do not
claim to have downloaded or reproduced its exact bytes merely by rebuilding it.

## Reproduce the development candidate

1. Review the [pilot instructions](../research/falsification/README.md) and
   [prospective protocol](scientific-falsification-pilot.md). Obtain the reviewed
   tooling/packets from commit `a5f72e6`; use a separate checkout/directory for
   candidate source `48d7ab5`. Inspect code before executing it.
2. Export and build the exact candidate source as described in those instructions.
   Preserve the source commit, source archive hash, build command/tool versions,
   wheel hash and build receipt. A new wheel hash is expected if build metadata
   differs; never copy the original hash into a new receipt without verification.
3. Install your wheel and research requirements into a clean environment. Run the
   pilot **outside an editable checkout**, retaining stdout/stderr, all failures,
   raw arrays and the new packet. Record OS, Python, dependencies and optional
   Wolfram kernel version. Report a setup failure as NOT_RUN, not success.
4. Compare numerical results under the original thresholds, not ZIP byte equality.
   The optional Wolfram comparator v1 intentionally accepts only the original
   hash-pinned candidate packet; it is a retained-data corroboration tool, not an
   importer for newly rebuilt candidate packets. Report any new cross-tool
   comparison separately with its inputs, method and hashes.
5. Submit one focused report using the
   [scientific-review form](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=scientific_review.yml).
   Pick the challenge ID, include your commands/environment and artifact hashes,
   and link #183. For conceptual feedback without execution, say NOT_RUN and give
   the reasoning; useful feedback is not automatically a reproduction assessment.

A counterexample should identify the exact in-scope condition, expected/observed
quantity and violated bound. Out-of-scope behavior can motivate a new prospectively
specified challenge but does not silently change this one's claim or tolerances.
Retain failures and inconclusive outcomes. Hashes establish byte identity, not
authorship, independence, correctness or scientific validity.

## Human-accountable intake and disposition

The form requests challenge/track, source and artifact identity, commands,
environment, outcome/counterexample, reviewer identity and independence, AI/tool
assistance, suggested change and human disposition. A public GitHub handle can
identify the accountable reviewer; do not post private contact information,
credentials, sensitive datasets or internal filesystem details. Disclose relevant
relationships/conflicts and whether the reviewer authored the candidate/reference.
AI-assisted work is welcome, but an AI tool cannot be the accountable human.

Every new submission starts **PENDING**. Self-reported independence, an uploaded
bundle, a green integrity check or a reviewer recommendation does not close #183.
A maintainer must link the submission and record a named human disposition:

```text
Challenge / submission URL:
Accountable reviewer and independence assessment:
Evidence source / artifact hashes:
Finding and scope (including counterexample or NOT_RUN reason):
Disposition: PENDING | ACCEPTED | ACTIONED | DEFERRED | REJECTED
Disposition author / date:
Rationale and supporting evidence:
Blocking finding: yes | no (with reason)
Follow-up issue or corrective commit:
Scientific gate impact: remains open unless explicitly assessed separately
```

ACCEPTED means the **finding** is accepted, not the model scientifically validated.
ACTIONED requires a linked corrective change; DEFERRED/REJECTED require rationale.
Keep the submission history and counterexamples even after a correction. Never
execute submitted scripts automatically or approve untrusted Actions as part of
intake; inspect evidence first and use a separately authorized isolated environment
for any reproduction. No email outreach or unsolicited messages are automated.

## Next milestone and future consumers

The read-only discovery consumer and independent-review invitation are described
in [Scientific Challenges: discovery and reviewer handoff](scientific-challenge-handoff.md).
That document distinguishes candidate UI availability from the published package
and describes catalog integrity and unavailable-data behavior.

The next milestone is one substantive, human-accountable independent reproduction
and methodological assessment under #183, prioritizing SC-GRAPH-001's measure,
boundaries, length scaling and multilevel interpretation. One report may address
only part of the questions; it does not automatically close the whole gate.
Invitation for an approved opt-in channel: “Choose one challenge, reproduce its
pinned candidate or explain a specific methodological objection, disclose your
methods/AI assistance, and submit the evidence for human disposition under #183.”

Registry PR #195 added **no studio/app UI**, release, hosted graph compute or AI
enablement. The read-only Scientific Challenges consumer uses this reviewed registry.
It must render prose as text, validate the complete registry/evidence relationship,
keep the three status dimensions visible, link limitations and #183, and show an
unavailable/inconclusive state when data fail validation. Do not derive an overall
“validated” badge from CI, registry integrity or numerical agreement. Historical
v1 is a frozen snapshot: later findings/dispositions belong in linked records and
an explicitly reviewed registry revision, not silent edits to archived evidence.

Developer check (existing `dev` dependencies):

```console
python research/challenges/validate_registry.py
python -m pytest -q tests/test_scientific_challenges.py
```

The validator checks schema, source/packet identities, manifests, result pointers,
counts, outcomes and exact protocol bounds without network access, extraction or
scientific execution. Its `CONSISTENT` result is metadata integrity only; the
scientific meaning of prose and reviewer judgments still require human assessment.
