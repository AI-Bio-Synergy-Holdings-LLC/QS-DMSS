# Public Technical Launch Post

Audience: technical readers, scientific-software reviewers, potential early
adopters, and research collaborators.

Suggested title:

```text
QS-DMSS v0.1.4: a citable, evidence-first alpha for reproducible dark matter simulation workflows
```

Post:

````markdown
Today I am releasing QS-DMSS v0.1.4 as a public alpha reference package for
reproducible QuantumScalar dark matter simulation workflows.

The point of this release is not to claim a new scientific result. The point is
to make the computational spine inspectable: install the package, run a bundled
demo, generate a deterministic evidence bundle, verify the manifest, replay the
captured configuration, and compare campaign variants through an objective-based
decision layer.

QS-DMSS currently includes:

- a NumPy-based split-step Schrodinger-Poisson solver;
- a packaged CLI available with `pip install qs-dmss`;
- manifest-verified run evidence bundles;
- deterministic replay and verification commands;
- template-driven decision campaigns across parameter grids;
- objective-based run ranking;
- a local cockpit for launching, inspecting, verifying, comparing, and exporting runs;
- GitHub Actions CI across Python 3.10 through 3.13 plus Docker smoke validation;
- GitHub release artifacts, PyPI distribution, and Zenodo DOI archival.

The project is intentionally evidence-first. Every run is meant to leave behind
enough information for another reviewer to ask: What configuration was used?
What environment produced it? What metrics were recorded? Do the artifact hashes
still match? Can the run be replayed? Can a campaign recommendation be traced
back to explicit constraints and ranking rules?

Public entry points:

- GitHub: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS
- PyPI: https://pypi.org/project/qs-dmss/
- Latest release: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.1.4
- Zenodo DOI: https://doi.org/10.5281/zenodo.20075891

Fast smoke test:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qs-dmss
qs-dmss run-demo
qs-dmss campaigns run-demo
```

What this release is:

- a public, citable, installable alpha;
- a reproducibility and productization spine;
- a concrete package for reviewer feedback;
- a foundation for future benchmark and research-use work.

What this release is not:

- not a peer-reviewed scientific result;
- not yet an ASCL-indexed code;
- not yet a JOSS submission;
- not a claim that the model has been externally validated.

The next scholarly-readiness steps are intentionally conservative: collect
reviewer feedback, document research-use evidence, prepare ASCL metadata once a
research paper or submitted preprint uses the code, and mature the JOSS paper
only after public development history and impact evidence are strong enough.

If you care about reproducible scientific software, simulation evidence bundles,
or auditable dark matter modeling workflows, I would value your review.
````

Short social version:

```text
QS-DMSS v0.1.4 is public: a citable, installable alpha for reproducible
QuantumScalar dark matter simulation workflows.

It focuses on the evidence spine: deterministic runs, manifest-verified bundles,
replay, campaign comparison, objective-based recommendations, CI, PyPI, and
Zenodo DOI archival.

This is not a peer-reviewed result or JOSS/ASCL claim yet. It is the public
baseline for review, adoption feedback, and research-readiness hardening.

GitHub: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS
PyPI: https://pypi.org/project/qs-dmss/
DOI: https://doi.org/10.5281/zenodo.20075891
```
