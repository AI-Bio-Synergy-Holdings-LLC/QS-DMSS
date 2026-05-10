# Evidence Bundle Glossary

QS-DMSS evidence bundles are designed to make a run inspectable without
depending on local memory, screenshots, or notebook state. A bundle is a ZIP
copy of the run directory plus a manifest of file hashes.

## Run Files

- `config.yaml`: The normalized configuration used for the run. Replay uses
  this file rather than the original source path.
- `run.json`: The run ledger record, including run ID, source config name,
  config digest, timestamps, metrics summary, replay commands, and optional
  experiment or campaign context.
- `metrics.json`: Machine-readable run metrics, including norm, energy,
  drift, max density, elapsed seconds, and logged history snapshots.
- `energy.csv`: A tabular history of recorded solver steps for quick review in
  spreadsheets or plotting tools.
- `environment.lock.json`: Lightweight runtime metadata such as Python,
  platform, package, and dependency versions.
- `manifest.sha256.json`: SHA-256 checksums for bundle files. `qs-dmss verify`
  uses this to detect missing or changed artifacts.
- `report.html`: A local HTML summary for human inspection of the run,
  evidence status, metrics, and decision profile when available.
- `evidence_bundle.zip`: The portable evidence archive for sharing or storing
  the full run record.

## Numerical Artifacts

- `artifacts/final_density.npy`: NumPy array containing the final density field.
  Replay comparisons can check this artifact for deterministic compatibility.
- `artifacts/final_state.npz`: NumPy archive containing the real and imaginary
  parts of the final wavefunction.

## Experiment And Campaign Files

Experiment bundles can also include copied run evidence, comparison summaries,
decision recommendations, manifests, reports, and campaign metadata. These
files are reproducibility artifacts for reviewing how a recommendation was
produced. They are not peer-reviewed scientific validation of the model.

## Reviewer Checks

Use these commands after a demo or benchmark run:

```powershell
qs-dmss verify runs\<run_id>
qs-dmss replay runs\<run_id>
qs-dmss benchmarks validate --scenario demo-baseline
```

A passing verification means the recorded files match the manifest. A passing
replay means the captured config can reproduce compatible outputs in the
current runtime.
