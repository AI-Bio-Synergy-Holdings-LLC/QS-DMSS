# QS-DMSS Premium Polish Backlog

Review date: 2026-06-07

Backlog purpose: convert the Lab Mode MVP from a functional technical cockpit
into a premium, fundable, contributor-attractive simulation lab experience.

Implementation update: the Priority 0 release-gating polish items below are
addressed in this PR's Lab Mode polish pass. The backlog keeps the acceptance
criteria visible for future regression checks.

Anchors:

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- NN/g 10 usability heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/

## Priority 0: Release-Gating Polish

These should be fixed before using Lab Mode as the public product centerpiece.

### P0-1: Fix Mobile Lab Mode Reflow

Outcome:

Lab Mode reads cleanly on mobile without clipped headings, hidden copy, or
trapped content.

Tasks:

- Add `min-width: 0` to Lab Mode grid children and cards.
- Ensure `.lab-hero`, `.lab-console`, `.recommendation-shell`, and flow chips
  collapse gracefully below 640px.
- Avoid `overflow: hidden` hiding primary text in narrow panels.
- Add a smoke check or screenshot note for 390px width.

Acceptance:

- Full Lab Mode headline visible at 390px width.
- No primary Lab Mode text clipped.
- No horizontal page overflow.

Standards:

- WCAG 1.4.10 Reflow
- NN/g Consistency and Standards

### P0-2: Replace Focusable Disabled Report Anchors

Outcome:

Inactive report actions do not confuse keyboard or screen-reader users.

Tasks:

- Before a Lab Mode run exists, render `Open Markdown` and `Open JSON` as
  non-focusable placeholders or disabled buttons.
- After completion, render real links with real URLs.
- Add a regression check for disabled report actions being out of tab order.

Acceptance:

- `Open Markdown` and `Open JSON` are not focusable before completion.
- After completion, both links are focusable and have descriptive destinations.

Standards:

- WCAG 2.1.1 Keyboard
- WCAG 4.1.2 Name, Role, Value
- NN/g Error Prevention

### P0-3: Raise Muted Text Contrast

Outcome:

Secondary explanatory text remains elegant but meets readable contrast.

Tasks:

- Replace or supplement `--muted` with a darker readable token.
- Apply the stronger token to body helper text, panel kickers, badges, chips,
  and form notes where text is essential.
- Recheck contrast on translucent panels and gradients.

Acceptance:

- Normal explanatory text reaches at least 4.5:1 contrast.
- Non-text controls and focus indicators reach at least 3:1 contrast.

Standards:

- WCAG 1.4.3 Contrast (Minimum)
- WCAG 1.4.11 Non-text Contrast

### P0-4: Add Strong Focus Treatment

Outcome:

Keyboard users can always see where they are.

Tasks:

- Create a focus token, for example `--focus-ring`.
- Apply it to buttons, rail links, report links, table rows/checkboxes, and
  modal controls.
- Keep existing motion/shadow as enhancement, not the only focus signal.

Acceptance:

- Every interactive control has a visible focus state.
- Focus state survives warm backgrounds, dark rail, and card clipping.

Standards:

- WCAG 2.4.7 Focus Visible
- WCAG 2.4.13 Focus Appearance
- NN/g Visibility of System Status

## Priority 1: Product Clarity Polish

These upgrades make QS-DMSS feel less like a stitched set of tools and more
like a deliberate lab workflow.

### P1-1: Add Lab Mode Progress Strip

Outcome:

Users see what is happening during a showcase launch.

Tasks:

- Add staged progress copy: prepare, simulate, verify, replay, export.
- Add `aria-live="polite"` to status updates.
- Show elapsed time or "usually under N seconds" helper copy.

Acceptance:

- Visible feedback appears within one second after launch.
- Completion state clearly explains what passed.

Standards:

- WCAG 4.1.3 Status Messages
- NN/g Visibility of System Status

### P1-2: Sync Rail Active State With Current Section

Outcome:

Navigation reflects where the user is.

Tasks:

- Make `Lab` active on initial page load.
- Update active nav on click and scroll.
- Consider renaming `Cockpit` to `Manual Run` or `Launch`.

Acceptance:

- The active rail item matches the visible section.
- No section begins with misleading navigation state.

Standards:

- NN/g Consistency and Standards
- NN/g Visibility of System Status

### P1-3: Improve Human-Readable Run Identity

Outcome:

Users can recognize the current run without parsing a long machine ID.

Tasks:

- Show friendly label: `Canonical showcase run`.
- Show short ID with full ID available through copy/details.
- Add a copy-ID button or lightweight inline affordance.

Acceptance:

- Current run is identifiable in two seconds.
- Full ID remains available for evidence/replay traceability.

Standards:

- WCAG 2.4.6 Headings and Labels
- NN/g Recognition Rather than Recall

### P1-4: Improve Empty and Error States

Outcome:

Failures and empty states teach the workflow rather than merely announcing
absence.

Tasks:

- Replace "No runs yet" with a Lab Mode-first suggestion.
- Add actionable recovery copy for failed Lab Mode runs.
- Show whether failure occurred during simulation, verification, replay, or
  export.

Acceptance:

- Every empty/error state gives the next best action.
- Errors are plain-language and map to workflow steps.

Standards:

- WCAG 3.3.1 Error Identification
- WCAG 3.3.3 Error Suggestion
- NN/g Help Users Recognize, Diagnose, and Recover from Errors

## Priority 2: Premium Experience Layer

These are not blockers, but they create a stronger donation/contribution story.

### P2-1: Add Evidence Explorer Preview

Outcome:

Users see evidence contents without downloading a ZIP or opening raw files.

Tasks:

- Add a manifest summary: config digest, environment lock, file count, verified
  files, artifact categories.
- Show the replay compatibility status in plain language.
- Provide direct links to key artifacts.

Acceptance:

- A non-maintainer can explain what the evidence bundle contains after one pass.

Standards:

- NN/g Match Between System and the Real World
- NN/g Help and Documentation

### P2-2: Add Report Preview Mode

Outcome:

Publication-grade report export feels like a first-class product feature.

Tasks:

- Open Markdown/JSON reports in a styled in-app preview or side panel.
- Include copy/download links.
- Add citation block preview.

Acceptance:

- Users can inspect the generated report without leaving the cockpit.

Standards:

- NN/g Flexibility and Efficiency of Use
- NN/g Aesthetic and Minimalist Design

### P2-3: Add Scenario Metadata Cards

Outcome:

Packaged scenarios feel curated, not hidden config files.

Tasks:

- Add scenario purpose, expected runtime, artifacts produced, limitations, and
  review questions.
- Render metadata in the scenario picker or adjacent card.
- Prepare for multiple scenarios without redesigning Lab Mode.

Acceptance:

- A new scenario can be added with metadata and immediately appears coherent in
  Lab Mode.

Standards:

- WCAG 3.3.2 Labels or Instructions
- NN/g Recognition Rather than Recall

### P2-4: Add Visual Run Timeline

Outcome:

The simulation becomes more legible as a process, not just a result.

Tasks:

- Show lifecycle: launched, completed, verified, replayed, exported.
- Link each lifecycle step to evidence/report artifacts.
- Use status icons plus text, not color alone.

Acceptance:

- Users can answer "what happened?" without inspecting JSON.

Standards:

- WCAG 1.4.1 Use of Color
- NN/g Visibility of System Status

### P2-5: Add Sponsor/Builder CTA In Context

Outcome:

Funding request appears tied to visible product outcomes.

Tasks:

- Add a small "Fund the next Lab Mode milestone" CTA after successful run.
- Link to Open Collective and builder board.
- Keep it secondary to the research workflow.

Acceptance:

- CTA is visible after success but does not interrupt task completion.

Standards:

- NN/g Aesthetic and Minimalist Design
- NN/g Help and Documentation

## Priority 3: Research-Grade UX Layer

These are strategic build slices for a stronger v0.5+ product arc.

### P3-1: Campaign Studio Flow

Outcome:

Users can design and understand objective-driven campaigns without editing YAML.

Tasks:

- Add parameter-grid editor.
- Add objective/constraint/ranking editor.
- Preview planned run count before execution.

Acceptance:

- A user can configure a small campaign from the cockpit and predict what will
  run.

### P3-2: Publication Export Composer

Outcome:

QS-DMSS can produce polished research objects from selected runs/campaigns.

Tasks:

- Add report sections: scenario, config, metrics, figures, evidence status,
  replay instructions, citation.
- Add export targets: Markdown, HTML, bundle ZIP.
- Add optional author/project metadata fields.

Acceptance:

- A generated report can be shared with a reviewer without extra explanation.

### P3-3: Scenario Gallery

Outcome:

QS-DMSS feels extensible and contributor-friendly.

Tasks:

- Add scenario gallery cards.
- Add "contribute a scenario" link.
- Add scenario readiness badges: fast, deterministic, benchmarked, reviewed.

Acceptance:

- Contributors can see where a new scientific/engineering scenario would fit.

## Suggested Implementation Order

1. Mobile reflow and clipping.
2. Disabled report actions and focus treatment.
3. Contrast token pass.
4. Lab Mode progress strip.
5. Active nav sync and run identity polish.
6. Evidence Explorer preview.
7. Report preview/composer.

This order protects accessibility first, then improves the conversion story.
