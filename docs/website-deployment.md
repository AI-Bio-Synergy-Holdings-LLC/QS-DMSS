# QS-DMSS Studio Website Deployment

This document records the intended website split for QS-DMSS.

## Static Public Front Door

The static site lives in [`site/`](../site/) and is intended for:

- `https://qs-dmss.studio`
- public positioning;
- install, GitHub, DOI, and Open Collective links;
- local cockpit instructions;
- claim-safe scientific boundaries;
- the live constrained `app.qs-dmss.studio` demo path.

The production edge service is the Render static site
`qs-dmss-studio-portal`:

```text
Source:            AI-Bio-Synergy-Holdings-LLC/QS-DMSS
Branch:            main
Root directory:    site
Build command:     python build_portal.py
Publish directory: .
Render origin:     https://qs-dmss-studio-portal.onrender.com
```

Render auto-deploys changes under `site/` from `main`. The existing
`.github/workflows/pages.yml` workflow remains a rollback publisher, but GitHub
Pages is not the production HTTP boundary after the DNS cutover. The
`site/CNAME` file is retained so that the rollback target remains complete.

The portal build writes `deployment.json` from Render's public build identity:

```text
https://qs-dmss.studio/deployment.json
```

The document contains the release version, full Git commit, branch, provider,
and UTC generation time. It contains no service IDs, credentials, filesystem
paths, or instance details. Keep `python build_portal.py` as the Render build
command; the generated file is deliberately ignored by Git and must represent
the deployed build rather than a developer checkout.

The Render service owns both custom-domain entries:

- `qs-dmss.studio` is the canonical domain;
- `www.qs-dmss.studio` redirects to the canonical domain; and
- the Render subdomain remains enabled as a direct recovery and smoke-test
  origin.

At the DNS provider, replace the four GitHub Pages apex `A` records with the
Render apex target `216.24.57.1`, replace the `www` GitHub Pages `CNAME` with
`qs-dmss-studio-portal.onrender.com`, and remove any conflicting `AAAA` record.
Do not change the separate `app.qs-dmss.studio` record for the hosted cockpit.
Keep the GitHub Pages records available in the change record until Render has
verified both domains and issued certificates.

### Static portal HTTP boundary

Render injects the following response headers for `/*` on the static service:

- `Content-Security-Policy`, including `frame-ancestors 'none'`;
- `X-Frame-Options: DENY`;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- `Strict-Transport-Security`; and
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`.

The production CSP is:

```text
default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'none'; script-src 'self' 'sha256-uQPjsLuxWo6Y5jZ3N/VPMV67/GD+W/MmwsScEXX88F8='; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; upgrade-insecure-requests
```

The hash allows only the inline JSON-LD block in `site/index.html`. Recompute
and replace it in the Render header rule whenever that block changes; otherwise
the browser will reject the updated structured data. Do not add
`'unsafe-inline'` as a maintenance shortcut.

Do not treat a `<meta http-equiv>` element or a host-specific `_headers` file as
equivalent. Verify the actual edge response after every header, domain, or
portal-content change. A minimal production check is:

```text
curl -sS -D - -o /dev/null https://qs-dmss.studio/
curl -sS -D - -o /dev/null https://qs-dmss.studio/assets/social-preview-v0132.png
```

Both responses must be `200`, the image must remain `image/png`, and the six
security headers above must be present. Also load the page in a clean browser
and confirm that the CSP produces no application-console violations.

## Automatic Deployment Verification

The `Verify production auto-deploy` GitHub Actions workflow runs after every
push to `main` that changes `site/**`. This path is intentional: the portal
uses a `site/` root-directory filter, while the Docker app deploys every new
`main` commit. The workflow waits up to 20 minutes for both public surfaces to
report the triggering commit:

- `https://qs-dmss.studio/deployment.json` for the portal; and
- `https://app.qs-dmss.studio/api/health` for the app.

It also verifies the package version, app health status, and baseline security
headers. A passing run therefore demonstrates that GitHub delivered the push,
both Render services deployed it, and both public edges serve the same source
revision. It does not substitute for the browser workflow smoke described in
[`hosted-studio-demo.md`](hosted-studio-demo.md).

Before merging the first provenance-enabled change, confirm the portal's Render
build command is exactly `python build_portal.py`. The workflow is expected to
fail if the portal still uses the former no-op `echo` command; this is a useful
configuration signal rather than a reason to weaken the check.

For a manual replay, dispatch the workflow with the full expected `main` SHA,
or run:

```text
python .github/scripts/verify_public_deployment.py \
  --expected-commit <40-character-main-sha> \
  --expected-version 0.13.2
```

If convergence times out, inspect the GitHub App repository authorization,
each service's `main` branch and auto-deploy settings, the portal root-directory
filter, and Render build/deploy logs. Do not use a manual deploy until the
missed automatic event has been captured for diagnosis.

## Constrained Live App (Live)

The live cockpit should not be deployed as an unrestricted public compute
service. The deployed application is:

```text
https://app.qs-dmss.studio
```

The hosted app is limited to:

- packaged scenarios and packaged study templates only;
- short-lived generated artifacts;
- explicit resource limits and cleanup;
- no arbitrary YAML uploads;
- no user-provided filesystem paths;
- no real Slurm, SSH, PBS, or scheduler submission;
- visible scientific non-claims and evidence/replay boundaries.

The Render service is deployed from the repository Blueprint, uses session-scoped
temporary outputs, and serves the custom domain with HTTPS. Run the public smoke
check in [`hosted-studio-demo.md`](hosted-studio-demo.md) after deployment or
guardrail changes.

## Public Story

The website should keep the current QS-DMSS product loop as the top-level
message:

```text
run simulations -> inspect evidence -> compare campaigns -> publish reproducible artifacts
```

The site should not imply peer-reviewed scientific validation, production HPC
support, or endorsed downstream use.
