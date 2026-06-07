const state = {
  configs: [],
  showcases: [],
  runs: [],
  experiments: [],
  sweepParameters: [],
  selectedShowcaseName: null,
  labResult: null,
  selectedRunId: null,
  selectedRun: null,
  selectedExperimentId: null,
  selectedExperiment: null,
  selectedTemplateName: null,
  selectedRunIds: [],
  comparison: null,
};

const els = {
  configTemplate: document.querySelector("#configTemplate"),
  loadTemplateButton: document.querySelector("#loadTemplateButton"),
  labScenarioSelect: document.querySelector("#labScenarioSelect"),
  launchLabButton: document.querySelector("#launchLabButton"),
  labScenarioSummary: document.querySelector("#labScenarioSummary"),
  labScenarioMeta: document.querySelector("#labScenarioMeta"),
  labRunId: document.querySelector("#labRunId"),
  labStatus: document.querySelector("#labStatus"),
  labProgressShell: document.querySelector("#labProgressShell"),
  labProgressText: document.querySelector("#labProgressText"),
  labVerification: document.querySelector("#labVerification"),
  labReplay: document.querySelector("#labReplay"),
  labMarkdownLink: document.querySelector("#labMarkdownLink"),
  labJsonLink: document.querySelector("#labJsonLink"),
  labSelectRunButton: document.querySelector("#labSelectRunButton"),
  labArtifactLinks: document.querySelector("#labArtifactLinks"),
  refreshRunsButton: document.querySelector("#refreshRunsButton"),
  refreshExperimentsButton: document.querySelector("#refreshExperimentsButton"),
  compareButton: document.querySelector("#compareButton"),
  clearCompareButton: document.querySelector("#clearCompareButton"),
  saveExperimentButton: document.querySelector("#saveExperimentButton"),
  openExperimentReportButton: document.querySelector("#openExperimentReportButton"),
  experimentBundleLink: document.querySelector("#experimentBundleLink"),
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
  recommendationLabel: document.querySelector("#recommendationLabel"),
  recommendationRun: document.querySelector("#recommendationRun"),
  recommendationReason: document.querySelector("#recommendationReason"),
  recommendationStatus: document.querySelector("#recommendationStatus"),
  recommendationScore: document.querySelector("#recommendationScore"),
  profileTitle: document.querySelector("#profileTitle"),
  profileMetric: document.querySelector("#profileMetric"),
  profileSummary: document.querySelector("#profileSummary"),
  profileGoalBadge: document.querySelector("#profileGoalBadge"),
  profileTargetChip: document.querySelector("#profileTargetChip"),
  profileConstraints: document.querySelector("#profileConstraints"),
  campaignTitle: document.querySelector("#campaignTitle"),
  campaignRunCount: document.querySelector("#campaignRunCount"),
  campaignSummary: document.querySelector("#campaignSummary"),
  campaignStrategyBadge: document.querySelector("#campaignStrategyBadge"),
  campaignMaxRunsChip: document.querySelector("#campaignMaxRunsChip"),
  campaignDimensions: document.querySelector("#campaignDimensions"),
  launchCampaignButton: document.querySelector("#launchCampaignButton"),
  experimentTitle: document.querySelector("#experimentTitle"),
  experimentContext: document.querySelector("#experimentContext"),
  experimentKind: document.querySelector("#experimentKind"),
  experimentRunCount: document.querySelector("#experimentRunCount"),
  experimentCreated: document.querySelector("#experimentCreated"),
  experimentRecommended: document.querySelector("#experimentRecommended"),
  experimentDecisionStatus: document.querySelector("#experimentDecisionStatus"),
  experimentBundleSize: document.querySelector("#experimentBundleSize"),
  experimentRegistryBody: document.querySelector("#experimentRegistryBody"),
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
  qualified: "is-success",
  ranked: "is-success",
  running: "is-warning",
  fallback: "is-warning",
  failed: "is-danger",
  out_of_bounds: "is-danger",
  unconfigured: "is-idle",
  idle: "is-idle",
};

const toneColorByEvidence = {
  teal: "var(--teal-soft)",
  copper: "rgba(217, 109, 46, 0.94)",
  olive: "rgba(126, 132, 80, 0.92)",
  stone: "rgba(217, 209, 193, 1)",
};

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function toneForStatus(status) {
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

function formatScore(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "-";
  return numeric.toFixed(3);
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

function showcaseByName(name) {
  return state.showcases.find((item) => item.name === name) || null;
}

function sweepParameterByPath(path) {
  return state.sweepParameters.find((item) => item.path === path) || null;
}

function parameterLabel(path) {
  return sweepParameterByPath(path)?.label || path;
}

function renderShowcaseOptions() {
  els.labScenarioSelect.innerHTML = state.showcases
    .map((item) => `<option value="${item.name}">${item.label}</option>`)
    .join("");
  if (state.selectedShowcaseName) {
    els.labScenarioSelect.value = state.selectedShowcaseName;
  }
}

function setLabLinksEnabled(enabled) {
  [
    [els.labMarkdownLink, "Open Markdown"],
    [els.labJsonLink, "Open JSON"],
  ].forEach(([link, readyLabel]) => {
    if (enabled) {
      link.removeAttribute("aria-disabled");
      link.removeAttribute("tabindex");
      link.textContent = readyLabel;
      link.classList.remove("is-disabled");
    } else {
      link.removeAttribute("href");
      link.setAttribute("aria-disabled", "true");
      link.setAttribute("tabindex", "-1");
      link.textContent = "Run first";
      link.classList.add("is-disabled");
    }
  });
  els.labSelectRunButton.disabled = !enabled;
}

function setLabProgress(isRunning, message) {
  els.launchLabButton.disabled = isRunning;
  els.launchLabButton.setAttribute("aria-busy", String(isRunning));
  els.launchLabButton.textContent = isRunning ? "Running Lab Mode..." : "Run Lab Mode Showcase";
  els.labProgressShell.hidden = !isRunning;
  els.labProgressText.textContent = message;
}

function renderLabMode() {
  const scenario = showcaseByName(state.selectedShowcaseName);
  els.labScenarioSummary.textContent =
    scenario?.description ||
    "Choose a packaged showcase to create a run, replay, artifacts, and a report.";
  els.labScenarioMeta.textContent = scenario
    ? `${scenario.grid_label} | ${scenario.steps} steps | ${scenario.claim_boundary}`
    : "No packaged showcase selected";

  if (!state.labResult) {
    els.labRunId.textContent = "No Lab Mode run yet";
    els.labStatus.textContent = "Idle";
    els.labStatus.className = "status-badge is-idle";
    els.labProgressText.textContent = "Ready to launch the packaged showcase.";
    els.labVerification.textContent = "Pending";
    els.labReplay.textContent = "Pending";
    els.labArtifactLinks.innerHTML = `
      <li>Run the canonical showcase to populate CSV/SVG artifacts and report links.</li>
    `;
    setLabLinksEnabled(false);
    return;
  }

  const { report, run, replay_run: replayRun, artifact_links: artifactLinks, urls } = state.labResult;
  els.labRunId.textContent = run.summary.run_id;
  els.labStatus.textContent = report.success ? "Passed" : "Needs review";
  els.labStatus.className = `status-badge ${toneForStatus(report.success ? "completed" : "failed")}`;
  els.labVerification.textContent = report.verification.success
    ? `Verified (${report.verification.checked_files})`
    : "Verification failed";
  els.labReplay.textContent = replayRun
    ? report.replay.final_density_allclose
      ? `Replay matched (${shortRunId(replayRun.summary.run_id)})`
      : "Replay mismatch"
    : "Replay skipped";
  els.labMarkdownLink.href = urls.markdown_report;
  els.labJsonLink.href = urls.json_report;
  els.labArtifactLinks.innerHTML = artifactLinks.length
    ? artifactLinks
        .map(
          (item) => `
            <li>
              <a href="${item.url}" target="_blank" rel="noreferrer">
                <strong>${item.label}</strong>
                <span>${item.name}</span>
              </a>
            </li>
          `,
        )
        .join("")
    : "<li>No exported showcase artifacts found.</li>";
  setLabLinksEnabled(true);
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
  const base = cloneJson(template?.config || {});
  return {
    run: {
      ...(base.run || {}),
      name: els.fields.runName.value.trim() || base?.run?.name || "cockpit",
      seed: Number(els.fields.seed.value),
      output_root: "runs",
    },
    engine: {
      ...(base.engine || {}),
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
      ...(base.initial || {}),
      kind: els.fields.initialKind.value,
      amplitude: Number(els.fields.amplitude.value),
      width: Number(els.fields.width.value),
      random_phase: els.fields.randomPhase.checked,
    },
    ...(base.objective ? { objective: base.objective } : {}),
    ...(base.constraints ? { constraints: base.constraints } : {}),
    ...(base.ranking ? { ranking: base.ranking } : {}),
    ...(base.campaign ? { campaign: base.campaign } : {}),
  };
}

function describeConstraint(key, value) {
  const labels = {
    max_abs_energy_drift: "Absolute energy drift cap",
    max_abs_norm_drift: "Absolute norm drift cap",
    min_max_density: "Minimum max density",
    max_elapsed_seconds: "Elapsed time cap",
    require_verification: "Verification required",
  };
  return `${labels[key] || key}: ${value}`;
}

function campaignRunCount(campaign) {
  if (!campaign?.dimensions?.length) return 0;
  return campaign.dimensions.reduce((total, dimension) => {
    const valueCount = Array.isArray(dimension.values) ? dimension.values.length : 0;
    return total * valueCount;
  }, 1);
}

function sharedExperimentContext(shared) {
  if (!shared) return "No experiment saved";
  if (shared.kind === "campaign") {
    const labels = (shared.dimensions || [])
      .map((dimension) => dimension.label || dimension.path)
      .join(" | ");
    const dimensionCount = shared.dimension_count || shared.dimensions?.length || 0;
    return labels ? `${dimensionCount}-dim campaign | ${labels}` : `${dimensionCount}-dim campaign`;
  }
  if (shared.parameter_label) {
    return `${shared.parameter_label} sweep`;
  }
  return shared.id || "Saved experiment";
}

function renderDecisionProfile(config) {
  const objective = config?.objective;
  if (!objective) {
    els.profileTitle.textContent = "No decision profile";
    els.profileMetric.textContent = "Select a study template";
    els.profileSummary.textContent =
      "Load a config template with objective, constraints, and ranking fields to launch a scored campaign.";
    els.profileGoalBadge.textContent = "No objective";
    els.profileGoalBadge.className = "status-badge is-idle";
    els.profileTargetChip.textContent = "No target";
    els.profileConstraints.innerHTML = `
      <li><strong>Template note</strong>This template only captures execution parameters, so QS-DMSS will compare runs but not recommend a winner.</li>
    `;
    return;
  }

  const constraints = config.constraints || {};
  const ranking = config.ranking || {};
  const weights = ranking.weights || {};
  const targetValue = objective.target_value === undefined ? null : objective.target_value;
  els.profileTitle.textContent = objective.name;
  els.profileMetric.textContent = `${objective.primary_metric} · ${objective.goal}`;
  els.profileSummary.textContent = objective.summary || "No objective summary provided.";
  els.profileGoalBadge.textContent = objective.goal;
  els.profileGoalBadge.className = `status-badge ${toneForStatus("qualified")}`;
  els.profileTargetChip.textContent =
    targetValue === null ? "No target value" : `Target ${targetValue}`;

  const constraintEntries = Object.entries(constraints);
  const weightEntries = Object.entries(weights);
  const items = [];
  if (constraintEntries.length) {
    items.push(
      `<li><strong>Constraints</strong>${constraintEntries
        .map(([key, value]) => describeConstraint(key, value))
        .join(" · ")}</li>`,
    );
  }
  if (weightEntries.length) {
    items.push(
      `<li><strong>Ranking</strong>Primary boost ${ranking.primary_metric_weight ?? "-"} · ${weightEntries
        .map(([metric, value]) => `${metric} ${value}`)
        .join(" · ")}</li>`,
    );
  }
  els.profileConstraints.innerHTML = items.join("");
}

function renderCampaignProfile(config) {
  const campaign = config?.campaign;
  if (!campaign) {
    els.campaignTitle.textContent = "No campaign plan";
    els.campaignRunCount.textContent = "Select a study template";
    els.campaignSummary.textContent =
      "Load a template with a campaign section to generate a multi-run search plan automatically.";
    els.campaignStrategyBadge.textContent = "No plan";
    els.campaignStrategyBadge.className = "status-badge is-idle";
    els.campaignMaxRunsChip.textContent = "0 runs";
    els.campaignDimensions.innerHTML = `
      <li><strong>Template note</strong>This template can still launch a single run or manual sweep, but it does not define an automated campaign matrix.</li>
    `;
    els.launchCampaignButton.disabled = true;
    return;
  }

  const plannedRuns = campaignRunCount(campaign);
  const dimensions = Array.isArray(campaign.dimensions) ? campaign.dimensions : [];
  els.campaignTitle.textContent = campaign.label || "Decision campaign";
  els.campaignRunCount.textContent = `${plannedRuns} planned runs`;
  els.campaignSummary.textContent =
    "QS-DMSS will expand this study into a reproducible search matrix, score every run, and save one experiment bundle with the recommended winner.";
  els.campaignStrategyBadge.textContent = campaign.strategy || "grid";
  els.campaignStrategyBadge.className = `status-badge ${toneForStatus("qualified")}`;
  els.campaignMaxRunsChip.textContent = `Max ${campaign.max_runs ?? plannedRuns} runs`;
  els.campaignDimensions.innerHTML = dimensions
    .map((dimension) => {
      const values = Array.isArray(dimension.values) ? dimension.values.map(String).join(", ") : "-";
      return `
        <li>
          <strong>${parameterLabel(dimension.path)}</strong>
          ${dimension.path} | values: ${values}
        </li>
      `;
    })
    .join("");
  els.launchCampaignButton.disabled = plannedRuns < 2;
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
    .map((item) => `<option value="${item.path}">${item.label} - ${item.path}</option>`)
    .join("");
}

function updateSelectionChip() {
  const count = state.selectedRunIds.length;
  els.selectedRunCount.textContent = `${count} selected`;
  els.saveExperimentButton.disabled = count < 2;
}

function setExperimentActionsEnabled(enabled) {
  els.openExperimentReportButton.disabled = !enabled;
  els.experimentBundleLink.style.pointerEvents = enabled ? "auto" : "none";
  els.experimentBundleLink.style.opacity = enabled ? "1" : "0.56";
  els.experimentBundleLink.tabIndex = enabled ? 0 : -1;
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
      const tone = toneForStatus(run.status);
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

function renderExperimentRegistry() {
  if (!state.experiments.length) {
    els.experimentRegistryBody.innerHTML = `
      <tr>
        <td colspan="6">No experiments saved yet.</td>
      </tr>
    `;
    return;
  }

  els.experimentRegistryBody.innerHTML = state.experiments
    .map((experiment) => {
      const selected = experiment.experiment_id === state.selectedExperimentId ? "is-selected" : "";
      const shared = experiment.shared_experiment;
      const label = shared
        ? `<div class="compare-run"><strong>${experiment.label}</strong><span>${sharedExperimentContext(shared)}</span></div>`
        : `<div class="compare-run"><strong>${experiment.label}</strong><span>${experiment.experiment_id}</span></div>`;
      return `
        <tr class="${selected}" data-experiment-id="${experiment.experiment_id}">
          <td>${label}</td>
          <td>${experiment.kind}</td>
          <td>${shortRunId(experiment.recommended_run_id)}</td>
          <td>${experiment.run_count}</td>
          <td>${formatTimestamp(experiment.created_at)}</td>
          <td>${experiment.bundle_size_label}</td>
        </tr>
      `;
    })
    .join("");

  els.experimentRegistryBody.querySelectorAll("tr[data-experiment-id]").forEach((row) => {
    row.addEventListener("click", () => {
      selectExperiment(row.dataset.experimentId);
    });
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
  els.statusBadge.className = `status-badge ${toneForStatus(detail.run_record.status)}`;
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

function renderRecommendation(decision) {
  if (!decision) {
    els.recommendationLabel.textContent = "Recommendation";
    els.recommendationRun.textContent = "No recommendation yet";
    els.recommendationReason.textContent =
      "Launch a sweep or compare runs from the same objective-driven template to get a ranked winner.";
    els.recommendationStatus.textContent = "Idle";
    els.recommendationStatus.className = "status-badge is-idle";
    els.recommendationScore.textContent = "Score -";
    return;
  }

  if (!decision.available) {
    els.recommendationLabel.textContent = "Recommendation unavailable";
    els.recommendationRun.textContent = "No ranked winner";
    els.recommendationReason.textContent = decision.reason;
    els.recommendationStatus.textContent = decision.status || "Idle";
    els.recommendationStatus.className = `status-badge ${toneForStatus(decision.status)}`;
    els.recommendationScore.textContent = "Score -";
    return;
  }

  els.recommendationLabel.textContent = decision.profile.objective.name;
  els.recommendationRun.textContent = decision.recommended_run_id;
  els.recommendationReason.textContent = decision.reason;
  els.recommendationStatus.textContent = decision.status;
  els.recommendationStatus.className = `status-badge ${toneForStatus(decision.status)}`;
  els.recommendationScore.textContent = `Score ${formatScore(decision.recommended_score)}`;
}

function renderComparison(comparison) {
  state.comparison = comparison;
  renderRecommendation(comparison?.decision || null);

  if (!comparison) {
    els.compareTitle.textContent = "Run Comparison";
    els.compareContext.textContent = "Select two or more runs";
    els.compareEnergySpan.textContent = "-";
    els.compareNormSpan.textContent = "-";
    els.compareDensitySpan.textContent = "-";
    els.compareFastestRun.textContent = "-";
    els.comparisonTableBody.innerHTML = `
      <tr>
        <td colspan="9">Select at least two runs to compare.</td>
      </tr>
    `;
    return;
  }

  const shared = comparison.shared_experiment;
  els.compareTitle.textContent = shared ? shared.label : "Run Comparison";
  els.compareContext.textContent = shared
    ? sharedExperimentContext(shared)
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
        <td>${row.decision_rank ?? "-"}</td>
        <td>${formatScore(row.decision_score)}</td>
        <td>${row.decision_qualified === undefined ? "-" : row.decision_qualified ? "yes" : "no"}</td>
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

async function refreshExperiments() {
  const payload = await fetchJson("/api/experiments");
  state.experiments = payload.items;
  const availableExperimentIds = new Set(state.experiments.map((item) => item.experiment_id));
  if (state.selectedExperimentId && !availableExperimentIds.has(state.selectedExperimentId)) {
    renderExperimentPlaceholder();
    return;
  }
  renderExperimentRegistry();
}

async function selectRun(runId) {
  const detail = await fetchJson(`/api/runs/${runId}`);
  renderSelectedRun(detail);
}

async function selectExperiment(experimentId) {
  const detail = await fetchJson(`/api/experiments/${experimentId}`);
  state.selectedRunIds = [...detail.summary.run_ids];
  renderSelectedExperiment(detail);
  renderComparison(detail.comparison);
  renderRunsTable();
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

function renderSelectedExperiment(detail) {
  state.selectedExperiment = detail;
  state.selectedExperimentId = detail.summary.experiment_id;

  els.experimentTitle.textContent = detail.summary.label;
  els.experimentContext.textContent = detail.summary.shared_experiment
    ? sharedExperimentContext(detail.summary.shared_experiment)
    : detail.summary.experiment_id;
  els.experimentKind.textContent = detail.summary.kind;
  els.experimentRunCount.textContent = String(detail.summary.run_count);
  els.experimentCreated.textContent = formatTimestamp(detail.summary.created_at);
  els.experimentRecommended.textContent = shortRunId(detail.summary.recommended_run_id);
  els.experimentDecisionStatus.textContent = detail.summary.decision_status || "-";
  els.experimentBundleSize.textContent = detail.summary.bundle_size_label;
  els.experimentBundleLink.href = detail.urls.bundle;
  els.experimentBundleLink.setAttribute("download", "");
  setExperimentActionsEnabled(true);

  renderExperimentRegistry();
}

function renderExperimentPlaceholder() {
  state.selectedExperiment = null;
  state.selectedExperimentId = null;
  els.experimentTitle.textContent = "Experiment Registry";
  els.experimentContext.textContent = "No experiment saved";
  els.experimentKind.textContent = "-";
  els.experimentRunCount.textContent = "-";
  els.experimentCreated.textContent = "-";
  els.experimentRecommended.textContent = "-";
  els.experimentDecisionStatus.textContent = "-";
  els.experimentBundleSize.textContent = "-";
  els.experimentBundleLink.href = "#";
  setExperimentActionsEnabled(false);
  renderExperimentRegistry();
}

async function hydrate() {
  const [configPayload, sweepPayload, showcasePayload, experimentPayload] = await Promise.all([
    fetchJson("/api/configs"),
    fetchJson("/api/sweeps/parameters"),
    fetchJson("/api/showcases"),
    fetchJson("/api/experiments"),
  ]);
  state.configs = configPayload.items;
  state.sweepParameters = sweepPayload.items;
  state.showcases = showcasePayload.items;
  state.experiments = experimentPayload.items;
  state.selectedTemplateName = configPayload.default_name || state.configs[0]?.name || null;
  state.selectedShowcaseName = showcasePayload.default_name || state.showcases[0]?.name || null;
  renderConfigOptions();
  renderSweepParameterOptions();
  renderShowcaseOptions();
  renderLabMode();
  renderExperimentRegistry();
  setExperimentActionsEnabled(false);

  const selectedConfig = configByName(state.selectedTemplateName);
  if (selectedConfig) {
    fillForm(selectedConfig.config);
    renderDecisionProfile(selectedConfig.config);
    renderCampaignProfile(selectedConfig.config);
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

  if (state.experiments[0]) {
    await selectExperiment(state.experiments[0].experiment_id);
  } else {
    renderExperimentPlaceholder();
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

async function handleLaunchLabMode() {
  const scenarioName = els.labScenarioSelect.value || state.selectedShowcaseName;
  if (!scenarioName) {
    toast("No showcase selected", "Choose a packaged showcase scenario first.", "danger");
    return;
  }

  setLabProgress(
    true,
    "Running the showcase now. QS-DMSS is generating the run, evidence bundle, replay, report, and artifacts.",
  );
  els.labStatus.textContent = "Running";
  els.labStatus.className = "status-badge is-warning";
  els.labVerification.textContent = "Generating evidence";
  els.labReplay.textContent = "Waiting for replay";
  setLabLinksEnabled(false);

  try {
    const payload = await fetchJson(`/api/showcases/${encodeURIComponent(scenarioName)}/run`, {
      method: "POST",
    });
    state.labResult = payload;
    state.selectedShowcaseName = payload.scenario.name;
    toast("Lab Mode complete", `Created ${payload.run.summary.run_id}`, "success");
    await refreshRuns();
    renderLabMode();
    renderSelectedRun(payload.run);
    setLabProgress(
      false,
      `Complete. Created ${shortRunId(payload.run.summary.run_id)} with report links and artifacts ready.`,
    );
  } catch (error) {
    els.labStatus.textContent = "Failed";
    els.labStatus.className = "status-badge is-danger";
    els.labVerification.textContent = "Not verified";
    els.labReplay.textContent = "Not replayed";
    setLabProgress(false, "Lab Mode failed. Review the error message and try again.");
    toast("Lab Mode failed", error.message, "danger");
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
    await refreshExperiments();
    renderComparison(payload.comparison);
    renderSelectedExperiment(payload.artifact);
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

async function handleLaunchCampaign() {
  const config = currentConfig();
  if (!config.campaign) {
    toast("No campaign plan", "Select a template with a campaign section first.", "danger");
    return;
  }

  els.launchCampaignButton.disabled = true;
  els.launchCampaignButton.textContent = "Launching...";

  try {
    const payload = await fetchJson("/api/campaigns", {
      method: "POST",
      body: JSON.stringify({
        config,
        source_name: els.configTemplate.value || "campaign.yaml",
      }),
    });
    toast("Campaign complete", `Created ${payload.runs.length} runs`, "success");
    state.selectedRunIds = payload.campaign.run_ids;
    await refreshRuns();
    await refreshExperiments();
    renderComparison(payload.comparison);
    renderSelectedExperiment(payload.artifact);
    if (payload.runs[0]) {
      await selectRun(payload.runs[0].run_id);
    }
  } catch (error) {
    toast("Campaign failed", error.message, "danger");
  } finally {
    renderCampaignProfile(configByName(state.selectedTemplateName)?.config || null);
    els.launchCampaignButton.textContent = "Launch Campaign";
  }
}

async function handleVerify() {
  if (!state.selectedRunId) return;
  try {
    const result = await fetchJson(`/api/runs/${state.selectedRunId}/verify`, { method: "POST" });
    toast(
      result.success ? "Verification passed" : "Verification failed",
      result.success ? `Checked ${result.checked_files} files` : result.errors.join(" | "),
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

async function handleSaveExperiment() {
  if (state.selectedRunIds.length < 2) {
    toast("Pick more runs", "Select at least two runs to save an experiment.", "danger");
    return;
  }

  els.saveExperimentButton.disabled = true;
  try {
    const detail = await fetchJson("/api/experiments", {
      method: "POST",
      body: JSON.stringify({ run_ids: state.selectedRunIds }),
    });
    await refreshExperiments();
    renderSelectedExperiment(detail);
    renderComparison(detail.comparison);
    toast("Experiment saved", `Created ${detail.summary.experiment_id}`, "success");
  } catch (error) {
    toast("Save failed", error.message, "danger");
  } finally {
    updateSelectionChip();
  }
}

function clearComparison() {
  state.selectedRunIds = [];
  renderRunsTable();
  renderComparison(null);
}

function openReport(url, heading) {
  if (!url) return;
  els.reportFrame.src = url;
  els.reportHeading.textContent = heading;
  els.reportDialog.showModal();
}

function openRunReport() {
  if (!state.selectedRun) return;
  openReport(state.selectedRun.urls.report, `Evidence Report - ${state.selectedRun.summary.run_id}`);
}

function openExperimentReport() {
  if (!state.selectedExperiment) return;
  openReport(
    state.selectedExperiment.urls.report,
    `Experiment Report - ${state.selectedExperiment.summary.experiment_id}`,
  );
}

function bindEvents() {
  els.labScenarioSelect.addEventListener("change", (event) => {
    state.selectedShowcaseName = event.target.value;
    state.labResult = null;
    renderLabMode();
  });

  els.launchLabButton.addEventListener("click", handleLaunchLabMode);
  els.labSelectRunButton.addEventListener("click", async () => {
    const runId = state.labResult?.run?.summary?.run_id;
    if (runId) {
      await selectRun(runId);
      document.querySelector("#artifacts")?.scrollIntoView({ behavior: "smooth" });
    }
  });

  els.loadTemplateButton.addEventListener("click", () => {
    const selected = configByName(els.configTemplate.value);
    if (selected) {
      fillForm(selected.config);
      renderDecisionProfile(selected.config);
      renderCampaignProfile(selected.config);
      toast("Template loaded", `Using ${selected.name}`, "success");
    }
  });

  els.configTemplate.addEventListener("change", (event) => {
    state.selectedTemplateName = event.target.value;
    const selected = configByName(state.selectedTemplateName);
    if (selected) {
      fillForm(selected.config);
      renderDecisionProfile(selected.config);
      renderCampaignProfile(selected.config);
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

  els.refreshExperimentsButton.addEventListener("click", async () => {
    try {
      await refreshExperiments();
      toast("Experiment registry refreshed", "Latest saved comparisons loaded.", "success");
    } catch (error) {
      toast("Refresh failed", error.message, "danger");
    }
  });

  els.compareButton.addEventListener("click", handleCompare);
  els.clearCompareButton.addEventListener("click", clearComparison);
  els.saveExperimentButton.addEventListener("click", handleSaveExperiment);
  els.launchCampaignButton.addEventListener("click", handleLaunchCampaign);
  els.launchForm.addEventListener("submit", handleLaunch);
  els.sweepForm.addEventListener("submit", handleLaunchSweep);
  els.verifyButton.addEventListener("click", handleVerify);
  els.replayButton.addEventListener("click", handleReplay);
  els.openReportButton.addEventListener("click", openRunReport);
  els.openExperimentReportButton.addEventListener("click", openExperimentReport);
}

bindEvents();

hydrate().catch((error) => {
  toast("Cockpit failed to load", error.message, "danger");
});
