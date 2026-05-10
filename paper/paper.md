---
title: "QS-DMSS: evidence-first reproducible workflows for QuantumScalar dark matter simulation"
tags:
  - Python
  - dark matter
  - scientific computing
  - reproducibility
  - simulation
authors:
  - name: "TODO: Confirm JOSS author list"
    affiliation: 1
affiliations:
  - name: "TODO: Confirm author affiliations"
    index: 1
date: 2026-05-09
bibliography: paper.bib
---

# Summary

QS-DMSS is a Python package for evidence-first QuantumScalar dark matter
simulation workflows. The current beta release combines a NumPy-based split-step
solver with deterministic run ledgers, manifest-verified evidence bundles,
replay and verification commands, template-driven decision campaigns,
objective-based ranking, and a local cockpit for inspecting and exporting runs.

This paper is a pre-submission scaffold. It should not be submitted to JOSS
until the author list, field comparison, research-use evidence, AI usage
disclosure, and public development-history expectations are satisfied.

# Statement of need

Exploratory simulation projects often produce output directories, plots, and
partial notes before they produce durable evidence trails. QS-DMSS is designed
for researchers and technical reviewers who need early simulation work to be
auditable from the start: each run preserves configuration, metrics, environment
metadata, numerical artifacts, checksums, reports, and replay commands.

The target audience is researchers, scientific-software reviewers, and research
engineering teams working on reproducible simulation workflows for dark matter
or adjacent computational physics problems. The package is intentionally
local-first and installable through PyPI so reviewers can validate the public
distribution without repository-specific setup.

# State of the field

TODO: Replace this section with a concrete comparison to commonly used
Schrodinger-Poisson, fuzzy/ultralight dark matter, and computational-physics
workflow tools. The final JOSS submission should explain why QS-DMSS is not
merely another solver, but an evidence-first workflow spine that joins solver
execution, artifact capture, replay, verification, campaign expansion, and
objective-based recommendation.

Relevant context includes ultralight scalar dark matter reviews [@hui2017] and
the scientific Python stack used by the implementation [@harris2020].

# Software design

QS-DMSS separates the workflow into explicit layers:

- configuration loading and validation;
- deterministic solver execution;
- run ledger and evidence bundle creation;
- manifest verification and replay;
- experiment export and campaign comparison;
- objective-driven ranking;
- local cockpit API and browser interface.

This design favors traceability over hidden convenience. Run outputs are
structured under stable run identifiers, bundle manifests capture file hashes,
and campaign recommendations are tied to explicit constraints and ranking rules.

# Research impact statement

TODO: Add concrete research-use evidence before submission. Acceptable evidence
may include a submitted preprint using QS-DMSS, benchmark notebooks, documented
external adoption, issue-driven review by another group, or integration into a
real research workflow.

The current public baseline provides near-term reproducibility evidence through
PyPI distribution, Zenodo DOI archival [@qsdmss030], CI across Python 3.10
through 3.13, Docker smoke validation, and installed-package demo/campaign smoke
tests across Linux, macOS, and Windows.

The post-beta development line adds a lightweight benchmark validation spine:
packaged benchmark scenarios, expected metric envelopes, evidence-bundle
verification, replay checks, and a JSON validation report. This benchmark spine
supports software-methods review of the reproducibility workflow, but it should
not be presented as peer-reviewed scientific validation of the underlying model.

# AI usage disclosure

TODO: Finalize this disclosure before submission. If generative AI tools were
used in software development, documentation, release engineering, or paper
drafting, describe how they were used and how human review, tests, and
validation controlled the quality of generated content.

# Acknowledgements

TODO: Add funding, institutional, collaborator, and reviewer acknowledgements.

# References
