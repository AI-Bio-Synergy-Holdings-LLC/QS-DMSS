# JOSS Preflight

This preflight maps the current QS-DMSS public baseline to the Journal of Open
Source Software expectations. It is intentionally conservative: the project can
prepare for JOSS now, but should not submit until the open gaps below are
credible.

Last reviewed: 2026-06-01

Primary sources:

- `https://joss.readthedocs.io/en/latest/submitting.html`
- `https://joss.readthedocs.io/en/latest/review_criteria.html`
- `https://joss.readthedocs.io/en/latest/paper.html`

## Current Decision

Do not submit to JOSS yet.

Prepare the packet, collect reviewer feedback, and use `v0.9.0` as the stable
public baseline for Lab Mode, Campaign Studio, Publication Export Composer, and reproducibility
review.

## Fit Summary

QS-DMSS is plausibly in scope as research software because it is an installable
open source Python package with tests, documentation, public issue tracking,
release archives, a DOI, and a reproducible workflow around simulation
evidence.

The current blocker is not packaging. The blocker is scholarly evidence:
QS-DMSS still needs a stronger state-of-the-field comparison and concrete
research-use or benchmark evidence that demonstrates why the evidence-first
workflow is a meaningful contribution to the research community.

## Preflight Matrix

| JOSS expectation | Current QS-DMSS evidence | Status | Next action |
| --- | --- | --- | --- |
| Public repository and issue workflow | Public GitHub repository, issue templates, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT | Ready | Keep development visible through ordinary issues and PRs |
| OSI-approved license | Apache-2.0 `LICENSE` file | Ready | No action |
| Installable package | PyPI `qs-dmss==0.10.0`, release wheel, Trusted Publishing, fresh-install smoke | Ready | `v0.10.0` ships the Fractal/Quadrant SSFM validation spine and public reference-data provenance sandbox; latest archived release DOI remains `10.5281/zenodo.20693736` until Zenodo archives `v0.10.0` |
| Tests and CI | Pytest suite, benchmark smoke, wheel smoke, Docker smoke, CodeQL | Ready | Add tests only when behavior changes |
| Documentation | README, reviewer quickstart, evidence glossary, benchmark docs, contributor map | Ready enough | Use reviewer feedback to patch confusing sections |
| Example usage | `run-demo`, `campaigns run-demo`, `benchmarks validate` | Ready enough | Add a short tutorial only if reviewers need more context |
| Community pathways | CONTRIBUTING, SECURITY, issue templates, review packet, Open Collective stewardship path | Ready | Keep labels/issues organized for external feedback |
| Software paper | `paper/paper.md` scaffold with required sections | Partial | Replace TODOs with owner-confirmed authorship, comparison, impact, and AI disclosure |
| State of the field | Initial citations and comparison targets identified | Not ready | Compare directly against PyUltraLight, SCALAR, AxioNyx, and adjacent workflow tools |
| Research impact | Reproducible release evidence and benchmark spine | Not ready | Collect external review, adoption, benchmark comparison, preprint, or real workflow evidence |
| AI usage disclosure | Draft placeholder exists | Not ready | Owner must confirm exact tools, scope, and human-review controls |
| Authorship and affiliations | Placeholder metadata | Not ready | Owner must confirm final paper authors, affiliations, acknowledgements, and conflicts |

## Paper Worklist

Before submission, update `paper/paper.md` with:

- Final author list and affiliations.
- A concise non-specialist summary that avoids overclaiming scientific results.
- A sharper statement of need that names the reviewer pain QS-DMSS solves.
- A state-of-field section comparing QS-DMSS to commonly used solver and
  workflow tools.
- A build-vs-contribute justification explaining why an evidence-first package
  spine is useful rather than only adding features to an existing solver.
- A research impact statement backed by concrete evidence rather than future
  intent.
- A complete AI usage disclosure that lists tools, scope, and human validation.
- Acknowledgements, funding, conflicts, and support statements.
- References for related software, scientific context, the Zenodo concept DOI,
  and the `v0.6.0` release DOI.
- Funding and stewardship statement if support materially contributed to the
  submitted work.

## Comparison Targets

The state-of-field section should compare against at least these categories:

- Ultralight/fuzzy dark matter solvers such as PyUltraLight.
- Adaptive mesh or cosmological simulation codes used for scalar/fuzzy dark
  matter studies, such as SCALAR and AxioNyx.
- General scientific workflow and reproducibility tooling, where the comparison
  is about evidence capture, replay, and reviewability rather than numerical
  method novelty.

The comparison should be precise about scope. QS-DMSS is not yet competing on
large-scale cosmological performance. Its current contribution is the
reproducible package/evidence workflow around deterministic simulation runs,
campaigns, objective ranking, evidence bundles, replay, and benchmark
validation.

## Reviewer Packet Links

- Review entrypoint: [reviewer-packet.md](reviewer-packet.md)
- Wheel quickstart: [reviewer-wheel-quickstart.md](reviewer-wheel-quickstart.md)
- Benchmark validation: [benchmark-validation.md](benchmark-validation.md)
- Demo and benchmark expectations:
  [demo-benchmark-expectations.md](demo-benchmark-expectations.md)
- Evidence glossary: [evidence-bundle-glossary.md](evidence-bundle-glossary.md)
- Research paper strategy: [research-paper-strategy.md](research-paper-strategy.md)
- ASCL and JOSS readiness: [ascl-joss-readiness.md](ascl-joss-readiness.md)

## Submission Guardrail

Submit to JOSS only when this statement is true:

```text
QS-DMSS has a public, reproducible release; a complete JOSS paper; clear
field comparisons; complete AI/authorship disclosures; and concrete evidence of
research impact or credible near-term scholarly significance beyond internal
aspiration.
```

Until then, use the repository, PyPI package, Zenodo DOI, and review packet to
collect public feedback.
