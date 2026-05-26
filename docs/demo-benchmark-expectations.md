# Demo And Benchmark Expectations

QS-DMSS has two lightweight validation paths with different purposes:

- `qs-dmss run-demo` and `qs-dmss campaigns run-demo` are installation and
  reproducibility smoke tests.
- `qs-dmss benchmarks validate` is a benchmark validation spine that runs
  packaged scenarios against expected metric envelopes and replay checks.
- `qs-dmss showcase run` is a reviewer-facing simulation walkthrough that
  generates CSV tables, SVG plots, verified evidence, and replay evidence for a
  canonical scenario.

None of these paths is peer-reviewed scientific validation of a dark matter
model.

## Demo Runtime Expectations

The bundled demo uses a small NumPy grid and should complete quickly on a
typical laptop or CI runner. Runtime can vary by Python version, operating
system, CPU, and dependency versions, so reviewers should treat elapsed seconds
as a practical smoke signal rather than a fixed performance benchmark.

Expected demo signals:

- The command creates a run directory under `runs/` or the requested
  `--output-root`.
- The command prints an evidence bundle path.
- `qs-dmss verify <run_dir>` reports `Verification passed`.
- `qs-dmss replay <run_dir>` creates a second verified run.

## Benchmark Runtime Expectations

The packaged benchmark scenarios are still intentionally small. They add
stronger checks than the demo by validating:

- evidence bundle verification;
- expected metric envelopes;
- expected history shape and final step;
- replay verification;
- final-density replay compatibility.

Run a fast benchmark smoke:

```powershell
qs-dmss benchmarks validate --scenario demo-baseline
```

Run every packaged scenario:

```powershell
qs-dmss benchmarks validate
```

Benchmark failures should be treated as review signals. They may indicate a
real regression, platform-specific numerical drift, or an expected envelope
that needs to be intentionally updated with clear rationale.

## Showcase Runtime Expectations

The canonical showcase uses a slightly larger grid than the demo while still
remaining small enough for local reviewer use. It should complete quickly on a
typical laptop, but reviewers should treat runtime as a practical signal rather
than a fixed performance benchmark.

Run the showcase from a source checkout that includes the command:

```powershell
qs-dmss showcase run --output-root simulation-showcase
```

Expected showcase signals:

- The command creates `simulation-showcase/simulation-showcase.md`.
- The command creates a verified run under `simulation-showcase/runs/`.
- The command creates a verified replay under `simulation-showcase/replays/`.
- The command creates CSV and SVG artifacts under
  `simulation-showcase/artifacts/` so reviewers can inspect energy history,
  radial density, and the final-density midplane without custom plotting code.
