# Reviewer Install Quickstart

This path validates QS-DMSS from a published distribution without a source
checkout. It is intended for reviewers who need a fast productization smoke
test.

Release: `v0.7.0`

PyPI:
`https://pypi.org/project/qs-dmss/`

Wheel:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/download/v0.7.0/qs_dmss-0.7.0-py3-none-any.whl`

## PyPI Install

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qs-dmss

qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss benchmarks validate --scenario demo-baseline
qs-dmss showcase run --output-root simulation-showcase
```

Linux/macOS Bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install qs-dmss

qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss benchmarks validate --scenario demo-baseline
qs-dmss showcase run --output-root simulation-showcase
```

## GitHub Release Wheel

Use this path when validating the GitHub release asset directly.

Windows PowerShell:

```powershell
$release = "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/download/v0.7.0"
Invoke-WebRequest "$release/qs_dmss-0.7.0-py3-none-any.whl" -OutFile "qs_dmss-0.7.0-py3-none-any.whl"
python -m pip install .\qs_dmss-0.7.0-py3-none-any.whl
```

Linux/macOS Bash:

```bash
release="https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/download/v0.7.0"
python -m pip install "$release/qs_dmss-0.7.0-py3-none-any.whl"
```

## Expected Signals

- `python -m pip install` reports the expected `qs-dmss` version.
- `qs-dmss run-demo` prints a run directory, evidence bundle path, and
  `Verification passed`.
- `qs-dmss campaigns run-demo` prints a saved campaign ID, planned run count,
  recommended run, decision status, and experiment bundle path.
- `qs-dmss benchmarks validate --scenario demo-baseline` prints
  `Benchmark passed: demo-baseline` and writes a benchmark validation report.
- `qs-dmss showcase run --output-root simulation-showcase` prints
  `Simulation showcase passed: canonical-simulation` and writes a reviewer
  summary, CSV tables, SVG plots, verified run evidence, and replay evidence.

The demo is a smoke test for installation, deterministic execution, evidence
generation, verification, and replay. It is not a scientific benchmark and does
not claim peer-reviewed physical significance.

The showcase is a small simulation-inspection path for the packaged reference
solver. It demonstrates workflow and simulation behavior; it is not
peer-reviewed scientific validation.

For artifact definitions, see
[docs/evidence-bundle-glossary.md](evidence-bundle-glossary.md). For the
difference between demo smoke tests and benchmark validation, see
[docs/demo-benchmark-expectations.md](demo-benchmark-expectations.md).

Representative `qs-dmss run-demo` output:

```text
Demo config: .../demo.yaml
Run complete: .../runs/demo-20260508T005532Z-e132e11e
Evidence bundle: .../runs/demo-20260508T005532Z-e132e11e/evidence_bundle.zip
Verification passed for .../runs/demo-20260508T005532Z-e132e11e
Checked files: 8
```

Representative `qs-dmss campaigns run-demo` output:

```text
Campaign saved: campaign-20260508T005536Z-a1acec40
Label: Stability frontier campaign
Planned runs: 6
Recommended run: demo-g-int-0-02-time-step-0-015-20260508T005536Z-134a1eaf
Decision status: qualified
Reason: Recommended run satisfies every active constraint and achieved the strongest weighted score.
Bundle: .../experiments/campaign-20260508T005536Z-a1acec40/evidence_bundle.zip
```

## Reproducibility Review Checklist

- Confirm `python -m pip install qs-dmss` succeeds in a fresh environment.
- Confirm `qs-dmss run-demo` writes outputs under a caller-controlled `runs/`
  path or the current working directory.
- Confirm the generated run includes `run.json`, `metrics.json`,
  `environment.lock.json`, `manifest.sha256.json`, and `evidence_bundle.zip`.
- Confirm `qs-dmss verify <run_dir>` reports `Verification passed`.
- Confirm `qs-dmss replay <run_dir>` creates a new verified replay run.
- Confirm `qs-dmss campaigns run-demo` writes an experiment bundle and reports
  a recommendation status.
- Confirm `qs-dmss benchmarks validate --scenario demo-baseline` verifies the
  packaged benchmark evidence and replay path.
- Confirm `qs-dmss showcase run --output-root simulation-showcase` writes
  `simulation-showcase.md`, CSV/SVG artifacts, and verified run/replay
  evidence.
- Open a Reproducibility Review issue if any install, output path, verification,
  replay, or campaign step behaves differently on your platform.

## Optional Source Checkout

Use this path only when reviewing repository contents or running the full test
suite.

```powershell
git clone https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS.git
cd QS-DMSS
git checkout v0.7.0
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pytest
```
