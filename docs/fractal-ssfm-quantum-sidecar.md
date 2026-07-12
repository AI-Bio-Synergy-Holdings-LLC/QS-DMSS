# Fractal SSFM Quantum-Readiness Sidecar

Status: experimental, simulator-only encoding validation.

QS-DMSS includes an optional local sidecar that compares one deliberately small
Fractal SSFM step against a quantum-circuit representation. The sidecar exists
to make quantum-readiness claims testable and evidence-backed. It is not a QPU
connector and does not replace the NumPy reference solver.

## Validated Slice

The packaged profile is fixed to:

- a `4 x 4` two-dimensional grid encoded in four qubits;
- `geometry.mode: fuzzy_potential`;
- `engine.g_int: 0.0`;
- one Strang split step;
- no hard or soft mask projection;
- no spectral de-alias filter;
- a deterministic Gaussian initial state.

This boundary isolates the unitary portion of the Fractal SSFM backend:

```text
2-D QFT -> kinetic phase -> inverse QFT
        -> fuzzy-potential phase
2-D QFT -> kinetic phase -> inverse QFT
```

The exact Qiskit statevector is compared with the existing NumPy
`FractalQuadrantSSFMSolver` result after global-phase alignment. Qiskit Aer then
produces deterministic ideal sampling and a separate synthetic depolarizing
noise diagnostic.

## Install and Run

Install the optional local simulator stack:

```powershell
python -m pip install "qs-dmss[quantum]"
```

From a source checkout:

```powershell
python -m pip install -e ".[dev,quantum]"
qs-dmss quantum validate-fractal --output-root quantum-sidecar-validation
```

No provider account, cloud credential, QPU, or remote submission is used.

## Evidence Object

The command writes:

```text
quantum-sidecar-validation/
  profile.yaml
  environment.lock.json
  quantum-sidecar-validation.json
  quantum-sidecar-validation.md
  manifest.sha256.json
  quantum-sidecar-evidence.zip
  artifacts/
    fractal-fuzzy-strang.openqasm
    fractal-fuzzy-strang.qpy
    fractal-fuzzy-strang.txt
    measurement-counts.json
    state-comparison.npz
```

The report records:

- global-phase-aligned statevector error;
- density mean absolute error;
- norm error;
- ideal and synthetic-noise sampling distances;
- conservative shot uncertainty;
- qubit count, circuit depth, basis operations, and two-qubit gate count;
- package versions, seeds, profile digest, and explicit submission policy.

The synthetic noise result is diagnostic only. It is not based on physical
device calibration and does not determine pass/fail.

## Research Context

The sidecar is motivated by hybrid quantum-classical proposals for nonlinear
wave and Schrodinger-Poisson systems, where the linear Fourier-space evolution
is circuit-compatible but self-consistent nonlinear feedback remains difficult.
Relevant conceptual references include:

- Mocz and Szasz, "Towards Cosmological Simulations of Dark Matter on Quantum
  Computers," arXiv:2101.05821.
- Weng et al., "Quantum simulation of the nonlinear Schrodinger equation via
  measurement-induced potential reconstruction," arXiv:2601.19184 (preprint).
- OpenQASM 3 specification and language resources: <https://openqasm.com/>.

These works motivate the experiment; they do not validate QS-DMSS or establish
quantum advantage for this sidecar.

## Claim Boundary

The defensible statement is:

> QS-DMSS includes a simulator-only quantum-readiness sidecar that validates a
> small, linear, phase-only Fractal SSFM circuit encoding against the NumPy
> reference and emits a manifest-verified evidence object.

The sidecar does not claim:

- QPU execution or quantum advantage;
- nonlinear `g_int` feedback on a quantum device;
- hard/soft mask encoding;
- production-scale quantum simulation;
- peer-reviewed physical validation.

## Hardware-Target Review Gate

The follow-on `quantum prepare-qpu-request` command generates the planned dry-run
QPU request bundle. It records OpenQASM, native circuit serialization, a generic
target topology, shots, logical-to-target resource estimates, zero authorized
spend, credential boundaries, and `submitted: false`. See
[`fractal-ssfm-qpu-request-bundle.md`](fractal-ssfm-qpu-request-bundle.md).

The generic target is not a physical backend and carries no calibration data.
A provider-specific target profile or execution adapter remains a later,
explicit opt-in decision requiring separate security, cost, and scientific
review.

Scientific feedback should remain linked to the classical Fractal SSFM review
gate in issue #105 so circuit agreement is not mistaken for model validation.
