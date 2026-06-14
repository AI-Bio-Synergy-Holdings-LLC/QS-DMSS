# Scientific Scope And Tangible Utility

QS-DMSS is an evidence-first simulation lab for small, deterministic
Schrodinger-Poisson-style quantum scalar dark matter studies. It is designed to
make a simulation run inspectable as a research object: configured, measured,
bundled, verified, replayable, comparable, citable, and ready for review.

## Strategic Lane

QS-DMSS should not be positioned as a replacement for production cosmological
codes such as adaptive-mesh, MPI, GPU, or RAMSES/GAMER-style simulation suites.
Its current lane is narrower and more practical:

- classical NumPy reference runs, not quantum-computing algorithms;
- laptop-scale or CI-scale sandbox studies, not cosmological-volume discovery;
- transparent configuration, evidence capture, replay, and campaign comparison;
- education, review, reproducibility, and prototype workflows before HPC scale;
- honest scientific boundaries until independent validation exists.

The product moat is therefore not "we have another solver." The moat is:

```text
run simulations -> inspect evidence -> compare campaigns -> publish reproducible artifacts
```

## Tangible Utility Summary

QS-DMSS is useful when someone needs to answer operational research-software
questions quickly:

- Can I run a small reference scenario without building an HPC stack?
- Can I compare how parameter choices affect drift, density, runtime, and
  verification status?
- Can I preserve the config, environment, metrics, plots, manifests, bundle,
  replay path, and citation metadata together?
- Can another person rerun or critique the same campaign design from a shared
  artifact?

This makes QS-DMSS most useful today as:

- a rapid sandbox for Schrodinger-Poisson-style model variations;
- an educational lab for wave-dark-matter workflow concepts;
- a reproducibility harness for deterministic simulation artifacts;
- an API/cockpit-accessible run and campaign launcher;
- a publication-object composer for evidence bundles and reports.

## What The Current Solver Does

The current reference build evolves a complex wavefunction with a NumPy-based
split-step/FFT-style solver and couples it to a Poisson-style gravitational
potential computed from the density field. It also supports a nonlinear
self-interaction control through `engine.g_int`.

The default demo config is intentionally small:

- `engine.grid_shape: [8, 8, 8]`
- `engine.backend: numpy`
- `engine.g_int: 0.05`
- `engine.num_steps: 6`
- `initial.kind: gaussian`

This scale is deliberate. It keeps install smoke tests, cockpit exploration,
campaign comparison, and replay validation fast enough for reviewers and new
contributors.

## Non-Claims

QS-DMSS does not currently claim:

- peer-reviewed scientific validation;
- equivalence to production cosmological simulation codes;
- large-scale structure discovery performance;
- AMR, MPI, CUDA, or multi-GPU scale;
- stable internal Python APIs;
- validated physical conclusions from bundled demo/showcase scenarios.

The correct claim is more modest and stronger: QS-DMSS makes small simulation
studies reproducible, inspectable, comparable, and citable.

## Concrete Guide: Self-Interaction Campaign Study

The quickest concrete study is to sweep the self-interaction control
`engine.g_int` and inspect how the evidence metrics respond. Current builds ship
a packaged Campaign Studio study template named `Self-Interaction Sweep`, so a
fresh cockpit session can run the study without first copying or editing YAML.

From an installed package, the quickest CLI fallback is the bundled demo
campaign. It includes `engine.g_int` as one dimension in a broader stability
frontier grid:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qs-dmss
qs-dmss campaigns run-demo --output-root self-interaction-study\runs
qs-dmss experiments list --output-root self-interaction-study\runs
```

From a source checkout, the same bundled demo campaign can be run directly:

```powershell
python -m pip install -e .[dev]
qs-dmss campaigns run configs/demo.yaml --output-root self-interaction-study\runs
qs-dmss experiments list --output-root self-interaction-study\runs
```

The campaign writes run evidence under `self-interaction-study/runs/` and a
campaign-level evidence object under `self-interaction-study/experiments/`.
Inspect the generated experiment report and bundle to compare:

- energy drift;
- norm drift;
- max density;
- elapsed runtime;
- manifest verification status;
- objective-driven recommendation status and rationale.

The packaged cockpit template uses the pure one-dimensional self-interaction
sweep below. To reproduce that grid from the CLI today, copy a config and set
the campaign section to:

```yaml
campaign:
  label: Self-interaction sandbox
  strategy: grid
  max_runs: 5
  dimensions:
    - path: engine.g_int
      values: [0.0, 0.02, 0.05, 0.08, 0.12]
```

Then run the copied config:

```powershell
qs-dmss campaigns run path\to\self-interaction.yaml --output-root self-interaction-study\runs
```

This does not prove which self-interaction value is scientifically correct. It
does produce a replayable, inspectable parameter study showing how the selected
metric envelope and decision profile respond across `engine.g_int` values.

## Cockpit Path

The same study can be run through the local cockpit:

```powershell
qs-dmss cockpit --host 127.0.0.1 --port 8001 --output-root self-interaction-study\runs
```

Open `http://127.0.0.1:8001`, then use Campaign Studio to:

1. select the packaged `Self-Interaction Sweep` study template;
2. inspect its purpose, expected runtime, metrics, limitations, and non-claims;
3. load it to see the one-dimensional `engine.g_int` grid and scoring contract;
4. launch the campaign through the existing Campaign Studio pipeline;
5. inspect the guided interpretation, recommendation, comparison report,
   evidence bundle, and last-run provenance;
6. compose a campaign research-object Markdown export with the scoring contract,
   recommendation rationale, and citation block;
7. optionally edit, save, import, or export the study template JSON so another
   user can reproduce the campaign design.

That workflow is the current center of gravity for QS-DMSS: not only computing a
field update, but preserving the full path needed for another person to inspect
and rerun the study.
