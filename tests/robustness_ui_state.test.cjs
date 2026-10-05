/* Actual UI callbacks under a minimal DOM/I/O shim. No browser or solver. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../src/qs_dmss/cockpit/static/robustness.js"), "utf8");
function section(start, end) {
  const begin = source.indexOf(start), finish = source.indexOf(end, begin);
  assert(begin >= 0 && finish > begin, `Missing UI test seam: ${start}`);
  return source.slice(begin, finish);
}
const callbacks = [
  section("  function variant(", "  function editor("),
  section("  function invalidate(", "  function svg("),
  section("  function svg(", "  function render("),
  section("  function render(", "  async function preview("),
  section("  async function preview(", "  async function openSource("),
  section("  async function openSource(", "  async function refreshSources("),
  section("  async function refreshSaved(", "  form.addEventListener(\"submit\""),
  section("  $(\"save\").addEventListener(", "  document.addEventListener(\"qs-dmss:experiment-selected\""),
].join("\n");

function result(id = "saved-a") {
  const row = {run_id: "run-a", decision_rank: 1, decision_score: 1, decision_qualified: true,
    energy_drift: .01, norm_drift: .001, max_density: 1, elapsed_seconds: 1};
  return {analysis_id: id, created_at: "2026-10-04T00:00:00Z",
    request: {preferred_run_id: row.run_id, profile: {}}, profile: {},
    current: {rows: [row], decision: {recommended_run_id: row.run_id, status: "qualified", qualified_run_count: 1}},
    sensitivity: {preferred_win_count: 1, case_count: 1, preferred_rank_range: [1, 1], qualification_fallback_count: 0, cases: []},
    source: {label: "Campaign", experiment_id: "campaign-a", source_fingerprint: "pin",
      energy_diagnostic_conventions: {"run-a": "fft_cell_measure_v2"}, sha256: {}},
    urls: {bundle: `/api/robustness/analyses/${id}/bundle`}};
}
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
}
function harness(io) {
  const elements = new Map(), requests = [], messages = [];
  const element = () => ({hidden: false, disabled: false, attrs: new Map(), children: [], clientWidth: 800,
    addEventListener(event, callback) { this[event] = callback; },
    setAttribute(key, value) { this.attrs.set(key, value); },
    removeAttribute(key) { this.attrs.delete(key); },
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
  });
  const $ = name => {
    if (!elements.has(name)) elements.set(name, element());
    return elements.get(name);
  };
  const state = {source: null, result: result(), displayed: result(), generation: 1,
    sourcesGeneration: 0, savedGeneration: 0, busy: false, timer: null};
  const context = vm.createContext({$, state, form: {hidden: false}, chart: $("chart"), clearTimeout, structuredClone,
    metrics: {}, node(tag, value) { const item = element(); item.tag = tag; if (value !== undefined) item.textContent = String(value); return item; },
    document: {createElementNS: () => element()}, editor() {}, requestPayload: () => result().request,
    option: (value, label) => ({value, label}),
    status(message) { messages.push(message); },
    async api(endpoint, payload) { requests.push({endpoint, payload}); return io(endpoint, payload); },
  });
  vm.runInContext(callbacks, context);
  return {$, state, requests, messages, context};
}
const listingError = "Robustness discovery exceeds the directory-entry resource limit";

const labelCases = [
  [{variant_label: "Interaction=0", name: "Run name"}, "Interaction=0"],
  [{variant_label: "  valid label  ", name: "Run name"}, "  valid label  "],
  [{variant_label: "", name: "Run name"}, "Run name"],
  [{variant_label: " \t ", name: "Run name"}, "Run name"],
  [{variant_label: null, name: "Run name"}, "Run name"],
  [{variant_label: {label: "object"}, name: "Run name"}, "Run name"],
  [{variant_label: ["array"], name: "Run name"}, "Run name"],
  [{variant_label: 42, name: "Run name"}, "Run name"],
  [{variant_label: true, name: "Run name"}, "Run name"],
  [{variant_label: {label: "object"}, name: ["array"]}, "run-a"],
  [{variant_label: false, name: 7}, "run-a"],
  [{variant_label: null, name: null}, "run-a"],
  [{variant_label: "λ <img src=x onerror=alert(1)> 🧪", name: "Run name"}, "λ <img src=x onerror=alert(1)> 🧪"],
  [{}, "run-a"],
];
for (const [index, [labels, expected]] of labelCases.entries()) {
  test(`display label ${index} renders actual SVG/table without altering recorded fields`, () => {
    const h = harness(async () => result());
    const analysis = result(); Object.assign(analysis.current.rows[0], labels);
    const before = JSON.stringify(analysis);
    for (const width of [800, 320]) {
      h.$("chart").clientWidth = width;
      assert.equal(h.context.variant(analysis.current.rows[0]), expected);
      h.context.render(analysis);
      assert.equal(h.$("save").disabled, false);
      assert.equal(h.$("chart").children.length, 1);
      assert.match(h.$("winner").textContent, /Current recommendation:/);
      assert.equal(h.$("rows").children[0].children[1].children[0].children[0].textContent, `${expected} · tracked`);
    }
    assert.equal(JSON.stringify(analysis), before);
  });
}

test("Save and download remain gated until complete chart rendering", () => {
  const h = harness(async () => result());
  h.$("save").disabled = false; h.$("download").hidden = false;
  h.context.drawChart = () => {
    assert.equal(h.$("save").disabled, true);
    assert.equal(h.$("download").hidden, true);
  };
  h.context.render(result());
  assert.equal(h.$("save").disabled, false);
  h.context.render(result(), true);
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.$("download").hidden, false);
});

for (const saved of [false, true]) {
  test(`failed ${saved ? "saved" : "preview"} render clears partial state and disables actions`, async () => {
    const h = harness(async () => result());
    h.$("save").disabled = false; h.$("download").hidden = false;
    h.context.drawChart = () => { throw new Error("Display failed"); };
    assert.throws(() => h.context.render(result(), saved), /Display failed/);
    assert.equal(h.$("save").disabled, true);
    assert.equal(h.$("download").hidden, true);
    assert.equal(h.$("output").hidden, true);
    assert.equal(h.$("output").attrs.has("aria-busy"), false);
    assert.equal(h.state.result, null);
    assert.equal(h.state.displayed, null);
    h.context.drawChart = () => {};
    h.context.render(result(), saved);
    assert.equal(h.$("output").hidden, false);
    assert.equal(h.$("save").disabled, saved);
  });
}

test("preview rendering failure cannot advertise a previous valid profile or issue Save", async () => {
  const h = harness(async () => result());
  h.context.drawChart = () => { throw new Error("Display failed"); };
  await h.context.preview();
  assert.equal(h.messages.at(-1), "Display failed");
  await h.$("save").click();
  assert.equal(h.requests.filter(item => item.endpoint === "/api/robustness/analyses").length, 0);
});

test("failed saved editor does not replace the active source or expose editable partial fields", async () => {
  const h = harness(async () => result());
  const original = {experiment_id: "healthy-source"}; h.state.source = original;
  h.context.editor = () => { throw new Error("Invalid saved profile"); };
  await h.$("saved").change({target: {value: "saved-a"}});
  assert.equal(h.state.source, original);
  assert.equal(h.context.form.hidden, true);
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.$("download").hidden, true);
});

test("older saved-list success cannot replace a newer post-save list", async () => {
  const old = deferred(), newer = deferred(); let count = 0;
  const h = harness(() => ++count === 1 ? old.promise : newer.promise);
  const first = h.context.refreshSaved(), second = h.context.refreshSaved();
  newer.resolve({items: [result("newly-saved")]}); await second;
  old.resolve({items: []}); await first;
  assert.deepEqual(h.$("saved").children.map(item => item.value), ["", "newly-saved"]);
});

test("older saved-list failure cannot propagate after a newer request starts", async () => {
  const old = deferred(), newer = deferred(); let count = 0;
  const h = harness(() => ++count === 1 ? old.promise : newer.promise);
  const first = h.context.refreshSaved(), second = h.context.refreshSaved();
  old.reject(new Error("Older list failed")); await first;
  newer.resolve({items: [result("newly-saved")]}); await second;
  assert.equal(h.$("saved").children[1].value, "newly-saved");
});

test("latest saved-list failure still propagates and older success stays ignored", async () => {
  const old = deferred(), newer = deferred(); let count = 0;
  const h = harness(() => ++count === 1 ? old.promise : newer.promise);
  const first = h.context.refreshSaved(), second = h.context.refreshSaved();
  newer.reject(new Error("Latest list failed"));
  await assert.rejects(second, /Latest list failed/);
  old.resolve({items: [result("stale-saved")]}); await first;
  assert.equal(h.$("saved").children.length, 0);
});

test("late initial list failure cannot replace completed save status or download", async () => {
  const old = deferred(); let lists = 0;
  const h = harness(async (endpoint, payload) => {
    if (payload) return result("newly-saved");
    return ++lists === 1 ? old.promise : {items: [result("newly-saved")]};
  });
  const initial = h.context.refreshSaved().catch(error => h.context.status(error.message));
  await h.$("save").click();
  const successfulStatus = h.messages.at(-1);
  old.reject(new Error("Older initial list failed")); await initial;
  assert.equal(h.messages.at(-1), successfulStatus);
  assert.match(successfulStatus, /Saved immutable analysis newly-saved/);
  assert.equal(h.$("download").href, result("newly-saved").urls.bundle);
  assert.equal(h.$("save").disabled, true);
});

test("rejected source clears busy state without exposing editor, stale result or save", async () => {
  const h = harness(async () => { throw new Error("Invalid recorded evidence"); });
  await h.context.openSource("campaign-a");
  assert.equal(h.$("output").attrs.has("aria-busy"), false);
  assert.equal(h.$("output").hidden, true);
  assert.equal(h.context.form.hidden, true);
  assert.equal(h.state.displayed, null);
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.$("download").hidden, true);
  assert.equal(h.messages.at(-1), "Invalid recorded evidence");
});

test("stale rejected source cannot clear a newer request's busy state", async () => {
  const pending = deferred();
  const h = harness(() => pending.promise);
  const action = h.context.openSource("campaign-a");
  h.context.invalidate("Newer source is loading");
  pending.reject(new Error("Old source failed")); await action;
  assert.equal(h.$("output").attrs.get("aria-busy"), "true");
  assert.equal(h.messages.at(-1), "Newer source is loading");
});

test("successful immutable save remains successful when selector refresh fails", async () => {
  const h = harness(async (endpoint, payload) => { if (payload) return result(); throw new Error(listingError); });
  await h.$("save").click();
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.$("download").hidden, false);
  assert.equal(h.$("download").href, result().urls.bundle);
  assert.equal(h.state.displayed.analysis_id, "saved-a");
  assert.match(h.messages.at(-1), /Saved immutable analysis saved-a/);
  assert.match(h.messages.at(-1), /Saved list could not be refreshed/);
  await h.$("save").click(); // Even programmatic repeat must not issue a second POST.
  assert.equal(h.requests.filter(item => item.payload).length, 1);
});
test("successful save and selector refresh retain normal state", async () => {
  const h = harness(async (endpoint, payload) => payload ? result() : {items: [result()]});
  await h.$("save").click();
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.$("saved").children[1].value, "saved-a");
  assert.match(h.messages.at(-1), /Saved immutable analysis saved-a/);
  assert.equal(h.state.busy, false);
});
test("a display exception after successful POST must not permit another save", async () => {
  const h = harness(async () => result());
  h.context.drawChart = () => { throw new Error("Display failed"); };
  await h.$("save").click();
  assert.equal(h.$("save").disabled, true);
  assert.match(h.messages.at(-1), /Saved immutable analysis saved-a.*Display update failed/);
  await h.$("save").click();
  assert.equal(h.requests.filter(item => item.payload).length, 1);
});
test("a failed POST remains retryable and does not expose a download", async () => {
  const h = harness(async () => { throw new Error("Save rejected"); });
  h.$("download").hidden = true;
  await h.$("save").click();
  assert.equal(h.$("save").disabled, false);
  assert.equal(h.$("download").hidden, true);
  assert.equal(h.messages.at(-1), "Save rejected");
  assert.equal(h.requests.length, 1);
  assert.equal(h.state.busy, false);
});
test("a stale POST error cannot re-enable Save or replace newer state", async () => {
  const pending = deferred();
  const h = harness(() => pending.promise);
  const action = h.$("save").click();
  h.context.invalidate("Newer profile is loading");
  pending.reject(new Error("Old save failed")); await action;
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.messages.at(-1), "Newer profile is loading");
});
test("a stale selector refresh error cannot overwrite a newer profile", async () => {
  const pending = deferred(), entered = deferred();
  const h = harness(async (endpoint, payload) => {
    if (payload) return result(); entered.resolve(); return pending.promise;
  });
  const action = h.$("save").click(); await entered.promise;
  h.context.invalidate("Newer profile is loading");
  pending.reject(new Error(listingError)); await action;
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.$("download").hidden, true);
  assert.equal(h.messages.at(-1), "Newer profile is loading");
  assert.equal(h.$("output").attrs.get("aria-busy"), "true");
});
test("failed saved reopen clears busy state and labels the previous result", async () => {
  const h = harness(async () => { throw new Error("Invalid retained evidence"); });
  await h.$("saved").change({target: {value: "saved-a"}});
  assert.equal(h.$("output").attrs.has("aria-busy"), false);
  assert.equal(h.$("output").hidden, false);
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.$("download").hidden, true);
  assert.match(h.messages.at(-1), /Invalid retained evidence/);
  assert.match(h.messages.at(-1), /previous valid result; saving is disabled/);
});
test("stale reopen failure must not clear a newer request's busy state", async () => {
  const pending = deferred();
  const h = harness(() => pending.promise);
  const action = h.$("saved").change({target: {value: "saved-a"}});
  h.context.invalidate("Newer analysis is loading");
  pending.reject(new Error("Old reopen failed")); await action;
  assert.equal(h.$("output").attrs.get("aria-busy"), "true");
  assert.equal(h.messages.at(-1), "Newer analysis is loading");
});
test("successful saved reopen clears busy state and stays read-only", async () => {
  const h = harness(async () => result());
  await h.$("saved").change({target: {value: "saved-a"}});
  assert.equal(h.$("output").attrs.has("aria-busy"), false);
  assert.equal(h.$("save").disabled, true);
  assert.equal(h.$("download").hidden, false);
  assert.equal(h.context.form.hidden, true);
});
for (const blocked of ["empty", "busy", "already-saved"]) {
  test(`${blocked} state cannot issue a save request`, async () => {
    const h = harness(async () => result());
    if (blocked === "empty") h.state.result = null;
    if (blocked === "busy") h.state.busy = true;
    if (blocked === "already-saved") h.$("save").disabled = true;
    await h.$("save").click(); assert.equal(h.requests.length, 0);
  });
}
