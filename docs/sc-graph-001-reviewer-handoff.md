# SC-GRAPH-001: focused independent-review handoff

Prepared 2026-10-10 for [scientific-review gate #183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183).
This is a reviewer briefing and unsent draft, not a new experiment, scientific
assessment, release, or authorization to contact anyone. No outreach is sent or
scheduled by this preparation pass. Reviewer identity and independence remain
unassessed until an accountable human participates.

## Review target and artifact identity

The primary target is the **frozen SC-GRAPH-001 candidate**, not the latest PyPI
wheel and not whichever commit the portal currently serves.

| Track | Source commit | Wheel SHA-256 | Role in this review |
| --- | --- | --- | --- |
| Published v0.14.0 | `15377b5ab1f9f3e32a37494e2e8973efce5211c3` | `22a2d4f3f6af64f562916f45ca319606a03132e89d8b7787da034c88ad87cbed` | Current published software; contains the experimental backend and challenge discovery, but is not the original pilot wheel. |
| Frozen challenge candidate; reports 0.13.2 | `48d7ab5d10da189caddbcad1dd6622e58d204940` | `1c269bb96cec6e262fe19292ee4b290450df14d3b80e4f2924c278caeee5cb2f` | Source and original locally retained wheel used for the registered evidence. |
| Reviewed pilot tooling and packets | `a5f72e614dc7d38e72ffe3f4b752aace0bb408b4` | Not an application-wheel identity | Obtain the reviewed runner, references, protocol and preserved packets here. |
| Current main/deployment snapshot, 2026-10-10 | `6ba2e46ec09f26418b0d34c537ad0ea78476d8f6` | Not a published-wheel identity | Post-release source serving the portal/app; UI availability is not a candidate reproduction receipt. |
| Historical published v0.13.2 | `7a063eb91af6c50e483c2d062bf6cee0daf709e4` | `6f22876fa625681aa72b96d99e14de92cfd5cfae870fc53d9d41673ebf82416f` | Preserved baseline predating graph admission and the FFT correction; not SC-GRAPH-001. |

The [published v0.14.0 record](release-v0.14.0.md) identifies its qualified
wheel, sdist, source tag and [version DOI](https://doi.org/10.5281/zenodo.23250727).
Version equality is not source or artifact equality. The original candidate wheel
is retained locally, not distributed in the public packets. Rebuilding the pinned
source creates a **new wheel and receipt**; its hash can legitimately differ.
Never copy the original wheel hash into a rebuilt-wheel receipt without measuring
the bytes. Installing `qs-dmss==0.14.0` does not reproduce the frozen candidate.
Any later-release comparison must be labeled as a separate evidence track.

## Preserved evidence and unchanged statuses

The [frozen registry](../research/challenges/registry-v1.json) records the claim:
for 15 specified small finite graphs, topology, mass/stiffness matrices, spectra,
complete weighted eigenspace projectors and tail diagnostics agree with the
independently assembled references within registered bounds.

| Dimension | Retained status | What it does not establish |
| --- | --- | --- |
| Numerical evidence | `NOT_FALSIFIED_WITHIN_SCOPE` | Physical correctness, continuum convergence or universal correctness. |
| Owner engineering review | `OWNER_APPROVED`, pilot #194 only | Independent human scientific approval. |
| Scientific assessment | `NOT_ESTABLISHED` | No validation badge is warranted. |
| Independent review and human disposition | `PENDING` | This briefing does not supply a reviewer or decide a finding. |

| Preserved packet | SHA-256 | Graph result pointer |
| --- | --- | --- |
| [Original pilot](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/a5f72e614dc7d38e72ffe3f4b752aace0bb408b4/docs/review-evidence/falsification-pilot-v1.zip) | `17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4` | `results.json#/exercises/graph` |
| [Wolfram supplement](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/a5f72e614dc7d38e72ffe3f4b752aace0bb408b4/docs/review-evidence/wolfram-falsification-v1.zip) | `fbdaa5c21a680f1d0a04be477c852ca1fedaddb2dae0f58be12b9256900e75b7` | `results.json#/exercises/graph` |

Wolfram compares the **same 15 graph cases**, not 15 additional experiments, and
uses preserved candidate data rather than rerunning the candidate. Its tail
power is reconstructed from retained candidate projectors, not a new invocation
of the candidate tail method. Both reference implementations were authored in
the same AI-assisted maintainer workflow; independently assembling an operator
is not independent human assessment or fully independent numerical infrastructure.

Preserve the original packets, protocol, registry and failed-attempt history.
The original Wolfram activation failure and Python 3.12 import stall remain
historical records; the subsequent Wolfram execution and maintainer dry-run are
separate evidence, not replacement receipts. No scientific run was performed
to prepare this handoff. See the [attempt history](../research/falsification/README.md)
and [maintainer dry-run](scientific-challenge-handoff.md#maintainer-handoff-dry-run-2026-09-28-utc).

## Bounded review questions

Review levels **0, 1 and 2**, lengths **0.75, 1.0 and 2.5**, and Neumann or
principal-restriction Dirichlet boundaries. Level-zero Dirichlet is excluded
because no active vertices remain. These give 15 registered graph cases.
Higher levels, altered lengths, and additional models are outside this v1 claim.
The finite graph is distinct from rectangular Fractal SSFM; agreement between
those two models is not an acceptance criterion.

| Priority | Question for the accountable reviewer | Useful assessment evidence |
| --- | --- | --- |
| 1 · Measure | Is the cell-incidence mass measure appropriate for the declared finite model and its intended interpretation? | Independently reason from cells/vertex incidence; explain normalization, units and the consequence of uniform versus incidence weights. Numerical agreement alone does not justify the convention. |
| 2 · Boundaries | Is principal restriction of the full stiffness matrix the intended Dirichlet treatment? | Identify full/active index spaces and boundary vertices; distinguish restriction from rebuilding an induced-subgraph Laplacian. Inspect the retained defective-control rejection. |
| 3 · Scaling | How should `L^-2` and `(5/3)^level` in stiffness be interpreted? | Explain the declared normalization, length units and finite-model rationale; separate consistency under this convention from physical applicability. |
| 4 · Multilevel meaning | What, if any, cross-level comparison or continuum target is defensible? | Separate finite spectra/subspaces from physical mode correspondence, cross-level equivalence and a continuum-convergence claim. Specify missing assumptions or further prospective work. |

Inspect the [finite-model specification](experimental-graph-spectral-backend.md#numerical-conventions-and-claim-boundary),
the [reviewed reference assembly](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/a5f72e614dc7d38e72ffe3f4b752aace0bb408b4/research/falsification/reference.py),
and the [pinned candidate source](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/tree/48d7ab5d10da189caddbcad1dd6622e58d204940).
Do not independently verify construction merely by importing candidate-exported
matrices as your reference. Compare complete mass-weighted eigenspace projectors,
not individual eigenvectors: rotations within a degenerate cluster are not by
themselves a counterexample. Inspect cluster membership and tail selection too.

### Registered bounds and parameters (not retuned)

These values come from the unchanged [protocol](../research/falsification/protocol-v1.json).
Its ID is `qs-dmss-falsification-pilot-v1`, with canonical JSON SHA-256
`fcecbf9ae403ad26ee8e28383ef90a5d15b7732a85af2d756ddeef03a748402b`
(sorted keys, compact separators, UTF-8), not a raw-file hash dependent on line
endings. The graph diagnostic conventions are `graph_mass_stiffness_v1` and
`whole_eigenvalue_cluster_v1`.
Scaled errors use `norm(actual-reference) / max(1, norm(reference))`, with the
Frobenius norm for matrices/projectors, as defined by the reviewed runner.
The reference cluster gap is a grouping parameter, not an error bound and not
the production eigensolver's adaptive cluster tolerance.

| Protocol key | Value |
| --- | --- |
| `scaled_matrix_error_max` | `5e-13` |
| `scaled_spectrum_error_max` | `1e-11` |
| `projector_error_max` | `1e-10` |
| `reference_cluster_relative_gap` | `1e-9` |
| `tail_fraction` | `0.8` |
| `tail_error_max` | `1e-11` |

An in-scope topology/boundary mismatch or bound violation is a numerical
counterexample. A reasoned objection to the modeling convention is also useful
scientific feedback even without such a violation; label conceptual work
`NOT_RUN`. Out-of-scope tests require their own prospective claim/protocol and
must not silently expand this challenge or loosen its limits.

## Choose a review lane before executing anything

1. **Methodological desk review (`NOT_RUN`).** Inspect the pinned source,
   specification and retained data; identify a precise objection or missing
   assumption. Do not claim reproduced execution or promote packet integrity
   checks to a numerical outcome.
2. **Installed-candidate reproduction.** Follow the
   [candidate reproduction guide](scientific-challenges.md#reproduce-the-development-candidate)
   and [reviewed runner instructions](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/a5f72e614dc7d38e72ffe3f4b752aace0bb408b4/research/falsification/README.md).
   Export exact candidate source `48d7ab5`, build a new wheel, retain its measured
   hash/build receipt, and install it in a clean isolated environment. Run from
   outside an editable checkout and preserve output, errors, environment, raw
   arrays and the new packet under new paths.

The reviewed v1 runner has **no graph-only switch**: it executes the fixed
72 FFT + 15 graph + 2 evolution cases (89 total) and negative controls. The
assessment requested here focuses on its graph results, not a modified runner.
Do not present a subset run as full v1 reproduction. A separately designed
graph-only reference calculation can be reported with its own inputs/method and
receipt, but is not the original runner's output or recovered historical evidence.

The documented runner invocation is:

```console
python /path/to/reviewed-runner/pilot.py --wheel /path/to/new-candidate.whl --build-receipt /path/to/new-build-receipt.json --output /new/path/reviewer-packet
```

Use the isolated environment's Python. Replace all paths; inspect trusted source
before execution and do not run participant-submitted code automatically.
Existing output directories/adjacent ZIPs are refused. Record setup failure as
`NOT_RUN`, numerical failure as `FAIL`, and unavailable/insufficient comparisons
as `INCONCLUSIVE`; preserve the reason and any partial output. Exit zero only
means `NOT_FALSIFIED_WITHIN_SCOPE`, not scientific approval. Retain and inspect
the seeded uniform-mass and induced-subgraph controls where applicable.

The reviewed runner does not guarantee a complete packet after a verification
failure or unexpected exception. Arrange command/environment receipts and
stdout/stderr capture outside its output directory before launching. Preserve
any partial directory and failed attempt; retry only under a new identity/path.
Do not regenerate missing historical output and describe it as recovered.

Wolfram is optional. The v1 comparator accepts only the original hash-pinned
candidate packet; it is **not an importer for new reviewer packets**. A new
cross-tool comparison needs separately identified inputs, method and receipt.
Do not substitute the original packet for a reviewer's newly measured results
and describe that comparison as independent reproduction.

## Submission and human disposition

Submit through the [Scientific Review form](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=scientific_review.yml).
Select `SC-GRAPH-001`, identify the frozen-candidate track, and link #183. Do not
prefill an executed outcome, reviewer independence, decided disposition or
unmeasured evidence hash. The form's initial disposition stays `PENDING`.
A public GitHub handle can identify the accountable human; never post secrets,
private contact information or sensitive data.

The report should contain:

- Accountable reviewer, relevant expertise, relationships/conflicts and an
  independence disclosure; state whether you authored candidate/reference code.
- AI/tool assistance, what the human inspected, and responsibility for judgments.
- Review lane, exact source/runner/protocol identities, newly measured wheel and
  evidence hashes (or `NOT_RUN`), environment and commands with observed exits.
- Findings against each of the four questions, with expected/observed quantities,
  exact case/array pointers, a counterexample or an explicit inconclusive reason.
- Scientific interpretation kept separate from numerical and integrity outcomes;
  omitted questions and limitations stated rather than implied to pass.
- Proposed correction or prospective follow-up; initial human disposition
  remains `PENDING` until a named maintainer assesses the finding.

Use the [existing disposition template](scientific-challenges.md#human-accountable-intake-and-disposition).
Accepting a finding does not validate the model. Actioned findings need a linked
correction; deferred/rejected findings need rationale. A partial SC-GRAPH-001
assessment does not automatically settle FFT/evolution questions or close #183.
Retain counterexamples and failures after any correction. Graph execution stays
experimental, CPU/local-only; hosted graph execution and AI remain disabled.

## Owner decisions before outreach

Approve a named opt-in reviewer/channel and the intended review lane first.
Confirm expertise, relevant conflicts, which questions they can assess, expected
deliverables and any separately agreed schedule or compensation. This draft
creates no deadline, engagement or compensation commitment. Invitations and
public updates require separate approval; no recipient is selected here.

### Unsent invitation draft

> Would you be interested in a bounded, human-accountable assessment of
> QS-DMSS's experimental finite graph-spectral model, SC-GRAPH-001? The review
> target is frozen candidate `48d7ab5`, not the published v0.14.0 wheel. We seek
> criticism of cell-incidence measure, Dirichlet restriction, length scaling and
> multilevel interpretation. You may provide a clearly labeled methodological
> NOT_RUN review or reproduce the pinned candidate using the reviewed protocol.
> Please disclose independence and AI assistance, retain measured identities
> and failures, and submit findings under #183. Existing numerical agreement is
> not physical validation; inconclusive results and counterexamples are welcome.

Attach this briefing through a reviewed, commit-pinned URL only after it is
available remotely. Do not send a local filename or an unpushed branch URL.

## Draft update for #183 (not posted)

Before posting, replace `HANDOFF_URL` with the reviewed commit-pinned briefing
URL and recheck the release/source context. Preserve existing issue history.

> Preparation update, 2026-10-10: published v0.14.0 pins source `15377b5` and
> qualified release artifacts; current app/portal source was verified at
> `6ba2e46`. Neither identity relabels the frozen challenge candidate `48d7ab5`,
> which reports 0.13.2 but is not the historical published 0.13.2 wheel.
> SC-GRAPH-001's focused reviewer handoff is at HANDOFF_URL. It prioritizes
> measure, boundary restriction, length scaling and multilevel interpretation,
> with distinct NOT_RUN and installed-candidate reproduction lanes. The reviewed
> runner still executes all 89 fixed cases; review focus is its 15 graph cases.
> Original packets, hashes, protocol, tolerances and archived failures are
> unchanged. No scientific measurements or outreach were performed by this
> preparation pass. Numerical status remains NOT_FALSIFIED_WITHIN_SCOPE;
> engineering approval is pilot #194 only; scientific assessment remains
> NOT_ESTABLISHED, independent review and human dispositions PENDING. Gate #183
> stays OPEN pending substantive human assessment and finding dispositions.
> Hosted AI/graph execution remain disabled. A partial review will not close the
> entire gate or authorize scientific promotion.

## Preparation qualification (documentation only)

On 2026-10-10, the available local Python 3.14.3 host passed **87 targeted tests**
covering this briefing, frozen-registry integrity, discovery, release metadata,
intake/navigation and governance links. Ruff and `git diff --check` passed.
Registry validation reported `CONSISTENT`, `NOT_ESTABLISHED` scientific status
and `PENDING` independent review; all six generated discovery assets were
already consistent. Both preserved packet hashes were reconfirmed, and no
evidence, protocol, registry, application or release file was changed.

```console
python -m pytest -q tests/test_graph_reviewer_handoff.py tests/test_scientific_challenges.py tests/test_challenge_discovery.py tests/test_release_preparation.py tests/test_governance.py
python -m ruff check tests/test_graph_reviewer_handoff.py
python research/challenges/validate_registry.py
python research/challenges/build_discovery.py --check
git diff --check
```

These are documentation/retained-data checks, not fresh numerical execution,
independent scientific assessment, the supported-Python release matrix or a new
release qualification. This pass leaves the invitation and issue update local
and unposted; preparing the briefing changes no scientific or release status.
