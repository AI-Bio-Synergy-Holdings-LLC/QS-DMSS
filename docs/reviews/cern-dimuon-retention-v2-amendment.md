# CERN retention amendment version 2

The owner approved a versioned 32 KiB transfer from input to sources within
the existing 26 MiB total. This amendment authorizes preparation and accounting
preflight only, not an adapter, pilot, deployment or release.

| Allocation in bytes | Preserved v1 | Version 2 |
| --- | ---: | ---: |
| Input | 4,194,304 | 4,161,536 |
| Sources and environment records | 262,144 | 294,912 |
| Total | 27,262,976 | 27,262,976 |

All other buckets, production limits, numerical criteria, candidate/input pins,
runtime locks, timeouts and failure-retention requirements remain unchanged.
The input size 2,639,302 comes from the frozen protocol, not a new CSV read.

[The full v2 protocol](../../research/cern_dimuon_qualification/amendments/protocol-v2.json)
identifies the raw and canonical hashes of its unchanged v1 predecessor.
Its separate namespace prevents automatic inclusion in v1's direct-file scan.
Existing helpers still select and enforce v1; v2 is not activated by this file.
Neither wheel is replaced or repinned. Equal version numbers do not establish
artifact identity.

The v2 accounting closure retains all 19 v1 files plus this note, the v2
protocol, its new regression file and .gitattributes. It counts the full index
and four unchanged 16 KiB environment slots. No source, test, partial output,
transport copy or failure receipt may be omitted to make a later packet fit.

The amendment itself consumes 3,695 additional source bytes. The approved
24 KiB planning allowance still covers new validation/adapter code, tests,
operative instructions/owner card and index growth. This note and .gitattributes
consume the instruction allowance; the new tests and index consume their
respective allowances. Future code, tests and the owner card are not yet sized.
With all 24 KiB reserved, the conditional remaining source space is 4,497 bytes.
This is a capacity model, not proof that an implementation or its results fit.

Any future adoption needs exact controller/source identities, complete peak
accounting, synthetic qualification, protected review and separate owner
authorization. Retain v1 and historical receipts without rewriting them.
Qualification remains NOT_EXECUTED; pilot ready false; validation
NOT_ESTABLISHED; scientific review/human disposition PENDING; AI advice null.
Gate #183 remains open. Allocation approval establishes no scientific validation.
