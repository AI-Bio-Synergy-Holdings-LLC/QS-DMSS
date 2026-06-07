# QS-DMSS UX Findings Report

Review date: 2026-06-07

Review target: QS-DMSS cockpit with Lab Mode MVP on `codex/lab-mode-mvp`

Review status: heuristic UX review, not a formal WCAG conformance claim

Implementation update: this PR now includes a Lab Mode polish pass addressing
the highest-leverage findings from this review: mobile reflow, disabled report
link semantics, muted text contrast, visible focus indicators, long-running
status feedback, and rail label crowding. The findings remain as the audit
trail for why those changes were made.

## Review Anchors

This review is anchored against:

- W3C Web Content Accessibility Guidelines (WCAG) 2.2: https://www.w3.org/TR/WCAG22/
- W3C WCAG 2.2 update summary: https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- Nielsen Norman Group 10 Usability Heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/

WCAG 2.2 is used here as the accessibility lens: perceivable, operable,
understandable, and robust. NN/g heuristics are used as the usability lens:
system status, real-world match, control/freedom, consistency, error
prevention, recognition, efficiency, minimalist design, error recovery, and
help/documentation.

## Scope

Reviewed surfaces:

- Cockpit landing structure and navigation.
- Lab Mode scenario selection and canonical showcase launch.
- Lab Mode completion state: evidence, replay, report, artifact links.
- Run handoff into existing cockpit detail/evidence panels.
- Desktop viewport around 1280 x 720.
- Mobile viewport around 390 x 844.
- Static structure from `index.html`, `styles.css`, and `app.js`.

Validation observed during review:

- Page title, main landmark, primary nav label, one H1, labeled inputs, and no
  unlabeled buttons were present.
- Lab Mode run completed successfully after a visible wait.
- Completion state showed `Passed`, verified evidence, replay match, report
  links, artifact links, and selected the generated run.
- Browser console warnings/errors were empty during the desktop completion pass.

## Executive Summary

The Lab Mode MVP materially improves QS-DMSS' first impression. It exposes the
product loop directly:

```text
choose scenario -> run simulation -> inspect evidence -> verify/replay -> export report
```

That is the right strategic direction. The experience now communicates "lab
session" more strongly than "plain simulator."

The current UX is strong enough for a technical reviewer on desktop, but not yet
strong enough to call premium or donor-ready. The highest-risk issues are
accessibility and responsive polish:

- Mobile Lab Mode content is clipped inside the panel at narrow width.
- Disabled report links remain keyboard-focusable before a run exists.
- Muted text appears below WCAG AA contrast minimum for normal text in sampled
  areas.
- Button and rail focus styles rely mostly on motion/shadow rather than a strong
  visible focus indicator.
- Long-running Lab Mode launch needs better progress feedback than a disabled
  button label.

## Findings

### UX-01: Mobile Lab Mode Content Clips at Narrow Width

Severity: P1

Observed behavior:

At a mobile-sized viewport around 390 x 844, Lab Mode content is visually
clipped inside the card. The heading truncates after "Run, Inspect, Verify,
Replay, E..." and the explanatory copy is cut. The page itself does not expose
horizontal scrolling, so the content is effectively hidden inside the panel.

Why it matters:

A first-time mobile user may see a premium-looking page that immediately hides
the value proposition. This damages trust and violates the "evidence-first lab"
story before the user reaches the simulation.

WCAG 2.2 anchor:

- 1.4.10 Reflow
- 1.4.4 Resize Text
- 2.4.6 Headings and Labels

NN/g anchor:

- Aesthetic and minimalist design
- Visibility of system status
- Consistency and standards

Recommended fix:

Make Lab Mode internals fully fluid below 640px:

- Set `min-width: 0` on `lab-hero`, `lab-console`, `recommendation-shell`, and
  relevant child containers.
- Ensure flow chips, status cards, and report cards wrap into one column without
  clipping.
- Avoid `overflow: hidden` hiding primary content on panels at mobile widths.
- Add a mobile visual regression check for the Lab Mode heading and first CTA.

Acceptance criteria:

- At 390px width, the full Lab Mode heading is visible.
- No primary Lab Mode copy is clipped.
- `document.documentElement.scrollWidth <= window.innerWidth`.
- The launch button and report cards remain reachable by keyboard and touch.

### UX-02: Disabled Report Links Remain Focusable Before Run

Severity: P1

Observed behavior:

Before a Lab Mode run exists, `Open Markdown` and `Open JSON` are anchors with
`href="#"` and `aria-disabled="true"`. They remain in the focus order.

Why it matters:

Keyboard and assistive-technology users encounter controls that appear actionable
but do nothing useful. This creates unnecessary cognitive load and weakens error
prevention.

WCAG 2.2 anchor:

- 2.1.1 Keyboard
- 2.4.3 Focus Order
- 2.4.4 Link Purpose
- 4.1.2 Name, Role, Value

NN/g anchor:

- Error prevention
- Recognition rather than recall
- Consistency and standards

Recommended fix:

Use one of these patterns:

- Render inactive report actions as non-focusable text until a run exists.
- Use disabled buttons for disabled actions, then replace them with anchors when
  URLs exist.
- If anchors remain, remove `href`, set `tabindex="-1"` while disabled, and
  expose a clear disabled state in text.

Acceptance criteria:

- Before Lab Mode completion, inactive report actions are not in the tab order.
- After completion, report links have real URLs and descriptive labels.

### UX-03: Muted Text Contrast Is Near or Below WCAG AA Minimum

Severity: P1

Observed behavior:

Computed samples for muted text such as Lab Mode copy and panel kicker text
showed approximately 4.08:1 contrast against the warm panel background. WCAG AA
requires at least 4.5:1 for normal text.

Why it matters:

The current palette is attractive, but the premium visual atmosphere depends
heavily on muted explanatory text. If that text is hard to read, the product
promise becomes less accessible and less persuasive.

WCAG 2.2 anchor:

- 1.4.3 Contrast (Minimum)
- 1.4.11 Non-text Contrast

NN/g anchor:

- Aesthetic and minimalist design
- Match between system and real world

Recommended fix:

- Darken `--muted` or create a stronger `--muted-readable` token for body copy.
- Re-check text on translucent panels and gradients, not only flat backgrounds.
- Keep secondary metadata visually quiet through size/spacing, not low contrast.

Acceptance criteria:

- Normal body/helper text reaches at least 4.5:1 contrast.
- Essential non-text controls and focus rings reach at least 3:1 contrast.

### UX-04: Focus Indicators Are Too Subtle for Premium Accessibility

Severity: P2

Observed behavior:

Form inputs have explicit focus outlines. Buttons, rail links, and inline links
primarily gain movement and shadow on focus. The focus state may be difficult to
track, especially for keyboard users and low-vision users.

Why it matters:

Lab Mode is meant to feel trustworthy. Keyboard navigation should feel
deliberate, not incidental.

WCAG 2.2 anchor:

- 2.4.7 Focus Visible
- 2.4.11 Focus Not Obscured (Minimum)
- 2.4.13 Focus Appearance

NN/g anchor:

- Visibility of system status
- User control and freedom

Recommended fix:

- Add a consistent high-contrast focus ring token.
- Apply it to buttons, anchors, table rows with click behavior, checkboxes,
  report links, and rail navigation.
- Avoid relying on transform or shadow alone.

Acceptance criteria:

- Every interactive element has a visible focus state.
- Focus indicator is not hidden by panel clipping or sticky rail placement.

### UX-05: Lab Mode Launch Needs Progress Feedback

Severity: P2

Observed behavior:

The Lab Mode run takes long enough that an early check can look stuck. The
button text changes to a running state, but there is no progress region, step
indicator, or live status update explaining that simulation, verification, and
replay are happening.

Why it matters:

The product claim is evidence-first workflow. Users need to see the workflow
advance, especially during the first run.

WCAG 2.2 anchor:

- 4.1.3 Status Messages
- 2.2.1 Timing Adjustable, where relevant for longer waits

NN/g anchor:

- Visibility of system status
- Help users recognize, diagnose, and recover from errors

Recommended fix:

- Add a Lab Mode progress strip: `Preparing scenario`, `Running simulation`,
  `Verifying evidence`, `Replaying result`, `Exporting report`.
- Mark the progress/status region with `aria-live="polite"`.
- If the backend cannot stream progress yet, show deterministic staged copy and
  elapsed time.

Acceptance criteria:

- Users receive visible feedback within one second of launch.
- Assistive technology receives a status update without focus theft.

### UX-06: Navigation Active State Does Not Follow Visible Section

Severity: P2

Observed behavior:

The rail highlights `Cockpit` as active even while the visible top section is
Lab Mode.

Why it matters:

The product now starts with Lab Mode, but navigation still implies the user is
in the older cockpit area. This weakens wayfinding and the repositioning story.

WCAG 2.2 anchor:

- 2.4.4 Link Purpose
- 2.4.8 Location, if targeting enhanced navigation support

NN/g anchor:

- Visibility of system status
- Consistency and standards

Recommended fix:

- Make Lab the default active rail item when the page loads at the top.
- Update active rail state on scroll or click.
- Consider renaming the first rail item from `Cockpit` to `Manual Run` or
  `Launch` so Lab Mode owns the top-level product story.

Acceptance criteria:

- The highlighted rail item matches the visible section.
- Users can infer where they are without reading the whole page.

### UX-07: Rail Labels Clip or Feel Crowded on Desktop

Severity: P3

Observed behavior:

The desktop rail is narrow. Longer labels such as `Experiments` are at risk of
clipping or feeling cramped.

Why it matters:

This is a small polish issue, but it affects perceived craftsmanship. The app is
trying to feel premium; cramped navigation pushes in the opposite direction.

WCAG 2.2 anchor:

- 1.4.10 Reflow
- 2.4.6 Headings and Labels

NN/g anchor:

- Aesthetic and minimalist design
- Recognition rather than recall

Recommended fix:

- Increase rail width or shorten labels.
- Consider icon plus text, or a top nav for desktop.
- Ensure labels remain readable at zoom and system font changes.

Acceptance criteria:

- No rail label clips at 100%, 200% zoom, or common desktop widths.

### UX-08: Long Run IDs Reduce Scannability

Severity: P3

Observed behavior:

Lab Mode run IDs are long and appear in pills/cards that are visually small.
They are valuable as evidence identifiers, but not easy to scan.

Why it matters:

Evidence-first products need traceability, but premium UX should distinguish
between human labels and machine identifiers.

WCAG 2.2 anchor:

- 2.4.6 Headings and Labels
- 3.3.2 Labels or Instructions

NN/g anchor:

- Recognition rather than recall
- Aesthetic and minimalist design

Recommended fix:

- Show a friendly run label and short ID by default.
- Provide copy/open-full-ID affordance for the full run ID.
- Use monospace and wrapping only where the full digest is intentionally shown.

Acceptance criteria:

- A user can identify the current run without parsing the full timestamped ID.
- The full ID remains available for reproducibility.

## Strengths To Preserve

- Lab Mode now leads with a clear product loop.
- The visual design has a distinctive research-lab atmosphere without feeling
  generic.
- The cockpit reuses existing evidence, verify, replay, bundle, and report
  primitives instead of duplicating concepts.
- The claim boundary is visible and honest: workflow demonstration, not
  peer-reviewed validation.
- Form labels and basic landmarks are in good shape.
- The generated run is selected in the existing run detail panel, preserving
  continuity.

## Recommended Next UX Move

Before publishing a new product release, resolve the P1 accessibility/readiness
items:

1. Mobile clipping/reflow.
2. Disabled report-link focusability.
3. Muted text contrast.

Then add one lightweight progress/status treatment for Lab Mode launch. These
four changes would move the cockpit from "technical reviewer usable" to
"credible public product preview."
