# Canonical Simulation Showcase

The canonical simulation showcase is the first reviewer-facing path focused on
the actual QS-DMSS simulation output rather than only installation,
verification, or benchmark-envelope status.

It demonstrates the QS-DMSS workflow and simulation behavior; it is not
peer-reviewed scientific validation.

## Purpose

The showcase gives reviewers one concrete, deterministic scenario to inspect:
a compact Gaussian scalar-field packet evolved with the NumPy split-step
Schrodinger-Poisson reference solver. The scenario is intentionally small enough
for a laptop or CI-style environment while still producing field-density,
energy-history, evidence-bundle, and replay artifacts.

Use it when the review question is:

```text
Can I understand what QS-DMSS is simulating, run it, inspect the output, and
verify/replay the evidence without needing private context?
```

## Run It From The Published Package

Install the release package and run the showcase:

```powershell
python -m pip install qs-dmss==0.9.0
qs-dmss showcase run --output-root simulation-showcase
```

For source development, install from the current checkout instead:

```powershell
python -m pip install -e .[dev]
qs-dmss showcase run --output-root simulation-showcase
```

List packaged showcase scenarios:

```powershell
qs-dmss showcase list
```

The default command runs `canonical-simulation` and writes:

- `simulation-showcase/simulation-showcase.json`
- `simulation-showcase/simulation-showcase.md`
- `simulation-showcase/runs/`
- `simulation-showcase/replays/`
- `simulation-showcase/artifacts/step-history.csv`
- `simulation-showcase/artifacts/radial-density-profile.csv`
- `simulation-showcase/artifacts/density-midplane.csv`
- `simulation-showcase/artifacts/energy-history.svg`
- `simulation-showcase/artifacts/radial-density-profile.svg`
- `simulation-showcase/artifacts/density-midplane.svg`

## What The Showcase Adds

`qs-dmss run-demo` proves a packaged demo can execute and verify.

`qs-dmss benchmarks validate` proves packaged scenarios stay within expected
workflow envelopes and replay tolerances.

`qs-dmss showcase run` adds a human-readable simulation walkthrough:

- a scenario narrative;
- a metrics table for norm, energy, density, and runtime;
- CSV tables for independent inspection;
- SVG plots for quick visual review;
- evidence-bundle verification;
- replay verification and final-density comparison;
- a clear claim boundary.

## Lab Mode Cockpit Path

`v0.6.0` also exposes the canonical simulation through Lab Mode in the local
cockpit:

```powershell
qs-dmss cockpit --host 127.0.0.1 --port 8001
```

Open `http://127.0.0.1:8001`, run Lab Mode, run Guided Comparison, then use
the Publication Export Composer. Expected signals include a plain-language
interpretation, an Evidence Explorer, SVG/CSV previews, a three-variant
comparison table, evidence-status summaries, report/bundle links, and a
downloadable research-object Markdown export.

## Suggested Reviewer Prompt

If you are asking a reviewer to inspect only one thing, ask:

```text
Please run `qs-dmss showcase run --output-root simulation-showcase` and leave
one public comment: did the generated
`simulation-showcase.md` make the simulation purpose, output, and evidence
boundary understandable?
```

Good places to file that feedback:

- Scientific validation gate: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105`
- HPC/RSE dry-run Slurm site-policy gate: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/99`
- Builder roadmap and contribution tracks: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/57`
- Reviewer opt-in form: `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new?template=reviewer_opt_in.yml`

## Non-Claims

The showcase does not claim:

- peer-reviewed scientific validation;
- validated physical conclusions from the scenario;
- equivalence to production cosmological simulation codes;
- performance claims beyond a small deterministic reference run;
- stable internal Python APIs.

Its purpose is to make the current simulation behavior inspectable enough that
external reviewers can critique the software, outputs, evidence, and paper
framing from a reproducible artifact.
