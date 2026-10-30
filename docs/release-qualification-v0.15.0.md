# v0.15.0 candidate qualification

Baseline: `1ef2c4eb3e64efeca002ec32d8172324863ff562`.
Scope: the owner-authorized focused release-preparation PR; source and QA only.
Raw receipts: `.tmp/release-v0150-preparation-20261029/`. This is not tag-built
publication evidence, a real-data pilot or a new scientific assessment.

## Executed local qualification

Preparation began 2026-10-29; some receipts have 2026-10-30 UTC timestamps.
GitHub's latest release and PyPI's current package were checked directly and
remain **v0.14.0**. Issue #183 remains **OPEN**. No publication availability or
scientific approval is inferred from the new source version.

| Gate | Result and scope |
| --- | --- |
| Final complete Linux suite | **1,835 passed, 7 skipped; 91.95% coverage**, unchanged 88% floor. Four skips require native Windows handles; three JS syntax checks lack Node in the QA image and passed separately on the host. Python 3.12.15 with quantum extra and pip 26.2.2; final source snapshot `source-r4.tar`. |
| Focused release/pack regressions | 197 passed after the compatibility correction; final metadata/governance/accessibility subset: 108 passed. |
| Fresh Windows base wheel | Passed the complete candidate-install smoke on Python 3.14.3: demo, verification/replay, campaign, benchmark, showcase, health/headers, graph, robustness, diagnostic pack and **synthetic** dimuon acceptance. Supplemental host result, not an expansion of supported Python versions. |
| Fresh Linux quantum wheel | Passed the complete `--with-quantum` candidate smoke on Python 3.12.16 in a new venv with `include-system-site-packages = false`, freshly resolved dependencies and pip 26.2.2. Includes all base paths and the three local never-submit quantum paths. |
| Installed wheel / sdist | Both passed the three local quantum paths and researcher-workflow acceptance on Linux 3.12.15 in separate venvs sharing the recorded QA dependency closure. The sdist-built installation also passed **760** focused tests with source import paths disabled. This is not a claim that repository-only workflow tests run from an sdist. |
| Docker | Unmodified Dockerfile built successfully; non-root `qsdmss` runtime, version 0.15.0. Local/hosted loopback acceptance passed sanitized 500 headers, normal/authored errors, missing-file contracts, cookie continuity and started-stream behavior. No host port or production service was deployed. |
| Static and presentation gates | Ruff, medium-or-higher/medium-confidence Bandit, package compilation, cockpit JS syntax, **113** Node tests, registry integrity, discovery synchronization and pinned social-card check passed. |
| Distribution checks | Wheel/sdist build, Twine and the current CI archive assertions passed. Both original/successor FFT packs are included; inactive admission drafts, local research corpora and MP4 media are excluded. Final closeout bindings are retained separately to avoid a self-referential sdist hash. |

Commands and receipts are retained below `.tmp/release-v0150-preparation-20261029/`.
The complete suite is run from the final source snapshot with the candidate
installed first, so synthetic child interpreters resolve the actual package.
CI's supported Python 3.10–3.13 matrix and macOS/Windows Python 3.12 quantum
installation still require **remote** qualification; local evidence does not
stand in for those jobs.

### Dependency and installer posture

No package dependency declarations, frozen locks or environments were changed.
pip-audit found no known vulnerabilities in the final inventoried third-party
sets: ordinary Windows QA **91**, fresh Windows base **17**, clean Linux quantum
**27**, current-tooling Linux QA **69**, and Docker runtime **17**. The unpublished
QS-DMSS project is separately identified/excluded, not treated as a missing PyPI
version or silently substituted with 0.14.0. Exact-version inventories and JSON
audit reports are retained; these are point-in-time advisory checks, not a proof
of absence of vulnerabilities or a dependency lock.

The reusable QA image initially contained pip 25.0.1; its audit flagged that
installer (including duplicate advisory aliases). This was **not waived**. The
final disposable full-suite environment and clean installation use pip 26.2.2;
their audited inventories passed. The older image and failed audit remain
historical QA records, not approved runtime/distribution artifacts. No frozen
CERN toolchain was upgraded. `pip check` passed for ordinary Windows QA and the
fresh Windows installation.

### Artifact identities and compatibility correction

The clean Linux installation tests this unpublished wheel:

`792f10d07c6061b49a8807cf6d4db656db23b2039a1509b089034bd4bd64a4b8`

The closeout retains those **exact wheel bytes**, rather than renaming an older
release or silently rebuilding the qualified wheel. The earlier Windows/installed
workflow wheel was
`c4bdc2a67d9cbbef36570b5331faa45f77eecae22e260ae3b4682f80faa4e0db`;
the earlier installed sdist was
`605256936afa2c8aa85e3a85be12056718c987d43269a2cd50f45e759e85535b`.
Wheel member bytes are checked equal across those builds; ZIP timestamps can
change the container hash. The closeout sdist is separately hashed after this
record is complete. Its only content differences from the installed sdist are
this qualification record and the two corrected version/policy test files;
the final full suite covers those corrections. Production/module, manifest,
case and packaged asset bytes must be identical, or qualification stops.

Installed testing correctly refused the unchanged FFT pack 1.0.0 on core 0.15.0:
its upper bound is exclusive. The correction **preserves it unchanged** and
adds pack 1.0.1 for `>=0.15.0,<0.16.0` as the new default. Only version/compatibility
metadata changes; exact case bytes, tolerances, limits, formula, result format
and scientific labels stay the same. Regression tests check the historical
manifest/case hashes, compare all other manifest fields and retain rejection
at both original and successor version boundaries. Existing evidence is not
migrated, and the original admission check is not relaxed.

### Retained failures and host limitations

- Initial metadata checks exposed stale generated editable-install identity;
  the normal versioned build refreshed it. No frozen installation was changed.
- The first complete revised suite retained **1,833 passed, 2 failed, 7 skipped**:
  stale cockpit-build and support-policy assertions. They were corrected to
  distinguish the prepared build, published release and continuing v0.13.x
  backport policy; no scientific, numerical or security assertions were removed.
- Partial/interrupted qualification attempts and failed setup logs are retained,
  not counted as passes. A source-launch path error occurred before installation;
  Linux venv setup on a Windows bind mount was stopped and repeated on native
  container storage. Missing QA build-backend tooling was explicitly installed
  in the disposable sdist environment before the successful retry.
- The historical Windows quantum/Rustworkx application-control restriction is
  **not declared resolved** by a base-wheel pass. No control was disabled and no
  alternate launch path was used to evade it. Native Windows 3.14 quantum was not
  retried; supported Windows 3.12 quantum CI remains a mandatory remote gate.

## Preservation and later gates

Both CERN wheels and their copies, all frozen evidence/environments/locks,
inactive drafts, protocols/criteria, allocations/caps and scientific statuses
remain outside the mutation scope. Ordinary release QA outputs are separate from
research evidence roots. The original untracked allocation draft stays untracked
and unadmitted. EDRS/v3 and semantic-checker admission remain deferred/HOLD.
Scientific validation remains NOT_ESTABLISHED; independent review/dispositions
remain PENDING. Graph/AI hosted execution stays disabled.

The final preservation check compared **46,762** retained/tracked records and
found no unexpected changes. It hashes retained artifacts/source/evidence and
checks frozen environment configuration/RECORD anchors and reparse metadata;
it does not claim to reread every environment binary. The untouched allocation
draft remains
`0b0be1b9f10c15c8603b7de790416f94a832120e1a3aa2cea993c00d5544fc26`.
Both original CERN wheel hashes and the active protocol's original candidate pin
remain as listed in the preparation scope. No research-budget amendment or
admission, real-data execution, scientific-status promotion or evidence rewrite
is part of release QA.

Remote review/qualification, protected merge, production rollout/verification,
tag-built artifact qualification and publication each remain distinct later
gates. Current authorization allows one draft preparation PR, not deployment,
tagging, publication or a scientific-status change.
