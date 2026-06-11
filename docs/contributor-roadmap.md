# Contributor Roadmap

QS-DMSS needs builders, not only reviewers. The strongest contributions are
ones that make simulation work easier to run, inspect, compare, verify, replay,
and publish.

## Build Lanes

### 1. Lab Mode and Cockpit UX

Goal: make the local cockpit feel like a simulation lab session.

High-value work:

- scenario selection and launch flow;
- run progress/status panel;
- embedded plots for density, radial profile, and energy history;
- verify/replay buttons for selected runs;
- comparison view for campaign variants;
- polished export action for reports and evidence bundles.

Good contributors: frontend developers, product engineers, UX-minded research
software engineers.

### 2. Scenario Library

Goal: make QS-DMSS useful immediately after install.

High-value work:

- named packaged scenarios with clear scientific/engineering purpose;
- expected runtime and output descriptions;
- scenario metadata for reports and cockpit display;
- contributor template for adding a new scenario safely.

Good contributors: scientists, numerical modelers, documentation contributors.

### 3. Evidence Explorer

Goal: make evidence bundles understandable without reading source code.

High-value work:

- manifest viewer;
- config digest and file-integrity summary;
- run/replay comparison view;
- environment lock summary;
- bundle-open path in the cockpit.

Good contributors: backend engineers, frontend developers, reproducibility
specialists.

### 4. Publication-Grade Reports

Goal: turn simulation outputs into shareable research artifacts.

High-value work:

- report templates for single runs, campaigns, and showcases;
- figure captions and metric explanations;
- citation and Zenodo metadata blocks;
- replay instructions embedded in exported reports;
- static HTML or Markdown report polish.

Good contributors: technical writers, scientific communicators, report/UI
engineers.

### 5. Campaign Studio

Goal: make parameter exploration and objective-driven recommendation easier to
design and explain.

High-value work:

- refine the visual parameter-grid builder;
- refine the decision-profile editor and scoring-contract preview;
- reusable campaign template presets;
- reusable decision-profile presets;
- campaign recommendation explanation panel;
- sensitivity summaries across variants;
- exportable campaign report.

Good contributors: full-stack engineers, optimization-minded contributors,
research-software engineers.

### 6. Numerical and Validation Spine

Goal: deepen confidence in the simulation and benchmark behavior.

High-value work:

- additional regression scenarios;
- metric envelope improvements;
- solver diagnostics;
- conservation and stability checks;
- documented assumptions and limitations.

Good contributors: numerical methods contributors, domain scientists,
scientific Python developers.

### 7. Release, Packaging, and Infrastructure

Goal: keep the public adoption path boring and reliable.

High-value work:

- cross-platform install smoke improvements;
- release artifact checks;
- PyPI/GitHub/Zenodo metadata consistency;
- container runtime improvements;
- contributor automation.

Good contributors: Python packaging maintainers, DevOps contributors,
research-software engineers.

## First Builder Board

Public board:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/57`

The immediate builder board should stay small:

1. Lab Mode cockpit flow.
2. Scenario library and scenario metadata.
3. Evidence Explorer.
4. Publication-grade report export.
5. Campaign Studio.
6. Numerical validation scenarios.
7. Release and infrastructure reliability.

Each board item should have a concrete first task small enough for a new
contributor to start, plus a larger destination that makes the project more
fundable and useful.

## Contribution Standard

Useful QS-DMSS contributions should answer at least one of these questions:

- Does this make a simulation easier to run?
- Does this make the output easier to inspect?
- Does this make evidence easier to verify or replay?
- Does this make campaigns easier to compare?
- Does this make artifacts easier to publish or cite?
- Does this make the project easier to fund or sustain?

If the answer is yes, it probably belongs on the roadmap.
