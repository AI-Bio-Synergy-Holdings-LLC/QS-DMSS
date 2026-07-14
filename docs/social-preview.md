# GitHub Social Preview

The repository social preview asset lives at:

```text
docs/assets/social-preview.png
```

The Studio portal Open Graph/Twitter image and editable source live at:

```text
site/assets/social-preview-v0131.png
docs/assets/studio-portal-social-preview.svg
```

The hosted cockpit Open Graph/Twitter image and editable source live at:

```text
src/qs_dmss/cockpit/static/hosted-demo-social-preview-v0131.png
docs/assets/hosted-demo-social-preview.svg
```

The GitHub repository preview is 1280x640. The Studio portal and hosted demo
Open Graph/Twitter images are 1200x630. Their versioned filenames make a
fresh social-image URL available when a crawler refreshes its metadata cache.
The previews use the same Studio visual direction and clearly distinguish the
local-first portal from the constrained hosted demo:

```text
QS-DMSS STUDIO — Evidence-first research workflows
Evidence before inference.
Research Runbook · local validation · Evidence Assistant
qs-dmss.studio
Local-first public beta. Workflows are evidence, not scientific claims.
```

## Upload Steps

Repository administrators can upload the image in GitHub:

1. Open repository `Settings`.
2. Open `General`.
3. Find `Social preview`.
4. Upload `docs/assets/social-preview.png`.
5. Save the repository settings.

GitHub and social platforms may cache social previews, so link previews can
take time to update after upload.

## Hosted Demo Card

The hosted card is 1200x630 and distinguishes the interactive demo from the
local-first product portal. It emphasizes the constrained workflow, contextual
guidance, and the temporary nature of exported outputs:

```text
Guided work. Reviewable evidence.
Packaged studies. Guided review. Temporary outputs.
```

## Positioning Guardrail

The preview should make QS-DMSS recognizable in public circulation without
claiming validated scientific results. Keep future preview copy aligned with
the current project language: beta for reproducible package/evidence workflows;
not peer-reviewed scientific validation.
