# QS-DMSS v0.9.0 Release Notes

QS-DMSS v0.9.0 is the HPC dry-run review milestone. It makes the Slurm
request-bundle prototype installable from PyPI so HPC administrators, research
software engineers, and research computing reviewers can inspect scheduler
artifacts without cloning the repository.

## Highlights

- Adds `qs-dmss executors slurm-dry-run <config>` as the public review path for
  scheduler request bundles.
- Emits a local `draft` job record plus `request-bundle/request-bundle.json`,
  `request-bundle/slurm-job.sh`, copied config, review README, and checksums.
- Records explicit non-submission metadata:
  `submission_policy.submitted=false` and
  `submission_policy.never_submit=true`.
- Documents the Slurm site-policy feedback packet and issue path for concrete
  reviewer comments before any real connector implementation.
- Keeps the executor boundary local-first: no `sbatch`, no `squeue`, no
  `sacct`, no SSH, and no remote scheduler command is invoked by this release.

## Reviewer Ask

After installing `qs-dmss==0.9.0`, generate a dry-run request bundle:

```powershell
qs-dmss executors slurm-dry-run configs/demo.yaml --request-root dry-run-jobs --job-name qs-demo
```

Then leave one concrete comment on
[issue #99](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/99)
about required Slurm directives, environment setup, filesystem staging,
artifact return, scheduler state mapping, or site-policy blockers.

## Claim Boundary

QS-DMSS remains beta for reproducible package/evidence workflows. This release
does not claim peer-reviewed scientific validation, validated physical
conclusions from bundled scenarios, or production HPC submission support.

The Slurm path is intentionally dry-run only. Real `sbatch` / `squeue` /
`sacct` support should wait until the request-bundle shape has been reviewed
against at least one real site policy.

## Validation Gate

Before tagging `v0.9.0`, validate:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall src
node --check src/qs_dmss/cockpit/static/app.js
.\.venv\Scripts\python.exe -m build --sdist --wheel
.\.venv\Scripts\python.exe -m twine check dist/*
```

After publication, run a fresh install smoke against PyPI `qs-dmss==0.9.0`
and the GitHub release wheel from `v0.9.0`.

## Citation Status

- Project DOI: `10.5281/zenodo.20074924`
- Latest archived release DOI at release prep: `10.5281/zenodo.20673804`
  (`v0.8.0`)
- `v0.9.0` release DOI: pending Zenodo archive after the GitHub release

After Zenodo archives `v0.9.0`, update CITATION.cff, README citation text,
Codemeta, and citation docs in a tiny DOI metadata PR.
