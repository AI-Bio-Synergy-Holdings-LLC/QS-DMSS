# v0.14.0 preparation qualification

Local qualification completed on 2026-10-08. Remote PR gates and owner review
remain required. No release, deployment or scientific approval is implied.

The clean starting source is `0073d361c2e25e911c46aecd3ad67df0fdc0b216`.
Release evidence is retained separately at
`C:/Dev/QS-DMSS-Release-Evidence/v0.14.0-20261008`, outside temporary directories
and outside the frozen semantic-checker evidence allowance. Historical packets
and semantic-checker files remain unchanged.

## Environment and results

Windows, CPython 3.12.14; Qiskit 2.5.2 and Aer 0.17.2. Dependency versions are
retained in `environment.txt`; commands/stdout/stderr are under `logs/`.

| Check | Local result |
| --- | --- |
| Complete quantum-enabled test suite | 847 passed, 25 skipped; 91.46% coverage, above the 88% gate |
| Ruff and Bandit medium/high-confidence scan | Pass; no reported findings |
| Installed dependency audit and pip check | Pass after upgrading the qualification environment's pip |
| Challenge registry and frozen discovery catalogs | Pass; no retained evidence or pack-byte changes |
| JavaScript syntax and robustness state contracts | Pass; 37 Node tests |
| Demo benchmark, manifest and replay | Pass |
| Versioned wheel and sdist; Twine | Pass; both report 0.14.0 |
| Fresh installed Windows wheel, outside the checkout | Pass through normal `qs-dmss.exe`; run/verify/replay, campaign, showcase, cockpit headers/health, graph replay, robustness save/reopen and 12-case pack |
| Installed quantum extra | Pass; sidecar, request preparation and all 12 compilation rows; no credentials, remote API, QPU submission or spend |
| Installed sdist | Pass; demo, all three benchmark scenarios, graph replay, robustness and data-only pack |
| Docker installed package | Pass; health/configs, graph replay, robustness, diagnostics pack |

All 25 local skips report that Windows symlink creation requires an unavailable
privilege; none waive quantum qualification. The remote
supported Python 3.10–3.13 matrix and all-OS fresh-install checks remain necessary.
The local environment used currently resolved dependencies, not a locked
reproducibility environment; retained versions identify this execution.

The first full run reported two stale metadata assertions (exact archived DOI
as current-build citation, and published support line inferred from development
version). Those contracts were corrected to distinguish project citation/current
source from immutable archive/published support. The full suite was rerun green.
The initial pip audit found vulnerabilities in bundled pip 25.0.1; upgrading only
the qualification environment to pip 26.2.1 cleared the audit. Preserve both logs.
The unpublished first-party `qs-dmss==0.14.0` distribution is skipped by the PyPI
advisory lookup; dependency audit is not a scientific or whole-source audit.

## Windows restriction disposition

The previous installed-wheel Application Control refusal (error 4551) is retained
as historical evidence. Fresh normal-launcher acceptance passed for the actual
0.14.0 wheel, including its quantum extra, without policy changes or a launcher
bypass. This establishes acceptance only for the tested artifact/environment/path;
it does not explain the old refusal or assert that the old path is now permitted.
Any recurrence must be retained and dispositioned by the authorized administrator
and owner, not worked around by disabling controls.

## Rendered spot-check

Browser skill/runtime was not exposed in this session, so the frontend-testing
skill selected the Playwright CLI fallback. The native Windows `npx` invocation
uses the same CLI as the bundled Bash wrapper; no browser dependency was added
to the project.

Flow: installed Docker cockpit at `http://127.0.0.1:8014/` → release identity →
Scientific Challenges navigation → registered evidence and current #183 handoff.
At 1440×1000 the nonblank cockpit displayed Build v0.14.0, separate v0.13.2
archive and concept DOI; no framework overlay or console warnings/errors were
observed. The link changed the URL to `#scientific-challenges` and exposed the
three challenges with pending independent-review statuses. Screenshots and DOM
snapshots are retained under `.playwright-cli/`. A 390×844 viewport was spot-checked;
this was not a complete mobile or accessibility regression suite.

A new standalone portal-server launch was refused by host tool policy; it was
not bypassed. Portal HTML/JSON-LD, links, version separation, discovery hashes and
exact CSP hash were tested statically, but the revised portal notice was not
qualified in a locally served browser. Before merge/deployment, an authorized
operator must stage the old and new JSON-LD CSP hashes at Render and verify the
real portal in a browser. The local Docker cockpit check does not establish that
the Render portal already serves this branch.

## Artifact identity and evidence retention

The working-tree preflight build and its failures/results remain retained as
preflight evidence. Final preparation wheel/sdist are rebuilt from the clean
preparation commit; exact source commit, filenames, byte counts and SHA-256
values are in `artifacts-final-receipt.json` and the PR qualification body.
Final-artifact installed checks are retained separately, not overwritten.
Publication must still rebuild/qualify from the approved tag and distribute
exactly those approved bytes.

Distribution inspection checks metadata, graph/robustness assets, byte-identical
pack inputs and discovery catalog, immutable v0.13.2 review packet, and absence
of semantic-checker paths. This release record does not repackage or rehabilitate
the semantic pilot's incomplete evidence. Local retained files are not an
off-device backup; their location and hashes support subsequent controlled backup.

## Outstanding gates

- Remote Python 3.10–3.13, quantum installed-wheel paths, all-OS fresh install,
  Docker, CodeQL and dependency review for this PR's exact head.
- Owner/Copilot review; no prior feature approval is approval of this release PR.
- Authorized Render CSP transition and rendered portal qualification.
- Protected merge, main CI and public app/portal version/commit/header verification.
- Separate publication authorization; no tag, release, PyPI upload, new DOI or
  deployment was performed in this pass. Independent scientific review #183 is open.

## PR #199 review corrections (2026-10-08)

All four findings in Copilot's review of `c5ca812` were confirmed. Candidate
CodeMeta and cockpit JSON-LD no longer advertise a generic PyPI download or
package identity. Research-object citations and Markdown exports omit that
target and explicitly distinguish the v0.13.2 historical archive from this
build. The release notes now use the registered `fft_cell_measure_v2` spelling.
The portal's explicitly versioned published-package links and its staged CSP
hash are unchanged. No solver, scientific status or semantic-checker scope changed.

Regression tests execute the actual Lab/Campaign Markdown and citation-rendering
callbacks, validate both structured-metadata surfaces and check the convention
against its schema. The new Node contract is included in the sdist and in CI.
The complete quantum-enabled source suite passed: **851 passed, 25 skipped,
91.44% coverage**. All skips retain the same Windows symlink-privilege reason.
All **40 Node tests**, JavaScript syntax, Ruff, Bandit, dependency audit, pip check
and frozen challenge/discovery checks passed. The first-party unpublished
distribution remains excluded from the external advisory lookup.

Chrome rendered the revised installed Docker cockpit at `http://127.0.0.1:8015/`.
A bounded packaged run verified and replayed; its research object was composed
and its actual Markdown download retained. The citation has no PyPI target and
labels the historical archive; no console errors or warnings were observed.
The Browser runtime was available for this correction pass; the frontend-testing
skill used it instead of the earlier Playwright fallback. This targeted desktop
check is not a complete mobile regression or served-portal qualification.

Correction logs, JUnit/coverage, screenshots, downloaded Markdown, generated
run/export evidence and rebuilt-artifact receipts are retained separately under
`C:/Dev/QS-DMSS-Release-Evidence/v0.14.0-20261008/review-correction-20261008`.
Earlier qualification and artifact identities above remain historical; revised
artifact identity and installed acceptance are recorded in that directory, not
inferred from the earlier artifacts. Remote gates and review must apply to the
correction head. No merge, publication or production deployment is implied.
