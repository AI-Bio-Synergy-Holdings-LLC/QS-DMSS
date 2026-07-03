# Public Technical Update Post

Audience: technical readers, scientific-software reviewers, potential early
adopters, research collaborators, RSE/HPC reviewers, and open-source funders.

Suggested title:

```text
QS-DMSS v0.9.0: evidence-first simulation workflows with dry-run HPC review artifacts
```

Post:

````markdown
QS-DMSS v0.9.0 is public as beta software for reproducible package/evidence
workflows around QuantumScalar dark matter simulation.

The point of this release is not to claim a new scientific result. It is not
peer-reviewed scientific validation. The point is to make the computational
spine inspectable: install the package, run a bundled demo, generate a
deterministic evidence bundle, verify the manifest, replay the captured
configuration, compare campaign variants, export research objects, and produce
reviewable dry-run Slurm request bundles without submitting scheduler jobs.

QS-DMSS currently includes:

- a NumPy-based split-step Schrodinger-Poisson reference solver;
- a packaged CLI available with `pip install qs-dmss`;
- Lab Mode for guided simulation inspection;
- Campaign Studio study templates, editable grids, and decision profiles;
- manifest-verified run evidence bundles;
- deterministic replay and verification commands;
- canonical simulation showcase reports with CSV and SVG artifacts;
- publication-style research-object export composition;
- workspace export/import metadata with collaborator and annotation fields;
- dry-run Slurm request bundles for HPC/RSE site-policy review;
- GitHub Actions CI across Python 3.10 through 3.13 plus Docker smoke validation;
- fresh-install smoke validation from PyPI and GitHub release wheels on Linux,
  macOS, and Windows;
- GitHub release artifacts, PyPI distribution, and Zenodo DOI archival.

The project is intentionally evidence-first. Every run is meant to leave behind
enough information for another reviewer to ask: What configuration was used?
What environment produced it? What metrics were recorded? Do the artifact hashes
still match? Can the run be replayed? Can a campaign recommendation be traced
back to explicit constraints and ranking rules?

Public entry points:

- Website: https://qs-dmss.studio
- GitHub: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS
- PyPI: https://pypi.org/project/qs-dmss/
- Latest release: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.9.0
- Zenodo concept DOI: https://doi.org/10.5281/zenodo.20074924
- v0.9.0 release DOI: https://doi.org/10.5281/zenodo.20693736
- Open Collective: https://opencollective.com/qs-dmss

Fast smoke test:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qs-dmss==0.10.0
qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss benchmarks validate --scenario demo-baseline
qs-dmss showcase run --output-root simulation-showcase
```

Dry-run Slurm review artifact:

```powershell
qs-dmss executors slurm-dry-run configs/demo.yaml --output-root slurm-review
```

Current source-review gate:

The current `main` branch is one validation slice ahead of the public package.
It adds an experimental Fractal/Quadrant SSFM validation harness for technical
review before any GPU expansion, v0.10.0 release prep, or decision-metric UI
for spectral diagnostics.

Review issue:
https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105

What this release is:

- public, citable, installable beta software;
- a reproducibility and productization spine;
- a concrete package for reviewer feedback;
- a foundation for future validation and research-use work.

What this release is not:

- not a peer-reviewed scientific result;
- not a production cosmological simulation code;
- not a real HPC scheduler submission connector;
- not a claim that the model has been externally validated.

If you care about reproducible scientific software, simulation evidence bundles,
auditable dark matter modeling workflows, or cautious HPC connector design, I
would value one small public comment on the review issue that matches your
expertise.
````

Short social version:

```text
QS-DMSS v0.9.0 is public: citable beta software for reproducible simulation
evidence workflows.

It now includes Lab Mode, Campaign Studio study templates, evidence bundles,
replay/verify, publication-style exports, workspace metadata, and dry-run Slurm
request bundles that never submit scheduler jobs.

This is not peer-reviewed scientific validation. Current source review is
focused on the experimental Fractal/Quadrant SSFM validation harness before any
GPU expansion or v0.10.0 release prep.

Website: https://qs-dmss.studio
GitHub: https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS
PyPI: https://pypi.org/project/qs-dmss/
DOI: https://doi.org/10.5281/zenodo.20693736
Open Collective: https://opencollective.com/qs-dmss
```
