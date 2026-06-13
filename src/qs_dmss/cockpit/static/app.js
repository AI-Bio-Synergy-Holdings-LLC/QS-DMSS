const state = {
  configs: [],
  showcases: [],
  campaignStudio: null,
  campaignStudioValues: {},
  campaignStudioDecisionValues: {},
  campaignStudyTemplates: [],
  selectedCampaignStudyTemplateId: null,
  activeCampaignStudyTemplate: null,
  lastCampaignStudyTemplate: null,
  lastCampaignStudioResult: null,
  runs: [],
  experiments: [],
  sweepParameters: [],
  selectedShowcaseName: null,
  labResult: null,
  labComparisonResult: null,
  researchObject: null,
  researchObjectDownloadUrl: null,
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
  scenarioRuntime: document.querySelector("#scenarioRuntime"),
  scenarioBadges: document.querySelector("#scenarioBadges"),
  scenarioPurpose: document.querySelector("#scenarioPurpose"),
  scenarioArtifacts: document.querySelector("#scenarioArtifacts"),
  scenarioLimitations: document.querySelector("#scenarioLimitations"),
  scenarioNextActions: document.querySelector("#scenarioNextActions"),
  scenarioComparisonPlan: document.querySelector("#scenarioComparisonPlan"),
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
  labComparisonStatus: document.querySelector("#labComparisonStatus"),
  labComparisonSummary: document.querySelector("#labComparisonSummary"),
  labComparisonMeaningList: document.querySelector("#labComparisonMeaningList"),
  labComparisonNonClaimList: document.querySelector("#labComparisonNonClaimList"),
  labComparisonReviewPrompt: document.querySelector("#labComparisonReviewPrompt"),
  launchLabComparisonButton: document.querySelector("#launchLabComparisonButton"),
  labComparisonReportLink: document.querySelector("#labComparisonReportLink"),
  labComparisonBundleLink: document.querySelector("#labComparisonBundleLink"),
  labComparisonProgressText: document.querySelector("#labComparisonProgressText"),
  campaignStudioStatus: document.querySelector("#campaignStudioStatus"),
  campaignStudioSummary: document.querySelector("#campaignStudioSummary"),
  campaignStudioPlan: document.querySelector("#campaignStudioPlan"),
  campaignStudioDimensions: document.querySelector("#campaignStudioDimensions"),
  campaignStudioEditor: document.querySelector("#campaignStudioEditor"),
  campaignStudioFields: document.querySelector("#campaignStudioFields"),
  campaignStudioDecisionFields: document.querySelector("#campaignStudioDecisionFields"),
  campaignStudioScoringContract: document.querySelector("#campaignStudioScoringContract"),
  campaignStudioFeedback: document.querySelector("#campaignStudioFeedback"),
  launchCampaignStudioButton: document.querySelector("#launchCampaignStudioButton"),
  resetCampaignStudioButton: document.querySelector("#resetCampaignStudioButton"),
  campaignStudioBoundary: document.querySelector("#campaignStudioBoundary"),
  campaignStudyTemplateStatus: document.querySelector("#campaignStudyTemplateStatus"),
  campaignStudyTemplateSummary: document.querySelector("#campaignStudyTemplateSummary"),
  campaignStudyTemplateSelect: document.querySelector("#campaignStudyTemplateSelect"),
  campaignStudyTemplateCards: document.querySelector("#campaignStudyTemplateCards"),
  saveCampaignStudyTemplateButton: document.querySelector("#saveCampaignStudyTemplateButton"),
  loadCampaignStudyTemplateButton: document.querySelector("#loadCampaignStudyTemplateButton"),
  runCampaignStudyTemplateButton: document.querySelector("#runCampaignStudyTemplateButton"),
  downloadCampaignStudyTemplateLink: document.querySelector("#downloadCampaignStudyTemplateLink"),
  importCampaignStudyTemplateInput: document.querySelector("#importCampaignStudyTemplateInput"),
  campaignStudyTemplateFeedback: document.querySelector("#campaignStudyTemplateFeedback"),
  labExplorerStatus: document.querySelector("#labExplorerStatus"),
  labReportPreviewTitle: document.querySelector("#labReportPreviewTitle"),
  labReportPreviewBody: document.querySelector("#labReportPreviewBody"),
  labReportMetrics: document.querySelector("#labReportMetrics"),
  labInterpretationTitle: document.querySelector("#labInterpretationTitle"),
  labInterpretationSummary: document.querySelector("#labInterpretationSummary"),
  labMeaningList: document.querySelector("#labMeaningList"),
  labNonClaimList: document.querySelector("#labNonClaimList"),
  labReviewPrompt: document.querySelector("#labReviewPrompt"),
  labEvidenceChecklist: document.querySelector("#labEvidenceChecklist"),
  labArtifactPreview: document.querySelector("#labArtifactPreview"),
  researchObjectStatus: document.querySelector("#researchObjectStatus"),
  researchObjectLede: document.querySelector("#researchObjectLede"),
  composeResearchObjectButton: document.querySelector("#composeResearchObjectButton"),
  researchObjectDownloadLink: document.querySelector("#researchObjectDownloadLink"),
  researchObjectSurface: document.querySelector("#researchObjectSurface"),
  researchObjectCta: document.querySelector("#researchObjectCta"),
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

const citationMetadata = {
  packageVersion: "0.8.0",
  releaseTag: "v0.8.0",
  conceptDoi: "10.5281/zenodo.20074924",
  releaseDoi: "10.5281/zenodo.20671389",
  releaseUrl: "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.8.0",
  pypiUrl: "https://pypi.org/project/qs-dmss/0.8.0/",
  repositoryUrl: "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS",
  openCollectiveUrl: "https://opencollective.com/qs-dmss",
  builderBoardUrl: "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/57",
  composerIssueUrl: "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/67",
};

const decisionMetricOptions = ["energy_drift", "norm_drift", "max_density", "elapsed_seconds"];
const objectiveGoalOptions = ["minimize", "minimize_abs", "maximize", "target"];
const constraintEditorFields = [
  {
    key: "max_abs_energy_drift",
    label: "Max Absolute Energy Drift",
    hint: "Optional non-negative threshold.",
    min: 0,
  },
  {
    key: "max_abs_norm_drift",
    label: "Max Absolute Norm Drift",
    hint: "Optional non-negative threshold.",
    min: 0,
  },
  {
    key: "min_max_density",
    label: "Minimum Peak Density",
    hint: "Optional lower bound for final density.",
  },
  {
    key: "max_elapsed_seconds",
    label: "Max Elapsed Seconds",
    hint: "Optional non-negative runtime threshold.",
    min: 0,
  },
];

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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

function formatRunCount(count) {
  const numeric = Number(count);
  if (!Number.isFinite(numeric)) return "0 planned runs";
  return `${numeric} planned ${numeric === 1 ? "run" : "runs"}`;
}

function parseEditorNumber(rawValue, label, errors, options = {}) {
  const text = String(rawValue ?? "").trim();
  if (!text) {
    if (options.optional) {
      return null;
    }
    errors.push(`${label} is required.`);
    return null;
  }

  const numeric = Number(text);
  if (!Number.isFinite(numeric)) {
    errors.push(`${label} must be numeric.`);
    return null;
  }
  if (options.integer && !Number.isInteger(numeric)) {
    errors.push(`${label} must be an integer.`);
  }
  if (options.min !== undefined && numeric < options.min) {
    errors.push(`${label} must be at least ${options.min}.`);
  }
  return numeric;
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
    let message = text;
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed.detail === "string") {
        message = parsed.detail;
      } else if (parsed.detail?.message) {
        message = parsed.detail.message;
      }
    } catch {
      message = text;
    }
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json();
}

async function fetchText(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.text();
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

function setLabComparisonLinksEnabled(enabled, result = null) {
  [
    [els.labComparisonReportLink, result?.urls?.report, "Open comparison report", "Report after run"],
    [els.labComparisonBundleLink, result?.urls?.bundle, "Download comparison bundle", "Bundle after run"],
  ].forEach(([link, href, readyLabel, disabledLabel]) => {
    if (enabled && href) {
      link.href = href;
      link.removeAttribute("aria-disabled");
      link.removeAttribute("tabindex");
      link.textContent = readyLabel;
      link.classList.remove("is-disabled");
    } else {
      link.removeAttribute("href");
      link.setAttribute("aria-disabled", "true");
      link.setAttribute("tabindex", "-1");
      link.textContent = disabledLabel;
      link.classList.add("is-disabled");
    }
  });
}

function setLabProgress(isRunning, message) {
  els.launchLabButton.disabled = isRunning;
  els.launchLabButton.setAttribute("aria-busy", String(isRunning));
  els.launchLabButton.textContent = isRunning ? "Running Lab Mode..." : "Run Lab Mode Showcase";
  els.labProgressShell.hidden = !isRunning;
  els.labProgressText.textContent = message;
}

function setLabComparisonProgress(isRunning, message) {
  els.launchLabComparisonButton.disabled = isRunning;
  els.launchLabComparisonButton.setAttribute("aria-busy", String(isRunning));
  els.launchLabComparisonButton.textContent = isRunning
    ? "Running Guided Comparison..."
    : "Run Guided Comparison";
  els.labComparisonProgressText.textContent = message;
}

function renderMetricPreview(metrics) {
  const rows = [
    ["Norm drift", formatScientific(metrics.norm_drift)],
    ["Energy drift", formatScientific(metrics.energy_drift)],
    ["Max density", formatScientific(metrics.max_density)],
    ["Elapsed", formatSeconds(metrics.elapsed_seconds)],
    ["History points", String(metrics.history_points)],
  ];
  els.labReportMetrics.innerHTML = rows
    .map(
      ([label, value]) => `
        <div>
          <dt>${escapeHtml(label)}</dt>
          <dd>${escapeHtml(value)}</dd>
        </div>
      `,
    )
    .join("");
}

function renderEvidenceChecklist(result) {
  const { report, run, replay_run: replayRun } = result;
  const replay = report.replay;
  const evidenceItems = [
    {
      tone: "is-success",
      label: "Evidence bundle",
      detail: `${run.evidence.bundle_size_label} bundle with ${run.evidence.file_count} manifest files.`,
    },
    {
      tone: report.verification.success ? "is-success" : "is-danger",
      label: "Verification",
      detail: report.verification.success
        ? `${report.verification.checked_files} files verified from the run directory.`
        : `${report.verification.errors.length} verification error(s) reported.`,
    },
    {
      tone: replay?.final_density_allclose ? "is-success" : "is-warning",
      label: "Replay",
      detail: replayRun
        ? `Replay ${shortRunId(replayRun.summary.run_id)} ${
            replay.final_density_allclose ? "matched final density." : "needs review."
          }`
        : "Replay was skipped for this showcase run.",
    },
    {
      tone: report.success ? "is-success" : "is-warning",
      label: "Research object",
      detail: report.success
        ? "Report, artifacts, evidence bundle, and replay status are ready to inspect."
        : "The generated research object needs review before sharing.",
    },
  ];
  els.labEvidenceChecklist.innerHTML = evidenceItems
    .map(
      (item) => `
        <li>
          <span class="status-pill ${item.tone}">${escapeHtml(item.label)}</span>
          <p>${escapeHtml(item.detail)}</p>
        </li>
      `,
    )
    .join("");
}

function renderPlainList(element, items) {
  element.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderGuidedInterpretation(report) {
  const interpretation = report?.interpretation;
  if (!interpretation) {
    els.labInterpretationTitle.textContent = "Run showcase first";
    els.labInterpretationSummary.textContent =
      "Plain-language scenario interpretation appears here after Lab Mode completes.";
    renderPlainList(els.labMeaningList, ["Run the showcase to generate interpretation notes."]);
    renderPlainList(els.labNonClaimList, ["The scientific claim boundary appears here after the run."]);
    els.labReviewPrompt.textContent = "Reviewer prompts appear here after evidence is generated.";
    return;
  }

  els.labInterpretationTitle.textContent = "What the canonical simulation is showing";
  els.labInterpretationSummary.textContent = interpretation.plain_language_summary;
  renderPlainList(els.labMeaningList, interpretation.what_this_result_means);
  renderPlainList(els.labNonClaimList, interpretation.what_this_result_does_not_claim);
  els.labReviewPrompt.textContent = interpretation.review_prompt;
}

function renderLabGuidedComparison(result) {
  if (!result) {
    els.labComparisonStatus.textContent = "Not run yet";
    els.labComparisonStatus.className = "selection-chip";
    els.labComparisonSummary.textContent =
      "Run baseline, wider-packet, and stronger-interaction variants with the same deterministic seed, then inspect the evidence deltas and exported comparison report.";
    renderPlainList(els.labComparisonMeaningList, [
      "Run Guided Comparison to generate variant deltas.",
    ]);
    renderPlainList(els.labComparisonNonClaimList, [
      "The comparison claim boundary appears after the variants complete.",
    ]);
    els.labComparisonReviewPrompt.textContent =
      "Reviewer prompts appear after the comparison report is generated.";
    setLabComparisonLinksEnabled(false);
    return;
  }

  const guide = result.guide;
  const runCount = result.runs?.length || result.comparison?.rows?.length || 0;
  els.labComparisonStatus.textContent = `${runCount} variants compared`;
  els.labComparisonStatus.className = "selection-chip";
  els.labComparisonSummary.textContent = guide.plain_language_summary;
  renderPlainList(els.labComparisonMeaningList, [
    ...(guide.what_changed || []),
    ...(guide.what_to_inspect || []),
  ]);
  renderPlainList(els.labComparisonNonClaimList, guide.what_this_does_not_claim || []);
  els.labComparisonReviewPrompt.textContent = guide.review_prompt;
  setLabComparisonLinksEnabled(true, result);
}

function parseCsvPreview(text, rowLimit = 4, columnLimit = 5) {
  return text
    .trim()
    .split(/\r?\n/)
    .slice(0, rowLimit + 1)
    .map((line) => line.split(",").slice(0, columnLimit));
}

function csvPreviewMarkup(text) {
  const rows = parseCsvPreview(text);
  if (!rows.length) {
    return "<p>No CSV rows found.</p>";
  }
  const [headers, ...bodyRows] = rows;
  return `
    <table class="lab-csv-preview-table">
      <thead>
        <tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${bodyRows
          .map(
            (row) => `
              <tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

async function loadCsvPreview(item, index, runId) {
  const target = els.labArtifactPreview.querySelector(`[data-csv-index="${index}"]`);
  if (!target) return;
  try {
    const text = await fetchText(item.url);
    if (state.labResult?.run?.summary?.run_id !== runId) return;
    target.innerHTML = csvPreviewMarkup(text);
  } catch (error) {
    target.innerHTML = `<p>CSV preview unavailable: ${escapeHtml(error.message)}</p>`;
  }
}

function artifactCalloutByKey(callouts) {
  return new Map((callouts || []).map((item) => [item.artifact_key, item]));
}

function artifactCalloutMarkup(callout) {
  if (!callout) return "";
  return `
    <div class="lab-artifact-callout">
      <strong>${escapeHtml(callout.title)}</strong>
      <p>${escapeHtml(callout.callout)}</p>
      <span>${escapeHtml(callout.why_it_matters)}</span>
    </div>
  `;
}

function renderArtifactPreviews(artifactLinks, runId, callouts = []) {
  const previewable = artifactLinks.filter(
    (item) => item.previewable || ["csv", "svg"].includes(item.kind),
  );
  if (!previewable.length) {
    els.labArtifactPreview.innerHTML = "<p>No previewable SVG or CSV artifacts were generated.</p>";
    return;
  }

  const calloutMap = artifactCalloutByKey(callouts);
  els.labArtifactPreview.innerHTML = previewable
    .map((item, index) => {
      const title = escapeHtml(item.label);
      const name = escapeHtml(item.name);
      const callout = artifactCalloutMarkup(calloutMap.get(item.key));
      if (item.kind === "svg") {
        return `
          <figure class="lab-artifact-preview-item">
            <figcaption>
              <strong>${title}</strong>
              <span>${name}</span>
            </figcaption>
            ${callout}
            <img src="${escapeHtml(item.url)}" alt="${title} preview" loading="lazy" />
          </figure>
        `;
      }
      if (item.kind === "csv") {
        return `
          <section class="lab-artifact-preview-item">
            <header>
              <strong>${title}</strong>
              <span>${name}</span>
            </header>
            ${callout}
            <div class="lab-csv-preview" data-csv-index="${index}">
              <p>Loading first rows...</p>
            </div>
          </section>
        `;
      }
      return "";
    })
    .join("");

  previewable.forEach((item, index) => {
    if (item.kind === "csv") {
      loadCsvPreview(item, index, runId);
    }
  });
}

function renderLabEvidenceExplorer(result) {
  if (!result) {
    els.labExplorerStatus.textContent = "Run showcase first";
    els.labReportPreviewTitle.textContent = "No showcase report yet";
    els.labReportPreviewBody.textContent =
      "Run Lab Mode to summarize the simulation narrative, claim boundary, and key numerical diagnostics directly inside the cockpit.";
    els.labReportMetrics.innerHTML = "";
    els.labEvidenceChecklist.innerHTML =
      "<li>Verification, replay, and bundle status appear after the showcase run.</li>";
    els.labArtifactPreview.innerHTML =
      "<p>SVG plots and CSV first rows appear here after Lab Mode completes.</p>";
    renderGuidedInterpretation(null);
    return;
  }

  const { report, artifact_links: artifactLinks } = result;
  els.labExplorerStatus.textContent = report.success ? "Research object ready" : "Needs review";
  els.labReportPreviewTitle.textContent = `${report.scenario} report summary`;
  els.labReportPreviewBody.textContent = `${report.scenario_narrative} ${report.claim_boundary}`;
  renderGuidedInterpretation(report);
  renderMetricPreview(report.metrics);
  renderEvidenceChecklist(result);
  renderArtifactPreviews(
    artifactLinks,
    result.run.summary.run_id,
    report.interpretation?.artifact_callouts || [],
  );
}

function clearResearchObject() {
  if (state.researchObjectDownloadUrl) {
    URL.revokeObjectURL(state.researchObjectDownloadUrl);
  }
  state.researchObject = null;
  state.researchObjectDownloadUrl = null;
}

function setResearchObjectDownloadEnabled(enabled) {
  const link = els.researchObjectDownloadLink;
  if (enabled && state.researchObjectDownloadUrl && state.researchObject) {
    link.href = state.researchObjectDownloadUrl;
    link.download = state.researchObject.fileName;
    link.removeAttribute("aria-disabled");
    link.removeAttribute("tabindex");
    link.textContent = "Download Markdown";
    link.classList.remove("is-disabled");
    return;
  }

  link.removeAttribute("href");
  link.removeAttribute("download");
  link.setAttribute("aria-disabled", "true");
  link.setAttribute("tabindex", "-1");
  link.textContent = "Download after compose";
  link.classList.add("is-disabled");
}

function selectedCampaignStudyTemplateSummary() {
  return (
    state.campaignStudyTemplates.find(
      (item) => item.template_id === state.selectedCampaignStudyTemplateId,
    ) || null
  );
}

function setCampaignStudyTemplateDownloadEnabled(summary) {
  const link = els.downloadCampaignStudyTemplateLink;
  if (summary?.urls?.download) {
    link.href = summary.urls.download;
    link.download = `${summary.template_id}.json`;
    link.removeAttribute("aria-disabled");
    link.removeAttribute("tabindex");
    link.textContent = "Download JSON";
    link.classList.remove("is-disabled");
    return;
  }

  link.removeAttribute("href");
  link.removeAttribute("download");
  link.setAttribute("aria-disabled", "true");
  link.setAttribute("tabindex", "-1");
  link.textContent = "Download JSON";
  link.classList.add("is-disabled");
}

function campaignStudyTemplateLastRunMarkup(item) {
  const lastRun = item.last_run;
  if (!lastRun) {
    return `
      <div class="campaign-study-template-last-run is-empty">
        <strong>No run provenance yet</strong>
        <span>Run this saved template to attach a recommendation, report, and bundle.</span>
      </div>
    `;
  }

  return `
    <div class="campaign-study-template-last-run">
      <strong>Last run ${escapeHtml(formatTimestamp(lastRun.ran_at))}</strong>
      <span>
        Recommended ${escapeHtml(shortRunId(lastRun.recommended_run_id))}
        from ${escapeHtml(lastRun.run_count || item.planned_run_count || "-")} runs.
      </span>
      <span>${escapeHtml(lastRun.reason || "Recommendation rationale was not recorded.")}</span>
      <div class="research-object-link-row">
        <a href="${escapeHtml(lastRun.experiment_report_url || "#")}" target="_blank" rel="noreferrer">
          Open last report
        </a>
        <a href="${escapeHtml(lastRun.experiment_bundle_url || "#")}" target="_blank" rel="noreferrer">
          Download last bundle
        </a>
      </div>
    </div>
  `;
}

function campaignStudyTemplateCardMarkup(item, selected) {
  const importStatus = item.imported
    ? `Imported from ${shortRunId(item.imported_from_template_id)}`
    : "Local template";
  const exportStatus = item.exportable ? "Export-ready JSON" : "Export pending";
  return `
    <article
      class="campaign-study-template-card ${selected ? "is-selected" : ""}"
      data-study-template-id="${escapeHtml(item.template_id)}"
      role="button"
      tabindex="0"
      aria-pressed="${selected ? "true" : "false"}"
    >
      <div class="campaign-study-template-card-head">
        <div>
          <p class="artifact-list-title">${escapeHtml(importStatus)}</p>
          <h5>${escapeHtml(item.label)}</h5>
        </div>
        <span class="scenario-badge ${selected ? "is-success" : "is-warning"}">
          ${selected ? "Selected" : "Reusable"}
        </span>
      </div>
      <p>${escapeHtml(item.description || "Reusable Campaign Studio study template.")}</p>
      <dl class="campaign-study-template-meta">
        <div>
          <dt>Objective</dt>
          <dd>${escapeHtml(item.objective_name || "Not documented")}</dd>
        </div>
        <div>
          <dt>Metric / goal</dt>
          <dd>${escapeHtml(item.primary_metric || "-")} / ${escapeHtml(item.goal || "-")}</dd>
        </div>
        <div>
          <dt>Plan</dt>
          <dd>${escapeHtml(formatRunCount(item.planned_run_count))}</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>${escapeHtml(formatTimestamp(item.created_at))}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>${escapeHtml(item.source_config_name || "campaign-study.yaml")}</dd>
        </div>
        <div>
          <dt>Portability</dt>
          <dd>${escapeHtml(exportStatus)}</dd>
        </div>
      </dl>
      ${campaignStudyTemplateLastRunMarkup(item)}
    </article>
  `;
}

function renderCampaignStudyTemplates() {
  const summaries = state.campaignStudyTemplates || [];
  const selected = selectedCampaignStudyTemplateSummary();
  els.campaignStudyTemplateStatus.textContent = summaries.length
    ? `${summaries.length} saved`
    : "No templates";
  els.campaignStudyTemplateStatus.className = `selection-chip ${toneForStatus(
    summaries.length ? "qualified" : "idle",
  )}`;
  els.campaignStudyTemplateSelect.innerHTML = summaries.length
    ? summaries
        .map(
          (item) => `
            <option
              value="${escapeHtml(item.template_id)}"
              ${item.template_id === state.selectedCampaignStudyTemplateId ? "selected" : ""}
            >
              ${escapeHtml(item.label)} (${escapeHtml(formatRunCount(item.planned_run_count))})
            </option>
          `,
        )
        .join("")
    : '<option value="">No saved templates yet</option>';

  if (state.selectedCampaignStudyTemplateId) {
    els.campaignStudyTemplateSelect.value = state.selectedCampaignStudyTemplateId;
  }
  els.campaignStudyTemplateCards.innerHTML = summaries.length
    ? summaries
        .map((item) => (
          campaignStudyTemplateCardMarkup(
            item,
            item.template_id === state.selectedCampaignStudyTemplateId,
          )
        ))
        .join("")
    : `
        <article class="campaign-study-template-card is-empty">
          <p class="artifact-list-title">Portable campaign design</p>
          <h5>No saved study templates yet</h5>
          <p>
            Save the edited grid and decision profile to create a reusable local
            JSON study. The JSON can be imported by another QS-DMSS user to rerun
            the same campaign design and inspect the same scoring contract.
          </p>
          <p>
            After a saved template runs, this library will show the latest
            recommendation, experiment report, and evidence bundle links.
          </p>
        </article>
      `;

  const draft = state.campaignStudio?.available
    ? campaignStudioDraft(state.campaignStudio)
    : { valid: false };
  els.saveCampaignStudyTemplateButton.disabled = !draft.valid;
  els.loadCampaignStudyTemplateButton.disabled = !selected;
  els.runCampaignStudyTemplateButton.disabled = !selected;
  setCampaignStudyTemplateDownloadEnabled(selected);
  els.campaignStudyTemplateSummary.textContent = selected
    ? `${selected.label}: ${formatRunCount(selected.planned_run_count)} scored by ${selected.primary_metric} (${selected.goal}). ${selected.last_run ? `Last run recommended ${shortRunId(selected.last_run.recommended_run_id)}.` : "Run it once to attach provenance."}`
    : "Save edited grids and decision profiles as reusable local JSON templates that another user can import and rerun.";
  els.campaignStudyTemplateFeedback.textContent = selected
    ? `Selected template ${selected.template_id}. Load it to edit, run it directly, or download portable JSON for another user.`
    : "Templates preserve the grid, scoring contract, launchable campaign config, and latest run provenance.";
}

async function refreshCampaignStudyTemplates() {
  const payload = await fetchJson("/api/campaign-studies");
  state.campaignStudyTemplates = payload.items || [];
  if (
    state.selectedCampaignStudyTemplateId &&
    !state.campaignStudyTemplates.some(
      (item) => item.template_id === state.selectedCampaignStudyTemplateId,
    )
  ) {
    state.selectedCampaignStudyTemplateId = null;
  }
  if (!state.selectedCampaignStudyTemplateId && state.campaignStudyTemplates[0]) {
    state.selectedCampaignStudyTemplateId = state.campaignStudyTemplates[0].template_id;
  }
  renderCampaignStudyTemplates();
}

function metricRowsForResearchObject(metrics) {
  return [
    ["Norm drift", formatScientific(metrics.norm_drift)],
    ["Relative norm drift", formatScientific(metrics.relative_norm_drift)],
    ["Energy drift", formatScientific(metrics.energy_drift)],
    ["Relative energy drift", formatScientific(metrics.relative_energy_drift)],
    ["Final max density", formatScientific(metrics.max_density)],
    ["Elapsed", formatSeconds(metrics.elapsed_seconds)],
    ["History points", String(metrics.history_points)],
  ];
}

function evidenceRowsForResearchObject(result) {
  const { report, run, replay_run: replayRun } = result;
  const replay = report.replay;
  return [
    {
      label: "Evidence bundle",
      status: run.evidence.bundle_size_label,
      detail: `${run.evidence.file_count} manifest files are available for audit.`,
    },
    {
      label: "Verification",
      status: report.verification.success ? "PASS" : "REVIEW",
      detail: report.verification.success
        ? `${report.verification.checked_files} files verified from the run directory.`
        : `${report.verification.errors.length} verification error(s) require inspection.`,
    },
    {
      label: "Replay",
      status: replay?.final_density_allclose ? "PASS" : "REVIEW",
      detail: replayRun
        ? `Replay ${shortRunId(replayRun.summary.run_id)} ${
            replay.final_density_allclose ? "matched final density." : "needs review."
          }`
        : "Replay was skipped for this showcase run.",
    },
    {
      label: "Claim boundary",
      status: "Scoped",
      detail: report.claim_boundary,
    },
  ];
}

function artifactRowsForResearchObject(artifactLinks) {
  return (artifactLinks || []).map((item) => ({
    label: item.label,
    name: item.name,
    kind: item.kind === "svg" ? "Figure" : "Data",
    url: item.url,
  }));
}

function comparisonRowsForResearchObject(result) {
  return (result?.comparison?.rows || []).map((row) => ({
    label: row.parameter_value_label || row.config_name || row.run_id,
    runId: row.run_id,
    energyDrift: formatScientific(row.energy_drift),
    normDrift: formatScientific(row.norm_drift),
    maxDensity: formatScientific(row.max_density),
    energyDelta: formatSignedScientific(row.delta_from_baseline?.energy_drift),
  }));
}

function buildResearchObjectMarkdown(researchObject) {
  const lines = [
    "# QS-DMSS Research Object Export",
    "",
    `Generated: ${researchObject.generatedAt}`,
    `Scenario: ${researchObject.scenario.label}`,
    `Run ID: ${researchObject.runId}`,
    `Package: qs-dmss==${citationMetadata.packageVersion}`,
    "",
    "## Scenario",
    "",
    researchObject.scenario.description,
    "",
    `Claim boundary: ${researchObject.claimBoundary}`,
    "",
    "## Key Metrics",
    "",
    "| Metric | Value |",
    "| --- | ---: |",
    ...researchObject.metrics.map(([label, value]) => `| ${label} | ${value} |`),
    "",
    "## Evidence Status",
    "",
    "| Check | Status | Detail |",
    "| --- | --- | --- |",
    ...researchObject.evidence.map(
      (item) => `| ${item.label} | ${item.status} | ${item.detail} |`,
    ),
    "",
    "## Figures And Artifacts",
    "",
    "| Type | Artifact | Local cockpit link |",
    "| --- | --- | --- |",
    ...researchObject.artifacts.map(
      (item) => `| ${item.kind} | ${item.label} (${item.name}) | ${item.url} |`,
    ),
    "",
    "## Guided Interpretation",
    "",
    researchObject.interpretation.summary,
    "",
    "What this result means:",
    ...researchObject.interpretation.means.map((item) => `- ${item}`),
    "",
    "What this result does not claim:",
    ...researchObject.interpretation.nonClaims.map((item) => `- ${item}`),
    "",
  ];

  if (researchObject.comparison.available) {
    lines.push(
      "## Guided Comparison",
      "",
      researchObject.comparison.summary,
      "",
      "| Variant | Run ID | Energy drift | Norm drift | Max density | Energy delta |",
      "| --- | --- | ---: | ---: | ---: | ---: |",
      ...researchObject.comparison.rows.map(
        (row) =>
          `| ${row.label} | ${row.runId} | ${row.energyDrift} | ${row.normDrift} | ${row.maxDensity} | ${row.energyDelta} |`,
      ),
      "",
      `Comparison report: ${researchObject.comparison.reportUrl}`,
      `Comparison bundle: ${researchObject.comparison.bundleUrl}`,
      "",
    );
  }

  if (researchObject.campaignStudy.available) {
    const study = researchObject.campaignStudy;
    const contract = study.scoringContract || {};
    const objective = contract.objective || {};
    const constraints = Object.entries(contract.constraints || {})
      .map(([key, value]) => `${key}: ${value}`)
      .join("; ");
    const weights = Object.entries(contract.ranking?.weights || {})
      .map(([key, value]) => `${key}: ${value}`)
      .join("; ");
    lines.push(
      "## Campaign Study Template",
      "",
      `Template: ${study.label}`,
      `Template ID: ${study.templateId}`,
      `Source config: ${study.sourceConfigName}`,
      `Description: ${study.description}`,
      "",
      "### Scoring Contract",
      "",
      `Objective: ${objective.name || "Not documented"}`,
      `Primary metric: ${objective.primary_metric || "Not documented"} (${objective.goal || "not documented"})`,
      `Constraints: ${constraints || "none"}`,
      `Weights: ${weights || "none"}; primary boost ${contract.ranking?.primary_metric_weight ?? "not documented"}`,
      `Launch envelope: ${contract.planned_run_count || "-"} planned runs, max ${contract.max_runs || "-"}`,
      "",
      "### Recommendation",
      "",
      `Status: ${study.recommendation.status}`,
      `Recommended run: ${study.recommendation.recommendedRunId || "Not available"}`,
      `Reason: ${study.recommendation.reason}`,
      study.reportUrl ? `Campaign report: ${study.reportUrl}` : "",
      study.bundleUrl ? `Campaign bundle: ${study.bundleUrl}` : "",
      "",
    );
  }

  lines.push(
    "## Replay Instructions",
    "",
    "```powershell",
    ...researchObject.replayCommands,
    "```",
    "",
    "## Citation",
    "",
    `Project DOI: https://doi.org/${citationMetadata.conceptDoi}`,
    `Latest archived release DOI: https://doi.org/${citationMetadata.releaseDoi}`,
    `Repository: ${citationMetadata.repositoryUrl}`,
    `Release: ${citationMetadata.releaseUrl}`,
    `PyPI: ${citationMetadata.pypiUrl}`,
    "",
    "## Build Participation",
    "",
    `Open Collective: ${citationMetadata.openCollectiveUrl}`,
    `Builder board: ${citationMetadata.builderBoardUrl}`,
    `Export composer issue: ${citationMetadata.composerIssueUrl}`,
    "",
  );

  return `${lines.join("\n")}\n`;
}

function buildResearchObject() {
  const result = state.labResult;
  const comparison = state.labComparisonResult;
  const report = result.report;
  const run = result.run;
  const runId = run.summary.run_id;
  const scenario = result.scenario;
  const interpretation = report.interpretation || {};
  const researchObject = {
    generatedAt: new Date().toISOString(),
    scenario: {
      label: scenario.label || report.scenario,
      name: scenario.name || report.scenario,
      description: scenario.description || report.scenario_narrative,
    },
    runId,
    claimBoundary: report.claim_boundary,
    status: report.success ? "Ready" : "Needs review",
    metrics: metricRowsForResearchObject(report.metrics),
    evidence: evidenceRowsForResearchObject(result),
    artifacts: artifactRowsForResearchObject(result.artifact_links),
    interpretation: {
      summary: interpretation.plain_language_summary || report.scenario_narrative,
      means: interpretation.what_this_result_means || [],
      nonClaims: interpretation.what_this_result_does_not_claim || [report.claim_boundary],
      reviewPrompt: interpretation.review_prompt || "Review the generated evidence before citing.",
    },
    comparison: {
      available: Boolean(comparison),
      summary: comparison?.guide?.plain_language_summary || "",
      rows: comparisonRowsForResearchObject(comparison),
      reportUrl: comparison?.urls?.report || "",
      bundleUrl: comparison?.urls?.bundle || "",
    },
    campaignStudy: campaignStudyForResearchObject(),
    replayCommands: [
      `qs-dmss verify "${report.run.run_dir}"`,
      `qs-dmss replay "${report.run.run_dir}" --output-root "replays"`,
      `qs-dmss showcase run --output-root "${report.output_root}"`,
    ],
  };
  const fileStem = `${researchObject.scenario.name}-${shortRunId(runId)}-research-object`;
  researchObject.fileName = `${fileStem}.md`;
  researchObject.markdown = buildResearchObjectMarkdown(researchObject);
  return researchObject;
}

function researchObjectMetricsMarkup(researchObject) {
  return researchObject.metrics
    .map(
      ([label, value]) => `
        <div>
          <dt>${escapeHtml(label)}</dt>
          <dd>${escapeHtml(value)}</dd>
        </div>
      `,
    )
    .join("");
}

function researchObjectEvidenceMarkup(researchObject) {
  return researchObject.evidence
    .map(
      (item) => `
        <li>
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.status)}</strong>
          <p>${escapeHtml(item.detail)}</p>
        </li>
      `,
    )
    .join("");
}

function researchObjectArtifactMarkup(researchObject) {
  return researchObject.artifacts
    .map(
      (item) => `
        <li>
          <span>${escapeHtml(item.kind)}</span>
          <a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">
            ${escapeHtml(item.label)}
          </a>
          <code>${escapeHtml(item.name)}</code>
        </li>
      `,
    )
    .join("");
}

function researchObjectComparisonMarkup(researchObject) {
  if (!researchObject.comparison.available) {
    return `
      <p>
        Guided Comparison has not been run yet. Compose again after comparison to add
        variant deltas and comparison bundle links.
      </p>
    `;
  }
  return `
    <p>${escapeHtml(researchObject.comparison.summary)}</p>
    <div class="research-object-table-wrap">
      <table class="research-object-comparison-table">
        <thead>
          <tr>
            <th>Variant</th>
            <th>Run</th>
            <th>Energy drift</th>
            <th>Norm drift</th>
            <th>Energy delta</th>
          </tr>
        </thead>
        <tbody>
          ${researchObject.comparison.rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(row.label)}</td>
                  <td>${escapeHtml(shortRunId(row.runId))}</td>
                  <td>${escapeHtml(row.energyDrift)}</td>
                  <td>${escapeHtml(row.normDrift)}</td>
                  <td>${escapeHtml(row.energyDelta)}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
    <div class="research-object-link-row">
      <a href="${escapeHtml(researchObject.comparison.reportUrl)}" target="_blank" rel="noreferrer">
        Open comparison report
      </a>
      <a href="${escapeHtml(researchObject.comparison.bundleUrl)}" target="_blank" rel="noreferrer">
        Download comparison bundle
      </a>
    </div>
  `;
}

function researchObjectCampaignStudyMarkup(researchObject) {
  const study = researchObject.campaignStudy;
  if (!study.available) {
    return `
      <p>
        Campaign Studio has not been run yet. Run or load a saved study template to attach
        campaign metadata, scoring contract, and recommendation rationale.
      </p>
    `;
  }

  const contract = study.scoringContract || {};
  const objective = contract.objective || {};
  const constraintText = Object.entries(contract.constraints || {})
    .map(([key, value]) => `${key}: ${value}`)
    .join(" | ");
  const weightText = Object.entries(contract.ranking?.weights || {})
    .map(([key, value]) => `${key}: ${value}`)
    .join(" | ");
  return `
    <p>${escapeHtml(study.description)}</p>
    <dl class="lab-report-metrics">
      <div>
        <dt>Template</dt>
        <dd>${escapeHtml(study.label)}</dd>
      </div>
      <div>
        <dt>Template ID</dt>
        <dd>${escapeHtml(study.templateId)}</dd>
      </div>
      <div>
        <dt>Objective</dt>
        <dd>${escapeHtml(objective.name || "Not documented")}</dd>
      </div>
      <div>
        <dt>Primary Metric</dt>
        <dd>${escapeHtml(objective.primary_metric || "-")} / ${escapeHtml(objective.goal || "-")}</dd>
      </div>
      <div>
        <dt>Launch Envelope</dt>
        <dd>${escapeHtml(contract.planned_run_count || "-")} planned, max ${escapeHtml(contract.max_runs || "-")}</dd>
      </div>
      <div>
        <dt>Recommendation</dt>
        <dd>${escapeHtml(shortRunId(study.recommendation.recommendedRunId))} (${escapeHtml(study.recommendation.status)})</dd>
      </div>
    </dl>
    <p><strong>Constraints:</strong> ${escapeHtml(constraintText || "none")}</p>
    <p><strong>Weights:</strong> ${escapeHtml(weightText || "none")} | primary boost ${escapeHtml(contract.ranking?.primary_metric_weight ?? "-")}</p>
    <p><strong>Recommendation rationale:</strong> ${escapeHtml(study.recommendation.reason)}</p>
    <div class="research-object-link-row">
      ${
        study.reportUrl
          ? `<a href="${escapeHtml(study.reportUrl)}" target="_blank" rel="noreferrer">Open campaign report</a>`
          : ""
      }
      ${
        study.bundleUrl
          ? `<a href="${escapeHtml(study.bundleUrl)}" target="_blank" rel="noreferrer">Download campaign bundle</a>`
          : ""
      }
    </div>
  `;
}

function renderResearchObjectSurface(researchObject) {
  const statusTone = researchObject.status === "Ready" ? "is-success" : "is-warning";
  els.researchObjectSurface.innerHTML = `
    <header class="research-object-head">
      <div>
        <p class="artifact-list-title">Shareable Report Surface</p>
        <h4>${escapeHtml(researchObject.scenario.label)} research object</h4>
        <p>
          Run ${escapeHtml(researchObject.runId)} exported with evidence status,
          replay instructions, artifact links, comparison context, and DOI citation metadata.
        </p>
      </div>
      <span class="status-badge ${statusTone}">${escapeHtml(researchObject.status)}</span>
    </header>
    <div class="research-object-grid">
      <section class="research-object-card">
        <p class="artifact-list-title">Scenario</p>
        <h5>${escapeHtml(researchObject.scenario.label)}</h5>
        <p>${escapeHtml(researchObject.scenario.description)}</p>
        <p class="research-object-boundary">${escapeHtml(researchObject.claimBoundary)}</p>
      </section>
      <section class="research-object-card">
        <p class="artifact-list-title">Metrics</p>
        <dl class="lab-report-metrics">${researchObjectMetricsMarkup(researchObject)}</dl>
      </section>
      <section class="research-object-card">
        <p class="artifact-list-title">Evidence And Replay</p>
        <ul class="research-object-evidence-list">${researchObjectEvidenceMarkup(researchObject)}</ul>
      </section>
      <section class="research-object-card">
        <p class="artifact-list-title">Figures And Data</p>
        <ul class="research-object-artifact-list">${researchObjectArtifactMarkup(researchObject)}</ul>
      </section>
      <section class="research-object-card research-object-wide">
        <p class="artifact-list-title">Guided Interpretation</p>
        <p>${escapeHtml(researchObject.interpretation.summary)}</p>
        <div class="lab-interpretation-grid">
          <article>
            <p class="artifact-list-title">What It Means</p>
            <ul>${researchObject.interpretation.means
              .map((item) => `<li>${escapeHtml(item)}</li>`)
              .join("")}</ul>
          </article>
          <article>
            <p class="artifact-list-title">What It Does Not Claim</p>
            <ul>${researchObject.interpretation.nonClaims
              .map((item) => `<li>${escapeHtml(item)}</li>`)
              .join("")}</ul>
          </article>
        </div>
      </section>
      <section class="research-object-card research-object-wide">
        <p class="artifact-list-title">Guided Comparison</p>
        ${researchObjectComparisonMarkup(researchObject)}
      </section>
      <section class="research-object-card research-object-wide">
        <p class="artifact-list-title">Campaign Study Template</p>
        ${researchObjectCampaignStudyMarkup(researchObject)}
      </section>
      <section class="research-object-card">
        <p class="artifact-list-title">Replay Instructions</p>
        <pre><code>${escapeHtml(researchObject.replayCommands.join("\n"))}</code></pre>
      </section>
      <section class="research-object-card">
        <p class="artifact-list-title">Citation</p>
        <p>
          Cite the project DOI
          <a href="https://doi.org/${citationMetadata.conceptDoi}" target="_blank" rel="noreferrer">
            ${citationMetadata.conceptDoi}
          </a>
          or the latest archived release DOI
          <a href="https://doi.org/${citationMetadata.releaseDoi}" target="_blank" rel="noreferrer">
            ${citationMetadata.releaseDoi}
          </a>.
        </p>
        <div class="research-object-link-row">
          <a href="${citationMetadata.repositoryUrl}" target="_blank" rel="noreferrer">Repository</a>
          <a href="${citationMetadata.releaseUrl}" target="_blank" rel="noreferrer">GitHub release</a>
          <a href="${citationMetadata.pypiUrl}" target="_blank" rel="noreferrer">PyPI package</a>
        </div>
      </section>
    </div>
  `;
}

function renderResearchObjectComposer() {
  const hasLabResult = Boolean(state.labResult);
  els.composeResearchObjectButton.disabled = !hasLabResult;
  els.composeResearchObjectButton.textContent = state.researchObject
    ? "Recompose Research Object"
    : "Compose Research Object";
  els.researchObjectCta.hidden = !state.researchObject;
  setResearchObjectDownloadEnabled(Boolean(state.researchObject));

  if (!hasLabResult) {
    els.researchObjectStatus.textContent = "Run showcase first";
    els.researchObjectStatus.className = "selection-chip";
    els.researchObjectLede.textContent =
      "Compose a shareable research object after Lab Mode generates scenario, evidence, replay, artifact, and citation metadata.";
    els.researchObjectSurface.innerHTML = `
      <p>
        Your publication-grade summary will appear here after export, including metrics,
        figure links, evidence status, replay instructions, and citation metadata.
      </p>
    `;
    return;
  }

  if (!state.researchObject) {
    els.researchObjectStatus.textContent = state.labComparisonResult
      ? "Ready with comparison"
      : "Ready to compose";
    els.researchObjectStatus.className = "selection-chip";
    els.researchObjectLede.textContent = state.labComparisonResult
      ? "Lab Mode and Guided Comparison are ready. Compose a research object with variant deltas and comparison bundle links."
      : "Lab Mode is ready. Compose a research object now, or run Guided Comparison first to include variant deltas.";
    els.researchObjectSurface.innerHTML = `
      <div class="research-object-placeholder">
        <strong>Export will include</strong>
        <ul>
          <li>Scenario narrative, metrics, and claim boundary.</li>
          <li>Evidence bundle, verification, replay status, and artifact links.</li>
          <li>DOI citation block for QS-DMSS ${citationMetadata.releaseTag} and the latest archived DOI.</li>
          <li>Guided Comparison details if they have been generated.</li>
          <li>Campaign Studio study template, scoring contract, and recommendation rationale if a campaign has been run.</li>
        </ul>
      </div>
    `;
    return;
  }

  els.researchObjectStatus.textContent = "Export composed";
  els.researchObjectStatus.className = "selection-chip";
  els.researchObjectLede.textContent =
    "This research object is ready to share as a reviewer-facing Markdown export or inspect directly in the cockpit.";
  renderResearchObjectSurface(state.researchObject);
}

function handleComposeResearchObject() {
  if (!state.labResult) {
    return;
  }
  clearResearchObject();
  state.researchObject = buildResearchObject();
  state.researchObjectDownloadUrl = URL.createObjectURL(
    new Blob([state.researchObject.markdown], { type: "text/markdown" }),
  );
  renderResearchObjectComposer();
  toast("Research object composed", "Markdown export and citation block are ready.", "success");
}

function renderBadgeRow(container, badges, emptyText) {
  const items = Array.isArray(badges) ? badges : [];
  container.innerHTML = items.length
    ? items
        .map((badge) => {
          const status = badge.status || "planned";
          const tone = status === "ready" ? "is-success" : "is-warning";
          return `<span class="scenario-badge ${tone}">${escapeHtml(badge.label || status)}</span>`;
        })
        .join("")
    : `<span class="scenario-badge is-idle">${escapeHtml(emptyText)}</span>`;
}

function renderMetadataList(container, items, emptyText) {
  const values = Array.isArray(items) ? items : [];
  container.innerHTML = values.length
    ? values
        .map((item) => {
          if (typeof item === "string") {
            return `<li>${escapeHtml(item)}</li>`;
          }
          return `
            <li>
              <strong>${escapeHtml(item.label || item.name || "Item")}</strong>
              ${escapeHtml(item.description || item.value || "")}
            </li>
          `;
        })
        .join("")
    : `<li>${escapeHtml(emptyText)}</li>`;
}

function renderScenarioLibrary(scenario) {
  if (!scenario) {
    els.scenarioRuntime.textContent = "No scenario";
    els.scenarioPurpose.textContent =
      "Choose a packaged scenario to see purpose, outputs, readiness, and limitations.";
    renderBadgeRow(els.scenarioBadges, [], "No metadata");
    renderMetadataList(els.scenarioArtifacts, [], "Scenario outputs appear here.");
    renderMetadataList(els.scenarioLimitations, [], "Scenario limitations appear here.");
    renderMetadataList(els.scenarioNextActions, [], "Suggested next actions appear here.");
    els.scenarioComparisonPlan.textContent =
      "Guided comparison metadata appears when a packaged scenario is selected.";
    return;
  }

  const comparison = scenario.guided_comparison || {};
  const dimensions = (comparison.dimensions || [])
    .map((dimension) => dimension.label || dimension.path)
    .join(", ");
  const variantLabels = (comparison.variants || [])
    .map((variant) => variant.label)
    .join(", ");
  els.scenarioRuntime.textContent = scenario.expected_runtime || "Runtime target pending";
  els.scenarioPurpose.textContent = scenario.purpose || scenario.description || "No purpose documented yet.";
  renderBadgeRow(els.scenarioBadges, scenario.readiness_badges, "Metadata pending");
  renderMetadataList(
    els.scenarioArtifacts,
    scenario.output_artifacts,
    "No output artifacts documented yet.",
  );
  renderMetadataList(
    els.scenarioLimitations,
    scenario.limitations,
    "No scenario limitations documented yet.",
  );
  renderMetadataList(
    els.scenarioNextActions,
    scenario.next_actions,
    "No suggested next actions documented yet.",
  );
  els.scenarioComparisonPlan.textContent = comparison.planned_run_count
    ? `${comparison.label}: ${comparison.planned_run_count} packaged variants (${variantLabels}) across ${dimensions}.`
    : "Guided comparison metadata is not available for this scenario yet.";
}

function defaultCampaignStudioValues(preview = state.campaignStudio) {
  return Object.fromEntries(
    (preview?.dimensions || []).map((dimension) => [
      dimension.path,
      (dimension.values || []).map(String).join(", "),
    ]),
  );
}

function ensureCampaignStudioValues(preview = state.campaignStudio) {
  const defaults = defaultCampaignStudioValues(preview);
  const nextValues = {};
  Object.entries(defaults).forEach(([path, value]) => {
    nextValues[path] = state.campaignStudioValues[path] ?? value;
  });
  state.campaignStudioValues = nextValues;
}

function defaultCampaignStudioDecisionValues(preview = state.campaignStudio) {
  const objective = preview?.objective || {};
  const constraints = preview?.constraint_values || {};
  const ranking = preview?.ranking || {};
  const weights = ranking.weights || {};
  const defaults = {
    objective_name: objective.name || "",
    objective_summary: objective.summary || "",
    primary_metric: objective.primary_metric || decisionMetricOptions[0],
    goal: objective.goal || "minimize_abs",
    target_value: objective.target_value ?? "",
    max_runs: preview?.max_runs ?? preview?.planned_run_count ?? 2,
    require_verification: constraints.require_verification ?? true,
    primary_metric_weight: ranking.primary_metric_weight ?? 2,
  };

  constraintEditorFields.forEach((field) => {
    defaults[field.key] = constraints[field.key] ?? "";
  });
  decisionMetricOptions.forEach((metric) => {
    defaults[`weight_${metric}`] = weights[metric] ?? 0;
  });
  return defaults;
}

function ensureCampaignStudioDecisionValues(preview = state.campaignStudio) {
  const defaults = defaultCampaignStudioDecisionValues(preview);
  const nextValues = {};
  Object.entries(defaults).forEach(([key, value]) => {
    nextValues[key] = state.campaignStudioDecisionValues[key] ?? value;
  });
  state.campaignStudioDecisionValues = nextValues;
}

function campaignStudioDecisionProfile(preview, errors) {
  ensureCampaignStudioDecisionValues(preview);
  const values = state.campaignStudioDecisionValues;
  const objectiveName = String(values.objective_name || "").trim();
  const objectiveSummary = String(values.objective_summary || "").trim();
  const supportedMetrics = preview?.objective?.supported_metrics || decisionMetricOptions;
  const supportedGoals = preview?.objective?.supported_goals || objectiveGoalOptions;
  const primaryMetric = String(values.primary_metric || "").trim();
  const goal = String(values.goal || "").trim();

  if (!objectiveName) {
    errors.push("Objective name is required.");
  }
  if (!supportedMetrics.includes(primaryMetric)) {
    errors.push(`Primary metric must be one of: ${supportedMetrics.join(", ")}.`);
  }
  if (!supportedGoals.includes(goal)) {
    errors.push(`Objective goal must be one of: ${supportedGoals.join(", ")}.`);
  }

  const targetValue = goal === "target"
    ? parseEditorNumber(values.target_value, "Target value", errors)
    : null;
  const constraints = {
    require_verification: Boolean(values.require_verification),
  };
  constraintEditorFields.forEach((field) => {
    const parsed = parseEditorNumber(values[field.key], field.label, errors, {
      optional: true,
      min: field.min,
    });
    if (parsed !== null) {
      constraints[field.key] = parsed;
    }
  });

  const primaryMetricWeight = parseEditorNumber(
    values.primary_metric_weight,
    "Primary metric boost",
    errors,
    { min: 0 },
  );
  const weights = {};
  decisionMetricOptions.forEach((metric) => {
    weights[metric] = parseEditorNumber(
      values[`weight_${metric}`],
      `${metric} weight`,
      errors,
      { min: 0 },
    ) ?? 0;
  });
  const effectiveWeightTotal = Object.entries(weights).reduce(
    (total, [metric, weight]) => (
      total + weight + (metric === primaryMetric ? (primaryMetricWeight ?? 0) : 0)
    ),
    0,
  );
  if (effectiveWeightTotal <= 0) {
    errors.push("At least one ranking weight or primary metric boost must be greater than zero.");
  }

  const objective = {
    name: objectiveName,
    summary: objectiveSummary,
    primary_metric: primaryMetric,
    goal,
  };
  if (targetValue !== null) {
    objective.target_value = targetValue;
  }

  return {
    objective,
    constraints,
    ranking: {
      primary_metric_weight: primaryMetricWeight ?? 0,
      weights,
    },
    effectiveWeightTotal,
  };
}

function campaignStudioBaseConfig() {
  const sourceName = state.campaignStudio?.source_config_name;
  return configByName(sourceName)?.config || configByName(state.selectedTemplateName)?.config || null;
}

function campaignStudioDraft(preview = state.campaignStudio) {
  if (!preview?.available) {
    return {
      valid: false,
      plannedRuns: 0,
      maxRuns: 0,
      dimensions: [],
      errors: ["Campaign Studio is not configured."],
    };
  }

  ensureCampaignStudioValues(preview);
  const errors = [];
  const dimensions = (preview.dimensions || []).map((dimension) => {
    const rawValue = state.campaignStudioValues[dimension.path] || "";
    const values = parseSweepValues(rawValue);
    if (!values.length) {
      errors.push(`${dimension.label || dimension.path} needs at least one value.`);
    }
    return {
      path: dimension.path,
      label: dimension.label || parameterLabel(dimension.path),
      description: dimension.description || "",
      value_type: dimension.value_type,
      values,
    };
  });

  const plannedRuns = dimensions.reduce(
    (total, dimension) => total * Math.max(dimension.values.length, 0),
    dimensions.length ? 1 : 0,
  );
  const decisionProfile = campaignStudioDecisionProfile(preview, errors);
  const maxRuns = parseEditorNumber(
    state.campaignStudioDecisionValues.max_runs,
    "Max runs",
    errors,
    { integer: true, min: 2 },
  ) ?? 0;
  if (plannedRuns < 2) {
    errors.push("Campaign Studio needs at least two planned runs.");
  }
  if (maxRuns > 0 && plannedRuns > maxRuns) {
    errors.push(`Campaign Studio plans ${plannedRuns} runs, exceeding max ${maxRuns}.`);
  }

  return {
    valid: errors.length === 0,
    plannedRuns,
    maxRuns,
    dimensions,
    decisionProfile,
    errors,
  };
}

function campaignStudioConfigFromDraft(draft) {
  const baseConfig = campaignStudioBaseConfig();
  if (!baseConfig) {
    throw new Error("No campaign-enabled base config is available.");
  }
  const config = cloneJson(baseConfig);
  config.campaign = {
    ...(config.campaign || {}),
    label: state.campaignStudio?.label || config.campaign?.label || "Campaign Studio grid",
    strategy: state.campaignStudio?.strategy || config.campaign?.strategy || "grid",
    max_runs: draft.maxRuns || config.campaign?.max_runs || draft.plannedRuns,
    dimensions: draft.dimensions.map((dimension) => ({
      path: dimension.path,
      values: [...dimension.values],
    })),
  };
  config.objective = draft.decisionProfile.objective;
  config.constraints = draft.decisionProfile.constraints;
  config.ranking = draft.decisionProfile.ranking;
  return config;
}

function campaignStudyTemplateFromDraft(draft) {
  const config = campaignStudioConfigFromDraft(draft);
  const objective = draft.decisionProfile.objective;
  return {
    label: `${state.campaignStudio?.label || "Campaign Studio"} - ${objective.primary_metric} ${draft.plannedRuns}-run study`,
    description:
      objective.summary ||
      "Reusable Campaign Studio study template created from the cockpit editor.",
    source_config_name: "campaign-study.yaml",
    campaign: {
      label: config.campaign.label,
      strategy: config.campaign.strategy,
      max_runs: config.campaign.max_runs,
      planned_run_count: draft.plannedRuns,
      dimension_count: draft.dimensions.length,
      dimensions: draft.dimensions,
    },
    objective,
    constraints: draft.decisionProfile.constraints,
    ranking: draft.decisionProfile.ranking,
    scoring_contract: {
      objective,
      constraints: draft.decisionProfile.constraints,
      ranking: draft.decisionProfile.ranking,
      planned_run_count: draft.plannedRuns,
      max_runs: draft.maxRuns,
    },
    config,
  };
}

function campaignStudyDecisionValuesFromConfig(config) {
  const objective = config.objective || {};
  const constraints = config.constraints || {};
  const ranking = config.ranking || {};
  const weights = ranking.weights || {};
  const values = {
    objective_name: objective.name || "",
    objective_summary: objective.summary || "",
    primary_metric: objective.primary_metric || decisionMetricOptions[0],
    goal: objective.goal || "minimize_abs",
    target_value: objective.target_value ?? "",
    max_runs: config.campaign?.max_runs ?? state.campaignStudio?.max_runs ?? 2,
    require_verification: constraints.require_verification ?? true,
    primary_metric_weight: ranking.primary_metric_weight ?? 0,
  };
  constraintEditorFields.forEach((field) => {
    values[field.key] = constraints[field.key] ?? "";
  });
  decisionMetricOptions.forEach((metric) => {
    values[`weight_${metric}`] = weights[metric] ?? 0;
  });
  return values;
}

function applyCampaignStudyTemplate(template) {
  const config = template?.config;
  if (!config?.campaign?.dimensions) {
    throw new Error("Selected study template does not include a campaign config.");
  }
  state.campaignStudioValues = Object.fromEntries(
    config.campaign.dimensions.map((dimension) => [
      dimension.path,
      (dimension.values || []).map(String).join(", "),
    ]),
  );
  state.campaignStudioDecisionValues = campaignStudyDecisionValuesFromConfig(config);
  state.activeCampaignStudyTemplate = template;
  renderCampaignStudioPreview(state.campaignStudio);
}

function campaignStudyForResearchObject() {
  const template = state.lastCampaignStudyTemplate || state.activeCampaignStudyTemplate;
  const campaignResult = state.lastCampaignStudioResult;
  const decision = campaignResult?.comparison?.decision || campaignResult?.artifact?.decision || null;
  const campaign = template?.campaign || campaignResult?.campaign || null;
  const scoringContract = template?.scoring_contract || {
    objective: template?.objective || decision?.profile?.objective || null,
    constraints: template?.constraints || decision?.profile?.constraints || null,
    ranking: template?.ranking || decision?.profile?.ranking || null,
    planned_run_count: campaign?.planned_run_count || null,
    max_runs: campaign?.max_runs || null,
  };
  const recommendation = decision
    ? {
        available: Boolean(decision.available),
        status: decision.status || "unknown",
        recommendedRunId: decision.recommended_run_id || campaignResult?.campaign?.recommended_run_id,
        reason: decision.reason || "Recommendation rationale not available.",
        score: decision.recommended_score,
      }
    : {
        available: false,
        status: "not run",
        recommendedRunId: null,
        reason: "Run a Campaign Studio template to attach recommendation rationale.",
        score: null,
      };

  return {
    available: Boolean(template || campaignResult),
    templateId: template?.template_id || "unsaved-campaign-studio-draft",
    label: template?.label || campaign?.label || "Campaign Studio study",
    description: template?.description || "Campaign Studio design used for objective-driven comparison.",
    sourceConfigName: template?.source_config_name || "campaign-study.yaml",
    campaign,
    scoringContract,
    recommendation,
    reportUrl: campaignResult?.artifact?.urls?.report || "",
    bundleUrl: campaignResult?.artifact?.urls?.bundle || "",
  };
}

function renderCampaignStudioFields(preview) {
  const dimensions = preview?.dimensions || [];
  if (!dimensions.length) {
    els.campaignStudioFields.innerHTML = "<p>No editable campaign dimensions are available.</p>";
    return;
  }

  ensureCampaignStudioValues(preview);
  els.campaignStudioFields.innerHTML = dimensions
    .map((dimension) => {
      const label = dimension.label || parameterLabel(dimension.path);
      const rawValue = state.campaignStudioValues[dimension.path] || "";
      return `
        <label class="field campaign-studio-field">
          <span>${escapeHtml(label)}</span>
          <input
            type="text"
            value="${escapeHtml(rawValue)}"
            data-campaign-path="${escapeHtml(dimension.path)}"
            aria-label="${escapeHtml(label)} campaign values"
          />
          <small>${escapeHtml(dimension.path)} | comma-separated ${escapeHtml(dimension.value_type || "numeric")} values</small>
        </label>
      `;
    })
    .join("");
}

function optionMarkup(options, selectedValue) {
  return options
    .map((option) => `
      <option value="${escapeHtml(option)}" ${option === selectedValue ? "selected" : ""}>
        ${escapeHtml(option)}
      </option>
    `)
    .join("");
}

function renderCampaignStudioDecisionFields(preview) {
  if (!preview?.available) {
    els.campaignStudioDecisionFields.innerHTML =
      "<p>No editable decision profile is available.</p>";
    return;
  }

  ensureCampaignStudioDecisionValues(preview);
  const values = state.campaignStudioDecisionValues;
  const supportedMetrics = preview.objective?.supported_metrics || decisionMetricOptions;
  const supportedGoals = preview.objective?.supported_goals || objectiveGoalOptions;
  const constraintFields = constraintEditorFields
    .map((field) => `
      <label class="field campaign-studio-field">
        <span>${escapeHtml(field.label)}</span>
        <input
          type="number"
          step="any"
          ${field.min !== undefined ? `min="${escapeHtml(field.min)}"` : ""}
          value="${escapeHtml(values[field.key])}"
          data-campaign-profile="${escapeHtml(field.key)}"
          aria-label="${escapeHtml(field.label)} constraint"
        />
        <small>${escapeHtml(field.hint)}</small>
      </label>
    `)
    .join("");
  const rankingFields = decisionMetricOptions
    .map((metric) => `
      <label class="field campaign-studio-field">
        <span>${escapeHtml(metric)} weight</span>
        <input
          type="number"
          min="0"
          step="0.1"
          value="${escapeHtml(values[`weight_${metric}`])}"
          data-campaign-profile="${escapeHtml(`weight_${metric}`)}"
          aria-label="${escapeHtml(metric)} ranking weight"
        />
        <small>Non-negative contribution to the recommendation score.</small>
      </label>
    `)
    .join("");

  els.campaignStudioDecisionFields.innerHTML = `
    <label class="field campaign-studio-field">
      <span>Objective Name</span>
      <input
        type="text"
        value="${escapeHtml(values.objective_name)}"
        data-campaign-profile="objective_name"
        aria-label="Objective name"
      />
      <small>Shown in evidence bundles and comparison reports.</small>
    </label>
    <label class="field campaign-studio-field">
      <span>Objective Summary</span>
      <textarea
        data-campaign-profile="objective_summary"
        aria-label="Objective summary"
      >${escapeHtml(values.objective_summary)}</textarea>
      <small>Plain-language reason for this scoring profile.</small>
    </label>
    <label class="field campaign-studio-field">
      <span>Primary Metric</span>
      <select data-campaign-profile="primary_metric" aria-label="Primary metric">
        ${optionMarkup(supportedMetrics, values.primary_metric)}
      </select>
      <small>The metric QS-DMSS emphasizes in the recommendation.</small>
    </label>
    <label class="field campaign-studio-field">
      <span>Goal</span>
      <select data-campaign-profile="goal" aria-label="Objective goal">
        ${optionMarkup(supportedGoals, values.goal)}
      </select>
      <small>Use target when a specific numeric target matters.</small>
    </label>
    <label class="field campaign-studio-field">
      <span>Target Value</span>
      <input
        type="number"
        step="any"
        value="${escapeHtml(values.target_value)}"
        data-campaign-profile="target_value"
        aria-label="Target value"
      />
      <small>Required only when goal is target.</small>
    </label>
    <label class="field campaign-studio-field">
      <span>Max Runs</span>
      <input
        type="number"
        min="2"
        step="1"
        value="${escapeHtml(values.max_runs)}"
        data-campaign-profile="max_runs"
        aria-label="Campaign max runs"
      />
      <small>Safety cap before launching the edited campaign.</small>
    </label>
    ${constraintFields}
    <div class="field campaign-studio-field campaign-studio-toggle">
      <span>Evidence Verification</span>
      <label>
        <input
          type="checkbox"
          ${values.require_verification ? "checked" : ""}
          data-campaign-profile="require_verification"
          aria-label="Require evidence verification"
        />
        Require verification success
      </label>
      <small>When enabled, failed evidence verification disqualifies a run.</small>
    </div>
    <label class="field campaign-studio-field">
      <span>Primary Metric Boost</span>
      <input
        type="number"
        min="0"
        step="0.1"
        value="${escapeHtml(values.primary_metric_weight)}"
        data-campaign-profile="primary_metric_weight"
        aria-label="Primary metric boost"
      />
      <small>Extra weight added to the selected primary metric.</small>
    </label>
    ${rankingFields}
  `;
}

function renderCampaignStudioScoringContract(draft) {
  if (!draft?.decisionProfile) {
    els.campaignStudioScoringContract.textContent = "Scoring contract preview appears here.";
    return;
  }
  const profile = draft.decisionProfile;
  const activeConstraints = Object.entries(profile.constraints)
    .filter(([key]) => key !== "require_verification")
    .map(([key, value]) => `${key}: ${value}`);
  if (profile.constraints.require_verification) {
    activeConstraints.push("require_verification: true");
  }
  const positiveWeights = Object.entries(profile.ranking.weights)
    .filter(([, value]) => Number(value) > 0)
    .map(([metric, value]) => `${metric}: ${value}`);
  const targetText = profile.objective.target_value !== undefined
    ? ` target ${profile.objective.target_value}`
    : "";

  els.campaignStudioScoringContract.innerHTML = `
    <strong>Scoring Contract Preview</strong>
    <ul>
      <li>Objective: ${escapeHtml(profile.objective.name || "Unnamed objective")}</li>
      <li>Primary metric: ${escapeHtml(profile.objective.primary_metric)} · ${escapeHtml(profile.objective.goal)}${escapeHtml(targetText)}</li>
      <li>Constraints: ${escapeHtml(activeConstraints.join(" · ") || "none")}</li>
      <li>Weights: ${escapeHtml(positiveWeights.join(" · ") || "none")} · primary boost ${escapeHtml(profile.ranking.primary_metric_weight)}</li>
      <li>Launch envelope: ${escapeHtml(formatRunCount(draft.plannedRuns))} with max ${escapeHtml(draft.maxRuns)}</li>
    </ul>
  `;
}

function updateCampaignStudioEditorState(preview = state.campaignStudio) {
  const draft = campaignStudioDraft(preview);
  if (!preview?.available) {
    els.campaignStudioStatus.textContent = "Not configured";
    els.campaignStudioStatus.className = "selection-chip";
    els.campaignStudioFeedback.textContent = draft.errors[0];
    renderCampaignStudioScoringContract(draft);
    els.launchCampaignStudioButton.disabled = true;
    els.resetCampaignStudioButton.disabled = true;
    renderCampaignStudyTemplates();
    return draft;
  }

  const hasGridError = draft.errors.some((error) => (
    error.includes("needs at least one value") ||
    error.includes("needs at least two planned runs") ||
    error.includes("plans") ||
    error.includes("Max runs")
  ));
  els.campaignStudioStatus.textContent = draft.valid
    ? formatRunCount(draft.plannedRuns)
    : hasGridError ? "Grid needs review" : "Profile needs review";
  els.campaignStudioStatus.className = `selection-chip ${toneForStatus(draft.valid ? "qualified" : "failed")}`;
  els.campaignStudioPlan.textContent =
    `${preview.label} uses a ${preview.strategy} strategy with ${draft.dimensions.length} editable dimensions, ${formatRunCount(draft.plannedRuns)}, max ${draft.maxRuns}, and objective "${draft.decisionProfile.objective.name}".`;
  els.campaignStudioFeedback.textContent = draft.valid
    ? `Ready to launch ${draft.plannedRuns} variants optimized for ${draft.decisionProfile.objective.primary_metric} (${draft.decisionProfile.objective.goal}).`
    : draft.errors[0];
  renderCampaignStudioScoringContract(draft);
  els.launchCampaignStudioButton.disabled = !draft.valid;
  els.resetCampaignStudioButton.disabled = false;
  renderCampaignStudyTemplates();
  return draft;
}

function renderCampaignStudioPreview(preview) {
  if (!preview?.available) {
    els.campaignStudioStatus.textContent = "Not configured";
    els.campaignStudioStatus.className = "selection-chip";
    els.campaignStudioSummary.textContent =
      preview?.summary || "Campaign Studio metadata appears when a campaign-enabled template is available.";
    els.campaignStudioPlan.textContent = preview?.current_boundary || "No campaign plan available.";
    renderMetadataList(
      els.campaignStudioDimensions,
      preview?.next_capabilities || [],
      "Campaign capabilities appear here.",
    );
    els.campaignStudioBoundary.textContent =
      "Add campaign metadata to make Scenario Library entries launch configurable studies.";
    els.campaignStudioFields.innerHTML = "<p>No editable campaign dimensions are available.</p>";
    els.campaignStudioDecisionFields.innerHTML =
      "<p>No editable decision profile is available.</p>";
    els.campaignStudioScoringContract.textContent = "Scoring contract preview appears here.";
    els.campaignStudioFeedback.textContent = "Campaign Studio is not configured.";
    els.launchCampaignStudioButton.disabled = true;
    els.resetCampaignStudioButton.disabled = true;
    return;
  }

  els.campaignStudioSummary.textContent = preview.summary;
  renderMetadataList(
    els.campaignStudioDimensions,
    preview.dimensions.map((dimension) => ({
      label: dimension.label,
      description: `${dimension.path} | values: ${(dimension.values || []).join(", ")}`,
    })),
    "No campaign dimensions documented yet.",
  );
  renderCampaignStudioFields(preview);
  renderCampaignStudioDecisionFields(preview);
  updateCampaignStudioEditorState(preview);
  els.campaignStudioBoundary.textContent = preview.current_boundary;
}

function renderLabMode() {
  const scenario = showcaseByName(state.selectedShowcaseName);
  els.labScenarioSummary.textContent =
    scenario?.purpose ||
    scenario?.description ||
    "Choose a packaged showcase to create a run, replay, artifacts, and a report.";
  els.labScenarioMeta.textContent = scenario
    ? `${scenario.grid_label} | ${scenario.steps} steps | ${scenario.expected_runtime}`
    : "No packaged showcase selected";
  renderScenarioLibrary(scenario);
  renderCampaignStudioPreview(state.campaignStudio);

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
    renderLabGuidedComparison(state.labComparisonResult);
    renderLabEvidenceExplorer(null);
    renderResearchObjectComposer();
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
  renderLabGuidedComparison(state.labComparisonResult);
  renderLabEvidenceExplorer(state.labResult);
  renderResearchObjectComposer();
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
  const [
    configPayload,
    sweepPayload,
    showcasePayload,
    experimentPayload,
    campaignStudyPayload,
  ] = await Promise.all([
    fetchJson("/api/configs"),
    fetchJson("/api/sweeps/parameters"),
    fetchJson("/api/showcases"),
    fetchJson("/api/experiments"),
    fetchJson("/api/campaign-studies"),
  ]);
  state.configs = configPayload.items;
  state.sweepParameters = sweepPayload.items;
  state.showcases = showcasePayload.items;
  state.campaignStudio = showcasePayload.campaign_studio || null;
  state.experiments = experimentPayload.items;
  state.campaignStudyTemplates = campaignStudyPayload.items || [];
  state.selectedCampaignStudyTemplateId = state.campaignStudyTemplates[0]?.template_id || null;
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
    clearResearchObject();
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

async function handleLaunchLabComparison() {
  const scenarioName = els.labScenarioSelect.value || state.selectedShowcaseName;
  if (!scenarioName) {
    toast("No showcase selected", "Choose a packaged showcase scenario first.", "danger");
    return;
  }

  setLabComparisonProgress(
    true,
    "Running three deterministic variants and building the comparison evidence bundle.",
  );
  els.labComparisonStatus.textContent = "Running";
  els.labComparisonStatus.className = "selection-chip";
  setLabComparisonLinksEnabled(false);

  try {
    const payload = await fetchJson(`/api/showcases/${encodeURIComponent(scenarioName)}/compare`, {
      method: "POST",
    });
    clearResearchObject();
    state.labComparisonResult = payload;
    state.selectedShowcaseName = payload.scenario.name;
    await refreshRuns();
    await refreshExperiments();
    renderLabMode();
    renderComparison(payload.comparison);
    renderSelectedExperiment(payload.artifact);
    setLabComparisonProgress(
      false,
      `Comparison complete. Created ${payload.artifact.summary.experiment_id}.`,
    );
    toast(
      "Guided comparison ready",
      `Compared ${payload.comparison.rows.length} packaged variants`,
      "success",
    );
  } catch (error) {
    els.labComparisonStatus.textContent = "Failed";
    els.labComparisonStatus.className = "selection-chip";
    setLabComparisonProgress(false, "Guided Comparison failed. Review the error and try again.");
    toast("Guided comparison failed", error.message, "danger");
  }
}

async function runCampaignStudioConfig({
  config,
  sourceName,
  studyTemplate = null,
  pendingMessage,
  successTitle,
}) {
  els.launchCampaignStudioButton.disabled = true;
  els.runCampaignStudyTemplateButton.disabled = true;
  els.launchCampaignStudioButton.textContent = "Launching...";
  els.runCampaignStudyTemplateButton.textContent = "Running...";
  els.campaignStudioFeedback.textContent = pendingMessage;
  let completedPayload = null;

  try {
    const payload = await fetchJson("/api/campaigns", {
      method: "POST",
      body: JSON.stringify({
        config,
        source_name: sourceName,
        ...(studyTemplate?.template_id ? { study_template_id: studyTemplate.template_id } : {}),
      }),
    });
    completedPayload = payload;
    clearResearchObject();
    if (payload.study_template) {
      state.selectedCampaignStudyTemplateId = payload.study_template.summary.template_id;
      state.activeCampaignStudyTemplate = payload.study_template.template;
      state.lastCampaignStudyTemplate = payload.study_template.template;
    } else {
      state.lastCampaignStudyTemplate = studyTemplate;
    }
    state.lastCampaignStudioResult = payload;
    toast(successTitle, `Created ${payload.runs.length} scored campaign runs`, "success");
    state.selectedRunIds = payload.campaign.run_ids;
    await refreshRuns();
    await refreshExperiments();
    if (payload.study_template) {
      await refreshCampaignStudyTemplates();
    }
    renderComparison(payload.comparison);
    renderSelectedExperiment(payload.artifact);
    if (payload.runs[0]) {
      await selectRun(payload.runs[0].run_id);
    }
    els.campaignStudioFeedback.textContent =
      `Edited decision campaign launched: ${payload.campaign.planned_run_count} variants, recommended ${shortRunId(payload.campaign.recommended_run_id)}.`;
    renderResearchObjectComposer();
  } catch (error) {
    updateCampaignStudioEditorState();
    toast("Campaign Studio failed", error.message, "danger");
  } finally {
    els.launchCampaignStudioButton.textContent = "Launch Edited Campaign";
    els.runCampaignStudyTemplateButton.textContent = "Run Saved Template";
    const finalDraft = updateCampaignStudioEditorState();
    if (completedPayload) {
      els.campaignStudioFeedback.textContent =
        `Edited decision campaign launched: ${completedPayload.campaign.planned_run_count} variants, recommended ${shortRunId(completedPayload.campaign.recommended_run_id)}.`;
      els.launchCampaignStudioButton.disabled = !finalDraft.valid;
    }
  }
}

async function handleLaunchCampaignStudio(event) {
  event.preventDefault();
  const draft = campaignStudioDraft();
  if (!draft.valid) {
    updateCampaignStudioEditorState();
    toast("Campaign Studio needs review", draft.errors[0], "danger");
    return;
  }

  const studyTemplate = campaignStudyTemplateFromDraft(draft);
  await runCampaignStudioConfig({
    config: studyTemplate.config,
    sourceName: studyTemplate.source_config_name,
    studyTemplate,
    pendingMessage:
      "Running the edited campaign and saving an objective-driven recommendation bundle.",
    successTitle: "Campaign Studio complete",
  });
}

async function handleSaveCampaignStudyTemplate() {
  const draft = campaignStudioDraft();
  if (!draft.valid) {
    updateCampaignStudioEditorState();
    toast("Template needs review", draft.errors[0], "danger");
    return;
  }

  els.saveCampaignStudyTemplateButton.disabled = true;
  els.saveCampaignStudyTemplateButton.textContent = "Saving...";
  try {
    const payload = await fetchJson("/api/campaign-studies", {
      method: "POST",
      body: JSON.stringify({ template: campaignStudyTemplateFromDraft(draft) }),
    });
    state.selectedCampaignStudyTemplateId = payload.summary.template_id;
    state.activeCampaignStudyTemplate = payload.template;
    await refreshCampaignStudyTemplates();
    toast("Study template saved", `${payload.summary.label} is ready to reopen or export.`, "success");
  } catch (error) {
    toast("Save failed", error.message, "danger");
  } finally {
    els.saveCampaignStudyTemplateButton.textContent = "Save Study Template";
    updateCampaignStudioEditorState();
  }
}

async function loadCampaignStudyTemplateDetail(templateId = state.selectedCampaignStudyTemplateId) {
  if (!templateId) {
    throw new Error("Select a saved study template first.");
  }
  return fetchJson(`/api/campaign-studies/${encodeURIComponent(templateId)}`);
}

async function handleLoadCampaignStudyTemplate() {
  try {
    const payload = await loadCampaignStudyTemplateDetail();
    state.selectedCampaignStudyTemplateId = payload.summary.template_id;
    applyCampaignStudyTemplate(payload.template);
    toast("Study template loaded", `${payload.summary.label} is ready to edit or run.`, "success");
  } catch (error) {
    toast("Load failed", error.message, "danger");
  }
}

async function handleRunCampaignStudyTemplate() {
  try {
    const payload = await loadCampaignStudyTemplateDetail();
    state.selectedCampaignStudyTemplateId = payload.summary.template_id;
    applyCampaignStudyTemplate(payload.template);
    await runCampaignStudioConfig({
      config: payload.template.config,
      sourceName: payload.summary.source_config_name || "campaign-study.yaml",
      studyTemplate: payload.template,
      pendingMessage:
        "Running the saved study template and attaching its scoring contract to the recommendation bundle.",
      successTitle: "Saved study launched",
    });
  } catch (error) {
    toast("Saved study failed", error.message, "danger");
  }
}

async function handleImportCampaignStudyTemplate(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  try {
    const template = JSON.parse(await file.text());
    const payload = await fetchJson("/api/campaign-studies/import", {
      method: "POST",
      body: JSON.stringify({ template }),
    });
    state.selectedCampaignStudyTemplateId = payload.summary.template_id;
    state.activeCampaignStudyTemplate = payload.template;
    await refreshCampaignStudyTemplates();
    applyCampaignStudyTemplate(payload.template);
    toast("Study template imported", `${payload.summary.label} is ready to rerun.`, "success");
  } catch (error) {
    toast("Import failed", error.message, "danger");
  } finally {
    event.target.value = "";
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
    state.labComparisonResult = null;
    clearResearchObject();
    renderLabMode();
  });

  els.launchLabButton.addEventListener("click", handleLaunchLabMode);
  els.launchLabComparisonButton.addEventListener("click", handleLaunchLabComparison);
  els.campaignStudioEditor.addEventListener("submit", handleLaunchCampaignStudio);
  els.campaignStudioFields.addEventListener("input", (event) => {
    const input = event.target.closest("[data-campaign-path]");
    if (!input) {
      return;
    }
    state.campaignStudioValues[input.dataset.campaignPath] = input.value;
    updateCampaignStudioEditorState();
  });
  els.campaignStudioDecisionFields.addEventListener("input", (event) => {
    const input = event.target.closest("[data-campaign-profile]");
    if (!input) {
      return;
    }
    state.campaignStudioDecisionValues[input.dataset.campaignProfile] =
      input.type === "checkbox" ? input.checked : input.value;
    updateCampaignStudioEditorState();
  });
  els.campaignStudioDecisionFields.addEventListener("change", (event) => {
    const input = event.target.closest("[data-campaign-profile]");
    if (!input) {
      return;
    }
    state.campaignStudioDecisionValues[input.dataset.campaignProfile] =
      input.type === "checkbox" ? input.checked : input.value;
    updateCampaignStudioEditorState();
  });
  els.resetCampaignStudioButton.addEventListener("click", () => {
    state.campaignStudioValues = defaultCampaignStudioValues();
    state.campaignStudioDecisionValues = defaultCampaignStudioDecisionValues();
    state.activeCampaignStudyTemplate = null;
    renderCampaignStudioPreview(state.campaignStudio);
    toast("Campaign Studio reset", "Packaged grid and decision profile restored.", "success");
  });
  els.campaignStudyTemplateSelect.addEventListener("change", (event) => {
    state.selectedCampaignStudyTemplateId = event.target.value || null;
    renderCampaignStudyTemplates();
  });
  els.campaignStudyTemplateCards.addEventListener("click", (event) => {
    if (event.target.closest("a")) {
      return;
    }
    const card = event.target.closest("[data-study-template-id]");
    if (!card) {
      return;
    }
    state.selectedCampaignStudyTemplateId = card.dataset.studyTemplateId;
    renderCampaignStudyTemplates();
  });
  els.campaignStudyTemplateCards.addEventListener("keydown", (event) => {
    if (!["Enter", " "].includes(event.key)) {
      return;
    }
    const card = event.target.closest("[data-study-template-id]");
    if (!card) {
      return;
    }
    event.preventDefault();
    state.selectedCampaignStudyTemplateId = card.dataset.studyTemplateId;
    renderCampaignStudyTemplates();
  });
  els.saveCampaignStudyTemplateButton.addEventListener("click", handleSaveCampaignStudyTemplate);
  els.loadCampaignStudyTemplateButton.addEventListener("click", handleLoadCampaignStudyTemplate);
  els.runCampaignStudyTemplateButton.addEventListener("click", handleRunCampaignStudyTemplate);
  els.importCampaignStudyTemplateInput.addEventListener("change", handleImportCampaignStudyTemplate);
  els.composeResearchObjectButton.addEventListener("click", handleComposeResearchObject);
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
