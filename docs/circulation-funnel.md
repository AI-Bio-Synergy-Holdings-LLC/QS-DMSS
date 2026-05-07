# Circulation Funnel

This guide turns public attention into useful review, issues, commits, and
release feedback. It is intentionally narrow: every path should end with a
specific GitHub issue, pull request, or reproducibility signal.

## Current Public Entry Points

- GitHub repository: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS`
- PyPI package: `https://pypi.org/project/qs-dmss/`
- Latest release: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases`
- Zenodo concept DOI: `10.5281/zenodo.20074924`
- Review entry point: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new/choose`

## Reviewer Paths

Use these calls to action in public posts, direct outreach, and release notes.

| Reviewer type | Ask | GitHub path |
| --- | --- | --- |
| Scientific reviewer | Review model framing, assumptions, and limitation language. | Open a Scientific Review issue. |
| Reproducibility reviewer | Install from PyPI, run the demo/campaign, and report friction. | Open a Reproducibility Review issue. |
| Python/package reviewer | Inspect packaging metadata, Trusted Publishing, and install behavior. | Open a bug, feature, or contributor task. |
| Documentation reviewer | Improve first-run clarity or reviewer onboarding. | Open a contributor task or PR. |
| New contributor | Claim a focused issue with clear files and validation. | Use `good first issue` tasks. |

## Copyable Review Ask

```text
QS-DMSS is a public, citable alpha for reproducible dark matter simulation
workflows. I am looking for review in three specific areas:

1. Reproducibility: does `pip install qs-dmss`, `qs-dmss run-demo`, and
   `qs-dmss campaigns run-demo` work cleanly on your machine?
2. Scientific framing: are the model boundaries and alpha-status claims clear
   and appropriately conservative?
3. Contributor path: are there small issues that would be reasonable for a
   first external pull request?

GitHub: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS
PyPI: https://pypi.org/project/qs-dmss/
DOI: https://doi.org/10.5281/zenodo.20074924
```

## Starter Issue Backlog

Open these as real GitHub issues after this funnel lands. Keep each issue small,
assignable, and independently reviewable.

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
wheel metadata. Add a short maintainer-facing snippet that inspects
`Project-URL` fields after `python -m build`.

Validation: The release checklist shows how to confirm Repository, Issues,
Documentation, PyPI, DOI, Review, and Reviewer Quickstart URLs appear in the
wheel `METADATA`.

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
