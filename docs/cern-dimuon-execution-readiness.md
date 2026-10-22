# CERN execution readiness — synthetic only

Run `python -B -m research.cern_dimuon_qualification.readiness --help`.
Supply a new output root, approved wheel/Windows runtime and offline wheelhouses.
Requires pinned Git objects/cached Linux image. No data/command/download/retry option.
Fixed order:
Windows → Linux → comparison → controls, with exclusive claims.

Workers check frozen CPython 3.12.15/NumPy 2.5.4, packages and interpreter/wheel/member
hashes, before/after analysis, using empty startup cache prefixes and `-B`.
Windows repeats Git identity; Linux uses the retained map/wheel, not independent
Git objects. Linux is offline/read-only with minimal mounts/bounded scratch.
Docker uses one environment. No CERN data, repository or secrets are mounted.
Only built-in synthetic data is used: 20,000 rows, 19,996 selected, four exclusions.
Both bundles and unchanged scalar/Decimal criteria are verified.

Both wheels, frozen evidence, #183 and all [criteria/caps](../research/cern_dimuon_qualification/protocol-v1.json)
stay unchanged. All sources/tests/locks/guide, complete compact index and four
16 KiB environment slots must fit 256 KiB before workers start. Every partial,
staging, transport, padding and inventory byte counts within the fixed 26 MiB
ledger. Cache directories stay empty; identified runtime/dependency caches and
historical reviews remain external, not hidden results. No aggregate archive.

Stages retain 300 s and 24 KiB logs. Gated Windows jobs/POSIX groups kill
descendants; nonblocking capture avoids pipe-reader locks. Vanished entries get
one complete rescan; permissions/repeated instability HOLD. Independent supervisor
HOLD and combined-failure receipts preserve diagnostics. Never reuse failed roots
or delete evidence; dispose only owned processes/containers.

Integrity checks are not OS/BLAS attestation, hostile-user isolation or scientific
validation. Qualification remains `NOT_EXECUTED`, pilot
ready false, validation `NOT_ESTABLISHED`, review/disposition `PENDING`, AI advice
null. A CERN pilot needs separate authorization. No deployment or release.
