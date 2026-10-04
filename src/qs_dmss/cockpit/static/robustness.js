/* Recorded-result island: no solver or AI endpoint is called here. */
(() => {
  "use strict";
  const root = document.querySelector("#recommendationRobustness");
  if (!root) return;
  const $ = (name) => root.querySelector(`[data-robustness-${name}]`);
  const metrics = {
    energy_drift: "Energy drift", norm_drift: "Norm drift",
    max_density: "Maximum density", elapsed_seconds: "Elapsed time",
  };
  const state = {source: null, result: null, displayed: null, generation: 0, sourcesGeneration: 0, timer: null, busy: false};
  const form = $("form");
  const chart = $("chart");
  function node(tag, value, className) {
    const element = document.createElement(tag);
    if (value !== undefined) element.textContent = String(value);
    if (className) element.className = className;
    return element;
  }
  function option(value, label) {
    const element = node("option", label); element.value = value; return element;
  }
  function status(message) { $("status").textContent = message; }
  async function api(path, payload) {
    const response = await fetch(path, payload ? {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload),
    } : {cache: "no-store"});
    const result = await response.json();
    if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Check the scoring profile and finite weight values.");
    return result;
  }
  function numberInput(name, label, value, {min = 0, max = 10000, optional = false} = {}) {
    const field = node("label", undefined, "rob-field");
    field.append(node("span", label));
    const input = document.createElement("input");
    Object.assign(input, {type: "number", name, step: "any", min: String(min), max: String(max), required: !optional});
    input.value = value ?? ""; field.append(input); return field;
  }
  function selectField(name, label, choices, value) {
    const field = node("label", undefined, "rob-field");
    const select = document.createElement("select"); select.name = name;
    choices.forEach(([key, text]) => select.append(option(key, text)));
    select.value = value; field.append(node("span", label), select); return field;
  }
  function variant(row) { return row.variant_label || row.name || row.run_id; }
  function editor(source, request = null) {
    const profile = request?.profile || source.comparison.decision.profile;
    const fields = $("fields"); fields.replaceChildren();
    fields.append(selectField("preferred", "Configuration to track", source.comparison.rows.map(row => [row.run_id, variant(row)]),
      request?.preferred_run_id || source.comparison.decision.recommended_run_id));
    const objective = profile.objective;
    fields.append(selectField("primary", "Primary objective", Object.entries(metrics), objective.primary_metric),
      selectField("goal", "Primary objective direction", [["minimize_abs", "Minimize absolute value"], ["minimize", "Minimize"], ["maximize", "Maximize"], ["target", "Closest to target"]], objective.goal),
      numberInput("target", "Target (required for target objective)", objective.target_value, {min: -1e12, max: 1e12, optional: true}),
      numberInput("bonus", "Additional primary-objective weight", profile.ranking.primary_metric_weight));
    Object.entries(metrics).forEach(([key, label]) => fields.append(numberInput(`weight_${key}`, `${label} weight`, profile.ranking.weights[key] ?? 0)));
    fields.append(selectField("sensitivity", "Weight to explore", Object.entries(metrics), request?.sensitivity_metric || "elapsed_seconds"),
      numberInput("maximum", "Sensitivity grid: 0 to this weight (17 points)", request ? Math.max(...request.weight_values) : 4));
    const constraints = $("constraints"); constraints.replaceChildren();
    const labels = {max_abs_energy_drift: "Maximum absolute energy drift", max_abs_norm_drift: "Maximum absolute norm drift", min_max_density: "Minimum terminal peak density", max_elapsed_seconds: "Maximum elapsed seconds"};
    Object.entries(labels).forEach(([key, label]) => constraints.append(numberInput(key, `${label} (blank = no limit)`, profile.constraints[key],
      {min: key === "min_max_density" ? -1e12 : 0, max: 1e12, optional: true})));
    const check = node("label", undefined, "rob-check");
    const input = document.createElement("input"); Object.assign(input, {name: "verification", type: "checkbox", checked: profile.constraints.require_verification !== false});
    check.append(input, node("span", "Require the verification state recorded at campaign creation")); constraints.append(check);
    form.querySelector(":scope > details").open = window.matchMedia("(min-width: 1101px)").matches;
    form.hidden = false;
  }
  function requestPayload() {
    if (!form.reportValidity()) throw new Error("Complete the finite scoring values before analyzing.");
    const values = new FormData(form);
    const base = structuredClone(state.source.comparison.decision.profile);
    base.objective.primary_metric = values.get("primary");
    base.objective.goal = values.get("goal");
    delete base.objective.target_value;
    if (values.get("target") !== "") base.objective.target_value = Number(values.get("target"));
    base.ranking.primary_metric_weight = Number(values.get("bonus"));
    Object.keys(metrics).forEach(key => { base.ranking.weights[key] = Number(values.get(`weight_${key}`)); });
    base.constraints = {require_verification: values.has("verification")};
    ["max_abs_energy_drift", "max_abs_norm_drift", "min_max_density", "max_elapsed_seconds"].forEach(key => {
      if (values.get(key) !== "") base.constraints[key] = Number(values.get(key));
    });
    const maximum = Number(values.get("maximum"));
    if (!(maximum > 0)) throw new Error("Choose a positive sensitivity-grid maximum.");
    return {
      experiment_id: state.source.experiment_id, source_fingerprint: state.source.source_fingerprint,
      preferred_run_id: values.get("preferred"), profile: base, sensitivity_metric: values.get("sensitivity"),
      weight_values: Array.from({length: 17}, (_, index) => maximum * index / 16),
    };
  }
  function invalidate(message = "Profile changed; recalculating recorded scores…") {
    state.generation += 1; state.result = null; $("save").disabled = true;
    $("download").hidden = true; $("output").setAttribute("aria-busy", "true");
    status(message);
  }
  function svg(tag, attributes, text) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = String(text);
    return element;
  }
  function drawChart() {
    chart.replaceChildren();
    if (!state.displayed) return;
    const rows = [...state.displayed.current.rows].sort((a, b) => a.decision_rank - b.decision_rank);
    const width = Math.max(260, Math.round(chart.clientWidth));
    const mobile = width < 500, lane = mobile ? 0 : Math.min(230, width * .3);
    const right = width - 52, top = 36, rowHeight = mobile ? 62 : 46;
    const height = top + rows.length * rowHeight + 26;
    const image = svg("svg", {viewBox: `0 0 ${width} ${height}`, width, height, role: "img", "aria-labelledby": "rob-chart-title rob-chart-desc"});
    image.append(svg("title", {id: "rob-chart-title"}, "Ranking under the current scoring profile"),
      svg("desc", {id: "rob-chart-desc"}, "Candidate-set normalized scores from zero to one. Qualified configurations rank before those failing constraints. Complete ranks and evidence values are in the table."));
    [0, .5, 1].forEach(value => {
      const x = lane + value * (right - lane);
      image.append(svg("line", {x1: x, x2: x, y1: top - 12, y2: height - 25, stroke: "#d7dfdb", "stroke-width": .75, "shape-rendering": "crispEdges"}),
        svg("text", {x, y: 14, "text-anchor": value === 0 ? "start" : "middle", fill: "#566d68", "font-size": 11}, value));
    });
    rows.forEach((row, index) => {
      const y = top + index * rowHeight;
      const preferred = row.run_id === state.displayed.request.preferred_run_id;
      image.append(svg("text", {x: 0, y: mobile ? y + 1 : y + 16, fill: "#173d37", "font-size": 12, "font-weight": preferred ? 700 : 500},
        `${row.decision_rank}. ${variant(row).slice(0, mobile ? 30 : 22)}${preferred ? " · tracked" : ""}${row.decision_qualified ? "" : " · fails"}`));
      const barY = mobile ? y + 13 : y + 3;
      image.append(svg("rect", {x: lane, y: barY, width: Math.max(0, row.decision_score * (right - lane)), height: 18,
        fill: preferred ? "#16766a" : "#7b8d87", opacity: row.decision_qualified ? 1 : .45}),
        svg("text", {x: right + 8, y: barY + 14, fill: "#173d37", "font-size": 12}, row.decision_score.toFixed(3)));
    });
    chart.append(image);
  }
  function table(headers, rows) {
    const table = node("table");
    const head = node("thead"), tr = node("tr");
    headers.forEach(label => { const th = node("th", label); th.scope = "col"; tr.append(th); });
    head.append(tr); const body = node("tbody");
    rows.forEach(values => { const row = node("tr"); values.forEach(value => row.append(node("td", value))); body.append(row); });
    table.append(head, body); return table;
  }
  function render(result, saved = false) {
    state.result = result; state.displayed = result; $("output").hidden = false; $("output").removeAttribute("aria-busy");
    const sensitivity = result.sensitivity;
    $("insight").textContent = `Tracked configuration wins ${sensitivity.preferred_win_count} of ${sensitivity.case_count} sampled profiles with constraints satisfied. Rank range: ${sensitivity.preferred_rank_range.join("–")}. ${sensitivity.qualification_fallback_count} profiles have no qualified configuration.`;
    const winner = result.current.rows.find(row => row.run_id === result.current.decision.recommended_run_id);
    $("winner").textContent = `Current recommendation: ${variant(winner)} · ${result.current.decision.status}. ${result.current.decision.qualified_run_count}/${result.current.rows.length} configurations satisfy constraints.${result.current.decision.status === "fallback" ? " Fallback only: no configuration meets every constraint." : ""}`;
    $("rows").replaceChildren(table(["Configuration", "Rank", "Score", "Constraints", "Energy drift", "Norm drift", "Peak density", "Seconds"],
      [...result.current.rows].sort((a, b) => a.decision_rank - b.decision_rank).map(row => [
        `${variant(row)}${row.run_id === result.request.preferred_run_id ? " · tracked" : ""}`, row.decision_rank,
        row.decision_score.toFixed(6), row.decision_qualified ? "Satisfied" : row.constraint_failures.join("; "),
        row.energy_drift.toExponential(3), row.norm_drift.toExponential(3), row.max_density.toPrecision(5), row.elapsed_seconds,
      ])));
    $("sensitivity-rows").replaceChildren(table([`${metrics[sensitivity.metric]} base weight`, "Recommended configuration", "Tracked rank", "Tracked score", "Qualification"],
      sensitivity.cases.map(item => [Number(item.weight.toPrecision(5)),
        variant(result.current.rows.find(row => row.run_id === item.recommended_run_id)), item.preferred_rank,
        item.preferred_score.toFixed(6), item.status === "fallback" ? "No qualified candidate — fallback" : "Qualified recommendation"])));
    $("provenance").replaceChildren(node("p", `Scoring: ${result.scoring_convention}; sensitivity: ${result.analysis_convention}.`),
      node("p", result.source.integrity_scope), node("p", result.source.verification_scope),
      node("p", `Energy convention: ${[...new Set(Object.values(result.source.energy_diagnostic_conventions))].join(", ")}${result.source.legacy_convention ? " — legacy semantics are unspecified; interpret cautiously." : ""}`),
      node("code", `Profile SHA-256: ${result.profile_sha256}`), node("code", `Source fingerprint: ${result.source.source_fingerprint}`),
      node("pre", JSON.stringify(result.profile, null, 2)), node("pre", JSON.stringify(result.source.sha256, null, 2)));
    $("boundary").textContent = result.claim_boundary;
    $("save").disabled = saved;
    if (saved) { $("download").href = result.urls.bundle; $("download").hidden = false; }
    drawChart(); status(saved ? `Saved immutable analysis ${result.analysis_id}. Evidence bundle ready.` : "Recorded scores updated. Original campaign evidence is unchanged.");
  }
  async function preview() {
    const generation = state.generation;
    try {
      const result = await api("/api/robustness/preview", requestPayload());
      if (generation === state.generation) render(result);
    } catch (error) { if (generation === state.generation) { $("output").removeAttribute("aria-busy"); status(`${error.message}${state.displayed ? " Showing the previous valid profile; saving is disabled." : ""}`); } }
  }
  async function openSource(id) {
    clearTimeout(state.timer);
    invalidate("Opening and checking recorded source evidence…");
    form.hidden = true; $("output").hidden = true; state.displayed = null; chart.replaceChildren();
    const generation = state.generation;
    try {
      const source = await api(`/api/robustness/sources/${encodeURIComponent(id)}`);
      if (generation !== state.generation) return;
      state.source = source; editor(source); await preview();
    } catch (error) { if (generation === state.generation) {
      $("output").removeAttribute("aria-busy"); status(error.message);
    } }
  }
  async function refreshSources(selected = null) {
    const generation = ++state.sourcesGeneration;
    try {
      const result = await api("/api/robustness/sources");
      if (generation !== state.sourcesGeneration) return;
      root.hidden = !result.available;
      if (!result.available) return;
      const select = $("source"); const value = selected || select.value;
      select.replaceChildren(option("", "Choose a completed campaign"));
      result.items.forEach(item => select.append(option(item.experiment_id, `${item.label} · ${item.run_count} configurations`)));
      if (result.items.some(item => item.experiment_id === value)) select.value = value;
      if (!select.value && state.source) {
        clearTimeout(state.timer); invalidate("The selected campaign is unavailable; choose another or reopen a saved analysis.");
        state.source = null; state.displayed = null; form.hidden = true; $("output").hidden = true;
      }
      if (!result.items.length) status("Run a Campaign Studio study first, then refresh recorded campaigns. No simulations are launched by this explorer.");
      if (selected && select.value) await openSource(select.value);
    } catch (error) { if (generation === state.sourcesGeneration) status(error.message); }
  }
  async function refreshSaved() {
    const result = await api("/api/robustness/analyses");
    $("saved").replaceChildren(option("", "Choose a saved analysis"));
    result.items.forEach(item => $("saved").append(option(item.analysis_id, `${item.created_at.slice(0, 19)} · ${item.source.label}`)));
  }
  form.addEventListener("submit", event => { event.preventDefault(); clearTimeout(state.timer); invalidate(); preview(); });
  form.addEventListener("input", () => {
    clearTimeout(state.timer); invalidate(); state.timer = setTimeout(preview, 350);
  });
  $("source").addEventListener("change", event => {
    state.sourcesGeneration += 1;
    clearTimeout(state.timer);
    if (event.target.value) openSource(event.target.value);
    else { invalidate("Choose a completed campaign."); state.source = null; state.displayed = null; form.hidden = true; $("output").hidden = true; }
  });
  $("refresh").addEventListener("click", () => refreshSources($("source").value || null));
  $("reset").addEventListener("click", () => { editor(state.source); invalidate(); preview(); });
  $("save").addEventListener("click", async () => {
    if (!state.result || state.busy || $("save").disabled) return;
    state.busy = true; $("save").disabled = true;
    const generation = state.generation, request = structuredClone(state.result.request);
    let saved = null;
    try {
      saved = await api("/api/robustness/analyses", request);
      if (generation === state.generation) render(saved, true);
      try { await refreshSaved(); }
      catch (error) { if (generation === state.generation) status(`Saved immutable analysis ${saved.analysis_id}. Evidence bundle ready. Saved list could not be refreshed: ${error.message}`); }
    } catch (error) { if (generation === state.generation) {
      $("save").disabled = Boolean(saved);
      status(saved ? `Saved immutable analysis ${saved.analysis_id}. Display update failed: ${error.message}` : error.message);
    } }
    finally { state.busy = false; }
  });
  $("saved").addEventListener("change", async event => {
    if (!event.target.value) return;
    state.sourcesGeneration += 1;
    clearTimeout(state.timer);
    invalidate("Checking retained analysis evidence…");
    const generation = state.generation;
    try {
      const result = await api(`/api/robustness/analyses/${encodeURIComponent(event.target.value)}`);
      if (generation !== state.generation) return;
      // Saved evidence can be inspected even if its original campaign is no longer present.
      state.source = {experiment_id: result.source.experiment_id, source_fingerprint: result.source.source_fingerprint,
        comparison: {rows: result.current.rows, decision: {profile: result.profile, recommended_run_id: result.request.preferred_run_id}}};
      editor(state.source, result.request); form.hidden = true; render(result, true);
    } catch (error) { if (generation === state.generation) {
      $("output").removeAttribute("aria-busy");
      status(`${error.message}${state.displayed ? " Showing the previous valid result; saving is disabled." : ""}`);
    } }
  });
  document.addEventListener("qs-dmss:experiment-selected", event => {
    if (event.detail?.kind === "campaign" && event.detail?.experiment_id) refreshSources(event.detail.experiment_id);
  });
  new ResizeObserver(drawChart).observe(chart);
  refreshSources().then(() => { if (!root.hidden) refreshSaved().catch(error => status(error.message)); });
})();
