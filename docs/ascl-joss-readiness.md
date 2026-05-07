# ASCL and JOSS Readiness

This document keeps QS-DMSS honest about public scholarly-indexing readiness.
It separates what can be prepared now from what should wait for external
research-use evidence.

Last reviewed: 2026-05-07

## Current Public Baseline

- Repository: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS`
- PyPI package: `https://pypi.org/project/qs-dmss/`
- Latest release: `v0.1.4`
- Zenodo version DOI: `10.5281/zenodo.20075891`
- Zenodo concept DOI: `10.5281/zenodo.20074924`
- License: Apache-2.0
- Public install path: `python -m pip install qs-dmss`
- Current maturity label: alpha reference implementation

## ASCL Readiness

ASCL is a strong fit once QS-DMSS has a research-use artifact in scope. The
ASCL states that it registers source codes used in astronomy, astrophysics, or
solar-system research that are available for examination, including research
submitted for peer review or accepted theses. It also asks submitters for a code
name, author names, description, download URL, and a link to a research paper in
which the code was used.

Sources:

- `https://www.ascl.net/submissions`
- `https://ascl.net/home/getwp/3593`

Ready now:

- Source code is public and downloadable.
- Apache-2.0 license is present.
- PyPI, GitHub release, Zenodo DOI, README, SECURITY, CONTRIBUTING, and tests
  are present.
- `codemeta.json` is present to speed ASCL metadata entry.

Blocking gate before submission:

- Provide a research paper, preprint submitted for peer review, or accepted
  thesis that uses QS-DMSS. Do not submit to ASCL on aspiration alone.

Recommended ASCL submission packet once the gate is satisfied:

```text
Code name:
QS-DMSS

Authors:
AI Bio Synergy Holdings LLC

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
QS-DMSS v0.1.4, Zenodo, doi:10.5281/zenodo.20075891

Research paper using the code:
TODO: add submitted preprint, peer-reviewed paper, or accepted thesis URL.
```

## JOSS Readiness

JOSS is also a fit eventually, but the current high-leverage move is
pre-submission hardening rather than immediate submission. JOSS requires an open
source repository, issue tracking, a research application, a `paper.md` in the
software repository, documentation, tests, and reviewable functionality. JOSS
also screens for sufficient public development history and concrete research-use
evidence.

Sources:

- `https://joss.readthedocs.io/en/latest/submitting.html`
- `https://joss.readthedocs.io/en/latest/review_criteria.html`
- `https://joss.readthedocs.io/en/latest/paper.html`

Ready now:

- Open source license and public repository are present.
- Install path is package-manager based through PyPI.
- CI validates Python 3.10 through 3.13 and Docker smoke.
- The package has tests, replay, verification, evidence bundles, and release
  artifacts.
- A pre-submission paper scaffold now lives under `paper/`.

Not ready yet:

- Public development history is still young relative to the JOSS screening
  expectation of more than six months of public development history.
- External research adoption is not yet demonstrated.
- The JOSS author list, affiliations, and acknowledgements need human owner
  confirmation.
- The paper still needs a stronger state-of-the-field comparison and a concrete
  research impact statement backed by adoption, benchmark, preprint, or workflow
  evidence.

Recommended JOSS path:

1. Keep improving the public repository through ordinary issues and pull
   requests rather than private bursts.
2. Add a small benchmark or reproducible example that demonstrates why the
   evidence-first design matters.
3. Use QS-DMSS in a submitted research preprint or documented research workflow.
4. Collect at least one external review, issue, fork, or usage signal.
5. Replace placeholders in `paper/paper.md` with final authors, affiliations,
   field comparison, impact evidence, and AI usage disclosure.
6. Submit only after the history and research-use gates are credible.

## Immediate Public Positioning

The right public claim today is:

```text
QS-DMSS is a public, installable, citable alpha reference implementation for
reproducible QuantumScalar dark matter simulation workflows.
```

Avoid claiming:

- ASCL indexed
- JOSS submitted
- JOSS accepted
- peer-reviewed scientific result
- externally validated dark matter model

Use the launch post in `docs/public-technical-launch-post.md` for a careful
public announcement.
