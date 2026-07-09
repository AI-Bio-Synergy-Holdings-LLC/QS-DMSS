# Outreach Contact Avenues

This guide identifies public, opt-in avenues that can produce valid QS-DMSS
review contacts. It is intentionally conservative: do not scrape anonymous
traffic, do not infer identities from downloads or clones, and do not collect
private contact details in public repository files.

Current public baseline target: `qs-dmss==0.10.1` / GitHub release `v0.10.1`

Canonical public website:
`https://qs-dmss.studio`

Primary opt-in discussion:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44`

Reviewer opt-in issue form:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml`

Historical community outreach wave 1:
`docs/community-outreach-wave-1.md`

Current focused reviewer outreach packet:
`docs/v0.10-reviewer-outreach.md`

## Contact Principle

Valid outreach contacts should come from explicit public opt-in or from a
community channel where review requests are expected. Treat GitHub handles from
discussion comments, issue comments, pull requests, forks, stars, and opt-in
issues as contact paths only within GitHub unless the person independently
offers another channel.

## Priority Avenues

| Priority | Avenue | Best contact produced | Best QS-DMSS ask |
| --- | --- | --- | --- |
| 1 | GitHub Discussion #44 | Public GitHub handles from opt-in comments | Ask people to choose one review lane. |
| 1 | Reviewer opt-in issue form | Public GitHub handles with lane consent | Route the reviewer to `#105`, `#99`, or `#57`. |
| 1 | US-RSE | Research software engineers and code-review volunteers | Ask for dry-run Slurm site-policy, install/reproducibility, and evidence-workflow feedback. |
| 1 | Scientific Python community | Scientific Python maintainers and users | Ask for packaging, validation-harness, and reproducibility feedback. |
| 2 | pyOpenSci | Python package peer-review contacts | Use later for package-quality review once scope is stable. |
| 2 | OpenAstronomy community | Astronomy/astrophysics software readers | Ask for domain framing, non-claims, and JOSS-readiness feedback. |
| 2 | ReSA | Research software policy and stewardship network | Ask for research-software sustainability and review-path feedback. |
| 3 | Zenodo communities | Curators and community reviewers | Submit only to relevant communities when metadata and scope match. |
| 3 | ASCL | Astrophysics software discoverability | Use once scientific framing is mature enough for domain indexing. |
| 3 | JOSS | Formal public software review | Do not submit until preflight gaps are addressed. |

## Avenue Notes

### GitHub Opt-In

Use GitHub as the home base because it creates a durable, public, consent-based
contact path.

- Discussion #44 is for lightweight opt-in and review coordination.
- The reviewer opt-in issue form is for people willing to be routed to a lane.
- Review lane issues remain the destination for actual feedback.

### US-RSE

US-RSE is a strong first outreach target because QS-DMSS is currently strongest
as research-software infrastructure. Use the community channels for a small
review ask, not a promotional announcement.

Primary link: `https://us-rse.org/get-involved/`

Best ask: "Could one or two RSEs sanity-check the dry-run Slurm request
bundle or install/reproducibility workflow and leave one GitHub comment?"

### Scientific Python

Scientific Python is best for packaging, CLI, validation harness, and
reproducibility workflow feedback. Keep the ask grounded in the Python package
and evidence workflow rather than the scientific model.

Primary links:

- `https://scientific-python.org/community/`
- `https://discuss.scientific-python.org/`

Best ask: "Does this PyPI package and current source-validation path provide a
clear enough reproducibility path from install to generated evidence?"

### pyOpenSci

pyOpenSci is a strong eventual review path for Python package quality and
scientific open-source practices. Treat it as a readiness target rather than a
casual outreach board.

Primary link: `https://www.pyopensci.org/about-peer-review/index.html`

Best ask now: study the peer-review criteria and ask individual contacts for
pre-review feedback. Submit only when the package scope, docs, and tests are
stable enough for formal review.

### OpenAstronomy

OpenAstronomy is the best domain-adjacent place to seek careful astronomy and
astrophysics software feedback. The ask should emphasize framing and boundaries:
QS-DMSS is not claiming peer-reviewed scientific validation.

Primary link: `https://community.openastronomy.org/`

Best ask: "Is the scientific framing cautious enough, and what comparison
context is missing before a paper or JOSS path?"

### ReSA

ReSA is useful for sustainability, stewardship, and research-software ecosystem
feedback. It is less likely to produce line-by-line technical review, but it
can produce strategic contacts.

Primary link: `https://www.researchsoft.org/`

Best ask: "Does the project have the right stewardship and review structure for
an early research-software package?"

### Zenodo Communities

Zenodo communities can create curator interaction, but submissions should be
targeted. Do not submit QS-DMSS broadly just to generate attention.

Primary links:

- `https://zenodo.org/communities`
- `https://help.zenodo.org/docs/share/submit-for-review/`

Best ask: submit to a relevant community only when the record clearly matches
the community scope and curation policy.

### ASCL

ASCL is a domain discoverability target, not a short-term contact list. It may
be appropriate when QS-DMSS is ready to be indexed as astrophysics source code.

Primary link: `https://www.ascl.net/about`

Best ask: prepare a concise software description, repository link, release DOI,
and careful non-claim language before seeking indexing.

### JOSS

JOSS review is public and can generate real reviewer engagement, but it should
not be used prematurely as an outreach mechanism. Use the existing JOSS
preflight path first.

Primary link: `https://joss.readthedocs.io/`

Best ask now: request informal preflight comments through `#105` for the
Fractal SSFM validation gate or through the reviewer opt-in form. Submit only
when the review packet, paper, examples, tests, and contribution path are
ready.

## Recommended Sequence

1. Keep Discussion #44 as the public opt-in hub.
2. Add the reviewer opt-in issue form to every outreach post where GitHub users
   are likely to respond.
3. Post one small ask to US-RSE and one to Scientific Python, each routing to
   Discussion #44 and the reviewer opt-in form.
4. Ask domain contacts from OpenAstronomy to comment on `#105`, not to endorse
   the model.
5. Use pyOpenSci, ASCL, Zenodo communities, and JOSS as staged readiness gates,
   not attention hacks.

## Copyable Cross-Community Ask

```text
QS-DMSS Studio is live at https://qs-dmss.studio.

QS-DMSS v0.10.1 is looking for a few focused external reviewers.

The project is beta software for reproducible package/evidence workflows, not
peer-reviewed scientific validation. The immediate goal is modest: a few public
comments across Fractal SSFM validation, dry-run Slurm site-policy review,
public reference-data provenance, and install/reproducibility clarity.

If you are open to reviewing one small lane, please comment on one active gate:

Fractal/Quadrant SSFM validation:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105

Dry-run Slurm site-policy review:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/99

Or opt in here:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml
```
