# QS-DMSS

QS-DMSS is a deterministic, evidence-first simulation lab for the
QuantumScalar Dark Matter Simulation Suite.

The product loop is simple:

```text
run simulations -> inspect evidence -> compare campaigns -> publish reproducible artifacts
```

QS-DMSS is not trying to be "just another solver." The project direction is to
turn simulation runs into trustworthy research objects: configured, measured,
bundled, verified, replayable, comparable, citable, and ready to share.

QS-DMSS is beta for reproducible package/evidence workflows; it is not
peer-reviewed scientific validation.

## Tangible Utility Summary

QS-DMSS is a classical, NumPy-first reference lab for small deterministic
Schrodinger-Poisson-style quantum scalar dark matter experiments. Its strongest
public lane is not high-performance cosmological discovery; it is making
simulation studies fast to set up, easy to inspect, reproducible, comparable,
and citable.

- Rapid sandbox studies for parameters such as the self-interaction term
  `engine.g_int`, timestep, packet width, amplitude, and random seed.
- Local Python package, CLI, cockpit, and JSON API paths that avoid HPC or
  cluster infrastructure for small reference runs.
- Evidence bundles, manifests, replay, verification, reports, and Zenodo/PyPI
  metadata that turn runs into portable research objects.
- Campaign Studio study templates for preserving, rerunning, importing,
  exporting, and explaining reproducible parameter-grid designs.
- Portable workspace snapshots for handing off selected runs, experiments,
  study templates, research-object exports, job provenance, collaborators, and
  annotations as local JSON.
- A packaged `Self-Interaction Sweep` study template focused on `engine.g_int`,
  with purpose, runtime target, metrics, limitations, non-claims, and guided
  interpretation visible in the cockpit before a user edits any YAML.

See
[docs/scientific-scope-and-utility.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/scientific-scope-and-utility.md)
for the scientific scope, non-claims, and a concrete self-interaction campaign
study using `engine.g_int`.

- Installable Python package
- Bundled demo assets for installed-package smoke testing
- Config-driven simulation CLI
- Local-first run cockpit and JSON API
- Parameter sweeps and multi-run comparison in the cockpit
- Experiment registry with saved comparison reports and bundles
- Objective-driven decision profiles with ranked recommendations
- Template-defined decision campaigns across multi-parameter search grids
- Reusable Campaign Studio study templates for preserving, rerunning, and sharing campaign designs
- Run ledger with stable run IDs and config digests
- Evidence bundle with artifacts, metrics, manifest, and HTML report
- Replay and verification commands for reproducibility checks
- Canonical simulation showcase with CSV, SVG, report, run evidence, and replay evidence
- GitHub Actions CI and containerized runtime

## What This Build Includes

The current reference implementation focuses on the backbone needed for an
evidence-first simulation lab:

- A NumPy-based split-step Schrodinger-Poisson solver
- YAML configuration loading with explicit validation
- Structured run outputs under `runs/<run_id>/`
- Structured experiment outputs under `experiments/<experiment_id>/`
- A local cockpit for launch, inspection, verification, replay, and bundle download
- Sweep support for exploring one parameter across multiple deterministic runs
- Decision campaign support for expanding a template into a multi-parameter grid automatically
- Campaign Studio study templates that save, reopen, import, export, and display edited grids, scoring contracts, and last-run provenance
- A packaged Self-Interaction Sweep template that turns `engine.g_int` into a
  concrete tangible-utility demo after install
- Local workspace export/import for portable collaboration handoffs with
  collaborator and annotation metadata
- Dry-run Slurm request bundles that emit reviewable scheduler artifacts
  without submitting jobs
- Experimental Fractal/Quadrant SSFM validation spine for nonlinear wave
  propagation through fuzzy fractal effective potentials, with a CPU reference
  backend and optional CuPy acceleration path
- Comparison tooling for energy drift, norm drift, density, and runtime deltas
- Decision profiles that score runs against an explicit objective, constraint set, and ranking policy
- Durable experiment exports with copied run evidence, comparison JSON, report HTML, manifest, and bundle ZIP
- LocalExecutor job records under `jobs/<job_id>/job.json` that preserve
  submitted config metadata, run/replay lifecycle state, multi-run
  campaign/comparison provenance, research-object export provenance, and
  returned artifact roles for future collaboration and HPC connector work
- Evidence artifacts:
  - `config.yaml`
  - `run.json`
  - `metrics.json`
  - `energy.csv`
  - `environment.lock.json`
  - `artifacts/final_density.npy`
  - `artifacts/final_state.npz`
  - `report.html`
  - `manifest.sha256.json`
  - `evidence_bundle.zip`
- Verification tooling for manifests and config digests
- Replay support for deterministic reruns

## Quickstart

Install the published package from PyPI:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qs-dmss
```

Run the bundled demo config from the installed package:

```powershell
qs-dmss run-demo
```

Launch the bundled installed-package demo campaign:

```powershell
qs-dmss campaigns run-demo
```

Run the benchmark validation spine:

```powershell
qs-dmss benchmarks validate --scenario demo-baseline
```

Run the experimental CPU reference Fractal/Quadrant SSFM validation spine:

```powershell
qs-dmss validation fractal-ssfm --config configs/fractal_quadrant_ssfm.yaml
```

See
[docs/fractal-quadrant-ssfm-validation-spine.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/fractal-quadrant-ssfm-validation-spine.md)
for the scientific claim boundary and validation expectations.

This writes `fractal-ssfm-validation/fractal-ssfm-validation.json` plus a
human-readable `fractal-ssfm-validation/fractal-ssfm-validation.md` summary.

Run the canonical simulation showcase:

```powershell
qs-dmss showcase run --output-root simulation-showcase
```

This writes a human-readable `simulation-showcase/simulation-showcase.md`
walkthrough, CSV tables, SVG plots, verified run evidence, and replay evidence
for the packaged canonical simulation scenario.

Generate a review-only Slurm request bundle without submitting to a scheduler:

```powershell
qs-dmss executors slurm-dry-run configs/demo.yaml --request-root dry-run-jobs --job-name qs-demo
```

This writes `job.json`, `request-bundle/request-bundle.json`,
`request-bundle/slurm-job.sh`, a copied config, and review instructions. The
job state remains `draft`; QS-DMSS does not call `sbatch`.

For source development, install the checked-out repository in editable mode:

```powershell
python -m pip install -e .[dev]
qs-dmss run configs/demo.yaml
```

Builders and sponsors can start with the product direction:

- [docs/scientific-scope-and-utility.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/scientific-scope-and-utility.md)
- [docs/product-vision.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/product-vision.md)
- [docs/contributor-roadmap.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/contributor-roadmap.md)
- [docs/funding-roadmap.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/funding-roadmap.md)
- [docs/distributed-research-workspace-executor-architecture.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/distributed-research-workspace-executor-architecture.md)
- [docs/slurm-site-policy-feedback.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/slurm-site-policy-feedback.md)

The current product milestone includes QS-DMSS Lab Mode plus an installable
dry-run Slurm review target: a richer cockpit/showcase experience for running
scenarios, inspecting outputs, comparing variants, verifying and replaying
evidence, exporting polished research objects, and generating reviewable HPC
request bundles that never submit jobs.

Public builder coordination now lives in
[issue #57](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/57).
The latest Campaign Studio product slices on `main` add scenario metadata,
editable parameter grids, decision-profile editing, scoring-contract preview,
reusable study-template cards, and a packaged Self-Interaction Sweep template.
That template gives fresh users one concrete `engine.g_int` campaign they can
run, inspect, rerun, export, and critique without first designing a study from
scratch.

Distributed collaboration and HPC connectors are possible future platform
layers, but live collaboration and scheduler submission are not shipped runtime
behavior yet. The current local-first seam supports portable workspace
export/import with collaborators and annotations plus a dry-run Slurm request
bundle generator that writes reviewable scheduler artifacts without calling
`sbatch`, SSH, or a remote scheduler. This documents the path toward shared
research workspaces, executor contracts, job lifecycle tracking, artifact
collection, and scheduler guardrails. HPC administrators and research
computing reviewers can use the
[Slurm site-policy feedback packet](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/slurm-site-policy-feedback.md)
to review the generated bundle shape before any real submit/status/collect
connector is attempted.

Review paths remain available for people who want to validate the public
package:

- [docs/reviewer-wheel-quickstart.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/reviewer-wheel-quickstart.md)
- [docs/reviewer-packet.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/reviewer-packet.md)

Start the local cockpit:

```powershell
qs-dmss cockpit --host 127.0.0.1 --port 8001
```

Then open [http://127.0.0.1:8001](http://127.0.0.1:8001) in a browser.

Inside the cockpit you can:

- Use Lab Mode to launch the packaged canonical simulation showcase, read guided interpretation, run a guided variant comparison, inspect the Evidence Explorer, preview generated reports/artifacts, compose a research object export, and open the full evidence outputs
- Inspect Scenario Library metadata for packaged scenarios, including purpose, expected runtime, artifacts, readiness, limitations, and suggested next actions
- Select the packaged Self-Interaction Sweep study template to inspect purpose, expected runtime, metrics, limitations, non-claims, and guided interpretation for an `engine.g_int` campaign
- Edit the Campaign Studio parameter grid and decision profile for the bundled decision campaign, preview the scoring contract, and launch the edited campaign through the existing evidence/recommendation workflow
- Save Campaign Studio edits as local study templates, inspect visible template cards with objective/run metadata, reload or rerun saved templates, and import/export the study JSON so another user can reproduce the same campaign design
- Inspect LocalExecutor job provenance for selected runs, campaign variants,
  saved experiment artifacts, and persisted research-object exports, including
  job ID, backend, lifecycle state, child jobs, and returned artifact roles
- Export or import a portable research workspace JSON with selected run,
  experiment, study-template, research-object, job, collaborator, and annotation
  metadata
- Generate a dry-run Slurm request bundle from a config for review before any
  manual HPC submission
- Launch a single run from a checked-in or edited config
- Launch a parameter sweep across interaction strength, timestep, step count, amplitude, width, or seed
- Launch a template-defined decision campaign that expands into a reproducible multi-parameter run matrix
- Compare multiple runs side by side with shared experiment metadata
- Save a comparison into the experiment registry and reopen it later with report and bundle downloads
- Load an objective-driven template and see the recommended winner directly in the comparison view

Verify the generated evidence bundle:

```powershell
qs-dmss verify runs\<run_id>
```

Replay a prior run using the captured config:

```powershell
qs-dmss replay runs\<run_id>
```

Persist a saved experiment bundle from two or more runs:

```powershell
qs-dmss experiments export <run_id> <run_id> --label "comparison bundle"
```

List saved experiment artifacts:

```powershell
qs-dmss experiments list
```

Launch the decision campaign defined by a template:

```powershell
qs-dmss campaigns run configs/demo.yaml
```

Or launch the bundled installed-package demo campaign:

```powershell
qs-dmss campaigns run-demo
```

The checked-in demo template now includes a decision profile:

- `objective`
- `constraints`
- `ranking`
- `campaign`

That means sweeps, experiment exports, and template-driven campaigns can now return a replayable recommendation instead of only raw metric tables.

The packaged showcase command adds a simulation inspection path
on top of that loop:

`run packaged scenario -> export CSV/SVG artifacts -> verify evidence -> replay -> compare final density`

## Container Runtime

Build the container image:

```powershell
docker build -t qs-dmss .
```

Run the cockpit in Docker:

```powershell
docker run --rm -p 8001:8001 qs-dmss
```

The image installs the built wheel, starts `qs-dmss cockpit --host 0.0.0.0 --port 8001`,
and exposes the health endpoint at `http://127.0.0.1:8001/api/health`.

## Project Layout

```text
configs/                 Checked-in example configs
benchmarks/              Benchmark validation guidance
schemas/                 JSON schema for run configs
src/qs_dmss/             Package source
tests/                   Smoke and reproducibility tests
runs/                    Run ledger outputs (generated)
experiments/             Saved comparison artifacts (generated)
```

## Development

Run the smoke tests:

```powershell
pytest
```

CI lives in
[.github/workflows/ci.yml](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/.github/workflows/ci.yml)
and validates:

- the editable install and test suite across Python 3.10 through 3.13
- static cockpit JavaScript syntax
- source distribution and wheel build metadata
- installed-wheel `run-demo` smoke test
- Docker build plus live `/api/health` and `/api/configs` probes

Fresh-install adoption smoke lives in
[.github/workflows/fresh-install-smoke.yml](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/.github/workflows/fresh-install-smoke.yml)
and validates PyPI and GitHub release-wheel installs on Linux, macOS, and
Windows.

Release-candidate versioning and distribution artifact rules live in
[RELEASE.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/RELEASE.md).

PyPI distribution details and Trusted Publishing provenance live in
[docs/pypi-distribution-readiness.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/pypi-distribution-readiness.md).

The beta promotion gate lives in
[docs/beta-readiness.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/beta-readiness.md).

Benchmark validation guidance lives in
[docs/benchmark-validation.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/benchmark-validation.md).

Canonical simulation showcase guidance lives in
[docs/simulation-showcase.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/simulation-showcase.md).

Evidence artifact definitions live in
[docs/evidence-bundle-glossary.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/evidence-bundle-glossary.md),
demo and benchmark expectations live in
[docs/demo-benchmark-expectations.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/demo-benchmark-expectations.md),
and decision profile fields are annotated in
[docs/decision-profile-example.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/decision-profile-example.md).

Product, funding, and builder-roadmap guidance lives in
[docs/product-vision.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/product-vision.md),
[docs/funding-roadmap.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/funding-roadmap.md),
and
[docs/contributor-roadmap.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/contributor-roadmap.md).

Contributor source-map guidance lives in
[docs/contributor-map.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/contributor-map.md),
and GitHub social preview setup lives in
[docs/social-preview.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/social-preview.md).

Scholarly indexing readiness and public-launch materials live in
[docs/ascl-joss-readiness.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/ascl-joss-readiness.md)
and
[docs/public-technical-launch-post.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/public-technical-launch-post.md).

The JOSS preflight checklist lives in
[docs/joss-preflight.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/joss-preflight.md).

The active builder roadmap lives in
[docs/post-v0.3-active-roadmap.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/post-v0.3-active-roadmap.md).

The next research-grade upgrade slice is defined in
[docs/research-grade-upgrade-slice.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/research-grade-upgrade-slice.md),
with paper strategy notes in
[docs/research-paper-strategy.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/research-paper-strategy.md).

## Funding And Stewardship

QS-DMSS has been accepted into Open Source Collective. Support can be directed
through [Open Collective](https://opencollective.com/qs-dmss).

The current funding ask is concrete: help build QS-DMSS Lab Mode and the
publication-grade artifact workflow around it. Funding should unlock visible
public outcomes such as cockpit improvements, scenario packs, evidence
exploration, report exports, campaign tooling, benchmark scenarios, and
research-software documentation.

The funding roadmap lives in
[docs/funding-roadmap.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/funding-roadmap.md).

Funding support does not imply peer-reviewed scientific validation or
endorsement of any physical model. Scientific claims should continue to be
reviewed through reproducible evidence, public issues, and formal scholarly
review.

## Citation

Citation metadata lives in
[CITATION.cff](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/CITATION.cff).
GitHub uses this file to populate the repository citation prompt, and Zenodo can
use it when archiving GitHub releases.

For formal research references, prefer the Zenodo DOI citation:

- Project DOI: [10.5281/zenodo.20074924](https://doi.org/10.5281/zenodo.20074924)
- Latest archived release DOI: [v0.9.0 / 10.5281/zenodo.20693736](https://doi.org/10.5281/zenodo.20693736)
- Previous archived release DOI: [v0.8.0 / 10.5281/zenodo.20673804](https://doi.org/10.5281/zenodo.20673804)
- Previous archived release DOI: [v0.7.0 / 10.5281/zenodo.20671389](https://doi.org/10.5281/zenodo.20671389)
- Previous archived release DOI: [v0.6.1 / 10.5281/zenodo.20631860](https://doi.org/10.5281/zenodo.20631860)
- Previous archived release DOI: [v0.6.0 / 10.5281/zenodo.20618884](https://doi.org/10.5281/zenodo.20618884)
- Earlier archived release DOI: [v0.5.0 / 10.5281/zenodo.20617028](https://doi.org/10.5281/zenodo.20617028)
- Older archived release DOI: [v0.4.0 / 10.5281/zenodo.20500433](https://doi.org/10.5281/zenodo.20500433)
- Prior archived release DOI: [v0.3.0 / 10.5281/zenodo.20112923](https://doi.org/10.5281/zenodo.20112923)
- Older archived release DOI: [v0.2.0 / 10.5281/zenodo.20091602](https://doi.org/10.5281/zenodo.20091602)
- Historical archived release DOI: [v0.1.5 / 10.5281/zenodo.20076871](https://doi.org/10.5281/zenodo.20076871)
- First archived release DOI: [v0.1.3 / 10.5281/zenodo.20074925](https://doi.org/10.5281/zenodo.20074925)
- Software Heritage archival: pending; add the SWHID after Software Heritage
  reports a completed archive for the release.

Zenodo citation notes live in
[docs/zenodo-citation.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/zenodo-citation.md).

## Product Spine

QS-DMSS already has the package/evidence/reproducibility spine needed for a
stronger product. Optional accelerator backends, plugin expansion, and broader
research modules can build on a stable execution loop:

`configure -> run -> measure -> bundle -> verify -> replay`

The cockpit adds the first browser-native product layer on top of that loop:

`configure -> launch -> inspect -> verify/replay -> compose research object`

The experiment registry now makes comparison durable too:

`select runs -> compare -> save -> report -> bundle -> reopen`

The decision layer adds recommendation semantics to that flow:

`select template -> launch campaign -> score runs -> recommend winner -> export evidence`

The campaign layer now automates the search plan too:

`select template -> expand campaign -> run matrix -> score variants -> recommend winner -> reopen bundle`

Lab Mode turns that spine into a reviewer-facing simulation lab:

`choose scenario -> run simulation -> inspect evidence -> compare variants -> verify/replay -> compose export`
