# Fractal SSFM QPU Request Bundle

Status: experimental, provider-neutral, review-only transpilation.

QS-DMSS can convert the simulator-validated Fractal SSFM sidecar into a
hardware-target request bundle without connecting to a quantum provider. This
phase makes circuit portability, topology cost, credentials, and spending
boundaries inspectable before any provider adapter is considered.

## Run

Install the optional quantum stack and prepare the bundle:

```powershell
python -m pip install "qs-dmss[quantum]"
qs-dmss quantum prepare-qpu-request --output-root qpu-request-bundle
```

The output directory must be empty. The command first reruns the exact
simulator-sidecar gate, constructs a measurement-ready circuit, and transpiles
it against the packaged `generic-linear-5q` review profile.

## Target Contract

The review profile is deliberately provider-neutral:

- five generic qubits;
- a bidirectional linear coupling map;
- `rz`, `sx`, `x`, and `cx` basis gates;
- no physical calibration or device noise model;
- deterministic transpiler seed and explicit optimization level;
- no provider account, backend identifier, API call, or credential lookup.

This is a portability and resource-estimation surface, not a claim that a
specific device can execute the circuit with useful fidelity.

## Evidence Object

The generated bundle contains:

```text
qpu-request-bundle/
  qpu-request.json
  README.md
  target-profile.json
  environment.lock.json
  manifest.sha256.json
  qpu-request-evidence.zip
  artifacts/
    fractal-fuzzy-logical.qpy
    fractal-fuzzy-target.qpy
    fractal-fuzzy-target.openqasm
    fractal-fuzzy-target.txt
  reference-validation/
    quantum-sidecar-validation.json
    quantum-sidecar-validation.md
    quantum-sidecar-evidence.zip
    ...
```

`qpu-request.json` records logical and transpiled resources, requested shots,
target topology, artifact hashes, and four hard boundaries:

- `submitted: false` and `never_submit: true`;
- no provider or remote API call;
- no credentials read or accepted in the bundle;
- `max_authorized_cost_usd: 0.0`.

## Review Gate

The request is suitable for review by quantum software engineers and
computational scientists. Useful feedback includes:

- whether the target profile exposes enough topology and basis information;
- whether state-preparation and routing costs are reported clearly;
- which additional resource metrics are needed before selecting a real target;
- what security and cost controls a later provider adapter must enforce.

The follow-on
[`quantum-compilation-validation.md`](quantum-compilation-validation.md) harness
tests semantic preservation and resource attribution across fixed generic
topologies before any provider-specific profile is considered. Real QPU
submission, account credentials, job polling, result collection, and cost
authorization remain separate future decisions.

## Claim Boundary

The bundle demonstrates that the validated small circuit can be transpiled to
a declared generic hardware topology. It does not demonstrate QPU execution,
hardware fidelity, physical noise realism, quantum advantage, nonlinear
Schrodinger-Poisson coverage, or scientific validation of QS-DMSS.
