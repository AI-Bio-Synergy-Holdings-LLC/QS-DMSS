# QS-DMSS v0.14.0 release preparation

Status on 2026-10-08: **development build under qualification, not published**.
The latest published GitHub/PyPI release remains v0.13.2, archived at
10.5281/zenodo.21366910. The project concept DOI remains
10.5281/zenodo.20074924. No v0.14.0 release DOI is assigned here.

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

## Actual-artifact qualification

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

## Public metadata and later publication

The source, cockpit build, citation metadata and portal build identify 0.14.0.
The portal separately describes the latest **published** application as 0.13.2;
its download/install/archive links remain valid for that version. The cockpit's
project citation uses the concept DOI and labels the historical archive explicitly.
Do not associate the v0.13.2 DOI with v0.14.0 results.

Candidate CodeMeta and cockpit structured metadata omit public download URLs.
The research-object composer and Markdown exports also omit the PyPI target;
the archived release links identify a separate historical publication, not an
install source for this build. Restore version-specific download metadata only
after the corresponding artifact is actually published and verified. The portal's
explicit v0.13.2 published-package links remain available and unchanged.

The portal JSON-LD change requires its exact new CSP hash at the Render edge;
see [deployment instructions](website-deployment.md). This external header change
must be staged with both old/new hashes before merge and narrowed after deployment,
under separate operational authorization. Do not weaken CSP with `unsafe-inline`.

After protected merge, post-merge verification and explicit publication approval:

1. Tag the approved main commit; build and qualify the exact tagged distributions.
2. Create the GitHub release and upload only those approved artifacts.
3. Publish the same bytes to PyPI through Trusted Publishing; verify hashes.
4. Verify the real Zenodo archive/DOI, then update public published links and
   manual fresh-install workflow defaults. Do not invent the DOI or pre-activate links.
5. Run published-source fresh installation, installed quantum checks, and public
   provenance/security-header checks. Keep experimental labels and #183 open.

This PR authorizes none of those publication or deployment operations itself.
