# QS-DMSS v0.14.0 release

Status: **published and verified** after separate owner authorization.
The annotated `v0.14.0` tag pins source commit
`15377b5ab1f9f3e32a37494e2e8973efce5211c3`. GitHub publication occurred on
2026-10-08 UTC; PyPI upload and Zenodo publication crossed into 2026-10-09 UTC
(still 2026-10-08 in the owner's local timezone).
The verified version DOI is [10.5281/zenodo.23250727](https://doi.org/10.5281/zenodo.23250727).
The concept DOI remains 10.5281/zenodo.20074924; historical v0.13.2 records remain unchanged.

## Verified publication

- [GitHub release and qualification receipt](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.14.0)
- [PyPI v0.14.0](https://pypi.org/project/qs-dmss/0.14.0/)
- [Published Zenodo source archive](https://zenodo.org/records/23250727)
- [Protected PyPI publication](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/actions/runs/37862435936)
- [Six-way published-install qualification](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/actions/runs/37862597285)

The GitHub and PyPI distributions were downloaded and checked against the exact
qualified tag-built bytes:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `qs_dmss-0.14.0-py3-none-any.whl` | 772788 | `22a2d4f3f6af64f562916f45ca319606a03132e89d8b7787da034c88ad87cbed` |
| `qs_dmss-0.14.0.tar.gz` | 1264118 | `bf54d49832fac8e227fea122eab6250f597941bd3c9ed8ccf908421fd29d76a1` |

Tag-built qualification passed 851 tests with 25 Windows symlink-privilege skips,
91.43% coverage, 40 Node tests, Ruff, Bandit, dependency checks, fresh native
Windows wheel/sdist paths, exact-wheel Docker checks, and installed quantum-extra
validation (12 compilation rows, local-only, no credentials/API/QPU/submission/spend).
Published PyPI and release-wheel installs passed on Windows, macOS and Linux.
The first macOS PyPI attempt could not yet see 0.14.0 in the index; its log is
retained, and only that failed job was rerun successfully. No product or policy
change was made to satisfy it.

Zenodo's 301 source files match canonical Git blob hashes for the tagged commit.
The first Windows-export comparison failed because 283 text files differed only
by CRLF/LF line endings; that failure and the corrected canonical comparison are
retained. The Zenodo source ZIP is not the wheel or source distribution above.
Its SHA-256 is `c11941b6be6748e38a9ac067d60b406945e215d180fed536b492a5e083e37d8c`.

The public `tagged-qualification-receipt.json` has SHA-256
`88408c2076eff45521bcb78b895f81ae547c838ed9de2bf1fb543f0f3adb2b0d`.
Detailed environments, commands, generated evidence and failures are retained at
`C:/Dev/QS-DMSS-Release-Evidence/v0.14.0-tagged-publication-20261008`.
Published artifacts and the tag are immutable; this metadata follow-up does not rebuild them.

## Frozen scope

- FFT energy correction (#192): `fft_cell_measure_v2` includes cell measure in
  the discrete kinetic-energy diagnostic. Historical energy numbers and benchmark
  expectations must be compared using their recorded convention, not mixed with
  corrected values. See [diagnostic migration](fft-energy-diagnostic-correction.md).
- Additive CPU-only graph-spectral backend (#193): experimental, local-only,
  bounded dense operators, basis-invariant diagnostics, retained operator artifacts
  and replay. It is not a replacement for rectangular Fractal SSFM or a claim of
  continuum convergence, physical validity, or quantum performance.
- Commit-pinned falsification evidence and Scientific Challenge Registry/reviewer
  handoff (#194–196). Historical candidate packets are unchanged; their original
  package version, source commit and artifact hashes remain authoritative.
- Local recorded-result recommendation robustness explorer (#197), with exact
  scoring profiles, immutable saves, stale-evidence protection and bounded analysis.
- One schema-validated data-only FFT plane-wave diagnostics pack (#198): twelve
  analytic cases, retained inputs/results and no executable plugin loading.

The semantic checker is **deferred from v0.14.0**. Its incomplete historical
evidence remains on HOLD, outside this release and its qualification budget.
Missing evidence is neither regenerated nor described as recovered.
No new solver, provider extension, hosted AI activation or broad UI expansion is
included. Existing optional AI advice retains its four approved intents and human
disposition boundary.

## Scientific and hosted boundaries

[Independent review #183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183)
remains open. `NOT_FALSIFIED_WITHIN_SCOPE`, engineering approval and pending
independent human assessment are distinct statuses. Passing tests, analytic
cross-checks, Wolfram agreement and owner review do not establish scientific
correctness or physical validation. The graph model remains experimental even
if this software release is published.

Hosted AI and graph execution remain disabled. The robustness pilot remains
local-only. Quantum paths remain provider-neutral, local simulator-only: no
credentials, remote API, QPU execution, submission or authorized spend.

## Preparation protocol (retained history)

Build and inspect `qs_dmss-0.14.0-py3-none-any.whl` and
`qs_dmss-0.14.0.tar.gz`, not a wheel still reporting 0.13.2. Qualify the installed
wheel outside the checkout and the extracted sdist separately. Retain artifact
SHA-256 values, source identity, environment, command logs, failures and generated
evidence. A source-test pass does not substitute for an installed-artifact pass.

The preparation qualification record is
[release-qualification-v0.14.0](release-qualification-v0.14.0.md). Candidate
artifacts are not the eventual tagged publication artifacts; rebuild from the
approved clean tag, qualify and publish exactly those bytes after separate
authorization. Never upload the local preparation artifacts as if tag-built.

Required PR gates: Python 3.10–3.13, coverage, installed base/quantum wheel paths,
all-OS fresh installation (including Windows), Docker, CodeQL, dependency review,
and owner/Copilot review. Publication requires green post-merge main checks and
verified app/portal deployment provenance as well.

## Local Windows installation disposition

The earlier local installed-wheel launcher was refused with Windows error 4551
(Application Control). This is a host-policy restriction, not evidence that the
wheel passed locally. Do not disable security controls, unblock executables or
substitute a launch path to evade the restriction. A retained attempt with the
actual 0.14.0 wheel is recorded separately from the earlier failure.

Disposition on 2026-10-08: the actual v0.14.0 wheel passed a fresh Windows
installation and the normal `qs-dmss.exe` launcher without policy changes,
including cockpit health, run/verify/replay, graph, robustness and diagnostics.
Installed quantum-extra paths also passed. Local acceptance is satisfied for
this tested environment/path; this does **not** prove why the earlier 4551 refusal
occurred, that the old path now works, or that Windows policy changed. Preserve
that historical failure; do not describe it as a product fix or waived test.
Require the new PR's Windows fresh-install check too. Any recurrence requires
retained evidence and administrator/owner disposition, not a bypass.

## Public metadata after publication

Before publication, CodeMeta and cockpit structured metadata deliberately omitted
v0.14.0 download links; the portal identified v0.13.2 as the published package.
The immutable tag-built distributions retain that preparation-time metadata.
Only this post-publication source update activates verified v0.14.0 links and DOI.
It does not replace the released package or relabel historical scientific packets.

The cockpit's project citation remains the concept DOI. Its archived-release
links require source-commit and artifact-hash comparison before identifying the
archive with a particular build. A matching version string alone is insufficient.
Research-object exports still omit a generic PyPI install target.

The post-publication metadata working tree passed 852 tests with 25 Windows
symlink-privilege skips and 91.46% coverage, all 40 Node contracts, Ruff and the
repository's medium/high-severity Bandit gate. The unrestricted informational
Bandit run retained four pre-existing low-severity notices; no zero-finding claim
is made. Two initial stale-version test expectations were corrected, with the
failed run retained separately from final results.
Chrome QA exercised the loopback portal with the proposed exact CSP hash,
desktop and 390×844 mobile challenge selection, cockpit archive identity, and a
real showcase → verification/replay → composed/downloaded research-object report.
No relevant console errors, blank pages, framework overlays or mobile horizontal
overflow were observed. This is local metadata QA, not verification of a new
production deployment. Public app/portal provenance still pins the release commit
above until the follow-up PR is reviewed and deployed.

The portal JSON-LD change requires its exact new CSP hash at the Render edge;
see [deployment instructions](website-deployment.md). This external header change
must be staged with both old/new hashes before merge and narrowed after deployment,
under separate operational authorization. Do not weaken CSP with `unsafe-inline`.

Completed sequence after protected merge, post-merge verification and explicit publication approval:

1. Tag the approved main commit; build and qualify the exact tagged distributions.
2. Create the GitHub release and upload only those approved artifacts.
3. Publish the same bytes to PyPI through Trusted Publishing; verify hashes.
4. Verify the real Zenodo archive/DOI, then update public published links and
   manual fresh-install workflow defaults. Do not invent the DOI or pre-activate links.
5. Run published-source fresh installation, installed quantum checks, and public
   provenance/security-header checks. Keep experimental labels and #183 open.

Publication was separately authorized and completed. The public-metadata follow-up
still requires review, protected merge, and separately authorized CSP staging;
publication approval does not waive those gates or approve scientific claims.
