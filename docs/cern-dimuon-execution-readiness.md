# CERN Dimuon execution readiness — synthetic only

This source-only layer rehearses the approved qualification machinery. It does
not execute `CERN-DIMUON-NR-001` on CERN data, change production code, or authorize
a pilot, deployment or release. The approved criteria in
[`protocol-v1.json`](../research/cern_dimuon_qualification/protocol-v1.json), both
historical wheels, and frozen scientific evidence remain unchanged.

## Admission and serial coordination

The coordinator accepts only a **new** output root, the approved unpublished
wheel, the reviewed Windows Python launcher, and the two offline wheel caches.
There is no dataset, arbitrary command, download, retry or actual-pilot option.
Stages are fixed: Windows → Linux → comparison → refusal controls. Exclusive
worker claims prevent duplicate starts; Linux requires Windows completion.
Any refusal stops the sequence and preserves the root, partial files, reserved
logs and HOLD receipt. A failed root must never be reused or represented as a
successful result.

Both native workers must admit the exact frozen CPython 3.12.15 runtime and
package set, including NumPy 2.5.4, **before opening the synthetic fixture**.
Admission hashes the frozen manifest, both locks, cached wheels, and every
original installed wheel member except pip's regenerated `RECORD`. Extra or
missing distributions, altered member bytes and non-venv imports cause HOLD.
Windows interpreter launcher/base bytes are pinned. Linux uses the frozen
image digest without pulling, a fresh offline venv, disabled networking and a
read-only container filesystem, except evidence and bounded temporary storage.
Package/runtime identities are checked again after analysis.

The controller checks the candidate's nine relevant modules against pinned Git
objects at `c158c3ba3f81cadf7d11bdfcab3441c8d99be851` and retains their hashes.
Windows independently repeats the Git/import comparison. The pinned Linux
image has no Git: Linux checks imported bytes against that retained map and the
approved wheel, rather than claiming another independent Git check. The full
repository and original CERN input are **not mounted** into Linux.

The built-in, original synthetic CSV has 20,000 rows, 19,996 selected rows and
four deliberately excluded rows. It is not collision data or an approximation
to the known CERN result. Each platform builds and verifies its own evidence
bundle and compares against the existing independent scalar/Decimal reference.
Cross-platform row identities, first-failure decisions and counts must agree;
numeric summaries still use the unchanged protocol tolerances, not bitwise
agreement. Reference digests are recorded, not promoted to a new criterion.

## Retention and limits

The 26 MiB root and all existing subcaps remain unchanged: input 4 MiB, wheel
1 MiB, each platform 10 MiB, sources 256 KiB, comparison 512 KiB, logs 192 KiB,
integrity 64 KiB. Sources include the complete active helper, protocol, locks,
tests and this guide. Four fixed 16 KiB before/after environment slots are
reserved **inside** the existing source bucket. The complete source plan must
fit before workers start. Historical review records are external, unchanged
and not relabelled as current approvals. Interpreter/dependency caches are
identified runtime prerequisites outside the evidence root, not hidden copies
of results. All retained result, transport, padding and inventory bytes count.

Each native stage has at most 300 seconds and a preallocated 24 KiB combined
log. Log overflow, timeout, source drift, unreadable enumeration, allocation
refusal, worker failure or unverified container cleanup causes HOLD. No limits
or tolerances are relaxed to obtain a passing run. Disposal applies only to the
new uniquely named container; evidence directories are retained.

Example (PowerShell, reviewed local paths substituted explicitly):

```powershell
python -B -m research.cern_dimuon_qualification.readiness `
  --output C:/qualification/new-synthetic-root `
  --wheel C:/artifacts/qs_dmss-0.14.0-py3-none-any.whl `
  --windows-python C:/locked-env/Scripts/python.exe `
  --windows-wheels C:/cache/windows-wheels `
  --linux-wheels C:/cache/linux-wheels
```

The controller may use a different stdlib Python; only the two admitted native
workers produce measurement evidence. A repository with the pinned Git objects,
the cached Linux image, and the exact approved offline artifacts are required.
This command is synthetic-only even after merge.

## Meaning and remaining gate

`SYNTHETIC_REHEARSAL_PASSED` is engineering evidence only. Actual qualification
remains `NOT_EXECUTED`, `pilot_execution_ready` remains false, scientific
validation is `NOT_ESTABLISHED`, independent review and human disposition remain
`PENDING`, and AI advice remains null. #183 and the frozen graph evidence are
unaffected. A separate owner execution authorization is required for any CERN
pilot; this helper intentionally does not offer one.

These checks are integrity controls for trusted, reviewed local code, not an
OS/BLAS attestation, protection from hostile same-user processes, or a scientific
validation. The fixed coordinator launches one worker at a time; it is not a
general multi-host scheduler. Windows filesystem permission failures observed
in earlier qualification remain operational evidence: preserve them and HOLD,
do not suppress assertions or automatically retry.
