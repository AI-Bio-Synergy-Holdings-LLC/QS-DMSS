# v0.4.0 External Review Outreach

Status: retained for historical outreach context. Current builder-facing
strategy lives in [product-vision.md](product-vision.md),
[contributor-roadmap.md](contributor-roadmap.md), and
[funding-roadmap.md](funding-roadmap.md).

Use this page to invite focused first-pass review without creating release
churn. The ask is intentionally small: leave one GitHub comment, even if
everything passes.

Current review baseline: `qs-dmss==0.4.0` / GitHub release `v0.4.0`

Release DOI: `10.5281/zenodo.20500433`

Open Collective: `https://opencollective.com/qs-dmss`

Canonical website: `https://qs-dmss.studio`

Reviewer opt-in discussion:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44`

Reviewer opt-in issue form:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml`

Wave 1 tracker and direct asks: `docs/external-review-wave-1.md`

Outreach contact avenues: `docs/outreach-contact-avenues.md`

Community outreach wave 1: `docs/community-outreach-wave-1.md`

Claim boundary: QS-DMSS is beta for reproducible package/evidence workflows;
it is not peer-reviewed scientific validation.

## Routing

| Reviewer profile | Send them to | Best ask |
| --- | --- | --- |
| Broad open-source reviewer | `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37` | Pick any review lane and leave one comment. |
| Python/package reviewer | `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39` | Fresh-install from PyPI and report install or first-run friction. |
| Reproducibility reviewer | `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39` | Run the demo and confirm outputs land in caller-controlled folders. |
| Evidence/benchmark reviewer | `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40` | Inspect evidence bundles, replay, and benchmark validation clarity. |
| Scientific software reviewer | `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/41` | Check framing, non-claims, JOSS readiness, and missing comparison context. |
| Potential contributor | `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37` | Comment with the first task that would make contribution easier. |

## Historical Short Broad Ask

```text
QS-DMSS v0.4.0 was ready for a small external review sprint.

It is beta software for reproducible package/evidence workflows, not
peer-reviewed scientific validation. If you have 10-20 minutes, please pick one
review lane and leave one GitHub comment, even if everything passes:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37
```

## Package/Reproducibility Ask

```text
Could you sanity-check the fresh-install path for QS-DMSS v0.4.0?

The useful test is small: install `qs-dmss==0.4.0` from PyPI in a clean
environment, run `qs-dmss run-demo`, `qs-dmss benchmarks validate --scenario
demo-baseline`, and `qs-dmss showcase run --output-root simulation-showcase`,
then leave one comment about whether the install, CLI output, generated
evidence, and showcase artifacts were clear:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39
```

## Evidence/Benchmark Ask

```text
Could you review whether the QS-DMSS v0.4.0 evidence, benchmark, and showcase path is
auditable enough for early external feedback?

The key question is not whether the model is scientifically validated. It is
whether the evidence bundle, replay path, benchmark validation docs, and
canonical simulation showcase make the software workflow inspectable:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40
```

## Scientific/JOSS Framing Ask

```text
Could you review the scientific-software framing for QS-DMSS v0.4.0 before any
formal JOSS or paper submission?

The project is explicitly beta for reproducible package/evidence workflows and
does not claim peer-reviewed scientific validation. Feedback on overclaiming,
missing comparison context, JOSS readiness, or unclear audience assumptions
would be especially useful:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/41
```

## Historical Public Post

```text
QS-DMSS v0.4.0 ran a small external review sprint.

The goal is first-pass feedback on reproducibility, evidence bundles,
benchmark validation, the canonical simulation showcase, and
JOSS/scientific-software framing. The boundary is important: QS-DMSS is beta
for reproducible package/evidence workflows, not
peer-reviewed scientific validation.

If you have 10-20 minutes, please pick one lane and leave one GitHub comment,
even if everything passes:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37
```

## Follow-Up Rhythm

1. Send the broad ask to general open-source contacts.
2. Send the lane-specific asks only to reviewers whose expertise matches the
   lane.
3. Wait for comments before cutting any new package release.
4. Convert each concrete blocker into a small issue or pull request.
5. Close the sprint by summarizing what was learned in issue `#37`.

Funding support through Open Collective is for stewardship, maintenance,
documentation, and reproducibility infrastructure. It should not be presented
as scientific endorsement.
