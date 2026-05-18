# v0.3.0 External Review Wave 1

This is the first manual reviewer-conversion push for the v0.3.0 review
sprint. Keep it private-contact friendly: do not publish personal contact
details in the repository, and do not tag random people into GitHub issues
without prior context.

Goal: earn three public comments, one each on install/reproducibility,
evidence/benchmark validation, and scientific/JOSS framing.

Stable baseline: `qs-dmss==0.3.0` / GitHub release `v0.3.0`

Review sprint hub: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37`

Reviewer opt-in discussion:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44`

## Operating Rules

1. Send one issue per person.
2. Keep the ask under 20 minutes.
3. Ask for one public GitHub comment, even if everything passes.
4. Do not ask for endorsement, citation, sponsorship, or scientific validation.
5. Wait for reviewer feedback before cutting another package release.
6. If someone is interested but not ready to review, route them to the opt-in
   discussion instead of collecting private contact details in the repository.

## Wave 1 Routing

Use this table as a no-PII tracker. Put names, emails, and private channel
notes in your own private notes, not in the public repository.

| Slot | Reviewer profile | Issue | Ask status | Outcome |
| --- | --- | --- | --- | --- |
| R01 | Broad open-source maintainer | `#37` | Ready to send | Awaiting comment |
| R02 | Python packaging reviewer | `#39` | Ready to send | Awaiting comment |
| R03 | Windows Python user | `#39` | Ready to send | Awaiting comment |
| R04 | macOS/Linux Python user | `#39` | Ready to send | Awaiting comment |
| R05 | Reproducibility workflow reviewer | `#39` | Ready to send | Awaiting comment |
| R06 | Scientific Python maintainer | `#40` | Ready to send | Awaiting comment |
| R07 | Data provenance/evidence reviewer | `#40` | Ready to send | Awaiting comment |
| R08 | Benchmark/regression testing reviewer | `#40` | Ready to send | Awaiting comment |
| R09 | Research software engineer | `#40` | Ready to send | Awaiting comment |
| R10 | JOSS-experienced reviewer | `#41` | Ready to send | Awaiting comment |
| R11 | Astrophysics/cosmology reviewer | `#41` | Ready to send | Awaiting comment |
| R12 | Computational physics reviewer | `#41` | Ready to send | Awaiting comment |
| R13 | Open-source governance reviewer | `#37` | Ready to send | Awaiting comment |
| R14 | Documentation/onboarding reviewer | `#37` | Ready to send | Awaiting comment |
| R15 | Early contributor / reproducibility learner | `#39` | Ready to send | Awaiting comment |

Recommended distribution:

- Five asks to `#39` for install/reproducibility.
- Four asks to `#40` for evidence/benchmark validation.
- Three asks to `#41` for scientific/JOSS framing.
- Three asks to `#37` for broad open-source and contributor feedback.

## Direct Ask Templates

### R01 Broad Open-Source Maintainer

```text
Could I ask for a very small review of QS-DMSS v0.3.0?

The project is beta software for reproducible package/evidence workflows, not
peer-reviewed scientific validation. The useful ask is just to pick one lane
from the sprint hub and leave one GitHub comment, even if everything passes:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37
```

### R02 Python Packaging Reviewer

```text
Could you sanity-check the package install path for QS-DMSS v0.3.0?

The useful test is small: install `qs-dmss==0.3.0` from PyPI in a clean
environment, run `qs-dmss run-demo`, and leave one comment about whether the
install, CLI output, and generated `./runs` artifacts were clear:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39
```

### R03 Windows Python User

```text
Could you test QS-DMSS v0.3.0 on Windows from a clean Python environment?

I am specifically looking for first-run friction: install from PyPI, run
`qs-dmss run-demo`, and comment whether the output path and verification
signals made sense:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39
```

### R04 macOS/Linux Python User

```text
Could you test the QS-DMSS v0.3.0 fresh-install path on macOS or Linux?

The useful check is intentionally small: PyPI install, `qs-dmss run-demo`, and
one GitHub comment about any install, CLI, or generated-output confusion:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39
```

### R05 Reproducibility Workflow Reviewer

```text
Could you review whether QS-DMSS v0.3.0 gives enough evidence for a basic
reproducibility pass?

The narrow ask is to run the demo, inspect the generated artifacts, and leave
one comment about what was clear or missing:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39
```

### R06 Scientific Python Maintainer

```text
Could you review the QS-DMSS v0.3.0 evidence/benchmark workflow as scientific
Python software infrastructure?

The project is not claiming peer-reviewed scientific validation. I am looking
for whether the evidence bundle, replay path, and benchmark validation docs are
inspectable enough for early review:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40
```

### R07 Data Provenance/Evidence Reviewer

```text
Could you take a quick look at the QS-DMSS v0.3.0 evidence bundle path?

The question is whether the generated artifacts, manifest, environment lock,
verification, and replay story are clear enough for an external reviewer to
audit the workflow:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40
```

### R08 Benchmark/Regression Testing Reviewer

```text
Could you review the QS-DMSS v0.3.0 benchmark validation lane?

I am looking for software validation feedback, not model endorsement: are the
benchmark scenario, expected envelopes, and validation output useful enough as
a regression signal?

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40
```

### R09 Research Software Engineer

```text
Could you review QS-DMSS v0.3.0 as a research-software evidence workflow?

The helpful feedback is practical: what would make the evidence bundle,
benchmark validation, or replay path more trustworthy to a first external
reviewer?

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40
```

### R10 JOSS-Experienced Reviewer

```text
Could you give a small JOSS-style preflight read of QS-DMSS v0.3.0?

The project is explicitly beta for reproducible package/evidence workflows and
does not claim peer-reviewed scientific validation. Feedback on scope,
overclaiming, missing citations, or submission-readiness gaps would be useful:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/41
```

### R11 Astrophysics/Cosmology Reviewer

```text
Could you review the scientific framing of QS-DMSS v0.3.0 from an
astrophysics/cosmology perspective?

The ask is not to validate the model. It is to identify overclaims, missing
comparison context, or wording that should be more careful before any formal
paper/JOSS path:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/41
```

### R12 Computational Physics Reviewer

```text
Could you review the QS-DMSS v0.3.0 framing as computational physics software?

I am looking for boundary-setting feedback: what should be clearer about
solver limitations, validation status, comparison baselines, or research-paper
scope?

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/41
```

### R13 Open-Source Governance Reviewer

```text
Could you give QS-DMSS v0.3.0 a quick open-source readiness read?

The useful ask is to leave one comment on whether the review sprint, docs,
stewardship language, and contributor path make the project approachable:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37
```

### R14 Documentation/Onboarding Reviewer

```text
Could you review the QS-DMSS v0.3.0 onboarding path as a fresh reader?

The useful test is to start from the review sprint hub and comment where the
first 10 minutes become confusing, too dense, or under-explained:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37
```

### R15 Early Contributor / Reproducibility Learner

```text
Could you try the smallest QS-DMSS v0.3.0 reproducibility path and tell me
where it gets confusing?

Install from PyPI, run `qs-dmss run-demo`, and leave one GitHub comment. A
basic "this worked" comment is useful too:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39
```

## Follow-Up

When a reviewer responds:

1. Thank them publicly on the issue.
2. If they report a blocker, open a focused follow-up issue.
3. If they report confusion, capture the exact doc or command that caused it.
4. If they report success, ask whether their environment can be noted in the
   sprint summary.
5. Do not cut a release unless the feedback exposes a real public-adoption
   blocker.
