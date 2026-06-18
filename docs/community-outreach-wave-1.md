# Community Outreach Wave 1

Status: retained as historical outreach planning for the early v0.3.0 review
sprint. Current outreach targets should use `v0.9.0`, issue #105, issue #99,
issue #57, and the reviewer opt-in form.

This wave targets three communities that can produce valid, opt-in reviewer
contacts for QS-DMSS `v0.3.0` without scraping anonymous traffic or collecting
private contact details in the repository.

Goal: earn three public review signals, one each on install/reproducibility,
evidence/benchmark validation, and scientific/JOSS framing.

Stable baseline: `qs-dmss==0.3.0` / GitHub release `v0.3.0`

Reviewer opt-in discussion:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44`

Reviewer opt-in issue form:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml`

## Execution Boundary

These communities require the maintainer's own membership, account, or
authenticated browser session. Do not post through an account that is not yours,
do not impersonate project maintainers, and do not send unsolicited direct
messages to individual community members.

## Targets

| Community | Channel | Status | Primary ask |
| --- | --- | --- | --- |
| US-RSE | Slack `#wg-code-review`, or relevant member channel | Ready for maintainer post | RSE review of install/reproducibility and evidence workflow |
| Scientific Python | Discussion forum or Discord | Ready for maintainer post | Scientific Python package/reproducibility feedback |
| OpenAstronomy | Community forum Showcase or question-style post | Ready for maintainer post | Scientific framing, non-claims, and JOSS-preflight feedback |

## Post 1: US-RSE

Suggested channel: US-RSE Slack `#wg-code-review` if available; otherwise a
general/relevant member channel where review asks are welcome.

```text
Small research-software review ask: QS-DMSS v0.3.0 is looking for first-pass
external feedback on its reproducible package/evidence workflow.

The project is beta software for reproducible package/evidence workflows, not
peer-reviewed scientific validation. The useful review is small: install from
PyPI, run the demo, inspect the generated evidence bundle, or comment on the
review path.

Current goal: three public comments, one each on install/reproducibility,
evidence/benchmark validation, and scientific/JOSS framing.

Opt-in / coordination:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44

Reviewer opt-in issue form:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml

No endorsement is requested; a "this worked on my machine" comment is useful.
```

## Post 2: Scientific Python

Suggested channel: Scientific Python discussion forum or Discord channel where
package/reproducibility feedback requests are welcome.

```text
Request for small Scientific Python package feedback: QS-DMSS v0.3.0 is seeking
first-pass review of its PyPI install and reproducible evidence workflow.

The package is beta for reproducible package/evidence workflows; it is not
claiming peer-reviewed scientific validation. I am looking for practical
feedback on whether the install -> run -> evidence bundle -> verify/replay path
is understandable to a fresh reviewer.

Useful lanes:

- Install/reproducibility: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39
- Evidence bundle and benchmark validation: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40
- Opt-in / coordination: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44

If you are open to one small review, please opt in here:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml
```

## Post 3: OpenAstronomy

Suggested channel: OpenAstronomy Community Showcase if a project-share post is
appropriate; otherwise use a question-style post asking for framing feedback.

```text
QS-DMSS v0.3.0 is looking for careful astronomy/astrophysics software framing
feedback before any formal paper or JOSS path.

Important boundary: QS-DMSS is beta software for reproducible package/evidence
workflows. It does not claim peer-reviewed scientific validation or validated
physical conclusions from the bundled demo.

The most useful feedback would be on overclaiming risk, missing comparison
context, solver/validation caveats, and whether the JOSS-preflight framing is
appropriately conservative.

Scientific/JOSS framing lane:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/41

Opt-in / coordination:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44

Reviewer opt-in issue form:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml
```

## Follow-Up

After each post:

1. Save the public post URL in the tracking issue.
2. Thank anyone who opts in through Discussion #44 or the issue form.
3. Route each reviewer to exactly one review lane.
4. Convert concrete blockers into focused issues.
5. Do not cut a release unless feedback exposes a real public-adoption blocker.

## Official Entry Points Checked

- US-RSE get involved: `https://us-rse.org/get-involved/`
- US-RSE working groups: `https://us-rse.org/working-groups/`
- Scientific Python community: `https://scientific-python.org/community/`
- Scientific Python forum: `https://discuss.scientific-python.org/`
- OpenAstronomy community: `https://community.openastronomy.org/`
