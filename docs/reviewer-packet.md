# Reviewer Packet

This packet is the shortest path for an external reviewer to understand what
QS-DMSS is claiming, reproduce the public baseline, and decide where feedback
would be most useful.

Current public baseline: `v0.3.0` / `qs-dmss==0.3.0`

Release DOI: `10.5281/zenodo.20112923`

Project DOI: `10.5281/zenodo.20074924`

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
python -m pip install qs-dmss==0.3.0

qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss benchmarks validate --scenario demo-baseline
```

Expected signals:

- `qs-dmss run-demo` writes a run under `runs/`, prints an evidence bundle, and
  reports `Verification passed`.
- `qs-dmss campaigns run-demo` writes an experiment under `experiments/` and
  reports a recommended run plus decision status.
- `qs-dmss benchmarks validate --scenario demo-baseline` writes
  `benchmark-validation/benchmark-validation.json` and reports
  `Benchmark passed: demo-baseline`.

Use [reviewer-wheel-quickstart.md](reviewer-wheel-quickstart.md) for the
cross-platform PyPI and GitHub release-wheel commands.

## Review Lanes

Choose the lane that matches the feedback you want to provide.

| Lane | What to check | Best issue type |
| --- | --- | --- |
| Installability | Fresh virtual environment, PyPI install, release wheel install, CLI help | Bug report or reproducibility review |
| Evidence workflow | `run-demo`, generated artifacts, `verify`, `replay`, bundle contents | Reproducibility review |
| Campaign workflow | `campaigns run-demo`, campaign metadata, recommendation status, experiment bundle | Reproducibility review or feature request |
| Benchmark workflow | `benchmarks list`, `benchmarks validate`, metric envelope report, replay compatibility | Scientific review or reproducibility review |
| Documentation | README, reviewer quickstart, evidence glossary, benchmark expectations | Documentation issue |
| Paper readiness | JOSS paper scaffold, state-of-field comparison, research impact evidence | Scientific review |

Open feedback through
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/new/choose`.

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
