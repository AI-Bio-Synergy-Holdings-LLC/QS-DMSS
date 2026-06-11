# Reviewer Packet

This packet is the shortest path for an external reviewer to understand what
QS-DMSS is claiming, reproduce the public baseline, and decide where feedback
would be most useful.

Current public baseline: `v0.7.0` / `qs-dmss==0.7.0`

Release DOI: pending Zenodo archive after the `v0.7.0` GitHub release

Latest archived release DOI: `10.5281/zenodo.20631860` (`v0.6.1`)

Project DOI: `10.5281/zenodo.20074924`

Open Collective: `https://opencollective.com/qs-dmss`

Active external review sprint:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37`

Reviewer opt-in discussion:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/discussions/44`

Reviewer opt-in issue form:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml`

## Review Claim

QS-DMSS is beta for reproducible package/evidence workflows; it is not
peer-reviewed scientific validation.

The review target is the workflow spine:

```text
install -> run -> bundle -> verify -> replay -> benchmark validate -> inspect
```

Reviewers should treat the bundled demo and benchmark scenarios as
reproducibility and packaging evidence, not as claims that the underlying
QuantumScalar dark matter model has been scientifically validated.

## Fast Review Path

Use the published PyPI package from a clean environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qs-dmss==0.7.0

qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss benchmarks validate --scenario demo-baseline
qs-dmss showcase run --output-root simulation-showcase
```

Expected signals:

- `qs-dmss run-demo` writes a run under `runs/`, prints an evidence bundle, and
  reports `Verification passed`.
- `qs-dmss campaigns run-demo` writes an experiment under `experiments/` and
  reports a recommended run plus decision status.
- `qs-dmss benchmarks validate --scenario demo-baseline` writes
  `benchmark-validation/benchmark-validation.json`,
  `benchmark-validation/benchmark-validation.md`, and reports
  `Benchmark passed: demo-baseline`.
- `qs-dmss showcase run --output-root simulation-showcase` writes
  `simulation-showcase/simulation-showcase.md`, CSV tables, SVG plots,
  verified run evidence, and replay evidence.

Use [reviewer-wheel-quickstart.md](reviewer-wheel-quickstart.md) for the
cross-platform PyPI and GitHub release-wheel commands.

## Simulation Showcase Path

The published `v0.6.0` package includes a canonical simulation showcase for
reviewers who want to inspect the actual simulated field output, not just the
install and benchmark envelopes:

```powershell
qs-dmss showcase run --output-root simulation-showcase
```

Expected signals:

- `simulation-showcase/simulation-showcase.md` explains the scenario, metrics,
  verification status, replay status, and claim boundary.
- `simulation-showcase/artifacts/` contains CSV tables and SVG plots for energy
  history, radial density, and the final-density midplane.
- `simulation-showcase/runs/` and `simulation-showcase/replays/` contain normal
  QS-DMSS evidence bundles.

Use [simulation-showcase.md](simulation-showcase.md) for the detailed path.

## Lab Mode Cockpit Path

`v0.7.0` is the product milestone where Campaign Studio becomes configurable:

- Scenario Library metadata explains packaged campaign scenarios, readiness,
  runtime expectations, artifacts, limitations, and next actions.
- Campaign Studio lets reviewers edit the packaged parameter grid and decision
  profile, preview the scoring contract, and launch the edited objective-driven
  campaign through the evidence/recommendation pipeline.

`v0.6.0` is the product milestone where Lab Mode can compose reviewer-facing
research objects:

- Publication Export Composer creates a Markdown research object with scenario,
  metrics, evidence status, replay commands, artifact links, and citation/DOI
  metadata.
- The Open Collective and Builder Board CTA appears only after a successful
  export.

`v0.5.0` was the first product milestone where Lab Mode became reviewer-facing:

```powershell
qs-dmss cockpit --host 127.0.0.1 --port 8001
```

Open `http://127.0.0.1:8001`, run Lab Mode, then run Guided Comparison.
Expected signals:

- Lab Mode explains what the canonical simulation result means and what it
  does not claim.
- The Evidence Explorer previews key report metrics, verification/replay
  status, SVG plots, and CSV first rows without leaving the cockpit.
- Guided Comparison runs three packaged variants, explains evidence deltas in
  plain language, and exposes a comparison report plus bundle.
- Publication Export Composer turns the successful Lab Mode run into a
  downloadable research-object Markdown export.

## Review Lanes

Choose the lane that matches the feedback you want to provide.

| Lane | What to check | Best issue type |
| --- | --- | --- |
| Installability | Fresh virtual environment, PyPI install, release wheel install, CLI help | Bug report or reproducibility review |
| Evidence workflow | `run-demo`, generated artifacts, `verify`, `replay`, bundle contents | Reproducibility review |
| Campaign workflow | `campaigns run-demo`, campaign metadata, recommendation status, experiment bundle | Reproducibility review or feature request |
| Benchmark workflow | `benchmarks list`, `benchmarks validate`, metric envelope report, replay compatibility | Scientific review or reproducibility review |
| Simulation showcase | `showcase run`, generated CSV/SVG outputs, replay comparison, scenario narrative | Scientific review or evidence review |
| Lab Mode guided comparison | Cockpit Lab Mode, Evidence Explorer, guided variant comparison, report/bundle links | Product UX review or evidence review |
| Documentation | README, reviewer quickstart, evidence glossary, benchmark expectations | Documentation issue |
| Paper readiness | JOSS paper scaffold, state-of-field comparison, research impact evidence | Scientific review |

Open feedback through the active review sprint:

- Overview: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/37`
- Fresh install and reproducibility:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/39`
- Evidence bundle and benchmark validation:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/40`
- Scientific framing and JOSS preflight:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/41`

## Funding And Stewardship

QS-DMSS has been accepted into Open Source Collective. The Open Collective page
provides a transparent support path for maintenance of the public package,
reviewer documentation, benchmark validation, and reproducibility infrastructure.

Funding support should be interpreted as support for open-source stewardship,
not as scientific endorsement. Reviewers should continue to evaluate QS-DMSS
through the reproducible artifacts, benchmark evidence, issue discussions, and
eventual scholarly review.

## Artifacts To Inspect

For a generated run directory, inspect:

- `config.yaml`
- `run.json`
- `metrics.json`
- `energy.csv`
- `environment.lock.json`
- `manifest.sha256.json`
- `report.html`
- `evidence_bundle.zip`
- `artifacts/final_density.npy`
- `artifacts/final_state.npz`

For a benchmark validation run, inspect:

- `benchmark-validation/benchmark-validation.json`
- `benchmark-validation/benchmark-validation.md`
- `benchmark-validation/runs/`
- `benchmark-validation/replays/`

Artifact definitions live in
[evidence-bundle-glossary.md](evidence-bundle-glossary.md). Demo and benchmark
boundaries live in
[demo-benchmark-expectations.md](demo-benchmark-expectations.md).

## Questions For Reviewers

- Did the package install without source-repository context?
- Did generated outputs land in caller-controlled directories rather than
  package assets?
- Was the evidence bundle understandable without reading source code?
- Did `verify` and `replay` make the run easier to trust?
- Did benchmark validation provide useful regression signal?
- Which artifact, command, or explanation would have reduced review friction?
- What comparison baseline should the eventual research paper include?

## Known Non-Claims

QS-DMSS does not currently claim:

- peer-reviewed scientific validation;
- validated physical conclusions from the bundled demo;
- equivalence to production cosmological simulation codes;
- stable internal Python APIs;
- GPU, distributed, or high-performance backend support;
- ASCL indexing or JOSS acceptance.

The current goal is to make early simulation workflows auditable enough that
external reviewers can critique the software, benchmarks, and paper direction
from reproducible evidence instead of screenshots or informal notes.
