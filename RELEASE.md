# QS-DMSS Release Policy

This policy keeps release builds, Python package metadata, GitHub release
artifacts, and PyPI distributions aligned before and after tags are published.

Current release target: `v0.1.3` / `0.1.3`. Published release-candidate tags
such as `v0.1.0-rc.1` and `v0.1.0-rc.2` remain immutable; do not move or
replace them.

## Version Alignment

- GitHub release-candidate tags use SemVer-style names such as `v0.1.0-rc.1`.
- Python package metadata uses the equivalent PEP 440 form, such as
  `0.1.0rc1`.
- Final releases use matching final versions: Git tags such as `v0.1.3` and
  package versions such as `0.1.3`.
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
- PyPI publication uses Trusted Publishing through
  [.github/workflows/publish-pypi.yml](.github/workflows/publish-pypi.yml).
- The initial PyPI `0.1.0` publication is complete. Track publication details in
  [docs/pypi-distribution-readiness.md](docs/pypi-distribution-readiness.md).
- PyPI uploads must use the exact GitHub release artifacts for the same tag. If
  any metadata or artifact content changes are needed, cut a new version instead
  of reusing an already-published version.

## Reviewer Onboarding

- PyPI is the preferred reviewer path for the public installed-package
  experience.
- GitHub release wheels remain the direct artifact validation path.
- The reviewer quickstart lives in
  [docs/reviewer-wheel-quickstart.md](docs/reviewer-wheel-quickstart.md).

## Patch Release Promotion Checklist

1. Resolve reviewer feedback against the latest release branch.
2. Bump package metadata, `qs_dmss.__version__`, and release docs to the target
   patch version.
3. Run the full local validation suite:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q
   .\.venv\Scripts\python.exe -m build --sdist --wheel
   .\.venv\Scripts\python.exe -m twine check dist/*
   ```

4. Merge through a green PR and wait for `main` CI to pass.
5. Tag the merge commit.
6. Create a GitHub release from that tag and attach only approved distribution
   artifacts.
7. Publish the same release artifacts to PyPI through Trusted Publishing.
