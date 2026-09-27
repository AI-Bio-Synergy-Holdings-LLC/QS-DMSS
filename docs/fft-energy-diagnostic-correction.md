# FFT energy diagnostic correction

The reference NumPy and rectangular fractal SSFM energy diagnostics previously
omitted the cell measure from the kinetic term. With the unnormalized forward FFT,
Parseval's identity requires `cell_measure * sum(k² |FFT(psi)|²) / (2 m N)`.
The correction uses cell volume in 3D and cell area in the embedded 2D backend
(including its existing CuPy path). No propagation, potential, or interaction
formula changes are included.

New metrics identify this convention as `fft_cell_measure_v2`. Missing convention
metadata in older evidence means legacy/unspecified, not the corrected formula.
Do not overwrite historical bundles, hashes, benchmark records, or published review
evidence. Replaying an old configuration creates new evidence under the current
formula; wavefunctions remain reproducible but energies and energy-based decisions
may change. Total energies cannot be corrected by multiplying the old total by a
cell measure: only the kinetic component was affected. Rebaseline energy thresholds
and comparisons explicitly with both provenance records retained.

The three executable packaged benchmark envelopes were explicitly rebaselined;
their previous ranges remain in `legacy_energy_drift_envelope`. Local observed
drifts were 0.000582695007 (demo), 0.000411987305 (resolution), and 0.001873970032
(parameter sensitivity). The envelopes allow cross-platform floating-point margin,
not physical error tolerances. The reference potential's existing zero-frequency
regularization produces a large constant offset and cancellation-sensitive energy
differences; changing that model/gauge is a separate scientific decision.

Analytic unit-norm plane waves test grid-size invariance, non-unit domains, masses,
and rectangular grids. Constant fields separately check the unchanged other terms.
This numerical diagnostic correction does not resolve independent scientific-review
gates or establish physical validation.
