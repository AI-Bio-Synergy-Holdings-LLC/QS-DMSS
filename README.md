# QS-DMSS

QS-DMSS is a deterministic, evidence-first reference build of the QuantumScalar
Dark Matter Simulation Suite. This repository now ships the productization spine
needed to move from prototype scripts into a reproducible package:

- Installable Python package
- Config-driven simulation CLI
- Local-first run cockpit and JSON API
- Run ledger with stable run IDs and config digests
- Evidence bundle with artifacts, metrics, manifest, and HTML report
- Replay and verification commands for reproducibility checks

## What This Build Includes

The current reference implementation focuses on the backbone needed for
productization:

- A NumPy-based split-step Schrodinger-Poisson solver
- YAML configuration loading with explicit validation
- Structured run outputs under `runs/<run_id>/`
- A local cockpit for launch, inspection, verification, replay, and bundle download
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

Create a virtual environment and install the package in editable mode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Run the checked-in demo config:

```powershell
qs-dmss run configs/demo.yaml
```

Start the local cockpit:

```powershell
qs-dmss cockpit --host 127.0.0.1 --port 8001
```

Then open [http://127.0.0.1:8001](http://127.0.0.1:8001) in a browser.

Verify the generated evidence bundle:

```powershell
qs-dmss verify runs\<run_id>
```

Replay a prior run using the captured config:

```powershell
qs-dmss replay runs\<run_id>
```

## Project Layout

```text
configs/                 Checked-in example configs
schemas/                 JSON schema for run configs
src/qs_dmss/             Package source
tests/                   Smoke and reproducibility tests
```

## Development

Run the smoke tests:

```powershell
pytest
```

## Current Scope

This branch intentionally focuses on the package/evidence/reproducibility spine
first. Optional accelerator backends, UI layers, plugin expansion, and broader
enterprise modules can now build on a stable execution loop:

`configure -> run -> measure -> bundle -> verify -> replay`

The cockpit adds the first browser-native product layer on top of that loop:

`configure -> launch -> inspect -> verify -> replay -> download`
