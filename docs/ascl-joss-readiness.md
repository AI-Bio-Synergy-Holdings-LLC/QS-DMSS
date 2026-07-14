# ASCL and JOSS Readiness

This document keeps QS-DMSS honest about public scholarly-indexing readiness.
It separates materials that can be prepared now from claims and submissions
that should wait for external research-use evidence.

Last reviewed: 2026-06-01

## Current Public Baseline

- Repository: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS`
- Website: `https://qs-dmss.studio`
- PyPI package: `https://pypi.org/project/qs-dmss/`
- Current GitHub and Zenodo release: `v0.13.1`
- Latest PyPI package: `v0.13.1`
- Latest archived release DOI: `10.5281/zenodo.21348597`
- `v0.13.1` release DOI: `10.5281/zenodo.21348597`
- Previous `v0.13.0` release DOI: `10.5281/zenodo.21348257`
- Previous `v0.12.0` release DOI: `10.5281/zenodo.21329711`
- `v0.11.0` release DOI: `10.5281/zenodo.21319023`
- Previous archived release DOI: `10.5281/zenodo.20693736`
- `v0.8.0` release DOI: `10.5281/zenodo.20673804`
- `v0.7.0` release DOI: `10.5281/zenodo.20671389`
- `v0.6.1` release DOI: `10.5281/zenodo.20631860`
- `v0.6.0` product milestone DOI: `10.5281/zenodo.20618884`
- `v0.5.0` release DOI: `10.5281/zenodo.20617028`
- Zenodo concept DOI: `10.5281/zenodo.20074924`
- License: Apache-2.0
- Public install path: `python -m pip install qs-dmss`
- Current maturity label: beta for reproducible package/evidence workflows; not peer-reviewed scientific validation

## ASCL Readiness

ASCL is a strong fit once QS-DMSS has a research-use artifact in scope. ASCL
describes itself as a registry for source codes of interest to astronomy,
astrophysics, and solar-system research, and its submission materials ask for
code metadata plus a research paper in which the code was used.

Sources:

- `https://www.ascl.net/submissions`
- `https://ascl.net/`
- `https://www.ascl.net/about`

Ready now:

- Source code is public and downloadable.
- Apache-2.0 license is present.
- PyPI, GitHub release, Zenodo DOI, README, SECURITY, CONTRIBUTING, issue
  templates, and tests are present.
- Cross-platform fresh-install smoke validates PyPI and GitHub release-wheel
  install paths on Linux, macOS, and Windows.
- `codemeta.json` is present to speed metadata entry and software discovery.

Blocking gate before submission:

- Provide a research paper, submitted preprint, peer-reviewed article, or
  accepted thesis that uses QS-DMSS. Do not submit to ASCL on aspiration alone.

Recommended ASCL submission packet once the gate is satisfied:

```text
Code name:
QS-DMSS

Authors:
AI-Bio Synergy Holdings LLC

Description:
QS-DMSS is an evidence-first reference package for deterministic
Schrodinger-Poisson-style dark matter simulation workflows. It packages a
NumPy-based split-step solver with reproducible run ledgers, manifest-verified
evidence bundles, replay and verification commands, template-driven parameter
campaigns, objective-based run ranking, and a local cockpit for inspection and
export. The project is intended to make early-stage simulation experiments
auditable by preserving configuration, environment, metrics, final state
artifacts, reports, and bundle manifests for each run.

Download URL:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS

Package URL:
https://pypi.org/project/qs-dmss/

Preferred citation:
QS-DMSS v0.9.0, Zenodo version DOI doi:10.5281/zenodo.20693736.
Use the concept DOI doi:10.5281/zenodo.20074924 for project-level references.

Research paper using the code:
TODO: add submitted preprint, peer-reviewed paper, or accepted thesis URL.
```

## JOSS Readiness

JOSS is also a fit eventually, but the current high-leverage move is
pre-submission hardening rather than immediate submission. JOSS submission and
review criteria emphasize a public open source repository, documentation,
tests, issue tracking, reviewable functionality, research application, a
software paper, and sufficient public development history.

Sources:

- `https://joss.readthedocs.io/en/latest/submitting.html`
- `https://joss.readthedocs.io/en/latest/review_criteria.html`
- `https://joss.readthedocs.io/en/latest/paper.html`

Ready now:

- Open source license and public repository are present.
- Install path is package-manager based through PyPI.
- CI validates Python 3.10 through 3.13 and Docker smoke.
- Fresh-install smoke validates PyPI and GitHub release-wheel paths on Linux,
  macOS, and Windows.
- The package has tests, replay, verification, evidence bundles, and release
  artifacts.
- A reviewer packet now gives external reviewers a single entrypoint for the
  review claim, fast validation path, artifacts to inspect, and issue lanes.
- A pre-submission paper scaffold lives under `paper/`.

Not ready yet:

- Public development history is still young relative to JOSS screening
  expectations.
- External research adoption is not yet demonstrated.
- The JOSS author list, affiliations, acknowledgements, and AI usage disclosure
  need human owner confirmation.
- The paper still needs a stronger state-of-the-field comparison and a concrete
  research impact statement backed by adoption, benchmark, preprint, or workflow
  evidence.

The detailed preflight matrix lives in
[joss-preflight.md](joss-preflight.md).

Recommended JOSS path:

1. Keep improving the public repository through ordinary issues and pull
   requests rather than private bursts.
2. Expand the packaged benchmark-validation spine with reviewer-driven
   scenarios that demonstrate why the evidence-first design matters.
3. Use QS-DMSS in a submitted research preprint or documented research workflow.
4. Collect at least one external review, issue, fork, or usage signal.
5. Replace placeholders in `paper/paper.md` with final authors, affiliations,
   field comparison, impact evidence, and AI usage disclosure.
6. Submit only after the history and research-use gates are credible.

## Immediate Public Positioning

The right public claim today is:

```text
QS-DMSS is public, citable beta software for reproducible package/evidence
workflows; it is not peer-reviewed scientific validation.
```

Avoid claiming:

- ASCL indexed
- JOSS submitted
- JOSS accepted
- peer-reviewed scientific result
- externally validated dark matter model

Use the launch post in `docs/public-technical-launch-post.md` for a careful
public announcement.
