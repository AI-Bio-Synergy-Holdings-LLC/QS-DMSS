# QS-DMSS v0.15.0 release preparation

Preparation record: 2026-10-29. Baseline: `1ef2c4eb3e64efeca002ec32d8172324863ff562`.
**This pass prepares source and QA artifacts, not a publication.** No tag, GitHub
release, PyPI upload, new DOI or production deployment is authorized. The verified
public release remains v0.14.0, source `15377b5ab1f9f3e32a37494e2e8973efce5211c3`,
archived at `10.5281/zenodo.23250727`. Its artifacts and historical records remain
immutable. Later publication status must be verified separately, not inferred
from this dated preparation record or the package version alone.

## Frozen engineering scope

| Component | Candidate scope and limits |
| --- | --- |
| Cockpit hardening | Include EH-013 protected unhandled-error responses, hosted-session continuity, parsing/packaging fixes and test reliability corrections already merged. Preserve error/status, cookie and report-CSP contracts. |
| EH-001 extraction | Include characterized run, experiment, showcase, quantum and remaining-export delivery boundaries. No new decomposition or solver/numerical changes in this preparation. |
| CERN Dimuon Evidence Lab | Include the already-merged local CLI as **experimental educational software**: bounded import, analysis, reporting and integrity verification. Synthetic engineering acceptance is not real-data numerical reconciliation, independent scientific assessment or pilot admission. |
| Reviewer explorer | Include the existing read-only four-case recorded-data handoff and caption/accessibility corrections. Preserve all media, rights/provenance, frozen evidence and credit policy. |
| Existing v0.14.0 features | Carry forward the local recorded-result robustness explorer, data-only diagnostics pack and experimental CPU/local graph backend without broad UI expansion, executable plugins or new provider integrations. |
| Pack compatibility | Preserve the original FFT pack 1.0.0 unchanged. Bundle metadata-only successor 1.0.1 for core `>=0.15.0,<0.16.0`; identical case bytes, tolerances and resource limits. No admission-guard bypass or old-evidence migration. |
| Qualification sources | Previously reviewed source-only helpers/contracts remain source-only, with their original identities and limits. Their presence in an sdist does not authorize execution or admission. |
| Deferred work | **EDRS/v3 execution, inactive checker/ledger/launcher drafts and semantic-checker admission remain DEFERRED, HOLD.** Inactive local drafts must not enter distributions. Reviewed historical data-only contracts are not executable admission. |

The graph model remains experimental, CPU-only and local-only. Hosted graph
execution and hosted AI remain disabled. Quantum qualification is local,
simulator-first and provider-neutral: **no provider credentials, remote API calls,
submission, QPU execution or authorized spend**. AI advice is not a scientific
assessment. Scientific gate #183 remains open; validation is `NOT_ESTABLISHED`
and independent human review/dispositions remain `PENDING`.

## Build, publication and frozen-candidate identity

- Source/package/installed metadata, cockpit build labels, CFF and CodeMeta target
  `0.15.0`. CFF has no invented release date, and no new version DOI is claimed.
- Candidate CodeMeta/cockpit structured metadata omit distribution links and
  `sameAs` release associations. The concept DOI remains the project citation.
- The portal build-provenance version is `0.15.0`, but public release badges,
  install links and JSON-LD remain on the verified **v0.14.0** publication.
  Portal inline JSON-LD and its active CSP hash/directives are unchanged. No
  Render CSP staging or configuration change is part of this PR.
- The cockpit separately identifies its current build and latest archive
  (v0.14.0). Never offer that older archive as an equivalent reconstruction of
  current evidence; compare source commit, artifact hashes and conventions.
- Manual published-install defaults remain v0.14.0 until v0.15.0 actually exists.
- The CERN reconciliation protocol still pins source
  `c158c3ba3f81cadf7d11bdfcab3441c8d99be851` and wheel
  `6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60`.
  The original wheel `b8434593e6b34abda2536e0c5752e5ade253d76a083537a34fb84d3b6b70974e`
  is also retained. A new 0.15.0 wheel must not replace either artifact or be
  silently admitted by those frozen identity checks. Criteria/protocols, locks,
  allocations/caps, failed results and historical evidence are not rewritten.
- Real CERN numerical reconciliation remains `NOT_EXECUTED`; pilot readiness is
  false. No actual CERN dataset, EDRS run or v3 helper is executed by this pass.

The security policy now correctly identifies v0.14.x as the published line while
retaining the existing maintainer-directed v0.13.x support/backport policy.
No end-of-support date, license change or automatic promotion of v0.15.x support
is implied. The public core/distributions remain Apache-2.0.

## Preparation qualification

See [the candidate qualification record](release-qualification-v0.15.0.md).
Qualify the actual 0.15.0 wheel and sdist, not a renamed old wheel. New artifacts
have new hashes and remain unpublished QA artifacts. Ordinary QA outputs live
outside the constrained research evidence corpora; no cap or allocation changes.

Required remote gates: Python 3.10–3.13, unchanged coverage floor, base and quantum
candidate-wheel installation on Linux/macOS/Windows, Docker, CodeQL, Code Quality,
dependency review, policy/metadata checks and exact-head owner/Copilot review.
The new all-OS quantum smoke checks the local never-submit paths; v0.15.0 install
smoke also exercises the CERN CLI with original **synthetic** inputs only.

Keep local attempts, failures, environment identities, source/artifact hashes and
their limitations. Native Windows 3.14 remains supplemental, not newly supported.
A Windows application-control refusal is a retained host-policy limitation,
not a passed installation or a product fix. Do not disable controls, substitute
launch paths to evade a refusal, or treat another machine's pass as its resolution.

## V0150-PACKAGE-ONLY-1 — adoption draft for review

2026-11-23. Project: `AI-Bio-Synergy-Holdings-LLC/QS-DMSS`. Adoption baseline:
`178fe4f91d196f0b5b78a3aaa32655ed3e6170e5`. Charles Martin Jones Jr, Founder and
Managing Member of AI-Bio Synergy Holdings LLC and Founder and CEO of AI Bio
Synergy, approved the package-only design. This AI-assisted adoption draft
records that decision for review; it does not authorize execution. Contribution
attestation reference: `ABS-PA-20261122-01` (private record, not included here).
The October preparation results above are historical and unchanged.

**One-time ordering change, v0.15.0 only.** A separately authorized local
engineering beta may be published on GitHub and PyPI before the hosted rollout
if the package gates below pass. No tag, upload, workflow dispatch, public
metadata change, deployment or change to future releases is authorized here.

### Package gates — separate authorizations

1. **Adopt the policy without deploying.** Require owner and Copilot review,
   a protected merge and green post-merge engineering checks. Limit the adoption
   diff to this record. A later authorized merge must retain `[skip render]` in
   its final commit message. Do not dispatch GitHub Pages, Render deploys,
   Blueprint syncs or the PyPI workflow for this adoption. The production
   provenance workflow can still start on a push to `main`: it checks for a
   live deploy but does not trigger one. Treat that check as not applicable to
   the no-deploy merge; any cancellation requires separate authorization and
   must not cancel engineering CI.
2. **Qualify the exact release artifacts.** Before creating or pushing the
   release tag, verify that tag-triggered integrations, including those outside
   the repository, cannot trigger hosted deployment. If this cannot be verified,
   hold tagging. Then separately authorize a clean release commit and tag, and
   build a fresh wheel and sdist. Retain the source commit, build environment,
   artifacts and their SHA-256 digests. Require the supported Python matrix,
   unchanged coverage floor, base and quantum installation on
   Linux/macOS/Windows, Docker, security, policy and package checks. Bind results
   to the exact release source and bytes; a tag alone does not run the existing
   PR and branch checks. The preparation artifacts do not substitute for this.
3. **Clear release and publication blockers.** Before creating or publishing
   the GitHub release, verify that release-event integrations, including those
   outside the repository, cannot trigger hosted deployment. If this cannot be
   verified, hold release creation and publication. Inventory live version
   labels: an accurately labeled v0.14.0 archive link may stay, but a v0.14.0
   “latest” claim cannot. If a metadata-only change is needed, separately
   authorize and verify it before publication; never use package approval to
   update the hosted app or approve a CSP change.
   If the labels cannot remain accurate without an unauthorized deploy, hold
   publication. Identify the package as available for local installation only
   after verification; distinguish it from the hosted demo's actual build.
4. **Authorize publication separately.** Publish only the qualified wheel and
   sdist, with the approved digests, to GitHub and PyPI through the protected
   path. Follow the [upload-integrity procedure](pypi-distribution-readiness.md#trusted-publishing-configuration)
   to bind the approved manifest to the exact tag, source commit and files.
   Metadata and Twine checks alone are not a digest comparison. If the workflow
   cannot verify the staged bytes against that approved manifest immediately
   before upload, hold publication. Re-download from both channels,
   verify matching digests and published-source installs, and record any
   partial publication without silently replacing artifacts. Confirm any
   archival trigger before release and verify the actual version DOI before
   advertising it. Do not invent URLs or mutate prior releases.

### Hosted acceptance — remains HOLD

Render remains on the existing Git-backed service and hosted ABA01 stays
parked. A later separately authorized rollout still requires app/portal source
provenance, isolated EH-013 sanitized **500** security/cache/noindex evidence
bound to the exact deploy artifact, and verified eligibility of the exact
retained rollback target. A healthy `200`, a preparation-only Docker test or
offline ABA01 mock does not meet that gate. Until then, EH-013 remains
operationally open. Preserve failed ABA01 R2, sealed R3, the 128 KiB evidence
ceiling and the US$10 operational cap.

Passing preparation, CI or publication does not promote scientific claims,
admit held research work, close #183 or grant deployment/release authority.
