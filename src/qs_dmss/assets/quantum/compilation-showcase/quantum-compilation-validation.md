# QS-DMSS Quantum Compilation Validation

Overall status: **PASS**
Generated at: `2026-07-13T02:26:19.563879+00:00`

The matrix validates exact logical-output preservation and attributes
resource growth across state preparation, SSFM evolution, routing, and
measurement for generic local targets only.

## Matrix

| Topology | Opt | Class | Pass | Pareto | Depth | CX | State L2 | Fidelity | TVD | Leakage |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| generic-linear-5q | 0 | reference_exact | PASS | no | 173 | 156 | 2.566e-15 | 1.000000000000 | 2.423e-15 | 0.000e+00 |
| generic-linear-5q | 1 | reference_exact | PASS | no | 147 | 144 | 2.282e-15 | 1.000000000000 | 2.129e-15 | 0.000e+00 |
| generic-linear-5q | 2 | bounded_approximation | PASS | no | 43 | 20 | 7.066e-07 | 1.000000000000 | 5.491e-07 | 0.000e+00 |
| generic-linear-5q | 3 | bounded_approximation | PASS | no | 42 | 19 | 7.066e-07 | 1.000000000000 | 5.491e-07 | 0.000e+00 |
| generic-ring-5q | 0 | reference_exact | PASS | no | 159 | 147 | 2.029e-15 | 1.000000000000 | 1.885e-15 | 0.000e+00 |
| generic-ring-5q | 1 | reference_exact | PASS | no | 147 | 135 | 2.025e-15 | 1.000000000000 | 1.902e-15 | 0.000e+00 |
| generic-ring-5q | 2 | bounded_approximation | PASS | no | 43 | 20 | 7.066e-07 | 1.000000000000 | 5.491e-07 | 0.000e+00 |
| generic-ring-5q | 3 | bounded_approximation | PASS | no | 42 | 19 | 7.066e-07 | 1.000000000000 | 5.491e-07 | 0.000e+00 |
| generic-all-to-all-5q | 0 | reference_exact | PASS | no | 113 | 84 | 2.168e-15 | 1.000000000000 | 1.995e-15 | 0.000e+00 |
| generic-all-to-all-5q | 1 | reference_exact | PASS | yes | 108 | 84 | 1.530e-15 | 1.000000000000 | 1.275e-15 | 0.000e+00 |
| generic-all-to-all-5q | 2 | bounded_approximation | PASS | no | 35 | 14 | 7.066e-07 | 1.000000000000 | 5.491e-07 | 0.000e+00 |
| generic-all-to-all-5q | 3 | bounded_approximation | PASS | yes | 34 | 13 | 7.066e-07 | 1.000000000000 | 5.491e-07 | 0.000e+00 |

## Recommended Generic Configuration

- Topology: `generic-all-to-all-5q`
- Optimization level: `3`
- Depth: `34`
- CX gates: `13`
- State L2 error: `7.066010e-07`
- Acceptance class: `bounded_approximation`
- Rule: minimum CX count, then depth and circuit size, among tolerance-passing Pareto rows

### Resource Attribution

| Component | Depth | CX | Size |
| --- | ---: | ---: | ---: |
| state_preparation | 9 | 2 | 26 |
| ssfm_evolution | 27 | 12 | 71 |
| measurement | 1 | 0 | 4 |
| full_experiment | 34 | 13 | 95 |

## Claim Boundary

Local, ideal-simulator validation of logical-to-target circuit semantics and resource attribution across fixed generic topologies. It is not physical hardware validation, calibrated-noise analysis, provider selection, QPU execution, cost prediction, quantum advantage, or scientific validation of the underlying Fractal SSFM model.

No provider, credential, remote API, QPU, or authorized spend was used.
