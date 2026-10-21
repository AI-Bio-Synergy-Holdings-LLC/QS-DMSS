# CERN dimuon environment locks — preparation only

These source-only records freeze **CPython 3.12.15 x86-64** on Windows and
Linux, with **NumPy 2.5.4 on both**. They do not authorize or execute the
numerical pilot. The existing protocol, tolerances, 26 MiB allocation and
scientific statuses are unchanged. The initial
[HOLD review](../../../../docs/reviews/cern-dimuon-helper-review-2026-10-20.md)
is preserved; the two retention findings were subsequently
[corrected and re-reviewed](../../../../docs/reviews/cern-dimuon-retention-correction-2026-10-20.md).
Owner review is complete for PR preparation only, not pilot execution.

## Contents and identity

- `manifest.json`: exact Python distribution/image identities, one native
  wheel filename/hash per dependency, and target-lock hashes.
- `windows-cp312.lock.txt`: 24 packages, including the approved QS-DMSS wheel,
  pytest and pinned pip 26.2.2.
- `linux-cp312.lock.txt`: the same common versions; only Windows-specific
  pytest dependency `colorama` is absent (23 packages).
- `verification.json`: observed offline native-install and synthetic-test
  results, initial helper identities and historical unresolved review findings.
- `retention-rereview-20261020.json`: later corrected helper identities and
  verification; it does not rewrite the earlier HOLD record.

The sole QS-DMSS artifact is the owner-approved, unpublished commit-built
wheel, SHA-256
`6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60`.
Do not substitute the published package merely because it shares version
0.14.0. The hash is mandatory. The approved wheel and original wheel are not
modified, rebuilt or published by this lock preparation.

Windows uses the hash-pinned Astral python-build-standalone 20261013 artifact;
Linux uses the digest-pinned official Python Debian Bookworm image. Both
reported CPython 3.12.15. The Linux digest is
`python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258`.
The verified Windows runtime-archive hash is
`7a2aef48e5ee569e310b29b32681debbc5d888e92790d85331a47736c6b06aad`.
These are platform-specific builds, not identical interpreter binaries or
identical BLAS builds. Retain each runtime's NumPy build configuration before
any separately authorized measurement. Identical version numbers do not
establish numerical agreement or scientific validity.

## Offline installation only

First verify the runtime identity, `manifest.json`, target lock digest, every
wheel digest and the approved candidate hash. Populate the third-party
wheelhouse from the exact filenames/URLs/hashes in the manifest; do not add
unreviewed packages or select other artifacts from the same release.

Create a new environment with the exact platform's CPython 3.12.15. Do not
upgrade an existing application environment. An installation-only recipe with
the separately hash-verified uv 0.13.4 tool is:

```text
PYTHON_3_12_15 -m venv --without-pip NEW_ENVIRONMENT
uv pip install --python NEW_ENVIRONMENT_PYTHON --no-index --find-links THIRD_PARTY_WHEELHOUSE --find-links APPROVED_CANDIDATE_DIRECTORY --require-hashes -r TARGET_LOCK
NEW_ENVIRONMENT_PYTHON -m pip check
```

The observed verification instead bootstrapped pip from the exact locked pip
26.2.2 wheel and used its binary-only, hash-required, no-index installation.
No outdated runtime-bundled pip was used to install the package set. Linux
verification ran with networking disabled and only task-specific inputs
mounted; the CERN dataset was not mounted. The Linux environment was temporary;
its pinned image and locks permit recreation, not a claim that a persistent
Linux measurement environment is already running.

## Boundaries and retention

Historical preflight receipts retain their original `NOT_FROZEN` environment
notation. This later preparation does not rewrite those receipts, add automatic
lock enforcement to the existing helper, or mark pilot readiness true.
Future execution must verify these lock identities against the actual native
environment and retain those environment receipts under the existing source
allocation. Source-only locks/verification belong in that allocation; large
interpreter and dependency installations/caches remain separately identified
outside the pilot evidence root. No retention subcap is enlarged.

Review evidence, initial failed checksum-sidecar lookup, successful manifest
completion, native install reports, tests, probes and audits are retained under
the ignored `.local/cern-dimuon-helper-review-locks-20261020/` workspace.
Download/runtime caches are separately identified under
`.local/cern-dimuon-environment-cache-20261020/`.

The two retention findings are corrected and re-reviewed, and owner review is
complete for the focused PR. Remote qualification and any protected merge
remain separate gates. Future measurement still requires actual environment
identity verification/retention and separate execution authorization. Physical
validation remains `NOT_ESTABLISHED`; independent scientific review and human
disposition remain `PENDING`.
