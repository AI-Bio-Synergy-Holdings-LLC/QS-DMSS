# Data-only diagnostics pilot: engineering review and qualification

Owner authorized one focused data-only diagnostic-pack pilot PR, followed by a
v0.14.0 feature-scope freeze. Baseline local/remote main was clean at
`999d49ce437565792ebcb3c8c5c39938df8b3476`, with no open PRs. Published v0.13.2,
the scientific-review gate, original evidence and the retained explorer worktree
are not altered. No protected merge/publication is authorized by this PR work.

## Pre-review boundary assessment

- CLI registration/dispatch delegates to an isolated family; existing routes,
  payloads, solver implementations and hosted capabilities are unchanged.
- Frozen strict models and synchronized schemas admit only two JSON files and
  one reviewed diagnostic/suite ID. Pack metadata cannot select imports, shell
  commands, providers, files to execute, dependency installation or network URLs.
- Bounded reads and directory scans precede parsing; parsing rejects duplicate,
  nonfinite, malformed and surrogate text. Long integer parser errors are
  sanitized. Declaration/coherence/grid budgets precede allocation.
- Only direct CPU energy/norm measurements are performed. Reference/tolerance
  checks are explicit; nonfinite/failed results remain counterexamples.
- Export retains exact source bytes and actual module/environment identities,
  labels caller-declared commit/wheel hashes, never overwrites an existing output,
  and retains partial writes rather than deleting paths. Bundle verification is
  extraction-free and explicitly integrity-only, not numerical/schema approval.
- Markdown contains only core-owned prose and restricted ASCII case IDs; no
  report HTML/CSP expansion, public-surface change or UI rendering is added.
- Real CLI/installed-wheel/Docker smoke is wired into the existing quality gates;
  fresh-install checks are candidate-only, not run against historical v0.13.2.
- Cross-platform review identified Git's configured CRLF conversion as a risk to
  byte-pinned references. A narrow LF attribute and regression test preserve
  only the new pack JSON bytes; existing evidence files are not normalized.

## Initial executed acceptance

The first implementation run was 93 passed / 1 failed: the tampering fixture
reencoded identical content and was corrected to actually change bytes. No
passing tamper-admission result is represented as a product fix. After focused
tests and negative-path additions: 99 tests passed, 100% new-module statement
coverage. A further tight-tolerance analytic-coherence check was added before
complete qualification. Statement coverage is not proof of absence of defects.

The source CLI smoke admits/runs all 12 cases, preserves both original input
files, exports/reopens the hash-verified bundle and refuses repeated output.
Earlier source QA artifacts are retained under ignored
`.tmp/diagnostic-pack-source-qa/`; subsequent candidate artifacts/remote results
are identified separately on the PR, not by version metadata alone.

Complete repository gates and candidate qualification are recorded below after
execution. Remote checks and accountable owner/Copilot review remain admission
requirements. No scientific approval, release, or production changes are implied.

## Local qualification before opening the draft

The quantum-enabled CPython 3.12.14 suite passed **836 tests / 25 existing
Windows symlink-privilege skips / 91.46% coverage** (unchanged 88% gate). The final
LF-policy regression was then added; the focused suite passed **101 tests**.
The new modules have 100% statement coverage; tests include injected numerical
counterexamples and nonfinite results, strict resource/coherence rejection,
JSON/storage failures, immutable snapshots, CLI exit codes, output collision,
partial-write retention and extraction-free bundle integrity checks.

Ruff, configured medium-or-higher Bandit, compilation, JavaScript syntax, all
37 Node UI contracts, scientific-registry/discovery consistency, and dependency
audit passed. The default audit cache emitted deserialization warnings; a fresh
dedicated cache rerun completed with no known vulnerabilities. No installed
dependency versions or user cache were changed to achieve that result.

Wheel/sdist build and Twine passed; archive inspection confirmed pack JSON bytes,
schemas and implementation are preserved. The first bounded development artifacts
are retained under ignored `.tmp/diagnostic-pack-dist/` (not release artifacts):

- Wheel SHA-256: `301b08de00e281928aee951e376c7e9e4bfa7c0e1c56a53f25ed8b9405db4215`.
- Sdist SHA-256: `9c6a79c99e1fd34a0127ad801c0d653ccef3698fb97d08454714d0b66c310e2f`.

The installed Docker Python 3.12 wheel passed the real CLI admission/run/export/
verify/no-overwrite workflow and existing `demo-baseline` benchmark. Its retained
12-case evidence bundle is under ignored
`.tmp/diagnostic-pack-container-qa/installed/result/diagnostic-pack-evidence.zip`,
SHA-256 `ff1ec1ea27dbd9d6b5529aa87f854467ad12a304b48ac5051ad6f240105d274b`.
This is separate installed-Linux evidence, not a fresh Windows wheel pass. It
does not replace the required remote Python 3.10–3.13/all-OS candidate/Docker gates.

Final source-tree rerun: **837 passed / 25 existing privilege skips / 91.44%
coverage**; the 101 pack contracts and all new-module statements are exercised.
Ruff/configured Bandit passed again. The final real source CLI bundle is retained
under `.tmp/diagnostic-pack-source-final-qa/result/`, SHA-256
`ff6df62449b1983ae5f183c331547a2d6d6b62dea2a0feae2f2bab6566bb2cff`.
The installed-container report's six implementation hashes were compared to
the current source bytes and all matched. Candidate identity/build hashes after
commit are recorded on the PR to avoid self-referential artifact identities.

## Honest limitations and remaining gates

Before any review request, a final negative-path assessment found two narrow
input-handling gaps: older Python's output-parent resolution RuntimeError was
not authored, and bundle verification did not explicitly reject nonregular input
before opening. The focused follow-up normalizes only that resolution boundary
and shares the bounded regular-file snapshot reader for both pack and bundle
inputs. Two regressions reproduce the gaps. Earlier commit/artifact qualifications
remain historical; the updated head is qualified separately and recorded on the PR.

Follow-up qualification: **839 passed / 25 existing privilege skips / 91.44%
coverage**, with **103 pack contracts** and 100% new-module statement coverage.
Ruff, configured Bandit and compilation pass. The rebuilt installed Docker wheel
passes the 12-case CLI/no-overwrite/integrity smoke, and actual Linux symlink
roots/children plus a FIFO are rejected before reads. The retained revised Docker
bundle is `.tmp/diagnostic-pack-container-qa/revised-installed/result/diagnostic-pack-evidence.zip`,
SHA-256 `a1c9e2a39a7ccbaf4b1bffd2bca9a57f035ba974dff8b6e99d6461131901d265`.
The first remote head had all gates green (862 Linux quantum tests, 91.40%
coverage; all-OS candidate and Docker smoke). Those results do not substitute
for the updated head's fresh remote qualification. No Copilot request was made
before this follow-up assessment.

This is a closed CLI pilot, not general plugin isolation or third-party licensing
validation. Resource ceilings are per-invocation work bounds, not hard wall-clock
or concurrent-load guarantees. Link checks are not descriptor-anchored TOCTOU
isolation. Bundle integrity is not authorship or scientific correctness.

The previously observed local Windows fresh-wheel Application Control block is
not bypassed or asserted resolved; all-OS CI supplies separate fresh-install
evidence. Existing architecture/supply-chain debt and independent assessment
under #183 remain. Release scope freezes after this pilot; the next pass must
qualify and clearly version the full candidate before any authorized publication.
