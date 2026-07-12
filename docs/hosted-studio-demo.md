# Hosted Studio Demo

QS-DMSS can run as a constrained public cockpit at `app.qs-dmss.studio`.
This mode is intentionally narrower than the local cockpit. It is meant to let a
fresh visitor experience the evidence-first workflow without exposing an open
compute or upload surface.

Production status: [https://app.qs-dmss.studio](https://app.qs-dmss.studio) is
deployed from `render.yaml`, DNS-verified, HTTPS-enabled, and linked from the
canonical Studio website.

## Public Demo Contract

Set `QS_DMSS_HOSTED_DEMO=1` to enable hosted-demo mode.

Allowed in hosted mode:

- Packaged Lab Mode scenarios: canonical simulation, self-interaction response,
  and Fractal/Quadrant SSFM validation preview.
- Packaged guided comparison.
- Packaged `self-interaction-sweep` Campaign Studio study template.
- Evidence verification and replay for generated runs.
- Report, portable HTML workbook, bundle, artifact, and research-object Markdown
  export downloads.

Disabled in hosted mode:

- Arbitrary run configs through `/api/runs`.
- Arbitrary sweeps through `/api/sweeps`.
- Edited/custom Campaign Studio launches.
- Study-template save/import uploads.
- Workspace import/export uploads and snapshots.

Visible user notice:

> Public hosted demo outputs are temporary; do not upload sensitive data.

## Runtime Guardrails

Hosted mode uses a browser-session cookie named `qs_dmss_demo_session` and stores
outputs under a session-scoped directory below the configured output root.
Session outputs are temporary and eligible for cleanup after the configured TTL.

Default hosted caps:

| Setting | Default | Purpose |
| --- | ---: | --- |
| `QS_DMSS_HOSTED_DEMO_TTL_SECONDS` | `3600` | Session-output retention window. |
| `QS_DMSS_HOSTED_DEMO_MAX_CAMPAIGN_RUNS` | `5` | Caps public campaign fan-out. |
| `QS_DMSS_HOSTED_DEMO_MAX_ENGINE_STEPS` | `12` | Caps each configured run. |
| `QS_DMSS_HOSTED_DEMO_MAX_TOTAL_ENGINE_STEPS` | `60` | Caps campaign-size envelope. |
| `QS_DMSS_HOSTED_DEMO_MAX_GRID_CELLS` | `4096` | Caps public grid size. |
| `QS_DMSS_HOSTED_DEMO_MAX_ARTIFACT_BYTES` | `10485760` | Caps each downloadable artifact. |

The hosted app also allows one active job per browser session/client pair.

## Interactive Demo Path

The hosted cockpit presents one progressive path before the deeper research
surfaces:

1. Run the packaged deterministic showcase and inspect verification/replay.
2. Run the three packaged variants and inspect their parameters, metrics,
   bundle filenames, and SHA-256 identities directly in the cockpit.
3. Open or download the comparison research workbook, then compose the
   publication-oriented research object.

Local configuration editing, workspace import/export, and template management
remain available in local mode but are hidden from the public hosted path. Run,
experiment, and evidence sections remain available and the navigation follows
the current section as the user scrolls.

## Accessibility and Usability Baseline

The hosted cockpit targets WCAG 2.2 Level AA across desktop and responsive
layouts. Its application shell includes a main-content skip link, named
landmarks and data tables, visible keyboard focus, minimum-size controls,
reduced-motion support, mobile reflow, and status announcements for long-running
operations. Navigation follows document order and reports the current section.

Interaction reviews also use Nielsen Norman Group's ten usability heuristics,
especially visibility of system status, consistency, error prevention,
recognition rather than recall, and help/documentation. This engineering target
is not an independent accessibility certification; assistive-technology and
user testing remain part of ongoing release validation.

## Render Deployment

This repository includes `render.yaml` for a single Docker-backed web service.
The Docker image builds the wheel, installs QS-DMSS, and starts:

```bash
qs-dmss cockpit --host 0.0.0.0 --port ${PORT:-8001} --output-root /app/runs
```

Recommended sequence:

1. Deploy the current green `main` commit (or the corresponding release tag).
2. Open Render Blueprint creation for the repository.
3. Confirm the `qs-dmss-studio-app` service uses `runtime: docker`.
4. Confirm `QS_DMSS_HOSTED_DEMO=1` is set.
5. Deploy and wait for `/api/health` to report `status: ok`.
6. Add the custom domain `app.qs-dmss.studio` in Render.
7. Add the DNS record Render provides for `app.qs-dmss.studio`.
8. Verify HTTPS, then run one public browser smoke:
   - Open `https://app.qs-dmss.studio`.
   - Run Lab Mode.
   - Run Guided Comparison.
   - Open the comparison workbook in a new tab and download the `.html` copy.
   - Run the Self-Interaction Sweep template.
   - Compose and download a research-object Markdown export.
   - Confirm custom run, sweep, import, and workspace upload actions are blocked.

Render notes:

- The public demo uses the Starter plan for an always-on instance without the
  free-tier inactivity delay.
- Reassess CPU and memory capacity from measured runtime and concurrency before
  moving to a larger service class.
- Do not add API tokens or external data credentials to this service until an
  authenticated workspace model exists.

## Optional Python Enhancement Libraries

The hosted baseline intentionally does not add visualization-specific runtime
dependencies. Visible enhancements should continue to preserve the hosted-demo
guardrails and the wheel-installed local cockpit path.

Good candidates:

- `plotly`: interactive artifact/metric plots inside report previews. Useful for
  visual polish, but heavier than the current static SVG path.
- `altair`: declarative charts for small CSV previews. Cleaner for scientific
  summaries, but adds a visualization stack.
- `pydantic-settings`: typed environment configuration for hosted limits if
  settings grow beyond the current small env-var surface.
- `slowapi`: rate limiting for public endpoints if Render traffic increases.
  This is best paired with a persistent store before relying on it seriously.
- `apscheduler`: more explicit background cleanup if session TTL cleanup needs
  to run independently of incoming requests.

Recommendation:

Keep the current dependency-light rendering path until measured use justifies a
larger client payload. The first operational enhancement should be persistent
rate limiting and a stronger cleanup worker only after traffic patterns justify
it.
