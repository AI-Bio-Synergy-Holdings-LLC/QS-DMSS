# QS-DMSS v0.13.1 Release

## Purpose

v0.13.1 is a metadata-only patch release. It does not change simulation,
quantum-validation, evidence, or cockpit behavior. It fixes the distributed
package metadata model after v0.13.0's PyPI description preserved pre-archive
release-candidate text and an earlier version DOI.

## What Changes

- The PyPI distribution now uses `README-pypi.md`, a release-stable package
  description that does not contain mutable publication status.
- Project URLs use the stable project concept DOI and GitHub Releases rather
  than a time-sensitive "latest archived release" DOI.
- `CITATION.cff` and `codemeta.json` use the stable concept DOI while retaining
  the installed package version.
- The public Studio "Run the cockpit" path installs the current package from
  PyPI with `python -m pip install --upgrade qs-dmss`.

## Claim Boundary

QS-DMSS remains beta workflow software for reproducible package and evidence
workflows. This patch does not expand scientific claims or enable provider
credentials, remote APIs, QPU execution, job submission, or authorized spend.

## Release Verification

Before publication, the release workflow must validate the tagged wheel and
source distribution, run `twine check`, and publish only through the guarded
GitHub OIDC / PyPI Trusted Publishing job.

## Citation

Use the stable project concept DOI for project-level citation:

```text
10.5281/zenodo.20074924
```

After Zenodo archives this exact version, cite its version-specific record for
release-level reproducibility.
