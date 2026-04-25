const state = {
  configs: [],
  runs: [],
  selectedRunId: null,
  selectedRun: null,
  selectedTemplateName: null,
};

const els = {
  configTemplate: document.querySelector("#configTemplate"),
  loadTemplateButton: document.querySelector("#loadTemplateButton"),
  refreshRunsButton: document.querySelector("#refreshRunsButton"),
  launchForm: document.querySelector("#launchForm"),
  launchButton: document.querySelector("#launchButton"),
  verifyButton: document.querySelector("#verifyButton"),
  replayButton: document.querySelector("#replayButton"),
  bundleLink: document.querySelector("#bundleLink"),
  openReportButton: document.querySelector("#openReportButton"),
  reportDialog: document.querySelector("#reportDialog"),
  reportFrame: document.querySelector("#reportFrame"),
  reportHeading: document.querySelector("#reportHeading"),
  runsTableBody: document.querySelector("#runsTableBody"),
  toastRegion: document.querySelector("#toastRegion"),
  fields: {
    runName: document.querySelector("#runNameInput"),
    seed: document.querySelector("#seedInput"),
    gridX: document.querySelector("#gridX"),
    gridY: document.querySelector("#gridY"),
    gridZ: document.querySelector("#gridZ"),
    steps: document.querySelector("#stepsInput"),
    boxSize: document.querySelector("#boxSizeInput"),
    mass: document.querySelector("#massInput"),
    gInt: document.querySelector("#gIntInput"),
    dt: document.querySelector("#dtInput"),
    initialKind: document.querySelector("#initialKindInput"),
    amplitude: document.querySelector("#amplitudeInput"),
    width: document.querySelector("#widthInput"),
    randomPhase: document.querySelector("#randomPhaseInput"),
  },
  statusHeading: document.querySelector("#statusHeading"),
  statusBadge: document.querySelector("#statusBadge"),
  statusRunId: document.querySelector("#statusRunId"),
  statusDigest: document.querySelector("#statusDigest"),
  statusFinished: document.querySelector("#statusFinished"),
  statusElapsed: document.querySelector("#statusElapsed"),
  statusSteps: document.querySelector("#statusSteps"),
  statusVerified: document.querySelector("#statusVerified"),
  detailTitle: document.querySelector("#detailTitle"),
  detailChip: document.querySelector("#detailChip"),
  detailDigest: document.querySelector("#detailDigest"),
  energyDriftValue: document.querySelector("#energyDriftValue"),
  normDriftValue: document.querySelector("#normDriftValue"),
  energyChart: document.querySelector("#energyChart"),
  normChart: document.querySelector("#normChart"),
  energyAxisMid: document.querySelector("#energyAxisMid"),
  energyAxisEnd: document.querySelector("#energyAxisEnd"),
  normAxisMid: document.querySelector("#normAxisMid"),
  normAxisEnd: document.querySelector("#normAxisEnd"),
  evidenceDonut: document.querySelector("#evidenceDonut"),
  evidenceCount: document.querySelector("#evidenceCount"),
  evidenceLegend: document.querySelector("#evidenceLegend"),
  bundleSizeValue: document.querySelector("#bundleSizeValue"),
  verificationStatusValue: document.querySelector("#verificationStatusValue"),
  artifactCountValue: document.querySelector("#artifactCountValue"),
  artifactList: document.querySelector("#artifactList"),
};

const toneClassByStatus = {
  completed: "is-success",
  running: "is-warning",
  failed: "is-danger",
};

const toneColorByEvidence = {
  teal: "var(--teal-soft)",
  copper: "rgba(217, 109, 46, 0.94)",
  olive: "rgba(126, 132, 80, 0.92)",
  stone: "rgba(217, 209, 193, 1)",
};

function statusTone(status) {
  const normalized = String(status || "idle").toLowerCase();
  return toneClassByStatus[normalized] || "is-idle";
}

function formatTimestamp(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatSeconds(value) {
  if (value === null || value === undefined) return "-";
  const total = Math.round(Number(value));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}m ${seconds}s`;
}

function formatScientific(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "-";
  return numeric.toExponential(2);
}

function toast(title, body, tone = "neutral") {
  const node = document.createElement("div");
  node.className = "toast";
  node.innerHTML = `<strong>${title}</strong><span>${body}</span>`;
  if (tone === "danger") {
    node.style.borderColor = "rgba(198, 79, 62, 0.3)";
  }
  if (tone === "success") {
    node.style.borderColor = "rgba(79, 135, 78, 0.32)";
  }
  els.toastRegion.append(node);
  window.setTimeout(() => node.remove(), 3400);
}

async function fetchJson(url, options) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json();
}

function configByName(name) {
  return state.configs.find((item) => item.name === name) || null;
}

function fillForm(config) {
  const { run, engine, initial } = config;
  els.fields.runName.value = run.name;
  els.fields.seed.value = run.seed;
  els.fields.gridX.value = engine.grid_shape[0];
  els.fields.gridY.value = engine.grid_shape[1];
  els.fields.gridZ.value = engine.grid_shape[2];
  els.fields.steps.value = engine.num_steps;
  els.fields.boxSize.value = engine.box_size;
  els.fields.mass.value = engine.mass;
  els.fields.gInt.value = engine.g_int;
  els.fields.dt.value = engine.time_step;
  els.fields.initialKind.value = initial.kind;
  els.fields.amplitude.value = initial.amplitude;
  els.fields.width.value = initial.width;
  els.fields.randomPhase.checked = Boolean(initial.random_phase);
}

function currentConfig() {
  const template = configByName(els.configTemplate.value);
  return {
    run: {
      name: els.fields.runName.value.trim() || template?.config?.run?.name || "cockpit",
      seed: Number(els.fields.seed.value),
      output_root: "runs",
    },
    engine: {
      backend: "numpy",
      grid_shape: [
        Number(els.fields.gridX.value),
        Number(els.fields.gridY.value),
        Number(els.fields.gridZ.value),
      ],
      box_size: Number(els.fields.boxSize.value),
      mass: Number(els.fields.mass.value),
      g_int: Number(els.fields.gInt.value),
      time_step: Number(els.fields.dt.value),
      num_steps: Number(els.fields.steps.value),
      log_every: 1,
    },
    initial: {
      kind: els.fields.initialKind.value,
      amplitude: Number(els.fields.amplitude.value),
      width: Number(els.fields.width.value),
      random_phase: els.fields.randomPhase.checked,
    },
  };
}

function renderConfigOptions() {
  els.configTemplate.innerHTML = state.configs
    .map(
      (item) =>
        `<option value="${item.name}" ${item.name === state.selectedTemplateName ? "selected" : ""}>${item.label}</option>`,
    )
    .join("");
}

function renderRunsTable() {
  if (!state.runs.length) {
    els.runsTableBody.innerHTML = `
      <tr>
        <td colspan="7">No runs yet. Launch the first deterministic run from the cockpit.</td>
      </tr>
    `;
    return;
  }

  els.runsTableBody.innerHTML = state.runs
    .map((run) => {
      const selected = run.run_id === state.selectedRunId ? "is-selected" : "";
      const tone = statusTone(run.status);
      return `
        <tr class="${selected}" data-run-id="${run.run_id}">
          <td>${run.run_id}</td>
          <td>${run.config_name}</td>
          <td>${run.seed}</td>
          <td>${run.grid_label}</td>
          <td>${run.steps.toLocaleString()}</td>
          <td><span class="status-pill ${tone}">${run.status}</span></td>
          <td>${formatTimestamp(run.finished_at)}</td>
        </tr>
      `;
    })
    .join("");

  els.runsTableBody.querySelectorAll("tr[data-run-id]").forEach((row) => {
    row.addEventListener("click", () => selectRun(row.dataset.runId));
  });
}

function renderTrace(svg, values, color) {
  const width = 280;
  const height = 110;
  const padding = 10;
  svg.innerHTML = "";

  if (!values.length) {
    return;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const points = values
    .map((value, index) => {
      const x = padding + ((width - padding * 2) * index) / Math.max(values.length - 1, 1);
      const y = height - padding - ((value - min) / span) * (height - padding * 2);
      return `${x},${y}`;
    })
    .join(" ");

  const axis = document.createElementNS("http://www.w3.org/2000/svg", "path");
  axis.setAttribute("d", `M${padding},${height - padding} L${width - padding},${height - padding}`);
  axis.setAttribute("stroke", "rgba(35, 57, 59, 0.16)");
  axis.setAttribute("stroke-width", "1");
  axis.setAttribute("fill", "none");

  const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  line.setAttribute("points", points);
  line.setAttribute("stroke", color);
  line.setAttribute("stroke-width", "3");
  line.setAttribute("stroke-linecap", "round");
  line.setAttribute("stroke-linejoin", "round");
  line.setAttribute("fill", "none");

  svg.append(axis, line);
}

function renderEvidence(detail) {
  const categories = detail.evidence.categories;
  const total = categories.reduce((sum, item) => sum + item.count, 0);
  const donutStops = [];
  let cursor = 0;

  categories.forEach((item) => {
    const slice = total ? (item.count / total) * 360 : 0;
    donutStops.push(`${toneColorByEvidence[item.tone]} ${cursor}deg ${cursor + slice}deg`);
    cursor += slice;
  });

  els.evidenceDonut.style.background = donutStops.length
    ? `conic-gradient(${donutStops.join(", ")})`
    : "conic-gradient(var(--stone) 0deg 360deg)";
  els.evidenceCount.textContent = String(detail.evidence.file_count);
  els.bundleSizeValue.textContent = detail.evidence.bundle_size_label;
  els.artifactCountValue.textContent = String(detail.evidence.artifact_paths.length);
  els.verificationStatusValue.textContent = detail.verification.success
    ? `Verified (${detail.verification.checked_files})`
    : "Pending";

  els.evidenceLegend.innerHTML = categories
    .map(
      (item) => `
        <li>
          <span class="legend-label">
            <span class="legend-swatch swatch-${item.tone}"></span>
            <span>${item.label}</span>
          </span>
          <strong>${item.count}</strong>
        </li>
      `,
    )
    .join("");

  els.artifactList.innerHTML = detail.evidence.artifact_paths
    .map((path) => `<li>${path}</li>`)
    .join("");
}

function renderSelectedRun(detail) {
  state.selectedRun = detail;
  state.selectedRunId = detail.summary.run_id;

  els.statusHeading.textContent = detail.run_record.status;
  els.statusBadge.textContent = detail.run_record.status;
  els.statusBadge.className = `status-badge ${statusTone(detail.run_record.status)}`;
  els.statusRunId.textContent = detail.summary.run_id;
  els.statusDigest.textContent = detail.summary.config_digest.slice(0, 16);
  els.statusFinished.textContent = formatTimestamp(detail.summary.finished_at);
  els.statusElapsed.textContent = formatSeconds(detail.summary.elapsed_seconds);
  els.statusSteps.textContent = detail.summary.steps.toLocaleString();
  els.statusVerified.textContent = detail.verification.success
    ? `Verified (${detail.verification.checked_files})`
    : "Pending";

  els.detailTitle.textContent = detail.summary.name;
  els.detailChip.textContent = detail.summary.run_id;
  els.detailDigest.textContent = detail.summary.config_digest;
  els.energyDriftValue.textContent = formatScientific(detail.metrics.energy_drift);
  els.normDriftValue.textContent = formatScientific(detail.metrics.norm_drift);
  els.energyAxisMid.textContent = Math.floor(detail.metrics.history.length / 2).toString();
  els.energyAxisEnd.textContent = String(detail.latest_snapshot.step);
  els.normAxisMid.textContent = Math.floor(detail.metrics.history.length / 2).toString();
  els.normAxisEnd.textContent = String(detail.latest_snapshot.step);

  renderTrace(
    els.energyChart,
    detail.metrics.history.map((item) => Number(item.energy)),
    "rgba(217, 109, 46, 0.94)",
  );
  renderTrace(
    els.normChart,
    detail.metrics.history.map((item) => Number(item.norm)),
    "rgba(42, 106, 106, 0.94)",
  );

  els.bundleLink.href = detail.urls.bundle;
  els.bundleLink.setAttribute("download", "");
  els.reportFrame.src = detail.urls.report;
  els.reportHeading.textContent = `Evidence Report · ${detail.summary.run_id}`;

  renderEvidence(detail);
  renderRunsTable();
}

async function refreshRuns() {
  const payload = await fetchJson("/api/runs");
  state.runs = payload.items;
  renderRunsTable();

  if (!state.selectedRunId && state.runs[0]) {
    await selectRun(state.runs[0].run_id);
  }
}

async function selectRun(runId) {
  const detail = await fetchJson(`/api/runs/${runId}`);
  renderSelectedRun(detail);
}

async function hydrate() {
  const [configPayload] = await Promise.all([fetchJson("/api/configs"), refreshRuns()]);
  state.configs = configPayload.items;
  state.selectedTemplateName = configPayload.default_name || state.configs[0]?.name || null;
  renderConfigOptions();

  const selectedConfig = configByName(state.selectedTemplateName);
  if (selectedConfig) {
    fillForm(selectedConfig.config);
  }

  if (state.runs[0]) {
    await selectRun(state.runs[0].run_id);
  }
}

async function handleLaunch(event) {
  event.preventDefault();
  els.launchButton.disabled = true;
  els.launchButton.textContent = "Launching...";

  try {
    const detail = await fetchJson("/api/runs", {
      method: "POST",
      body: JSON.stringify({
        config: currentConfig(),
        source_name: els.configTemplate.value || "cockpit.yaml",
      }),
    });
    toast("Run complete", `Created ${detail.summary.run_id}`, "success");
    state.runs = [detail.summary, ...state.runs.filter((item) => item.run_id !== detail.summary.run_id)];
    renderSelectedRun(detail);
  } catch (error) {
    toast("Launch failed", error.message, "danger");
  } finally {
    els.launchButton.disabled = false;
    els.launchButton.textContent = "Launch Run";
  }
}

async function handleVerify() {
  if (!state.selectedRunId) return;
  try {
    const result = await fetchJson(`/api/runs/${state.selectedRunId}/verify`, { method: "POST" });
    toast(
      result.success ? "Verification passed" : "Verification failed",
      result.success
        ? `Checked ${result.checked_files} files`
        : result.errors.join(" | "),
      result.success ? "success" : "danger",
    );
    await selectRun(state.selectedRunId);
  } catch (error) {
    toast("Verification failed", error.message, "danger");
  }
}

async function handleReplay() {
  if (!state.selectedRunId) return;
  els.replayButton.disabled = true;
  try {
    const detail = await fetchJson(`/api/runs/${state.selectedRunId}/replay`, { method: "POST" });
    toast("Replay complete", `Created ${detail.summary.run_id}`, "success");
    state.runs = [detail.summary, ...state.runs.filter((item) => item.run_id !== detail.summary.run_id)];
    renderSelectedRun(detail);
  } catch (error) {
    toast("Replay failed", error.message, "danger");
  } finally {
    els.replayButton.disabled = false;
  }
}

function openReport() {
  if (!state.selectedRun) return;
  els.reportDialog.showModal();
}

function bindEvents() {
  els.loadTemplateButton.addEventListener("click", () => {
    const selected = configByName(els.configTemplate.value);
    if (selected) {
      fillForm(selected.config);
      toast("Template loaded", `Using ${selected.name}`, "success");
    }
  });

  els.configTemplate.addEventListener("change", (event) => {
    state.selectedTemplateName = event.target.value;
    const selected = configByName(state.selectedTemplateName);
    if (selected) {
      fillForm(selected.config);
    }
  });

  els.refreshRunsButton.addEventListener("click", async () => {
    try {
      await refreshRuns();
      toast("Run ledger refreshed", "Latest deterministic runs loaded.", "success");
    } catch (error) {
      toast("Refresh failed", error.message, "danger");
    }
  });

  els.launchForm.addEventListener("submit", handleLaunch);
  els.verifyButton.addEventListener("click", handleVerify);
  els.replayButton.addEventListener("click", handleReplay);
  els.openReportButton.addEventListener("click", openReport);
}

bindEvents();

hydrate().catch((error) => {
  toast("Cockpit failed to load", error.message, "danger");
});
