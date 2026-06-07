# QS-DMSS User Readiness Scorecard

Review date: 2026-06-07

Reviewed surface: QS-DMSS cockpit with Lab Mode MVP on `codex/lab-mode-mvp`

Implementation update: after this scorecard was created, the same PR received a
Lab Mode polish pass for the largest readiness blockers: mobile reflow,
disabled report-link semantics, muted text contrast, visible focus indicators,
long-running status feedback, and rail label crowding. Treat the numeric score
as the pre-polish baseline until a formal re-score is performed.

Score scale:

- 5: ready for broad public use
- 4: strong beta, minor polish remains
- 3: usable by technical reviewers, important friction remains
- 2: promising but fragile
- 1: not ready for external users

This scorecard is not a WCAG conformance claim. It is a product-readiness view
anchored against WCAG 2.2 and Nielsen Norman Group usability heuristics.

References:

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- NN/g 10 usability heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/

## Overall Score

Current readiness: 3.3 / 5

Readiness label: reviewer-ready desktop beta, not yet premium public product

Summary:

QS-DMSS now has a much clearer first-use product loop through Lab Mode. A
technical reviewer can run the showcase, verify/replay evidence, and inspect
artifacts. The remaining readiness gap is not the simulation spine; it is
accessibility polish, mobile behavior, progress feedback, and premium
orientation.

## Category Scores

### 1. First Impression and Product Promise

Score: 4.0 / 5

What works:

- Lab Mode leads with a clear workflow: run, inspect, verify, replay, export.
- The visual direction feels distinct and credible.
- The claim boundary is honest and visible.

What holds it back:

- Navigation still highlights `Cockpit` while Lab Mode is the visible lead
  section.
- Long labels and IDs reduce polish.

Next lift:

- Make Lab Mode the default active product entry.
- Separate human-readable labels from machine IDs.

### 2. Lab Mode Task Completion

Score: 3.8 / 5

What works:

- A user can launch the canonical showcase.
- Completion shows pass status, evidence verification, replay match, report
  links, artifacts, and selected run detail.
- The flow reuses existing cockpit primitives cleanly.

What holds it back:

- Launch progress feels quiet during the wait.
- Report links are disabled-but-focusable before a run exists.

Next lift:

- Add staged progress feedback.
- Improve inactive/active report action semantics.

### 3. Evidence Comprehension

Score: 3.4 / 5

What works:

- Evidence, replay, bundle, report, and artifact concepts are all present.
- Lab Mode ties the run to generated artifacts.

What holds it back:

- Users still need to infer what each artifact means.
- Evidence bundle contents are more inventory than explanation.

Next lift:

- Add Evidence Explorer preview with manifest summary, replay status, config
  digest, and artifact categories.

### 4. Accessibility Readiness

Score: 2.6 / 5

What works:

- Page title, main landmark, primary nav label, H1, labeled form controls, and
  no unlabeled buttons were observed.
- Inputs have explicit focus outlines.

What holds it back:

- Mobile Lab Mode content clips at narrow widths.
- Muted text samples are around 4.08:1 contrast, below the 4.5:1 WCAG AA target
  for normal text.
- Button and rail focus states are too subtle.
- Disabled report anchors remain focusable.

Next lift:

- Fix reflow, contrast, disabled action semantics, and focus treatment before
  positioning Lab Mode as premium-ready.

### 5. Mobile Readiness

Score: 2.0 / 5

What works:

- The page adapts into a single-column shell.
- The rail changes into a compact two-column nav.
- No page-level horizontal overflow was observed at 390px.

What holds it back:

- Lab Mode card content is clipped inside the panel.
- Heading and copy are visibly cut.
- Flow chips consume too much vertical/inner width.

Next lift:

- Treat mobile Lab Mode as a release-gating polish pass.

### 6. Visual Design and Premium Feel

Score: 3.7 / 5

What works:

- The warm research-lab palette, typography, and card system feel intentional.
- The UI avoids generic dashboard blandness.
- The product loop chips are memorable.

What holds it back:

- Rail label crowding and clipped mobile content make the experience feel less
  finished.
- Some muted text is too low contrast.
- Long IDs create visual noise.

Next lift:

- Apply a polish pass to navigation, typography contrast, and ID presentation.

### 7. Error Prevention and Recovery

Score: 3.0 / 5

What works:

- Existing API errors are surfaced through toasts.
- Campaign failure handling is already stronger than earlier phases.

What holds it back:

- Lab Mode does not yet explain where a failure occurred.
- Empty states are plain and not always next-action oriented.

Next lift:

- Add workflow-step failure messages: simulation, verification, replay, export.

### 8. Contributor and Reviewer Readiness

Score: 3.8 / 5

What works:

- The flow is test-backed and reproducible.
- The UI demonstrates the evidence-first moat better than docs alone.
- New docs and tests give contributors a clear seam.

What holds it back:

- Scenario metadata is hard-coded/lightweight.
- The cockpit does not yet advertise how to add a scenario.

Next lift:

- Add scenario metadata cards and a contributor scenario template.

### 9. Sponsor/Donation Conversion Readiness

Score: 3.1 / 5

What works:

- Lab Mode creates a concrete funding story.
- The workflow demonstrates why QS-DMSS is more than another simulator.

What holds it back:

- The cockpit does not yet connect successful use to the next funded milestone.
- Premium polish gaps may lower confidence for non-technical sponsors.

Next lift:

- Add a secondary post-success CTA that points to Open Collective and the next
  Lab Mode milestone.

## Readiness Gates

### Gate A: Public Product Preview

Status: Not yet

Required:

- Fix mobile clipping.
- Fix disabled report actions.
- Improve contrast.
- Improve focus states.

### Gate B: Technical Reviewer Demo

Status: Yes, with caveats

Current caveats:

- Recommend desktop review first.
- Tell reviewers that mobile polish is in progress.
- Do not claim WCAG conformance yet.

### Gate C: v0.5.0 Candidate

Status: Close, but should wait

Required:

- Resolve Gate A.
- Add Lab Mode progress strip.
- Add at least one Evidence Explorer/report-preview improvement.
- Re-run local browser smoke and fresh-install smoke.

### Gate D: Donation-Worthy Product Demo

Status: Emerging

Required:

- Premium Lab Mode polish.
- Clear Evidence Explorer preview.
- Report preview/export composer.
- One visible "fund this next milestone" path after successful use.

## Recommended Readiness Target

Target before public v0.5.0 positioning:

- Overall score: 4.1 / 5 or higher
- Accessibility readiness: 3.8 / 5 or higher
- Mobile readiness: 3.8 / 5 or higher
- Lab Mode task completion: 4.3 / 5 or higher

Best next action:

Open a focused UI polish PR that fixes the P0 items from
`docs/premium-polish-backlog.md`. Do not cut a new release until those are
resolved and Lab Mode feels strong on both desktop and mobile.
