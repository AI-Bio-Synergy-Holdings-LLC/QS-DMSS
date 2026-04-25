const state = {
  configs: [],
  runs: [],
  sweepParameters: [],
  selectedRunId: null,
  selectedRun: null,
  selectedTemplateName: null,
  selectedRunIds: [],
  comparison: null,
};

const els = {
  configTemplate: document.querySelector("#configTemplate"),
  loadTemplateButton: document.querySelector("#loadTemplateButton"),
  refreshRunsButton: document.querySelector("#refreshRunsButton"),
  compareButton: document.querySelector("#compareButton"),
  clearCompareButton: document.querySelector("#clearCompareButton"),
  selectedRunCount: document.querySelector("#selectedRunCount"),
  launchForm: document.querySelector("#launchForm"),
  launchButton: document.querySelector("#launchButton"),
  sweepForm: document.querySelector("#sweepForm"),
  sweepParameter: document.querySelector("#sweepParameter"),
  sweepValues: document.querySelector("#sweepValues"),
  experimentNameInput: document.querySelector("#experimentNameInput"),
  launchSweepButton: document.querySelector("#launchSweepButton"),
  verifyButton: document.querySelector("#verifyButton"),
  replayButton: document.querySelector("#replayButton"),
  bundleLink: document.querySelector("#bundleLink"),
  openReportButton: document.querySelector("#openReportButton"),
  reportDialog: document.querySelector("#reportDialog"),
  reportFrame: document.querySelector("#reportFrame"),
  reportHeading: document.querySelector("#reportHeading"),
  runsTableBody: document.querySelector("#runsTableBody"),
  comparisonTableBody: document.querySelector("#comparisonTableBody"),
  compareTitle: document.querySelector("#compareTitle"),
  compareContext: document.querySelector("#compareContext"),
  compareEnergySpan: document.querySelector("#compareEnergySpan"),
  compareNormSpan: document.querySelector("#compareNormSpan"),
  compareDensitySpan: document.querySelector("#compareDensitySpan"),
  compareFastestRun: document.querySelector("#compareFastestRun"),
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

function formatSignedScientific(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "-";
  return `${numeric >= 0 ? "+" : ""}${numeric.toExponential(2)}`;
}

function shortRunId(value) {
  if (!value) return "-";
  return String(value).slice(-8);
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

function sweepParameterByPath(path) {
  return state.sweepParameters.find((item) => item.path === path) || null;
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

function renderSweepParameterOptions() {
  els.sweepParameter.innerHTML = state.sweepParameters
    .map(
      (item) =>
        `<option value="${item.path}">${item.label} - ${item.path}</option>`,
    )
    .join("");
}

function updateSelectionChip() {
  const count = state.selectedRunIds.length;
  els.selectedRunCount.textContent = `${count} selected`;
}

function renderRunsTable() {
  if (!state.runs.length) {
    els.runsTableBody.innerHTML = `
      <tr>
        <td colspan="8">No runs yet. Launch the first deterministic run from the cockpit.</td>
      </tr>
    `;
    updateSelectionChip();
    return;
  }

  els.runsTableBody.innerHTML = state.runs
    .map((run) => {
      const selected = run.run_id === state.selectedRunId ? "is-selected" : "";
      const tone = statusTone(run.status);
      const checked = state.selectedRunIds.includes(run.run_id) ? "checked" : "";
      const experimentLabel = run.experiment?.parameter_value_label
        ? `<div class="compare-parameter"><strong>${run.experiment.parameter_value_label}</strong><span>${run.experiment.parameter_label}</span></div>`
        : "";
      return `
        <tr class="${selected}" data-run-id="${run.run_id}">
          <td class="run-select-cell">
            <input class="run-select" type="checkbox" data-run-check="${run.run_id}" ${checked} />
          </td>
          <td>${run.run_id}</td>
          <td>
            <div class="compare-run">
              <strong>${run.config_name}</strong>
              ${experimentLabel || `<span>${run.name}</span>`}
            </div>
          </td>
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
    row.addEventListener("click", (event) => {
      if (event.target.closest('input[type="checkbox"]')) {
        return;
      }
      selectRun(row.dataset.runId);
    });
  });

  els.runsTableBody.querySelectorAll("input[data-run-check]").forEach((checkbox) => {
    checkbox.addEventListener("click", (event) => event.stopPropagation());
    checkbox.addEventListener("change", (event) => {
      toggleRunSelection(event.target.dataset.runCheck, event.target.checked);
    });
  });

  updateSelectionChip();
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
  els.detailChip.textContent = detail.run_record.experiment?.parameter_value_label
    ? `${detail.summary.run_id} - ${detail.run_record.experiment.parameter_value_label}`
    : detail.summary.run_id;
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
  els.reportHeading.textContent = `Evidence Report - ${detail.summary.run_id}`;

  renderEvidence(detail);
  renderRunsTable();
}

function renderComparison(comparison) {
  state.comparison = comparison;

  if (!comparison) {
    els.compareTitle.textContent = "Run Comparison";
    els.compareContext.textContent = "Select two or more runs";
    els.compareEnergySpan.textContent = "-";
    els.compareNormSpan.textContent = "-";
    els.compareDensitySpan.textContent = "-";
    els.compareFastestRun.textContent = "-";
    els.comparisonTableBody.innerHTML = `
      <tr>
        <td colspan="6">Select at least two runs to compare.</td>
      </tr>
    `;
    return;
  }

  const shared = comparison.shared_experiment;
  els.compareTitle.textContent = shared ? shared.label : "Run Comparison";
  els.compareContext.textContent = shared
    ? `${shared.parameter_label} sweep`
    : `${comparison.rows.length} runs selected`;
  els.compareEnergySpan.textContent = formatScientific(comparison.ranges.energy_drift.span);
  els.compareNormSpan.textContent = formatScientific(comparison.ranges.norm_drift.span);
  els.compareDensitySpan.textContent = formatScientific(comparison.ranges.max_density.span);
  els.compareFastestRun.textContent = shortRunId(comparison.ranges.elapsed_seconds.min_run_id);

  els.comparisonTableBody.innerHTML = comparison.rows
    .map((row, index) => `
      <tr>
        <td>
          <div class="compare-run">
            <strong>${row.run_id}</strong>
            <span>${index === 0 ? "Baseline" : row.config_name}</span>
          </div>
        </td>
        <td>
          <div class="compare-parameter">
            <strong>${row.parameter_value_label || "-"}</strong>
            <span>${row.parameter_label || "Manual selection"}</span>
          </div>
        </td>
        <td>${formatScientific(row.energy_drift)}</td>
        <td>${formatScientific(row.norm_drift)}</td>
        <td>${formatScientific(row.max_density)}</td>
        <td>
          <div class="compare-delta">
            <strong>${formatSignedScientific(row.delta_from_baseline.energy_drift)}</strong>
            <span>energy vs baseline</span>
          </div>
        </td>
      </tr>
    `)
    .join("");
}

async function refreshRuns() {
  const payload = await fetchJson("/api/runs");
  state.runs = payload.items;
  const availableRunIds = new Set(state.runs.map((item) => item.run_id));
  state.selectedRunIds = state.selectedRunIds.filter((runId) => availableRunIds.has(runId));

  if (state.selectedRunId && !availableRunIds.has(state.selectedRunId)) {
    state.selectedRunId = null;
    state.selectedRun = null;
  }

  renderRunsTable();
}

async function selectRun(runId) {
  const detail = await fetchJson(`/api/runs/${runId}`);
  renderSelectedRun(detail);
}

function toggleRunSelection(runId, checked) {
  if (checked) {
    if (!state.selectedRunIds.includes(runId)) {
      state.selectedRunIds = [...state.selectedRunIds, runId];
    }
  } else {
    state.selectedRunIds = state.selectedRunIds.filter((value) => value !== runId);
  }

  renderRunsTable();
  if (state.comparison) {
    renderComparison(null);
  }
}

function parseSweepValues(text) {
  return text
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

async function hydrate() {
  const [configPayload, sweepPayload] = await Promise.all([
    fetchJson("/api/configs"),
    fetchJson("/api/sweeps/parameters"),
  ]);
  state.configs = configPayload.items;
  state.sweepParameters = sweepPayload.items;
  state.selectedTemplateName = configPayload.default_name || state.configs[0]?.name || null;
  renderConfigOptions();
  renderSweepParameterOptions();

  const selectedConfig = configByName(state.selectedTemplateName);
  if (selectedConfig) {
    fillForm(selectedConfig.config);
  }

  const defaultSweepParameter = state.sweepParameters[0];
  if (defaultSweepParameter) {
    els.sweepParameter.value = defaultSweepParameter.path;
  }

  await refreshRuns();
  renderComparison(null);

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

async function handleLaunchSweep(event) {
  event.preventDefault();
  const selectedParameter = sweepParameterByPath(els.sweepParameter.value);
  const values = parseSweepValues(els.sweepValues.value);
  if (!selectedParameter || !values.length) {
    toast("Sweep needs values", "Enter one or more comma-separated values.", "danger");
    return;
  }

  els.launchSweepButton.disabled = true;
  els.launchSweepButton.textContent = "Launching...";

  try {
    const payload = await fetchJson("/api/sweeps", {
      method: "POST",
      body: JSON.stringify({
        config: currentConfig(),
        parameter_path: selectedParameter.path,
        values,
        source_name: els.configTemplate.value || "sweep.yaml",
        experiment_name: els.experimentNameInput.value.trim() || null,
      }),
    });
    toast("Sweep complete", `Created ${payload.runs.length} runs`, "success");
    state.selectedRunIds = payload.experiment.run_ids;
    await refreshRuns();
    renderComparison(payload.comparison);
    if (payload.runs[0]) {
      await selectRun(payload.runs[0].run_id);
    }
  } catch (error) {
    toast("Sweep failed", error.message, "danger");
  } finally {
    els.launchSweepButton.disabled = false;
    els.launchSweepButton.textContent = "Launch Sweep";
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

async function handleCompare() {
  if (state.selectedRunIds.length < 2) {
    toast("Pick more runs", "Select at least two runs to compare.", "danger");
    return;
  }

  try {
    const comparison = await fetchJson("/api/compare", {
      method: "POST",
      body: JSON.stringify({ run_ids: state.selectedRunIds }),
    });
    renderComparison(comparison);
    toast("Comparison ready", `Compared ${comparison.rows.length} runs`, "success");
  } catch (error) {
    toast("Compare failed", error.message, "danger");
  }
}

function clearComparison() {
  state.selectedRunIds = [];
  renderRunsTable();
  renderComparison(null);
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

  els.compareButton.addEventListener("click", handleCompare);
  els.clearCompareButton.addEventListener("click", clearComparison);
  els.launchForm.addEventListener("submit", handleLaunch);
  els.sweepForm.addEventListener("submit", handleLaunchSweep);
  els.verifyButton.addEventListener("click", handleVerify);
  els.replayButton.addEventListener("click", handleReplay);
  els.openReportButton.addEventListener("click", openReport);
}

bindEvents();

hydrate().catch((error) => {
  toast("Cockpit failed to load", error.message, "danger");
});
