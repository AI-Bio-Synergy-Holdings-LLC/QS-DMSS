# CERN retention amendment version 3

V3 proposes a 64 KiB input-to-source transfer within 26 MiB. Input becomes
4,096,000 bytes; sources become 360,448 bytes. Other buckets, production
limits, numerical criteria, artifact pins, locks and failure retention stay fixed.
The frozen 2,639,302-byte input leaves 1,456,698 bytes headroom; no new CSV read
is implied. Two retained input copies still exceed the proposed input cap.

[The complete v3 protocol](../../research/cern_dimuon_qualification/amendments_v3/protocol-v3.json)
pins its v2 predecessor. Preserve v1/v2, all 27 legacy source files, both
indexes, both wheels and historical outputs. Old commands keep their revisions;
this data-only amendment activates no runtime policy.

New ceilings total 62,464 bytes for v3 policy, metadata inspection, tests,
source/qualification helpers, full contract/approval records, instructions and
indexes. Full reservations total 353,199 bytes, leaving 7,249 spare.
Keep at least 4,096 spare;
3,153 stays unassigned; no automatic borrowing.
These ceilings are not measured code sizes.

Count every dependency, fixture/generator and partial/staging/transport file. Index static
sources; hash the binding card separately. Keep four full environment slots,
old card/guide reservations and separate
v3 card/guide/approval slots. No inactive design file is an uncounted dependency.

Allocation approval is separate from implementation, integration and one-shot
execution approval. Later adoption needs exact source identities, complete
sizing, locked synthetic qualification and protected review. Coordinator,
transport/control and final inventory proofs remain deferred. No pilot,
deployment or release is authorized.

Qualification remains NOT_EXECUTED; pilot ready false; scientific validation
NOT_ESTABLISHED; scientific review/human disposition PENDING; AI advice null.
Recorded gate #183 and historical evidence remain unchanged.
