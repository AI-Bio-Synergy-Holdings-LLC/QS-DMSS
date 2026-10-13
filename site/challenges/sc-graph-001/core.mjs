export const CASE_IDS = ["graph_04", "graph_07", "graph_10", "graph_13"];
const MANIFEST_SCOPE = Object.freeze({
  origin: "Recorded fields copied from frozen pilot; no new calculations",
  control_scope:
    "Rejection flags only. Defective matrices/spectra were not retained and are not generated.",
  presentation_scope:
    "Read-only recorded-data explorer. No AI, solver, reference or scientific-control execution.",
});
const META = {
  graph_04: [1, "neumann", 6, 6],
  graph_07: [1, "dirichlet", 6, 3],
  graph_10: [2, "neumann", 15, 15],
  graph_13: [2, "dirichlet", 15, 12],
};
const require = (condition, message) => {
  if (!condition) throw new Error(message);
};
const finite = (value) => typeof value === "number" && Number.isFinite(value);
const vector = (values, n) =>
  Array.isArray(values) && values.length === n && values.every(finite);
const matrix = (values, n, m = n) =>
  Array.isArray(values) &&
  values.length === n &&
  values.every((row) => vector(row, m));

export function validateManifest(m, digest, bytes) {
  require(m?.schema_version === 1 &&
    m.data_file === "data.json" &&
    m.data_sha256 === digest &&
    m.data_bytes === bytes, "Presentation identity differs");
  require(m.candidate_source === "48d7ab5d10da189caddbcad1dd6622e58d204940" &&
    m.source_packet_sha256 ===
      "17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4" &&
    m.source_measurements_member_sha256 ===
      "adedcc1aa04484ca925373a36701a52498913b6c4a030bf51a0a26adf43ebe33", "Source identity differs");
  require(m.scientific_status === "NOT_ESTABLISHED" &&
    m.independent_review === "PENDING" &&
    m.human_disposition === "PENDING", "Manifest status differs");
  require(JSON.stringify(m.selected_cases) ===
    JSON.stringify(CASE_IDS), "Manifest scope differs");
  for (const [field, expected] of Object.entries(MANIFEST_SCOPE))
    require(m[field] === expected, "Manifest execution scope differs");
  return m;
}

export function validateRecordedData(data) {
  require(data?.schema_version === 1 &&
    data.challenge_id === "SC-GRAPH-001", "Unsupported data identity");
  require(data.source_commit ===
    "48d7ab5d10da189caddbcad1dd6622e58d204940", "Candidate identity differs");
  require(data.source_packet_sha256 ===
    "17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4", "Packet identity differs");
  require(data.scientific_assessment?.status === "NOT_ESTABLISHED" &&
    data.scientific_assessment.independent_review === "PENDING" &&
    data.scientific_assessment.human_disposition ===
      "PENDING", "Scientific status differs");
  require(data.full_registered_graph_cases === 15, "Registered scope differs");
  const limits = {
    scaled_matrix_error_max: 5e-13,
    scaled_spectrum_error_max: 1e-11,
    projector_error_max: 1e-10,
    reference_cluster_relative_gap: 1e-9,
    tail_fraction: 0.8,
    tail_error_max: 1e-11,
  };
  require(data.acceptance_limits &&
    Object.keys(data.acceptance_limits).length === 6 &&
    Object.entries(limits).every(
      ([key, value]) => data.acceptance_limits[key] === value,
    ), "Registered bounds differ");
  require(Array.isArray(data.cases) &&
    data.cases.length === 4 &&
    new Set(data.cases.map((c) => c.id)).size === 4 &&
    data.cases.every((c) => CASE_IDS.includes(c.id)), "Unsupported case set");
  for (const c of data.cases) {
    const [level, boundary, full, n] = META[c.id];
    require(c.level === level &&
      c.boundary === boundary &&
      c.length === 1, "Case identity differs");
    const r = c.reference;
    require(r &&
      matrix(r.vertices, full, 2) &&
      r.vertices.flat().every(Number.isInteger), "Invalid lattice vertices");
    require(Array.isArray(r.active) &&
      r.active.length === n &&
      new Set(r.active).size === n &&
      r.active.every(
        (x) => Number.isInteger(x) && x >= 0 && x < full,
      ), "Invalid active indices");
    require(Array.isArray(r.boundary) &&
      r.boundary.length === 3 &&
      new Set(r.boundary).size === 3 &&
      r.boundary.every(
        (x) => Number.isInteger(x) && x >= 0 && x < full,
      ), "Invalid boundary indices");
    require(matrix(r.edges, level === 1 ? 9 : 27, 2) &&
      r.edges
        .flat()
        .every(
          (x) => Number.isInteger(x) && x >= 0 && x < full,
        ), "Invalid edges");
    for (const source of [c.reference, c.candidate]) {
      require(source &&
        vector(source.mass, n) &&
        source.mass.every((x) => x > 0) &&
        matrix(source.stiffness, n) &&
        vector(source.spectrum, n), "Invalid recorded arrays");
    }
    require(c.record?.artifact_prefix === c.id &&
      c.record.status ===
        "NOT_FALSIFIED_WITHIN_SCOPE", "Missing recorded comparison");
    for (const k of [
      "matrix_error",
      "spectrum_error",
      "projector_error",
      "tail_error",
    ])
      require(finite(c.record[k]) &&
        c.record[k] >= 0, "Invalid recorded error");
    const controls = c.record.negative_controls;
    require(controls &&
      (boundary === "dirichlet"
        ? controls.induced_laplacian_rejected === true
        : controls.uniform_mass_rejected === true), "Missing recorded control");
  }
  return data;
}

export function parseState(hash, data) {
  if (!hash || hash === "#")
    return { caseId: "graph_07", view: "matrix", source: "candidate", node: 1 };
  require(hash.length <= 256, "Unsupported view state");
  const p = new URLSearchParams(hash.replace(/^#/, ""));
  const allowed = ["case", "view", "source", "node"];
  for (const k of p.keys())
    require(allowed.includes(k) &&
      p.getAll(k).length === 1, "Unsupported view state");
  const caseId = p.get("case");
  const view = p.get("view") || "matrix";
  const source = p.get("source") || "candidate";
  require(CASE_IDS.includes(caseId) &&
    ["matrix", "spectrum"].includes(view) &&
    ["candidate", "reference"].includes(source), "Unsupported view state");
  const c = data.cases.find((c) => c.id === caseId);
  let node = c.reference.active[0];
  if (p.has("node")) {
    require(/^\d{1,2}$/.test(p.get("node")), "Unsupported vertex");
    node = Number(p.get("node"));
  }
  require(Number.isInteger(node) &&
    node >= 0 &&
    node < c.reference.vertices.length, "Unsupported vertex");
  return { caseId, view, source, node };
}

export function stateHash(state) {
  return (
    "#" +
    new URLSearchParams({
      case: state.caseId,
      view: state.view,
      source: state.source,
      node: String(state.node),
    }).toString()
  );
}
export function displayNumber(value) {
  if (!finite(value)) throw new Error("Nonfinite display value");
  if (value === 0) return "0";
  return Math.abs(value) < 0.0001 || Math.abs(value) >= 100000
    ? value.toExponential(3)
    : Number(value.toPrecision(6)).toString();
}
