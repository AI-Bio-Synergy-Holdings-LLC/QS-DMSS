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
  section("  function invalidate(", "  function svg("),
  section("  function render(", "  async function preview("),
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
  const $ = name => {
    if (!elements.has(name)) elements.set(name, {hidden: false, disabled: false, attrs: new Map(), children: [],
      addEventListener(event, callback) { this[event] = callback; },
      setAttribute(key, value) { this.attrs.set(key, value); },
      removeAttribute(key) { this.attrs.delete(key); },
      replaceChildren(...children) { this.children = children; },
      append(...children) { this.children.push(...children); },
    });
    return elements.get(name);
  };
  const state = {source: null, result: result(), displayed: result(), generation: 1,
    sourcesGeneration: 0, busy: false, timer: null};
  const context = vm.createContext({$, state, form: {hidden: false}, clearTimeout, structuredClone,
    metrics: {}, node: () => ({}), table: () => ({}), drawChart() {}, editor() {},
    option: (value, label) => ({value, label}),
    variant: row => row.variant_label || row.name || row.run_id,
    status(message) { messages.push(message); },
    async api(endpoint, payload) { requests.push({endpoint, payload}); return io(endpoint, payload); },
  });
  vm.runInContext(callbacks, context);
  return {$, state, requests, messages, context};
}
const listingError = "Robustness discovery exceeds the directory-entry resource limit";

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
