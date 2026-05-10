# Decision Profile Example

The checked-in demo config includes four decision-related sections:
`objective`, `constraints`, `ranking`, and `campaign`. Together they describe
what the workflow is optimizing, what must remain acceptable, how ties are
scored, and which parameter grid should be expanded for campaign runs.

The example below is valid YAML and maps directly to the demo configuration.

```yaml
objective:
  name: Stability-first recommendation
  summary: Prefer low drift with verified evidence while keeping density high enough for a credible final state.
  primary_metric: energy_drift
  goal: minimize_abs

constraints:
  max_abs_energy_drift: 0.2
  max_abs_norm_drift: 0.2
  min_max_density: 0.5
  max_elapsed_seconds: 5.0
  require_verification: true

ranking:
  primary_metric_weight: 2.4
  weights:
    energy_drift: 1.0
    norm_drift: 0.9
    max_density: 0.7
    elapsed_seconds: 0.3

campaign:
  label: Stability frontier campaign
  strategy: grid
  max_runs: 6
  dimensions:
    - path: engine.g_int
      values: [0.02, 0.05, 0.08]
    - path: engine.time_step
      values: [0.015, 0.02]
```

## Field Map

- `objective.name`: Human-readable name shown in reports and decision payloads.
- `objective.summary`: Short reviewer-facing statement of the decision intent.
- `objective.primary_metric`: Main metric used for scoring. Supported values
  include `energy_drift`, `norm_drift`, `max_density`, and `elapsed_seconds`.
- `objective.goal`: Optimization goal, such as `minimize_abs`, `minimize`,
  `maximize`, or `target`.
- `constraints.max_abs_energy_drift`: Maximum allowed absolute energy drift.
- `constraints.max_abs_norm_drift`: Maximum allowed absolute norm drift.
- `constraints.min_max_density`: Minimum acceptable final max density.
- `constraints.max_elapsed_seconds`: Maximum acceptable runtime for the run.
- `constraints.require_verification`: Requires manifest verification before a
  run can qualify.
- `ranking.primary_metric_weight`: Extra weight applied to the objective's
  primary metric.
- `ranking.weights`: Per-metric weights used when comparing qualified runs.
- `campaign.label`: Human-readable campaign name.
- `campaign.strategy`: Expansion strategy. The reference build supports
  `grid`.
- `campaign.max_runs`: Safety cap for expanded campaign variants.
- `campaign.dimensions`: Parameter paths and candidate values to sweep.

## Try It

Run the campaign from the checked-in demo config:

```powershell
qs-dmss campaigns run configs/demo.yaml
```

Or run the installed-package demo campaign:

```powershell
qs-dmss campaigns run-demo
```

The command expands the grid, runs each variant, scores the resulting evidence,
and writes a campaign-level experiment bundle under `experiments/`.
