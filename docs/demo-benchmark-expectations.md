# Demo And Benchmark Expectations

QS-DMSS has two lightweight validation paths with different purposes:

- `qs-dmss run-demo` and `qs-dmss campaigns run-demo` are installation and
  reproducibility smoke tests.
- `qs-dmss benchmarks validate` is a benchmark validation spine that runs
  packaged scenarios against expected metric envelopes and replay checks.

Neither path is peer-reviewed scientific validation of a dark matter model.

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
