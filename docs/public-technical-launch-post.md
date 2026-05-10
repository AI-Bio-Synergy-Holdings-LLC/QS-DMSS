# Public Technical Launch Post

Audience: technical readers, scientific-software reviewers, potential early
adopters, and research collaborators.

Suggested title:

```text
QS-DMSS v0.2.0: a citable beta for reproducible simulation evidence workflows
```

Post:

````markdown
Today I am sharing QS-DMSS v0.2.0 as public beta software for reproducible
package/evidence workflows around QuantumScalar dark matter simulation.

The point of this release is not to claim a new scientific result. It is not
peer-reviewed scientific validation. The point is to make the computational
spine inspectable: install the package, run a bundled demo, generate a
deterministic evidence bundle, verify the manifest, replay the captured
configuration, and compare campaign variants through an objective-based
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
- fresh-install smoke validation from PyPI and GitHub release wheels on Linux, macOS, and Windows;
- GitHub release artifacts, PyPI distribution, and Zenodo DOI archival.

The project is intentionally evidence-first. Every run is meant to leave behind
enough information for another reviewer to ask: What configuration was used?
What environment produced it? What metrics were recorded? Do the artifact hashes
still match? Can the run be replayed? Can a campaign recommendation be traced
back to explicit constraints and ranking rules?

Public entry points:

- GitHub: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS
- PyPI: https://pypi.org/project/qs-dmss/
- Latest release: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.2.0
- Zenodo DOI: https://doi.org/10.5281/zenodo.20091602

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

- public, citable, installable beta software;
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
QS-DMSS v0.2.0 is public: citable beta software for reproducible
package/evidence workflows around QuantumScalar dark matter simulation.

It focuses on the evidence spine: deterministic runs, manifest-verified bundles,
replay, campaign comparison, objective-based recommendations, CI, PyPI, and
Zenodo DOI archival.

This is not peer-reviewed scientific validation, and it is not a JOSS/ASCL claim
yet. It is the public baseline for review, adoption feedback, and
research-readiness hardening.

GitHub: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS
PyPI: https://pypi.org/project/qs-dmss/
DOI: https://doi.org/10.5281/zenodo.20091602
```
