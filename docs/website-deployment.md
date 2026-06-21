# QS-DMSS Studio Website Deployment

This document records the intended website split for QS-DMSS.

## Phase 1: Static Public Front Door

The static site lives in [`site/`](../site/) and is intended for:

- `https://qs-dmss.studio`
- public positioning;
- install, GitHub, DOI, and Open Collective links;
- local cockpit instructions;
- claim-safe scientific boundaries;
- the future `app.qs-dmss.studio` path.

The site is deployed by `.github/workflows/pages.yml` through GitHub Pages.
GitHub Pages should be configured to use **GitHub Actions** as the publishing
source. The repository includes `site/CNAME` with:

```text
qs-dmss.studio
```

After the workflow is active, configure DNS for the domain provider according
to GitHub Pages custom-domain instructions, verify the domain in GitHub, and
enable HTTPS enforcement.

## Phase 2: Constrained Live App

The live cockpit should not be deployed as an unrestricted public compute
service. The future application target is:

```text
https://app.qs-dmss.studio
```

The first hosted app should be limited to:

- packaged scenarios and packaged study templates only;
- short-lived generated artifacts;
- explicit resource limits and cleanup;
- no arbitrary YAML uploads;
- no user-provided filesystem paths;
- no real Slurm, SSH, PBS, or scheduler submission;
- visible scientific non-claims and evidence/replay boundaries.

This keeps the public website focused on trust and adoption before exposing a
runtime surface.

## Public Story

The website should keep the current QS-DMSS product loop as the top-level
message:

```text
run simulations -> inspect evidence -> compare campaigns -> publish reproducible artifacts
```

The site should not imply peer-reviewed scientific validation, production HPC
support, or endorsed downstream use.
