# Benchmark Validation

The QS-DMSS benchmark spine is a lightweight validation layer for the
package/evidence workflow. It is stronger than `run-demo` because it compares
generated metrics against packaged expected envelopes, verifies the evidence
bundle, and replays each selected scenario.

It is still not peer-reviewed scientific validation. The benchmarks validate
deterministic execution, evidence capture, manifest verification, replay, and
metric-envelope stability for the current reference implementation.

## Run The Benchmarks

List packaged scenarios:

```powershell
qs-dmss benchmarks list
```

Validate every packaged scenario:

```powershell
qs-dmss benchmarks validate
```

Run a fast single-scenario smoke:

```powershell
qs-dmss benchmarks validate --scenario demo-baseline
```

Write outputs to an explicit directory:

```powershell
qs-dmss benchmarks validate --output-root benchmark-validation
```

The validator writes:

- `benchmark-validation/runs/` for fresh benchmark run evidence.
- `benchmark-validation/replays/` for replay evidence.
- `benchmark-validation/benchmark-validation.json` for the summary report.

## Packaged Scenarios

- `demo-baseline`: demo-scale deterministic baseline for run, evidence,
  verification, metric-envelope, and replay checks.
- `resolution-smoke`: smaller-grid scenario proving validation is not tied to
  the demo resolution.
- `parameter-sensitivity`: shifted interaction-strength scenario validating
  bounded metrics under a different reference parameter.

The packaged benchmark assets live under
`src/qs_dmss/assets/benchmarks/` so source checkouts and installed wheels run
the same validator.

## What Gets Checked

Each selected scenario runs through the normal QS-DMSS execution path and must
produce the standard evidence artifacts:

- `config.yaml`
- `run.json`
- `metrics.json`
- `energy.csv`
- `environment.lock.json`
- `report.html`
- `manifest.sha256.json`
- `evidence_bundle.zip`

The benchmark validator then checks:

- manifest verification for the fresh run;
- expected metric envelopes for norm drift, energy drift, density, and runtime;
- expected history shape and final step;
- replay evidence verification;
- final-density replay compatibility within packaged tolerances.

## Interpreting Results

A passing benchmark means the packaged workflow remains reproducible for the
selected benchmark envelopes on the current platform. It does not mean the
model has been externally validated as a physical dark matter result.

A failing benchmark should be treated as review signal. It may indicate a real
regression, a numerical drift caused by dependency/runtime changes, or an
expected envelope that needs to be intentionally updated with reviewer-visible
rationale.

## CI Role

CI runs a single `demo-baseline` benchmark smoke in addition to the regular
test suite and installed-wheel smoke. The full benchmark set remains available
as a local or reviewer-driven command.
