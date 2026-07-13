# Quantum Compilation Validation and Resource Attribution

Status: experimental, local-simulator validation; no provider integration.

QS-DMSS validates whether the Fractal SSFM reference experiment survives
target transpilation and shows where circuit cost is introduced. This gate sits
between the provider-neutral QPU request bundle and any future consideration of
a provider-specific target profile.

## Run

```powershell
python -m pip install "qs-dmss[quantum]"
qs-dmss quantum validate-compilation --output-root quantum-compilation-validation
```

The command reruns the exact simulator sidecar and baseline QPU request before
building a fixed 12-row matrix:

- generic linear, ring, and fully connected five-qubit targets;
- transpiler optimization levels `0`, `1`, `2`, and `3`;
- `rz`, `sx`, `x`, and `cx` basis gates;
- deterministic target construction and transpiler seed.

No named device, provider SDK, account, credential, calibration snapshot,
pricing API, remote request, or QPU job is used.

## Hosted Read-only Showcase

The public [QS-DMSS Studio](https://app.qs-dmss.studio/#quantum-validation)
ships a fixed v0.12.0 snapshot of this validation object. It exposes the
matrix, topology/resource charts, validation status, limitations, a polished
HTML report, Markdown and CSV summaries, JSON report, manifest, and evidence
ZIP through allowlisted GET routes. It does not expose a compilation POST route and does not require the
optional Qiskit stack at runtime.

## Semantic Gate

Each transpiled circuit is run with the local ideal statevector simulator. The
final physical layout and measurement map are used to reconstruct the original
four-qubit logical state. The report records:

- global-phase-aligned state L2 error;
- state fidelity;
- output-density total-variation distance;
- probability leakage into the unused fifth qubit.

The source sidecar retains its strict `1e-10` reference tolerance. Compilation
uses a separate declared `1e-6` tolerance because Qiskit optimization levels
`2` and `3` introduce a small synthesis approximation while substantially
reducing resource cost. Rows are labelled:

- `reference_exact` when they also satisfy the strict source tolerance;
- `bounded_approximation` when they satisfy only the compilation tolerance.

This distinction prevents lower gate counts from being presented as free or
exact improvements.

## Resource Attribution

Every matrix row reports target depth, size, operation counts, and CX count for:

- initial-state preparation;
- the Fractal SSFM evolution circuit;
- measurement;
- the optimized full experiment.

Routing overhead is measured against the fully connected topology at the same
optimization level. Pareto status considers semantic class, depth, and CX
count. The resource-minimizing passing row is reported separately from the
near-machine-precision frontier.

The initial reference result demonstrates the tradeoff:

- fully connected, optimization level `1`: near-machine-precision semantics,
  depth `108`, CX count `84`;
- fully connected, optimization level `3`: bounded state error near `7.1e-7`,
  depth `34`, CX count `13`.

These values are reproducible software-target diagnostics, not device
performance predictions.

## Evidence Object

```text
quantum-compilation-validation/
  quantum-compilation-validation.json
  quantum-compilation-validation.html
  quantum-compilation-validation.md
  quantum-compilation-matrix.csv
  manifest.sha256.json
  quantum-compilation-evidence.zip
  circuits/
    generic-linear-5q-opt0.openqasm
    ...
    generic-all-to-all-5q-opt3.qpy
  baseline-request/
    qpu-request.json
    reference-validation/
    ...
```

The nested baseline preserves the exact encoding and request-bundle evidence,
while the outer manifest verifies every matrix and circuit artifact.

## Decision Boundary

This harness must be reviewed before adding a provider-specific target. The
next review question is not "which QPU should run QS-DMSS?" It is whether the
semantic classes, topology matrix, attribution model, and resource frontier are
sufficient to justify evaluating a named provider profile.

Real submission, credentials, job polling, result collection, physical noise,
cost authorization, and hosted quantum execution remain separate future gates.

## Claim Boundary

The harness demonstrates ideal-simulator semantic preservation within declared
tolerances and measures generic compilation resource costs. It does not
demonstrate hardware fidelity, physical-noise robustness, quantum advantage,
nonlinear quantum feedback, or scientific validation of the Fractal SSFM model.
