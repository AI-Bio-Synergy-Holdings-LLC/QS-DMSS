# QS-DMSS Release Policy

This policy keeps release builds, Python package metadata, and GitHub release
artifacts aligned before tags are published.

Current release target: `v0.1.0` / `0.1.0`. Published release-candidate tags
such as `v0.1.0-rc.1` and `v0.1.0-rc.2` remain immutable; do not move or
replace them.

## Version Alignment

- GitHub release-candidate tags use SemVer-style names such as `v0.1.0-rc.1`.
- Python package metadata uses the equivalent PEP 440 form, such as
  `0.1.0rc1`.
- Final releases use matching final versions: Git tag `v0.1.0` and package
  version `0.1.0`.
- `pyproject.toml`, `qs_dmss.__version__`, and installed package metadata must
  agree before a release tag is cut.
- CI enforces version alignment through `tests/test_packaging.py`.

## Distribution Artifacts

- Release candidates are GitHub prereleases intended for reviewer validation.
- Build artifacts are generated from a clean tag using `python -m build --sdist
  --wheel`.
- Every wheel and source distribution must pass `python -m twine check dist/*`
  before publication.
- Source distributions must include `RELEASE.md`, checked-in demo configs, and
  checked-in JSON schemas.
- Wheels must include the bundled demo config and schema package assets used by
  `qs-dmss run-demo`.
- Runtime evidence bundles under `runs/` and `experiments/` are reproducibility
  outputs, not package distribution artifacts.
- Docker images are validation artifacts for this phase; publish a registry image
  only after a registry namespace, tagging policy, and retention policy are chosen.
- Do not publish to PyPI until package-name ownership, final metadata, and
  support expectations are explicitly approved. Track that approval in
  [docs/pypi-distribution-readiness.md](docs/pypi-distribution-readiness.md).
- If `v0.1.0` is published to an external package index after the GitHub
  release, publish the exact GitHub release artifacts. If any metadata or
  artifact content changes are needed, cut a new version instead of reusing
  `0.1.0`.

## Reviewer Onboarding

- GitHub release wheels are the preferred reviewer path for this phase because
  they validate the installed-package experience without requiring a source
  checkout.
- The reviewer quickstart lives in
  [docs/reviewer-wheel-quickstart.md](docs/reviewer-wheel-quickstart.md).

## Final `v0.1.0` Promotion Checklist

1. Resolve reviewer feedback against the latest release-candidate branch.
2. Bump package metadata from the current prerelease version to `0.1.0`.
   Completed for this branch.
3. Run the full local validation suite:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q
   .\.venv\Scripts\python.exe -m build --sdist --wheel
   .\.venv\Scripts\python.exe -m twine check dist/*
   ```

4. Merge through a green PR and wait for `main` CI to pass.
5. Tag the merge commit as `v0.1.0`.
6. Create a GitHub release from that tag and attach only approved distribution
   artifacts.
