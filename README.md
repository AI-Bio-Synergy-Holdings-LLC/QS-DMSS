# QS-DMSS

QS-DMSS is a deterministic, evidence-first reference build of the QuantumScalar
Dark Matter Simulation Suite. This repository now ships the productization spine
needed to move from prototype scripts into a reproducible package:

QS-DMSS is beta for reproducible package/evidence workflows; it is not
peer-reviewed scientific validation.

- Installable Python package
- Bundled demo assets for installed-package smoke testing
- Config-driven simulation CLI
- Local-first run cockpit and JSON API
- Parameter sweeps and multi-run comparison in the cockpit
- Experiment registry with saved comparison reports and bundles
- Objective-driven decision profiles with ranked recommendations
- Template-defined decision campaigns across multi-parameter search grids
- Run ledger with stable run IDs and config digests
- Evidence bundle with artifacts, metrics, manifest, and HTML report
- Replay and verification commands for reproducibility checks
- GitHub Actions CI and containerized runtime

## What This Build Includes

The current reference implementation focuses on the backbone needed for
productization:

- A NumPy-based split-step Schrodinger-Poisson solver
- YAML configuration loading with explicit validation
- Structured run outputs under `runs/<run_id>/`
- Structured experiment outputs under `experiments/<experiment_id>/`
- A local cockpit for launch, inspection, verification, replay, and bundle download
- Sweep support for exploring one parameter across multiple deterministic runs
- Decision campaign support for expanding a template into a multi-parameter grid automatically
- Comparison tooling for energy drift, norm drift, density, and runtime deltas
- Decision profiles that score runs against an explicit objective, constraint set, and ranking policy
- Durable experiment exports with copied run evidence, comparison JSON, report HTML, manifest, and bundle ZIP
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

For source development, install the checked-out repository in editable mode:

```powershell
python -m pip install -e .[dev]
qs-dmss run configs/demo.yaml
```

Reviewers who want to validate the published release without a source checkout
can use the wheel-first path in
[docs/reviewer-wheel-quickstart.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/reviewer-wheel-quickstart.md).

External reviewers and contributors can start with the circulation funnel in
[docs/circulation-funnel.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/circulation-funnel.md),
then open a scientific review, reproducibility review, bug report, feature
request, or contributor task through
[GitHub Issues](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new/choose).

Start the local cockpit:

```powershell
qs-dmss cockpit --host 127.0.0.1 --port 8001
```

Then open [http://127.0.0.1:8001](http://127.0.0.1:8001) in a browser.

Inside the cockpit you can:

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

Scholarly indexing readiness and public-launch materials live in
[docs/ascl-joss-readiness.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/ascl-joss-readiness.md)
and
[docs/public-technical-launch-post.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/public-technical-launch-post.md).

The next research-grade upgrade slice is defined in
[docs/research-grade-upgrade-slice.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/research-grade-upgrade-slice.md),
with paper strategy notes in
[docs/research-paper-strategy.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/research-paper-strategy.md).

## Citation

Citation metadata lives in
[CITATION.cff](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/CITATION.cff).
GitHub uses this file to populate the repository citation prompt, and Zenodo can
use it when archiving GitHub releases.

For formal research references, prefer the Zenodo DOI citation:

- Project DOI: [10.5281/zenodo.20074924](https://doi.org/10.5281/zenodo.20074924)
- Latest archived release DOI: [v0.2.0 / 10.5281/zenodo.20091602](https://doi.org/10.5281/zenodo.20091602)
- Previous archived release DOI: [v0.1.5 / 10.5281/zenodo.20076871](https://doi.org/10.5281/zenodo.20076871)
- First archived release DOI: [v0.1.3 / 10.5281/zenodo.20074925](https://doi.org/10.5281/zenodo.20074925)
- Software Heritage archival: pending; add the SWHID after Software Heritage
  reports a completed archive for the release.

Zenodo citation notes live in
[docs/zenodo-citation.md](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/zenodo-citation.md).

## Current Scope

This branch intentionally focuses on the package/evidence/reproducibility spine
first. Optional accelerator backends, UI layers, plugin expansion, and broader
enterprise modules can now build on a stable execution loop:

`configure -> run -> measure -> bundle -> verify -> replay`

The cockpit adds the first browser-native product layer on top of that loop:

`configure -> launch -> inspect -> verify -> replay -> download`

The experiment registry now makes comparison durable too:

`select runs -> compare -> save -> report -> bundle -> reopen`

The decision layer adds recommendation semantics to that flow:

`select template -> launch campaign -> score runs -> recommend winner -> export evidence`

The campaign layer now automates the search plan too:

`select template -> expand campaign -> run matrix -> score variants -> recommend winner -> reopen bundle`
