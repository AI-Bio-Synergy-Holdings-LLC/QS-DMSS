# Research Paper Strategy

QS-DMSS can support a serious paper, but the paper should be staged carefully.
The strongest near-term paper is a research-software and engineering methods
paper, not a scientific-results paper.

## Recommendation

Write a scientific/engineering/research-grade paper in two phases:

- Phase 1: research-software and methods paper.
- Phase 2: scientific validation or applied research paper, only after
  benchmark evidence, comparison baselines, and research-use artifacts exist.

This keeps the paper ambitious without overclaiming. It also matches the public
beta posture: QS-DMSS is beta for reproducible package/evidence workflows; it
is not peer-reviewed scientific validation.

## Phase 1 Paper

Working frame:

```text
QS-DMSS: an evidence-first software architecture for reproducible dark matter
simulation workflows
```

Appropriate claims:

- Origin and motivation for an evidence-first simulation workflow.
- Package architecture and reproducibility model.
- How configs, ledgers, manifests, bundles, replay, campaigns, and decision
  profiles connect.
- What v0.2.0 proves as a public beta package.
- What the software does not yet validate scientifically.

Evidence needed:

- Fresh install smoke from PyPI and GitHub release wheels.
- Deterministic run-demo and campaign-demo evidence.
- Benchmark scenarios from `docs/research-grade-upgrade-slice.md`.
- A clear limitations section.
- Human-confirmed authorship, affiliations, acknowledgements, and AI usage
  disclosure.

Best outlets or uses:

- Repository white paper while the work matures.
- Zenodo-hosted technical report.
- arXiv preprint when benchmark evidence exists.
- JOSS submission only after public history and research-use gates are credible.

## Phase 2 Paper

Working frame:

```text
Validation and application of QS-DMSS workflows for QuantumScalar dark matter
simulation studies
```

Appropriate only after:

- Benchmarks compare against known analytical expectations or accepted
  numerical references.
- Model assumptions are fully specified.
- Physical units, nondimensionalization, and parameter interpretation are
  documented.
- At least one research workflow, preprint, or external review uses the code.

Potential claims:

- Numerical behavior under benchmark scenarios.
- Reproducibility of campaign recommendations.
- Evidence bundle utility for scientific review.
- Comparison to related computational physics workflows.

Claims to avoid until then:

- Discovery or validation of a dark matter model.
- Peer-reviewed scientific correctness.
- ASCL or JOSS acceptance.
- General physical applicability beyond tested scenarios.

## Proposed Paper Structure

1. Origin and motivation.
2. Conceptual model and scope boundaries.
3. Software architecture.
4. Reproducibility and evidence model.
5. Benchmark and validation design.
6. Current v0.2.0 state.
7. Limitations and non-goals.
8. Roadmap toward external validation.
9. AI usage, provenance, and human review.

## Immediate Writing Task

Do not expand `paper/paper.md` into submission form yet. First, build the
benchmark and validation spine. Then update the paper scaffold with evidence
that a reviewer can reproduce.

The current paper should remain a disciplined scaffold until the benchmark
slice provides data.
