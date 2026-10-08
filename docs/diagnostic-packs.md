# Data-only diagnostics pack pilot

This feature is in the v0.14.0 development build, not the published v0.13.2 wheel.
Identify a candidate by commit, wheel SHA-256 and retained implementation hashes,
not the version string alone. No publication,
scientific promotion, hosted compute or AI activation is authorized by this pilot.

## Complete researcher workflow

Use a qualified candidate installation. All commands print JSON; exit status 0
means admission/integrity success or all numerical cases passing, respectively.
Status 1 means an authored failure or a retained numerical counterexample.

```console
qs-dmss diagnostic-packs inspect
qs-dmss diagnostic-packs run --output fft-reference-result
qs-dmss diagnostic-packs verify fft-reference-result/diagnostic-pack-evidence.zip
```

The output parent must already exist and the output directory must be new, even
if an existing directory is empty. `inspect` is read-only. `run` admits once into
an immutable in-memory snapshot, evaluates that snapshot, and exports it without
changing the original files. Interrupted/failed writes retain partial output for
diagnosis; a bundle is written last. Choose a new directory for a retry.

To inspect or run an external data pack, add `--pack PATH_TO_DIRECTORY`. It must
contain **exactly** `manifest.json` and `cases.json`. This pilot has no installation
registry, auto-discovery, ZIP import, pack UI, or network dependency resolver.
Do not treat schema admission as an endorsement of third-party source or license
assertions; a human must review those before redistribution.

For a source-pinned qualification, optionally add `--source-commit FULL_40_HEX`
and `--candidate-wheel-sha256 FULL_64_HEX` to `run`. These are explicitly
**caller-declared**, not independently verified. The result separately records
actual input/module byte hashes, core metadata, Python, platform and NumPy.
Retain the candidate wheel separately; it is not copied into this bundle.

## Closed admission contract

The checked-in schemas are [manifest v1](../schemas/diagnostic-pack-v1.schema.json)
and [cases v1](../schemas/diagnostic-pack-cases-v1.schema.json). They are generated
from the strict, extra-forbidden, frozen Pydantic models and are also packaged.
Tests require source, packaged and model schemas to agree. Runtime additionally
checks relationships that JSON Schema cannot express, such as content hashes,
aggregate grid budgets, Nyquist bounds, unique case IDs and analytic coherence.

The manifest declares ID/type/version/title, a stable three-component inclusive
minimum/exclusive maximum core-version interval, diagnostic conventions, an
explicit empty list of **additional** dependencies, SPDX license, attribution,
source and redistribution assertion, resource ceilings, evidence format,
content SHA-256, built-in diagnostic ID and core-owned acceptance-suite ID.

The pilot supports only `fft_plane_wave_energy_v1`, convention
`fft_cell_measure_v2`, and acceptance suite `fft_plane_wave_pack_contract_v1`.
The suite is implemented in `tests/test_diagnostic_packs.py`; packs cannot name
commands or test files to execute. License admission is intentionally restricted
to `Apache-2.0` and `CC0-1.0`, not all valid SPDX identifiers. Compatibility applies
to admission-capable source builds; it does not imply this command exists in
the historical published v0.13.2 wheel.

Unknown keys/actions, nonempty dependencies, incompatible versions/conventions,
invalid/unsupported licenses, duplicate JSON members, nonfinite numbers,
invalid UTF-8 or escaped surrogates, malformed/deep JSON and reference forgery
fail closed. Scalars are strict: booleans or numeric strings cannot stand in for
numeric controls. Content paths are the literal `cases.json`; arbitrary paths,
linked/reparse roots or children, nonregular files and extra entries are rejected.
The directory scan stops at its third entry, before reading pack files.

Core ceilings are 64 KiB per input file, 32 cases, 128 cells per axis,
16,384 cells per case, 65,536 cells across the complete case set, and 512 KiB per
exported/read evidence bundle. A pack may declare only tighter ceilings, which
are enforced before any numerical allocation. Reads consume at most the byte
ceiling plus one overflow-detection byte, not an unchecked `read_bytes()`.
Mass and domain length are bounded to 0.1–100; modes must be strictly below
Nyquist. Absolute/relative energy tolerances are each 1e-14–1e-9. The bundled
12-case pack declares tighter file/count/aggregate limits and uses 1e-12 energy
tolerances. These are per-invocation size/work bounds, not wall-clock guarantees
or concurrent-process control. Check-time link rejection is not descriptor-
anchored protection against an adversary concurrently replacing filesystem paths.

## Numerical scope and acceptance

The bundled references cover zero mode, multiple resolutions, a rectangular
grid, positive/negative and joint-axis modes, domain-length and mass changes,
maximum supported grid size, and a high resolved mode. They are original,
maintainer-authored analytic data under Apache-2.0, not imported third-party data.

For a square periodic two-dimensional domain, with hbar=1, zero potential and
interaction, choose the unit-norm wavefunction
`psi(x,y)=exp(2*pi*i*(mode_x*x/L+mode_y*y/L))/L`. Integration over area `L^2`
gives norm 1 and kinetic energy
`E=(2*pi/L)^2*(mode_x^2+mode_y^2)/(2*mass)`. The CPU Fractal SSFM solver's
existing `compute_energy` and `compute_norm` are measured directly; no trajectory,
projection, graph, QPU, AI or provider operation is requested.

The declared reference must agree with the core-owned formula within **both**
the core coherence tolerance and the case's declared tolerance. Measurement is
compared to the fresh analytic formula, not an arbitrary supplied target:
`abs(measured-analytic) <= absolute_tolerance + relative_tolerance*abs(analytic)`.
Norm error must be at most 1e-12. Nonfinite measurements or any failed case produce
`FALSIFIED_WITHIN_SCOPE`, exit 1 and retained evidence—not a silently omitted case.
All passing cases produce `NOT_FALSIFIED_WITHIN_SCOPE`. Neither outcome supplies
independent scientific review, physical calibration or continuum convergence.
Scientific status stays `NOT_ESTABLISHED`, human disposition `PENDING`, AI advice
`null`; [gate #183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183)
remains separate and open.

## Result/evidence format v1

`result.json` (`qs-dmss-diagnostic-pack-result/v1`) retains the admitted manifest,
exact normalized cases/tolerances, analytic/measured energy and norm, finite or
null measurements, absolute error and allowed error, case pass flags, aggregate
outcome, scientific/human/AI statuses, limitations, environment, module/input
hashes, explicit execution policy and caller-declared candidate identities.
`summary.md` gives exact per-case values and the limitations without a validation
badge. Source JSON bytes are copied unchanged under `pack/`.

`manifest.sha256.json` (`qs-dmss-diagnostic-pack-integrity/v1`) hashes and records
the byte size of exactly four files: `result.json`, `summary.md`,
`pack/manifest.json`, `pack/cases.json`. The unencrypted, stored ZIP contains those
four files plus the manifest. Its own SHA-256 is returned by `run`/`verify`;
self-referential manifest/bundle hashes are deliberately excluded. The archive
uses fixed entry ordering/timestamps, but environment/implementation bytes can
differ across systems, so cross-platform bundle identity is not promised.

`verify` never extracts or executes archive content. It checks the exact entry
set, duplicates, storage/compression policy, expanded/physical byte bounds, CRCs,
all four hashes/sizes and manifest shape. It explicitly reports
`content_hashes_only_not_rerun_or_authorship`: it is not result-schema admission,
a fresh numerical replay, a signature, or proof that references/measurements
are correct. A malicious party can replace a file and its manifest together.
Rerun a preserved `pack/` snapshot with the pinned candidate to reproduce.

Bundle input must itself be a literal regular file, not a link, reparse point,
directory or pipe. It is checked before opening and rechecked after opening;
check-time race limitations still apply. Legacy output-parent resolution loops
receive an authored failure before output creation, not a parser/storage traceback.

## Scope freeze after this pilot

After protected review/merge and post-merge checks, freeze v0.14.0 feature scope.
The next work is a release qualification/preparation pass, not another add-on:
supported Python matrix, all-OS candidate wheel, Docker, full tests/coverage,
security/dependency/license/provenance review, artifact compatibility and a
researcher acceptance walkthrough. Explicitly dispose of the local Windows
Application Control restriction (WinError 4551) without bypassing policy.
Green hosted checks cannot qualify a feature that remains local-only.

No new solver/provider IDs, executable plugins, Wolfram adapter, hosted AI/graph
execution, multidimensional explorer or broad UI expansion is bundled here.
Do not bump/tag/upload until separately authorized and release gates pass.
