# PyPI Distribution Readiness

QS-DMSS `v0.1.0` is currently distributed through the GitHub release artifacts.
PyPI publication is intentionally gated until package-name ownership, account
ownership, and support expectations are explicitly approved.

## Current Name Check

Checked on `2026-04-30`: the PyPI JSON endpoint for `qs-dmss`
(`https://pypi.org/pypi/qs-dmss/json`) returned `404`, so no public PyPI
project was observed at that endpoint.

This is not ownership approval. PyPI project names are only controlled after an
authorized owner publishes or otherwise secures the project, and the name can
become unavailable before QS-DMSS publishes there.

## Package Identity

- PyPI project name: `qs-dmss`
- Python import package: `qs_dmss`
- Console command: `qs-dmss`
- Organization: `AI Bio Synergy Holdings LLC`
- License: `Apache-2.0`
- Supported Python range: `>=3.10`
- CI validation range for `v0.1.0`: Python 3.10 through 3.13 plus Docker smoke

## Approval Gate

Do not publish to PyPI until each item is resolved and recorded in the release
issue or PR:

- Approving owner for the `qs-dmss` PyPI name is identified.
- PyPI account or organization ownership is confirmed with mandatory 2FA.
- A publication method is selected, preferably PyPI Trusted Publishing from
  GitHub Actions rather than a long-lived API token.
- The repository, workflow, and environment names required by Trusted
  Publishing are approved before the first upload.
- Support expectations are approved: issue intake, security contact, supported
  Python versions, and expected response owner.
- The artifact policy is approved: either publish the exact `v0.1.0` artifacts
  from the GitHub release, or bump to a new version before any package metadata
  or artifact contents change.

## Approval Record

Approved on `2026-04-30` by repository owner instruction for the next external
distribution preparation phase:

- Package-name owner: `AI Bio Synergy Holdings LLC`.
- Support owner: `AI Bio Synergy Holdings LLC`.
- Non-sensitive support intake: GitHub Issues on
  `AI-Bio-Synergy-Holdings-LLC/QS-DMSS`.
- Sensitive report intake: `SECURITY.md`.
- Supported release line: `v0.1.x`, beginning with `v0.1.0`.
- Supported Python range: package metadata `>=3.10`, with CI validation on
  Python 3.10 through 3.13.
- Artifact policy: any later PyPI upload of `0.1.0` must use the exact GitHub
  release artifacts listed below. If metadata or artifact contents change, cut a
  new version instead of reusing `0.1.0`.

This approval does not by itself authorize an upload. PyPI account or
organization ownership, mandatory 2FA, and the Trusted Publishing configuration
still need to be completed before publication.

## `v0.1.0` Artifact Policy

The GitHub `v0.1.0` release is the canonical artifact source for this version.
If `0.1.0` is published to PyPI later, use the same files and verify their
digests before upload:

- `qs_dmss-0.1.0-py3-none-any.whl`
  `sha256:c3acdcfac27a9108013f9f0774c9bd48775070edf11fb447b992e8288aa30870`
- `qs_dmss-0.1.0.tar.gz`
  `sha256:36eb80c9994405206df4a80e246bd9fc61d64d5085e8981db13bec8a118fbce9`

If metadata changes are needed before public package-index distribution, do not
reuse version `0.1.0`. Cut a new patch or prerelease version so GitHub and PyPI
artifacts remain traceable.

## Preflight Commands

Run these commands from a clean checkout at the release tag before any approved
upload:

```powershell
git checkout v0.1.0
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip build twine
python -m build --sdist --wheel
python -m twine check dist/*
python -m pip install .\dist\qs_dmss-0.1.0-py3-none-any.whl
qs-dmss run-demo
qs-dmss campaigns run-demo
```

Only publish after the approval gate is complete.
