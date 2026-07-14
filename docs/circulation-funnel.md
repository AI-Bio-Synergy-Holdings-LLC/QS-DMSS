# Circulation Funnel

Status: retained for historical outreach context. Current builder-facing
strategy lives in [product-vision.md](product-vision.md),
[contributor-roadmap.md](contributor-roadmap.md), and
[funding-roadmap.md](funding-roadmap.md).

This guide turns public attention into useful review, issues, commits, and
release feedback. It is intentionally narrow: every path should end with a
specific GitHub issue, pull request, or reproducibility signal.

## Current Public Entry Points

- Canonical website: `https://qs-dmss.studio`
- GitHub repository: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS`
- PyPI package: `https://pypi.org/project/qs-dmss/`
- Latest release: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases`
- Current GitHub and Zenodo release: `v0.13.0`
- Latest PyPI package: `v0.13.0`
- Latest archived Zenodo release DOI: `10.5281/zenodo.21348257` (`v0.13.0`)
- Open Collective: `https://opencollective.com/qs-dmss`
- Scientific review gate: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105`
- HPC/RSE site-policy review gate: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/99`
- Builder board: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/57`
- Reviewer opt-in discussion: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44`
- Reviewer opt-in issue form: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml`
- Historical outreach copy: `docs/external-review-outreach.md`
- Outreach contact avenues: `docs/outreach-contact-avenues.md`
- Historical community outreach wave 1: `docs/community-outreach-wave-1.md`

## Reviewer Paths

Use these calls to action in public posts, direct outreach, and release notes.

| Reviewer type | Ask | GitHub path |
| --- | --- | --- |
| Numerical/scientific reviewer | Comment on the Fractal SSFM validation harness, convergence, conservation, or diagnostics-only boundary. | `#105` |
| HPC/RSE reviewer | Comment on dry-run Slurm directives, environment setup, filesystem staging, or scheduler-state mapping. | `#99` |
| Reproducibility reviewer | Install from PyPI, run the demo/campaign/showcase, and report friction through the reviewer opt-in form. | reviewer opt-in form |
| Builder/contributor | Identify the first task or build lane that would make contribution easier. | `#57` |
| Sponsor/funder | Review whether funding asks map to concrete public artifacts. | Open Collective or `#57` |

## Historical Review Ask

```text
QS-DMSS v0.3.0 ran a small external review sprint.

It is beta software for reproducible package/evidence workflows, not
peer-reviewed scientific validation. If you have 10-20 minutes, please pick one
review lane and leave one GitHub comment, even if everything passes:

https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37
```

## Starter Issue Backlog

The starter backlog was seeded as GitHub issues `#17` through `#26`. Keep each
issue small, assignable, and independently reviewable; use this list as the
source of truth for future replacements or follow-up tasks.

### 1. Add Linux/macOS snippets to the reviewer quickstart

Labels: `documentation`, `good first issue`, `help wanted`

Problem: The reviewer quickstart is PowerShell-first. Add Bash equivalents for
virtualenv creation, PyPI install, wheel install, `run-demo`, and campaign demo.

Validation: Markdown renders correctly and commands are consistent with the
existing Windows path.

### 2. Add expected output examples for `qs-dmss run-demo`

Labels: `documentation`, `good first issue`

Problem: New reviewers benefit from seeing representative successful output.
Add a short sanitized output block to the reviewer quickstart.

Validation: Output includes run directory, evidence bundle, and verification
success signals without machine-local paths.

### 3. Add expected output examples for `qs-dmss campaigns run-demo`

Labels: `documentation`, `good first issue`

Problem: Campaign output includes recommendation semantics. Add a sanitized
example so reviewers know what to look for.

Validation: Output includes campaign ID, planned run count, recommendation, and
bundle path signals.

### 4. Add a glossary for evidence-bundle artifacts

Labels: `documentation`, `help wanted`

Problem: Reviewers need a quick explanation of `metrics.json`, `run.json`,
`environment.lock.json`, `manifest.sha256.json`, and final state artifacts.

Validation: README or docs link to the glossary, and every generated artifact
has a one-sentence purpose.

### 5. Add a minimal benchmark note for demo runtime expectations

Labels: `documentation`, `research-validation`, `help wanted`

Problem: The demo is a smoke path, not a scientific benchmark. Add language that
sets runtime expectations and avoids overclaiming physical significance.

Validation: Documentation distinguishes smoke validation from scientific
benchmarking.

### 6. Add a schema example for decision profiles

Labels: `documentation`, `good first issue`

Problem: The demo config includes objective, constraints, ranking, and campaign
blocks. Add a concise annotated example for reviewers editing their first
campaign.

Validation: Example remains valid YAML and maps directly to the checked-in demo.

### 7. Add a reproducibility review checklist

Labels: `reproducibility`, `documentation`, `help wanted`

Problem: External reviewers need a checklist for install, run, verify, replay,
campaign, and experiment export.

Validation: Checklist maps to existing CLI commands and issue template fields.

### 8. Add a contributor map for package modules

Labels: `documentation`, `good first issue`

Problem: New contributors need a map from user-facing features to source files.
Add a short guide covering CLI, config loading, solver, evidence, experiments,
decision logic, and cockpit API/static files.

Validation: Guide links to source paths and tests.

### 9. Add a release-check snippet for built wheel project URLs

Labels: `packaging`, `good first issue`

Problem: PyPI discoverability depends on project URLs making it into the built
wheel metadata. Keep `https://qs-dmss.studio` as the Homepage and
Documentation target, and add a short maintainer-facing snippet that inspects
`Project-URL` fields after `python -m build`.

Validation: The release checklist shows how to confirm Homepage, QS-DMSS
Studio, Repository, Issues, Documentation, PyPI, DOI, Review, and Reviewer
Quickstart URLs appear in the wheel `METADATA`.

### 10. Add a GitHub social preview asset

Labels: `documentation`, `help wanted`

Problem: Shared GitHub links currently rely on default preview behavior. Create
a simple `docs/assets/social-preview.png` concept and document upload steps for
repository settings.

Validation: Asset is 1280x640, includes QS-DMSS name and conservative
evidence-first positioning, and does not imply peer review.

## Maintainer Follow-Through

Once a starter issue is opened:

- Keep the title concrete.
- Add only labels that match the actual task.
- Include the likely files and validation command.
- Avoid assigning new contributors tasks that require scientific judgment unless
  a maintainer commits to close review.
- Prefer small documentation and test tasks for the first outside commits.

## Release Loop

When circulation metadata changes need PyPI exposure, cut a patch release rather
than editing docs only. PyPI renders metadata per immutable release, so keywords,
classifiers, and project URLs become public only after a new version is
published.
