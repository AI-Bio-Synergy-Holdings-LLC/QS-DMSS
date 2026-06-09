# PyPI Distribution

QS-DMSS is published on PyPI:
`https://pypi.org/project/qs-dmss/`.

Install from PyPI:

```powershell
python -m pip install qs-dmss
```

## Publication Record

Initial PyPI publication completed on `2026-05-05` through GitHub Actions
Trusted Publishing.

- Initial published version: `0.1.0`
- Current release target: `0.5.0`
- PyPI project URL: `https://pypi.org/project/qs-dmss/`
- Initial publish workflow run:
  `https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/actions/runs/25393532837`
- Initial publish commit: `3cd208ff985041cf95261f8de289e4dd5a14df49`
- Upload method: Trusted Publishing / GitHub OIDC
- Current release files:
  - `qs_dmss-0.5.0-py3-none-any.whl`
  - `qs_dmss-0.5.0.tar.gz`
- Initial published files:
  - `qs_dmss-0.1.0-py3-none-any.whl`
  - `qs_dmss-0.1.0.tar.gz`

Run post-publication smoke validation from a fresh virtual environment:

```powershell
python -m pip install --no-cache-dir qs-dmss==0.5.0
qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss benchmarks validate --scenario demo-baseline
qs-dmss showcase run --output-root simulation-showcase
```

Cross-platform adoption validation lives in
`.github/workflows/fresh-install-smoke.yml`. It validates both the PyPI install
path and the GitHub release-wheel path on Linux, macOS, and Windows.

## Built Wheel Project URL Check

PyPI renders project links from wheel metadata, so release preflight should
confirm `Project-URL` fields after building artifacts:

```powershell
python -m build --sdist --wheel
$env:WHEEL_PATH = (Get-ChildItem dist\qs_dmss-*.whl | Sort-Object Name | Select-Object -Last 1).FullName
python - <<'PY'
import email
import os
import zipfile
from pathlib import Path

wheel = Path(os.environ["WHEEL_PATH"])
required = {
    "Repository",
    "Issues",
    "Documentation",
    "PyPI",
    "DOI",
    "Review",
    "Reviewer Quickstart",
}

with zipfile.ZipFile(wheel) as archive:
    metadata_name = next(
        name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
    )
    message = email.message_from_bytes(archive.read(metadata_name))

project_urls = message.get_all("Project-URL") or []
labels = {item.split(",", 1)[0].strip() for item in project_urls}
missing = required - labels
if missing:
    raise SystemExit(f"Missing Project-URL labels: {sorted(missing)}")
print("Project-URL labels present:", ", ".join(sorted(labels)))
PY
```

The check should include at least Repository, Issues, Documentation, PyPI, DOI,
Review, and Reviewer Quickstart before publication.

## Package Identity

- PyPI project name: `qs-dmss`
- Python import package: `qs_dmss`
- Console command: `qs-dmss`
- Organization: `AI Bio Synergy Holdings LLC`
- License: `Apache-2.0`
- Supported Python range: `>=3.10`
- CI validation range for `v0.5.x`: Python 3.10 through 3.13 plus Docker smoke
- Citation metadata: `CITATION.cff`

## Citation and Archival Metadata

QS-DMSS uses `CITATION.cff` as the canonical software-citation metadata file.
GitHub uses this file for the repository citation prompt, and Zenodo can use it
when archiving GitHub releases.

The current citation metadata includes the Zenodo concept DOI so package-facing
metadata has a stable citation target:

- Zenodo concept DOI: `10.5281/zenodo.20074924`
- Latest archived release DOI before `v0.5.0` archival: `10.5281/zenodo.20500433`
- Latest archived release record before `v0.5.0` archival: `https://zenodo.org/records/20500433`
- `v0.5.0` release DOI: pending Zenodo archive after the GitHub release is created
- Previous archived release DOI for `v0.3.0`: `10.5281/zenodo.20112923`
- Previous archived release record for `v0.3.0`: `https://zenodo.org/records/20112923`
- Previous archived release DOI for `v0.2.0`: `10.5281/zenodo.20091602`
- Previous archived release record for `v0.2.0`: `https://zenodo.org/records/20091602`
- Earlier archived release DOI: `10.5281/zenodo.20076871`
- First archived release DOI: `10.5281/zenodo.20074925`
- First archived release record: `https://zenodo.org/records/20074925`
- Software Heritage archival status: pending; no SWHID is recorded yet

Use the concept DOI for project-level citation. Use the version DOI when citing
exact archived release artifacts.

## Approval Gate Status

The initial `0.1.0` publication gate is complete:

- Package-name owner is identified.
- PyPI project is claimed by the first successful `qs-dmss` publication.
- Trusted Publishing is configured and was used for upload.
- Support expectations are recorded through GitHub Issues and `SECURITY.md`.
- Published artifacts match the approved `v0.1.0` GitHub release artifacts.

## Approval Record

Approved on `2026-04-30` by repository owner instruction for the next external
distribution preparation phase:

- Package-name owner: `AI Bio Synergy Holdings LLC`.
- Support owner: `AI Bio Synergy Holdings LLC`.
- Non-sensitive support intake: GitHub Issues on
  `AI-Bio-Synergy-Holdings-LLC/QS-DMSS`.
- Sensitive report intake: `SECURITY.md`.
- Supported release line: `v0.5.x`, beginning with `v0.5.0`.
- Supported Python range: package metadata `>=3.10`, with CI validation on
  Python 3.10 through 3.13.
- Artifact policy: any later PyPI upload of `0.1.0` must use the exact GitHub
  release artifacts listed below. If metadata or artifact contents change, cut a
  new version instead of reusing `0.1.0`.

Future uploads must continue to use Trusted Publishing unless the release owner
explicitly approves a replacement publication method. Do not use long-lived PyPI
API tokens for routine releases.

## Trusted Publishing Configuration

Use PyPI Trusted Publishing instead of a long-lived API token.

Repository-side configuration:

- GitHub environment: `pypi`
- Environment required reviewer: `SIONSOULSION`
- Environment deployment branch policy: `main`
- Publishing workflow: `.github/workflows/publish-pypi.yml`
- Trigger: manual `workflow_dispatch`
- Required confirmation input: `publish-to-pypi`
- Distribution source: files already attached to the GitHub release for the
  requested tag

GitHub-side setup completed on `2026-05-01`: the `pypi` environment exists,
requires `SIONSOULSION` approval, and is restricted to deployments from `main`.

PyPI Trusted Publisher values:

- PyPI project name: `qs-dmss`
- Publisher: GitHub Actions
- Owner: `AI-Bio-Synergy-Holdings-LLC`
- Repository name: `QS-DMSS`
- Workflow name: `publish-pypi.yml`
- Environment name: `pypi`

For future releases, run the GitHub workflow manually from
Actions -> Publish to PyPI with:

- `tag`: the final release tag, such as `v0.5.0`
- `confirm`: `publish-to-pypi`

The workflow downloads the GitHub release assets for the requested tag,
validates package metadata, checks the distributions with Twine, then publishes
through the `pypi` environment using PyPI's short-lived OIDC token exchange.

## Artifact Policy

Each GitHub release is the canonical artifact source for the same PyPI version.
The PyPI `0.1.0` upload used these GitHub release files and digests:

- `qs_dmss-0.1.0-py3-none-any.whl`
  `sha256:c3acdcfac27a9108013f9f0774c9bd48775070edf11fb447b992e8288aa30870`
- `qs_dmss-0.1.0.tar.gz`
  `sha256:36eb80c9994405206df4a80e246bd9fc61d64d5085e8981db13bec8a118fbce9`

If metadata changes are needed, do not reuse an already-published version. Cut a
new patch or prerelease version so GitHub and PyPI artifacts remain traceable.

## Preflight Commands

Run these commands from a clean checkout at a future release tag before any
approved upload:

```powershell
git checkout v0.5.0
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip build twine
python -m build --sdist --wheel
python -m twine check dist/*
python -m pip install .\dist\qs_dmss-0.5.0-py3-none-any.whl
qs-dmss run-demo
qs-dmss campaigns run-demo
qs-dmss benchmarks validate --scenario demo-baseline
qs-dmss showcase run --output-root simulation-showcase
```

Only publish after the release artifacts are attached to GitHub and the
environment reviewer approves the `pypi` deployment.
