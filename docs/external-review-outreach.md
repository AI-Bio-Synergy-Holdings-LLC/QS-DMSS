# v0.3.0 External Review Outreach

Use this page to invite focused first-pass review without creating release
churn. The ask is intentionally small: leave one GitHub comment, even if
everything passes.

Current review baseline: `qs-dmss==0.3.0` / GitHub release `v0.3.0`

Release DOI: `10.5281/zenodo.20112923`

Open Collective: `https://opencollective.com/qs-dmss`

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

## Short Broad Ask

```text
QS-DMSS v0.3.0 is ready for a small external review sprint.

It is beta software for reproducible package/evidence workflows, not
peer-reviewed scientific validation. If you have 10-20 minutes, please pick one
review lane and leave one GitHub comment, even if everything passes:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37
```

## Package/Reproducibility Ask

```text
Could you sanity-check the fresh-install path for QS-DMSS v0.3.0?

The useful test is small: install `qs-dmss==0.3.0` from PyPI in a clean
environment, run `qs-dmss run-demo`, and leave one comment about whether the
install, CLI output, and generated `./runs` artifacts were clear:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39
```

## Evidence/Benchmark Ask

```text
Could you review whether the QS-DMSS v0.3.0 evidence and benchmark path is
auditable enough for early external feedback?

The key question is not whether the model is scientifically validated. It is
whether the evidence bundle, replay path, and benchmark validation docs make
the software workflow inspectable:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40
```

## Scientific/JOSS Framing Ask

```text
Could you review the scientific-software framing for QS-DMSS v0.3.0 before any
formal JOSS or paper submission?

The project is explicitly beta for reproducible package/evidence workflows and
does not claim peer-reviewed scientific validation. Feedback on overclaiming,
missing comparison context, JOSS readiness, or unclear audience assumptions
would be especially useful:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/41
```

## Public Post

```text
QS-DMSS v0.3.0 is running a small external review sprint.

The goal is first-pass feedback on reproducibility, evidence bundles, benchmark
validation, and JOSS/scientific-software framing. The boundary is important:
QS-DMSS is beta for reproducible package/evidence workflows, not
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
