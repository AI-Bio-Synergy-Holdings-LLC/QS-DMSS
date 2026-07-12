# Reviewer Packet

This packet is the shortest path for an external reviewer to understand what
QS-DMSS is claiming, reproduce the public baseline, and decide where feedback
would be most useful.

Current public baseline: `v0.11.0` / `qs-dmss==0.11.0`

Canonical website: `https://qs-dmss.studio`

Latest archived release DOI: `10.5281/zenodo.21270512` (`v0.10.1`); the
`v0.11.0` DOI is pending Zenodo archive.

Project DOI: `10.5281/zenodo.20074924`

Open Collective: `https://opencollective.com/qs-dmss`

Scientific scope and tangible utility guide:
[`scientific-scope-and-utility.md`](scientific-scope-and-utility.md)

Conceptual and citation role map:
[`conceptual-reference-map.md`](conceptual-reference-map.md)

Active scientific review target:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105`

Active HPC/RSE site-policy review target:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/99`

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

References in the conceptual map are role-labeled as scientific context,
numerical-method precedent, public source-data provenance, research-object
infrastructure, or future comparison targets. They should not be read as
endorsements of QS-DMSS or as validation against external datasets.

## Fast Review Path

Use the published PyPI package from a clean environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qs-dmss==0.11.0

qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss benchmarks validate --scenario demo-baseline
qs-dmss showcase run --output-root simulation-showcase
qs-dmss data calibration run --output-root reference-data-calibration
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
- `qs-dmss data calibration run --output-root reference-data-calibration`
  writes source URL, access date, citation, transform script, cache checksum,
  config, and evidence ZIP records for public reference-data provenance.

Use [reviewer-wheel-quickstart.md](reviewer-wheel-quickstart.md) for the
cross-platform PyPI and GitHub release-wheel commands.

## Scientific Review Gate

The public package baseline includes `qs-dmss validation fractal-ssfm` for the
experimental `numpy_fractal_ssfm` backend.

Use this review path when commenting on issue #105:

```powershell
python -m pip install qs-dmss==0.11.0
qs-dmss validation fractal-ssfm
```

Expected signals:

- `fractal-ssfm-validation/fractal-ssfm-validation.json`
- `fractal-ssfm-validation/fractal-ssfm-validation.md`
- Strang refinement checks for decreasing `time_step`
- fuzzy-potential norm-conservation status
- explicit non-conservative labels for `soft_mask` and `hard_mask`

Please leave one public comment on
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105`.
GPU expansion and decision-metric UI for `spectral_leakage` /
`aliasing_ratio` remain paused until that target receives substantive
technical feedback.

## Simulation Showcase Path

The published `v0.11.0` package includes a canonical simulation showcase for
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

`v0.11.0` is the Hosted Studio baseline where the public reference-data
provenance calibration sandbox, Fractal/Quadrant SSFM validation spine, Conceptual
Reference Map, and job-registry path hardening are installable from PyPI.

`v0.9.0` is the product milestone where the dry-run Slurm request-bundle review
path becomes installable from PyPI without real scheduler submission.

`v0.8.0` is the product milestone where Campaign Studio study templates become
visible reusable research assets:

- Saved study templates appear as cards with objective, metric, planned runs,
  source config, portability, and import/export status.
- Running a saved template records last-run provenance: recommendation, report,
  and bundle links.
- The public repository now has zero open GitHub code-scanning alerts.

`v0.7.0` was the product milestone where Campaign Studio became configurable:

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
| Fractal SSFM validation | Published package or source checkout, `validation fractal-ssfm`, JSON/Markdown report, conservation labels | Scientific review on #105 |
| Dry-run Slurm review | `executors slurm-dry-run`, request bundle, scheduler script, no-submit policy | HPC/RSE review on #99 |
| Documentation | README, reviewer quickstart, evidence glossary, benchmark expectations | Documentation issue |
| Paper readiness | JOSS paper scaffold, state-of-field comparison, research impact evidence | Scientific review |

Open feedback through the active public gates:

- Fractal SSFM validation:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105`
- HPC/RSE dry-run Slurm site-policy review:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/99`
- Builder Board and product roadmap:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/57`

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
