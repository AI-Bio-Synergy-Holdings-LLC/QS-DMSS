# QS-DMSS Release Policy

This policy keeps release-candidate builds, Python package metadata, and GitHub
release artifacts aligned before the final `v0.1.0` release.

Current hardening target: `v0.1.0-rc.2` / `0.1.0rc2`. The published
`v0.1.0-rc.1` tag remains immutable; do not move or replace it.

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
  support expectations are explicitly approved.

## Final `v0.1.0` Promotion Checklist

1. Resolve reviewer feedback against the latest release-candidate branch.
2. Bump package metadata from the current prerelease version to `0.1.0`.
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
