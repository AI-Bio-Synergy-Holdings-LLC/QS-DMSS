import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import crypto from "node:crypto";
import {
  validateRecordedData,
  validateManifest,
  parseState,
  stateHash,
  displayNumber,
  CASE_IDS,
} from "../site/challenges/sc-graph-001/core.mjs";
import { DATA_SHA256 } from "../site/challenges/sc-graph-001/config.mjs";
import { readBoundedBytes } from "../site/challenges/sc-graph-001/loader.mjs";
const bytes = fs.readFileSync(
  new URL("../site/challenges/sc-graph-001/data.json", import.meta.url),
);
const original = JSON.parse(bytes);
const fresh = () => structuredClone(original);
const manifest = JSON.parse(
  fs.readFileSync(
    new URL("../site/challenges/sc-graph-001/manifest.json", import.meta.url),
  ),
);
test("provenance manifest passes exact identity contract", () =>
  assert.equal(
    validateManifest(manifest, DATA_SHA256, bytes.length),
    manifest,
  ));
for (const change of [
  (m) => (m.candidate_source = "main"),
  (m) => (m.source_measurements_member_sha256 = "wrong"),
  (m) => (m.scientific_status = "VALIDATED"),
  (m) => (m.independent_review = "COMPLETE"),
  (m) => m.selected_cases.reverse(),
  (m) => m.data_bytes++,
])
  test(`manifest mutation refused ${change}`, () => {
    const m = structuredClone(manifest);
    change(m);
    assert.throws(() => validateManifest(m, DATA_SHA256, bytes.length));
  });
for (const field of ["origin", "control_scope", "presentation_scope"]) {
  test(`missing manifest scope refused: ${field}`, () => {
    const m = structuredClone(manifest);
    delete m[field];
    assert.throws(() => validateManifest(m, DATA_SHA256, bytes.length));
  });
  for (const value of [null, 42, {}, [], "Live solver/control execution enabled"])
    test(`manifest scope mutation refused: ${field} = ${JSON.stringify(value)}`, () => {
      const m = structuredClone(manifest);
      m[field] = value;
      assert.throws(() => validateManifest(m, DATA_SHA256, bytes.length));
    });
}
for (const change of [
  (d) => (d.acceptance_limits.projector_error_max = 1),
  (d) => (d.full_registered_graph_cases = 4),
])
  test(`claim scope mutation refused ${change}`, () => {
    const d = fresh();
    change(d);
    assert.throws(() => validateRecordedData(d));
  });
test("presentation bytes and manifest match pinned digest", () => {
  assert.equal(
    crypto.createHash("sha256").update(bytes).digest("hex"),
    DATA_SHA256,
  );
  const m = JSON.parse(
    fs.readFileSync(
      new URL("../site/challenges/sc-graph-001/manifest.json", import.meta.url),
    ),
  );
  assert.equal(m.data_sha256, DATA_SHA256);
  assert.equal(m.data_bytes, bytes.length);
});
test("all four recorded cases meet shape and identity contract", () => {
  assert.equal(validateRecordedData(fresh()).cases.length, 4);
});
test("no route means approved Dirichlet default", () => {
  assert.deepEqual(parseState("", original), {
    caseId: "graph_07",
    view: "matrix",
    source: "candidate",
    node: 1,
  });
});
for (const id of CASE_IDS)
  for (const view of ["matrix", "spectrum"])
    for (const source of ["candidate", "reference"])
      test(`URL round trip ${id}/${view}/${source}`, () => {
        const s = { caseId: id, view, source, node: 0 };
        assert.deepEqual(parseState(stateHash(s), original), s);
      });
for (const hash of [
  "#case=graph_00",
  "#case=graph_07&view=solver",
  "#case=graph_07&source=wolfram",
  "#case=graph_07&node=-1",
  "#case=graph_07&node=6",
  "#case=graph_07&node=1.5",
  "#case=graph_07&case=graph_04",
  "#case=graph_07&file=other",
])
  test(`unsupported state refused: ${hash}`, () =>
    assert.throws(() => parseState(hash, original)));
for (const change of [
  (d) => (d.source_commit = "main"),
  (d) => (d.source_packet_sha256 = "wrong"),
  (d) => (d.scientific_assessment.status = "VALIDATED"),
  (d) => (d.scientific_assessment.independent_review = "COMPLETE"),
  (d) => d.cases.pop(),
  (d) => (d.cases[0].length = 2),
  (d) => (d.cases[0].candidate.spectrum[0] = Infinity),
  (d) => (d.cases[1].reference.active[0] = true),
  (d) =>
    (d.cases[1].record.negative_controls.induced_laplacian_rejected = false),
])
  test(`invalid recorded-data mutation refused ${change}`, () => {
    const d = fresh();
    change(d);
    assert.throws(() => validateRecordedData(d));
  });
test("tiny and negative roundoff values remain visible", () => {
  assert.notEqual(displayNumber(-2.220446049250313e-15), "0");
  assert.equal(displayNumber(0), "0");
  assert.throws(() => displayNumber(NaN));
});
test("bounded loader keeps exact bytes including UTF-8", async () => {
  const raw = new TextEncoder().encode("recorded λ");
  assert.deepEqual(await readBoundedBytes(new Response(raw), raw.length), raw);
});
test("bounded loader rejects declared oversize before reading", async () => {
  let cancelled = false;
  const body = new ReadableStream({
    cancel() {
      cancelled = true;
    },
  });
  await assert.rejects(
    readBoundedBytes(
      new Response(body, { headers: { "content-length": "100001" } }),
      100000,
    ),
  );
  assert.equal(cancelled, true);
});
for (const header of ["-1", "1.5", "unknown"])
  test(`invalid advertised length refused: ${header}`, async () => {
    await assert.rejects(
      readBoundedBytes(
        new Response("recorded", { headers: { "content-length": header } }),
        100,
      ),
    );
  });
test("streaming overflow refused without an advertised length", async () => {
  let cancelled = false;
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new Uint8Array(8));
      controller.enqueue(new Uint8Array(8));
    },
    cancel() {
      cancelled = true;
    },
  });
  await assert.rejects(readBoundedBytes(new Response(stream), 10));
  assert.equal(cancelled, true);
});
test("exact cap and split chunks accepted", async () => {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new Uint8Array([1, 2]));
      controller.enqueue(new Uint8Array([3, 4]));
      controller.close();
    },
  });
  assert.deepEqual(
    await readBoundedBytes(new Response(stream), 4),
    new Uint8Array([1, 2, 3, 4]),
  );
});
test("null body and invalid caller limits refused", async () => {
  await assert.rejects(readBoundedBytes(new Response(null), 10));
  for (const limit of [0, -1, Infinity, 1.5])
    await assert.rejects(readBoundedBytes(new Response("x"), limit));
});
test("transport failures remain failures", async () => {
  const stream = new ReadableStream({
    start(controller) {
      controller.error(new Error("transport failed"));
    },
  });
  await assert.rejects(readBoundedBytes(new Response(stream), 10));
});
