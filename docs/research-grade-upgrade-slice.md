# Research-Grade Upgrade Slice

This slice defines the next contribution path after the v0.2.0 beta launch
packet. The goal is to strengthen every layer of QS-DMSS without cutting a new
package release until the work produces measurable capability.

## Strategic Objective

Move QS-DMSS from "installable beta evidence workflow" toward "research-grade
simulation workflow candidate" by adding a benchmark and validation spine that
connects scientific assumptions, engineering checks, evidence bundles, decision
profiles, reviewer onboarding, and the paper scaffold.

The target public claim after this slice should be:

```text
QS-DMSS includes reproducible benchmark scenarios and evidence-backed validation
checks for its package/evidence workflow; it is still not peer-reviewed
scientific validation.
```

## Why This Is Highest Leverage

- It gives external reviewers concrete artifacts to inspect instead of only
  prose claims.
- It turns the paper scaffold from narrative into evidence-backed methods.
- It creates contribution surfaces across science, engineering, docs, and CI.
- It supports future ASCL/JOSS readiness without prematurely submitting.
- It avoids release churn while building toward a meaningful next package
  release.

## Build Slice

Working title: benchmark and validation spine.

Primary deliverable:

- Add a small set of canonical benchmark scenarios that can run quickly,
  produce evidence bundles, and report acceptance signals.

Initial implementation status:

- Packaged benchmark scenarios and expected metric envelopes live under
  `src/qs_dmss/assets/benchmarks/`.
- `qs-dmss benchmarks list` exposes the packaged scenario names.
- `qs-dmss benchmarks validate` runs selected scenarios, verifies evidence,
  checks metric envelopes, replays runs, and writes
  `benchmark-validation/benchmark-validation.json`.
- Reviewer guidance lives in `docs/benchmark-validation.md`.
- `v0.3.0` is the first intended public release target for this benchmark
  validation spine.

Suggested structure:

```text
benchmarks/
  README.md
  scenarios/
    demo-baseline.yaml
    resolution-smoke.yaml
    parameter-sensitivity.yaml
  expected/
    demo-baseline.metrics.json
docs/
  benchmark-validation.md
```

The exact paths can change during implementation, but the slice should keep the
benchmark assets separate from regular demos so reviewers can distinguish
"quick install smoke" from "research-grade validation evidence."

## Layer Coverage

Scientific/model layer:

- Document the modeled equations, assumptions, nondimensionalization choices,
  and known non-goals.
- Define what a benchmark can and cannot validate.
- Avoid claiming physical validation beyond the implemented numerical workflow.

Numerics/engineering layer:

- Add deterministic benchmark configs with bounded runtime.
- Record expected metric ranges for norm drift, energy drift, density summary,
  and runtime envelope.
- Add tests that validate benchmark outputs against tolerant thresholds.

Evidence/reproducibility layer:

- Require each benchmark run to produce config, metrics, environment lock,
  manifest, report, and bundle.
- Add a benchmark replay check that proves the captured config can reproduce a
  compatible metric envelope.

Decision layer:

- Add a benchmark decision profile that ranks benchmark variants against
  explicit constraints.
- Ensure the recommendation can be traced to objective weights and constraints.

Cockpit/API layer:

- Document how benchmark runs appear in the cockpit and how reviewers can
  inspect bundles.
- Keep UI changes optional for this slice unless the current cockpit blocks
  benchmark review.

Packaging/CI layer:

- Run benchmark validation in a lightweight CI mode.
- Keep full benchmark suites opt-in if they become expensive.
- Preserve PyPI/GitHub release-wheel smoke as the adoption gate.

Documentation/paper layer:

- Add a benchmark validation note that can be cited by `paper/paper.md`.
- Replace paper placeholders only when evidence exists.

## Acceptance Criteria

- A fresh contributor can run the benchmark path from a clean checkout.
- CI has at least one benchmark validation check with deterministic thresholds.
- Benchmark outputs produce normal QS-DMSS evidence bundles.
- Documentation clearly separates workflow validation from scientific model
  validation.
- The JOSS scaffold references concrete benchmark evidence, while still marking
  the paper as pre-submission.
- No package release is cut until the benchmark slice is reviewed and merged.

## Suggested First Issues

- Add benchmark scenario configs with runtime targets under 60 seconds.
- Add expected metric envelopes for demo baseline benchmark outputs.
- Add a benchmark validation command or script.
- Add docs explaining model assumptions and benchmark limitations.
- Add a decision profile for benchmark variant ranking.
- Update `paper/paper.md` to reference benchmark evidence after it exists.

## Release Policy

Do not release a patch version for planning docs alone. Consider `v0.2.1` or
`v0.3.0` only after the benchmark/validation spine ships with tests, evidence,
and reviewer-facing documentation.
