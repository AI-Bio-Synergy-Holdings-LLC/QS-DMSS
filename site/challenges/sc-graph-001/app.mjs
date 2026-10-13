import {
  validateRecordedData,
  validateManifest,
  parseState,
  stateHash,
  displayNumber,
} from "./core.mjs";
import { DATA_SHA256, MAX_DATA_BYTES } from "./config.mjs";
import { readBoundedBytes } from "./loader.mjs";

const $ = (id) => document.getElementById(id);
const svgNS = "http://www.w3.org/2000/svg";
let data = null,
  state = null,
  focusNode = null,
  loadId = 0;
let activeController = null;
function el(tag, text, attrs = {}) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}
function svg(tag, attrs = {}, text) {
  const e = document.createElementNS(svgNS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  if (text !== undefined) e.textContent = text;
  return e;
}
function unavailable(message, invalid = false) {
  $("view-link-output").hidden = true;
  $("explorer").hidden = true;
  $("unavailable").hidden = false;
  $("unavailable-reason").textContent = message;
  $("load-status").textContent =
    "Recorded view unavailable. No new numerical outcome is assigned.";
  $("invalid-reset").hidden = !invalid;
  for (const id of [
    "graph",
    "matrix",
    "spectrum",
    "spectrum-table",
    "errors",
    "node-detail",
    "vertices-table",
    "case-pointers",
  ])
    $(id).replaceChildren();
}
function choose(patch) {
  const next = { ...state, ...patch };
  if (patch.caseId)
    next.node = data.cases.find(
      (c) => c.id === patch.caseId,
    ).reference.active[0];
  const hash = stateHash(next);
  if (location.hash === hash) render();
  else location.hash = hash;
}
function current() {
  return data.cases.find((c) => c.id === state.caseId);
}

function drawGraph(c) {
  const host = $("graph"),
    width = Math.max(260, Math.round(host.clientWidth)),
    height = width < 420 ? 280 : 320;
  const extent = c.level === 1 ? 2 : 4,
    pad = 42,
    scale = Math.min(
      (width - 2 * pad) / extent,
      (height - 2 * pad) / ((extent * Math.sqrt(3)) / 2),
    );
  const offsetX = (width - scale * extent) / 2,
    offsetY = (height - (scale * extent * Math.sqrt(3)) / 2) / 2;
  const pos = ([i, j]) => [
    offsetX + (i + j / 2) * scale,
    height - offsetY - ((j * Math.sqrt(3)) / 2) * scale,
  ];
  const active = new Set(c.reference.active),
    boundaries = new Set(c.reference.boundary);
  const root = svg("svg", {
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    role: "group",
    "aria-labelledby": "graph-svg-title graph-svg-desc",
  });
  root.append(
    svg(
      "title",
      { id: "graph-svg-title" },
      `Recorded reference graph: level ${c.level}, ${c.boundary}`,
    ),
  );
  root.append(
    svg(
      "desc",
      { id: "graph-svg-desc" },
      `${c.reference.vertices.length} full vertices, ${active.size} active. Select a numbered vertex with click, tap, Enter or Space. Positions illustrate integer lattice coordinates, not physical distances.`,
    ),
  );
  for (const [a, b] of c.reference.edges) {
    const [x1, y1] = pos(c.reference.vertices[a]);
    const [x2, y2] = pos(c.reference.vertices[b]);
    root.append(
      svg("line", {
        x1,
        y1,
        x2,
        y2,
        class: active.has(a) && active.has(b) ? "edge" : "edge ghost",
      }),
    );
  }
  c.reference.vertices.forEach((v, id) => {
    const [x, y] = pos(v);
    const isBoundary = boundaries.has(id),
      included = active.has(id);
    const group = svg("g", {
      transform: `translate(${x} ${y})`,
      role: "button",
      tabindex: 0,
      "data-node": id,
      "aria-pressed": id === state.node ? "true" : "false",
      "aria-label": `Vertex ${id}: ${isBoundary ? "boundary" : "interior"}, ${included ? "active" : "excluded"}`,
      class: [
        "node",
        isBoundary ? "boundary" : "",
        !included ? "excluded" : "",
        id === state.node ? "selected" : "",
      ].join(" "),
    });
    group.append(svg("circle", { r: 22, class: "hit" }));
    group.append(svg("circle", { r: 19, class: "selection" }));
    group.append(
      isBoundary
        ? svg("path", { d: "M 0 -10 L 10 0 L 0 10 L -10 0 Z", class: "mark" })
        : svg("circle", { r: 8, class: "mark" }),
    );
    group.append(svg("text", { y: 33 }, String(id)));
    const select = () => {
      focusNode = id;
      choose({ node: id });
    };
    group.addEventListener("click", select);
    group.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        select();
      }
    });
    root.append(group);
  });
  host.replaceChildren(root);
  if (focusNode !== null) {
    host.querySelector(`[data-node="${focusNode}"]`)?.focus();
    focusNode = null;
  }
}

function makeTable(caption, headers, rows, large = false) {
  const table = el("table", undefined, { class: large ? "large" : "" });
  table.append(el("caption", caption));
  const head = el("thead"),
    hr = el("tr");
  headers.forEach((h) => hr.append(el("th", h, { scope: "col" })));
  head.append(hr);
  table.append(head);
  const body = el("tbody");
  rows.forEach((row) => {
    const tr = el("tr");
    row.forEach((cell, i) => {
      const spec = typeof cell === "object" ? cell : { text: cell };
      const node = el(
        i === 0 ? "th" : "td",
        spec.text,
        i === 0 ? { scope: "row" } : {},
      );
      if (spec.class) node.className = spec.class;
      if (spec.raw !== undefined) node.setAttribute("title", String(spec.raw));
      tr.append(node);
    });
    body.append(tr);
  });
  table.append(body);
  return table;
}
function renderNode(c) {
  const id = state.node,
    activeIndex = c.reference.active.indexOf(id),
    detail = $("node-detail");
  detail.replaceChildren(
    el("strong", `Selected full vertex ${id}`),
    el(
      "span",
      `Lattice [${c.reference.vertices[id].join(", ")}] · ${c.reference.boundary.includes(id) ? "boundary" : "interior"}`,
    ),
  );
  detail.append(el("br"));
  if (activeIndex < 0)
    detail.append(
      el(
        "span",
        "Excluded from the Dirichlet active space. No active matrix row or mass entry is assigned.",
      ),
    );
  else
    detail.append(
      el(
        "span",
        `Active index ${activeIndex} · mass weight: candidate ${displayNumber(c.candidate.mass[activeIndex])}, reference ${displayNumber(c.reference.mass[activeIndex])}. Weights are copied without renormalization.`,
      ),
    );
  const rows = c.reference.vertices.map((v, id) => {
    const i = c.reference.active.indexOf(id);
    return [
      String(id),
      `[${v.join(", ")}]`,
      i < 0 ? "Excluded" : String(i),
      i < 0 ? "—" : displayNumber(c.candidate.mass[i]),
      i < 0 ? "—" : displayNumber(c.reference.mass[i]),
    ];
  });
  $("vertices-table").replaceChildren(
    makeTable(
      "Recorded full/active mapping and mass weights",
      ["Full ID", "Lattice", "Active index", "Candidate M", "Reference M"],
      rows,
    ),
  );
}
function renderMatrix(c) {
  const ids = c.reference.active,
    source = c[state.source],
    matrix = source.stiffness;
  const headers = ["Full ID", ...ids.map(String)];
  const rows = matrix.map((row, i) => [
    {
      text: String(ids[i]),
      class: ids[i] === state.node ? "selected-cell" : "",
    },
    ...row.map((v, j) => ({
      text: displayNumber(v),
      raw: v,
      class: [
        i === j ? "diagonal" : "",
        ids[i] === state.node || ids[j] === state.node ? "selected-cell" : "",
      ].join(" "),
    })),
  ]);
  $("matrix").replaceChildren(
    makeTable(
      `${state.source === "candidate" ? "Candidate" : "Reference"} stiffness K · ${ids.length}×${ids.length}`,
      headers,
      rows,
      ids.length > 6,
    ),
  );
  $("matrix-note").textContent =
    c.boundary === "dirichlet"
      ? "Principal restriction: boundary unknowns are excluded, while retained full-matrix entries are kept. Diagonal shading is an annotation, not a new calculation."
      : "Neumann retains the full graph and all vertex unknowns. Select a boundary vertex to inspect its recorded mass weight.";
}
function drawSpectrum(c) {
  const host = $("spectrum"),
    width = Math.max(260, Math.round(host.clientWidth)),
    n = c.reference.spectrum.length,
    height = 70 + 28 * n;
  const vals = [...c.reference.spectrum, ...c.candidate.spectrum];
  const low = Math.min(0, ...vals),
    high = Math.max(...vals),
    range = high - low || 1;
  const left = 43,
    right = width - 35,
    x = (v) => left + ((v - low) / range) * (right - left);
  const root = svg("svg", {
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    role: "img",
    "aria-label":
      "Recorded candidate and reference generalized eigenvalues. Values and exact numbers are available in the following table.",
  });
  for (let i = 0; i <= 4; i++) {
    const value = low + (range * i) / 4;
    root.append(
      svg("line", {
        x1: x(value),
        x2: x(value),
        y1: 29,
        y2: height - 32,
        class: "edge",
      }),
    );
    root.append(
      svg(
        "text",
        {
          x: x(value),
          y: height - 12,
          "text-anchor": "middle",
          "font-size": 12,
          fill: "#536763",
        },
        displayNumber(value),
      ),
    );
  }
  c.reference.spectrum.forEach((v, i) => {
    const y = 42 + 28 * i;
    root.append(
      svg(
        "text",
        {
          x: 20,
          y: y + 4,
          "text-anchor": "middle",
          "font-size": 12,
          fill: "#536763",
        },
        String(i),
      ),
    );
    root.append(
      svg("circle", {
        cx: x(v),
        cy: y,
        r: 7,
        fill: "#fff",
        stroke: "#b14f16",
        "stroke-width": 2,
      }),
    );
    root.append(
      svg("circle", {
        cx: x(c.candidate.spectrum[i]),
        cy: y,
        r: 3.5,
        fill: "#15393d",
      }),
    );
  });
  host.replaceChildren(root);
  $("spectrum-table").replaceChildren(
    makeTable(
      "Candidate: filled dot · reference: open ring. Degeneracies repeat values; individual eigenvectors are not canonical.",
      ["Ordered index", "Candidate λ (raw)", "Reference λ (raw)"],
      c.reference.spectrum.map((v, i) => [
        String(i),
        String(c.candidate.spectrum[i]),
        String(v),
      ]),
    ),
  );
}
function renderComparison(c) {
  const dl = $("errors");
  dl.replaceChildren();
  const items = [
    [
      "Scaled matrix error",
      c.record.matrix_error,
      data.acceptance_limits.scaled_matrix_error_max,
    ],
    [
      "Scaled spectrum error",
      c.record.spectrum_error,
      data.acceptance_limits.scaled_spectrum_error_max,
    ],
    [
      "Projector error",
      c.record.projector_error,
      data.acceptance_limits.projector_error_max,
    ],
    ["Tail error", c.record.tail_error, data.acceptance_limits.tail_error_max],
  ];
  for (const [label, value, limit] of items)
    dl.append(
      el("dt", label),
      el(
        "dd",
        `${displayNumber(value)} · registered bound ${displayNumber(limit)}`,
      ),
    );
  $("control-note").textContent =
    c.boundary === "dirichlet"
      ? "Retained seeded control: induced-subgraph Laplacian rejected. The record stores a rejection flag, not a new reviewer counterexample."
      : "Retained seeded control: uniform mass rejected. The record stores a rejection flag, not a new reviewer counterexample.";
}
function render() {
  $("view-link-output").hidden = true;
  if (!data) return;
  try {
    state = parseState(location.hash, data);
  } catch {
    unavailable(
      "This URL requests an unsupported recorded case or view. Reset to the approved level-1 Dirichlet case.",
      true,
    );
    return;
  }
  const c = current();
  $("unavailable").hidden = true;
  $("explorer").hidden = false;
  $("load-status").textContent =
    `Recorded-data identity checked · ${c.id} · source ${data.source_commit.slice(0, 7)}. This is not a scientific approval.`;
  $("level").value = String(c.level);
  $("boundary").value = c.boundary;
  $("matrix-source").value = state.source;
  $("case-id").textContent = c.id;
  $("case-summary").textContent =
    `Level ${c.level} · ${c.boundary === "dirichlet" ? "Dirichlet" : "Neumann"} · length 1 · ${c.reference.vertices.length} full / ${c.reference.active.length} active vertices`;
  $("mobile-case-summary").textContent = $("case-summary").textContent;
  $("matrix-tab").setAttribute("aria-pressed", state.view === "matrix");
  $("spectrum-tab").setAttribute("aria-pressed", state.view === "spectrum");
  $("matrix-view").hidden = state.view !== "matrix";
  $("spectrum-view").hidden = state.view !== "spectrum";
  drawGraph(c);
  renderNode(c);
  renderMatrix(c);
  renderComparison(c);
  if (state.view === "spectrum") drawSpectrum(c);
  $("data-source").textContent =
    `Recorded at ${data.source_recorded_at}. Original packet SHA-256: ${data.source_packet_sha256}. Presentation SHA-256: ${DATA_SHA256}.`;
  $("case-pointers").textContent = JSON.stringify(c.pointers, null, 2);
}

async function start() {
  const attempt = ++loadId;
  activeController?.abort();
  const controller = new AbortController();
  activeController = controller;
  const timeout = setTimeout(() => controller.abort(), 15000);
  data = null;
  state = null;
  $("explorer").hidden = true;
  $("unavailable").hidden = true;
  $("load-status").textContent = "Checking the recorded-data identity…";
  try {
    const [response, mr] = await Promise.all([
      fetch("./data.json", { cache: "no-store", signal: controller.signal }),
      fetch("./manifest.json", {
        cache: "no-store",
        signal: controller.signal,
      }),
    ]);
    if (!response.ok || !mr.ok) throw new Error("Unavailable");
    const [bytes, manifestBytes] = await Promise.all([
      readBoundedBytes(response, MAX_DATA_BYTES),
      readBoundedBytes(mr, 10000),
    ]);
    const digest = Array.from(
      new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
      (b) => b.toString(16).padStart(2, "0"),
    ).join("");
    const manifest = JSON.parse(
      new TextDecoder("utf-8", { fatal: true }).decode(manifestBytes),
    );
    if (digest !== DATA_SHA256) throw new Error("Identity mismatch");
    validateManifest(manifest, DATA_SHA256, bytes.byteLength);
    const verified = validateRecordedData(
      JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)),
    );
    if (attempt !== loadId) return;
    data = verified;
    render();
  } catch {
    if (attempt === loadId)
      unavailable(
        "The recorded data or provenance is missing, changed, malformed, timed out, or unavailable. No scientific result has been generated.",
      );
  } finally {
    clearTimeout(timeout);
    controller.abort();
    if (activeController === controller) activeController = null;
  }
}

document.querySelector(".skip").addEventListener("click", (e) => {
  e.preventDefault();
  $("main").setAttribute("tabindex", "-1");
  $("main").focus();
  $("main").scrollIntoView();
});
$("level").addEventListener("change", () => {
  if (!state) return;
  choose({
    caseId: data.cases.find(
      (c) =>
        c.level === Number($("level").value) && c.boundary === stateBoundary(),
    ).id,
  });
});
function stateBoundary() {
  return current().boundary;
}
$("boundary").addEventListener("change", () => {
  if (!state) return;
  choose({
    caseId: data.cases.find(
      (c) => c.level === current().level && c.boundary === $("boundary").value,
    ).id,
  });
});
$("matrix-source").addEventListener("change", () =>
  choose({ source: $("matrix-source").value }),
);
$("matrix-tab").addEventListener("click", () => choose({ view: "matrix" }));
$("spectrum-tab").addEventListener("click", () => choose({ view: "spectrum" }));
function reset() {
  focusNode = null;
  if (location.hash) location.hash = "";
  else render();
}
$("reset").addEventListener("click", reset);
$("show-graph").addEventListener("click", () => {
  const heading = $("graph-heading");
  heading.setAttribute("tabindex", "-1");
  heading.focus({ preventScroll: true });
  heading.scrollIntoView({ block: "start", behavior: "instant" });
});
$("invalid-reset").addEventListener("click", reset);
$("retry").addEventListener("click", start);
$("copy").addEventListener("click", async () => {
  if (!state) return;
  const url = new URL(location.href);
  url.search = "";
  url.hash = stateHash(state);
  $("view-link").href = url.href;
  $("view-link").textContent = url.href;
  $("view-link-output").hidden = false;
  try {
    await navigator.clipboard.writeText(url.href);
    $("load-status").textContent =
      location.hostname === "127.0.0.1" || location.hostname === "localhost"
        ? "View link copied. This local preview requires its local server; the public URL is shareable only after deployment."
        : "Recorded view link copied. It preserves the selected case, evidence view, matrix source and vertex—not a new result.";
  } catch {
    $("load-status").textContent = `Copy this recorded view link: ${url.href}`;
  }
});
window.addEventListener("hashchange", render);
let resizing = false;
new ResizeObserver(() => {
  if (resizing || !data || !state || $("explorer").hidden) return;
  resizing = true;
  requestAnimationFrame(() => {
    try {
      const c = current();
      drawGraph(c);
      if (state.view === "spectrum") drawSpectrum(c);
    } finally {
      resizing = false;
    }
  });
}).observe($("graph"));
start();
