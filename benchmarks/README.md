# QS-DMSS Benchmarks

The benchmark spine is the post-beta validation path for QS-DMSS. It is
separate from the quick demo so reviewers can distinguish install smoke tests
from evidence-backed benchmark checks.

Run the packaged benchmark validator from a source checkout or installed wheel:

```powershell
qs-dmss benchmarks validate
```

For a faster single-scenario check:

```powershell
qs-dmss benchmarks validate --scenario demo-baseline
```

The command writes normal QS-DMSS run evidence under
`benchmark-validation/runs/`, replay evidence under
`benchmark-validation/replays/`, and a summary report at
`benchmark-validation/benchmark-validation.json`.

Canonical benchmark assets are packaged under
`src/qs_dmss/assets/benchmarks/` so the same validator can run from source
checkouts and installed distributions.
