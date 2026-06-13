# QS-DMSS v0.8.0 Release Notes

QS-DMSS v0.8.0 is the Campaign Studio Template Library milestone. It turns
saved campaign designs from dropdown-only JSON records into visible reusable
research assets with metadata, import/export guidance, and last-run provenance.

## Highlights

- Adds visible Campaign Studio study-template cards in the cockpit.
- Shows objective, primary metric/goal, planned runs, created time, source
  config, import/export state, and portability metadata for saved templates.
- Records last-run provenance after executing a saved template, including the
  recommended run, experiment report link, and evidence bundle link.
- Keeps study-template JSON portable so another user can import and rerun the
  same campaign design.
- Adds regression coverage for saved-template execution provenance.
- Resolves the public CodeQL stack-trace exposure alert path; the public repo
  has zero open code-scanning alerts at release prep.

## Claim Boundary

QS-DMSS remains beta for reproducible package/evidence workflows. This release
does not claim peer-reviewed scientific validation or validated physical
conclusions from the bundled demo/showcase scenarios.

## Validation Gate

Before tagging `v0.8.0`, validate:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build --sdist --wheel
.\.venv\Scripts\python.exe -m twine check dist/*
```

After GitHub release publication, run the fresh-install smoke workflow against:

- package version: `0.8.0`
- release tag: `v0.8.0`

## Citation Status

- Project DOI: `10.5281/zenodo.20074924`
- Latest currently archived release DOI: `10.5281/zenodo.20671389` (`v0.7.0`)
- `v0.8.0` release DOI: pending Zenodo archival after the GitHub release

After Zenodo archives `v0.8.0`, update the GitHub release notes, `CITATION.cff`,
README citation text, `codemeta.json`, and citation docs with the new version
DOI.
