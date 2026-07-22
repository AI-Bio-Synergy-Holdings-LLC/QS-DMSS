const state = {
  hostedDemo: null,
  quantumValidation: null,
  previousQuantumValidation: null,
  quantumRuntime: null,
  quantumAttributionPrimaryKey: null,
  quantumAttributionCompareKey: null,
  configs: [],
  showcases: [],
  campaignStudio: null,
  campaignStudioValues: {},
  campaignStudioDecisionValues: {},
  campaignStudyTemplates: [],
  selectedCampaignStudyTemplateId: null,
  activeCampaignStudyTemplate: null,
  lastCampaignStudyTemplate: null,
  lastCampaignStudyGuide: null,
  lastCampaignStudioResult: null,
  runs: [],
  experiments: [],
  sweepParameters: [],
  selectedShowcaseName: null,
  labResult: null,
  labComparisonResult: null,
  comparisonDownloadUrl: null,
  evidenceAssistantIntent: "next",
  aiStatus: null,
  aiDraft: null,
  aiDraftLoading: false,
  researchObject: null,
  researchObjectDownloadUrl: null,
  workspaceExport: null,
  workspaceDownloadUrl: null,
  selectedRunId: null,
  selectedRun: null,
  selectedExperimentId: null,
  selectedExperiment: null,
  selectedTemplateName: null,
  selectedRunIds: [],
  comparison: null,
  comparisonMetrics: {
    main: "energy_drift",
    lab: "energy_drift",
    research: "energy_drift",
  },
};

const EVIDENCE_ASSISTANT_INTENTS = new Set([
  "summary",
  "claim",
  "comparison",
  "next",
]);

function normalizedEvidenceAssistantIntent() {
  return EVIDENCE_ASSISTANT_INTENTS.has(state.evidenceAssistantIntent)
    ? state.evidenceAssistantIntent
    : "next";
}

let artifactPreviewTrigger = null;
const svgPreviewCache = new Map();

const els = {
  hostedDemoBanner: document.querySelector("#hostedDemoBanner"),
  railModeLabel: document.querySelector("#railModeLabel"),
  apiModePill: document.querySelector("#apiModePill"),
  executionModeStatus: document.querySelector("#executionModeStatus"),
  releaseVersion: document.querySelector("#releaseVersion"),
  releaseDoi: document.querySelector("#releaseDoi"),
  projectDoi: document.querySelector("#projectDoi"),
  overviewResearchObjectTitle: document.querySelector("#overviewResearchObjectTitle"),
  overviewResearchObjectSummary: document.querySelector("#overviewResearchObjectSummary"),
  overviewObjectType: document.querySelector("#overviewObjectType"),
  overviewObjectId: document.querySelector("#overviewObjectId"),
  overviewObjectStatus: document.querySelector("#overviewObjectStatus"),
  overviewObjectCreated: document.querySelector("#overviewObjectCreated"),
  overviewObjectMethod: document.querySelector("#overviewObjectMethod"),
  overviewObjectEvidence: document.querySelector("#overviewObjectEvidence"),
  quantumValidationStatus: document.querySelector("#quantumValidationStatus"),
  quantumRowsPassing: document.querySelector("#quantumRowsPassing"),
  quantumReferenceExact: document.querySelector("#quantumReferenceExact"),
  quantumBoundedApproximation: document.querySelector("#quantumBoundedApproximation"),
  quantumExecutionMode: document.querySelector("#quantumExecutionMode"),
  quantumAuthorizedSpend: document.querySelector("#quantumAuthorizedSpend"),
  quantumSnapshotDate: document.querySelector("#quantumSnapshotDate"),
  quantumSnapshotId: document.querySelector("#quantumSnapshotId"),
  quantumBundleLink: document.querySelector("#quantumBundleLink"),
  quantumSummaryLink: document.querySelector("#quantumSummaryLink"),
  quantumMatrixLink: document.querySelector("#quantumMatrixLink"),
  quantumReportLink: document.querySelector("#quantumReportLink"),
  quantumTopologyCharts: document.querySelector("#quantumTopologyCharts"),
  quantumVisualProvenance: document.querySelector("#quantumVisualProvenance"),
  quantumVisualSourceBadge: document.querySelector("#quantumVisualSourceBadge"),
  quantumVisualProvenanceTitle: document.querySelector("#quantumVisualProvenanceTitle"),
  quantumVisualProvenanceSummary: document.querySelector("#quantumVisualProvenanceSummary"),
  quantumVisualRunId: document.querySelector("#quantumVisualRunId"),
  quantumVisualParameters: document.querySelector("#quantumVisualParameters"),
  quantumVisualDataDigest: document.querySelector("#quantumVisualDataDigest"),
  quantumTopologySource: document.querySelector("#quantumTopologySource"),
  quantumAttributionSource: document.querySelector("#quantumAttributionSource"),
  quantumAttributionPrimarySelect: document.querySelector("#quantumAttributionPrimarySelect"),
  quantumAttributionCompareSelect: document.querySelector("#quantumAttributionCompareSelect"),
  quantumAttributionPrimaryLabel: document.querySelector("#quantumAttributionPrimaryLabel"),
  quantumAttributionCompareLabel: document.querySelector("#quantumAttributionCompareLabel"),
  quantumAttributionChart: document.querySelector("#quantumAttributionChart"),
  quantumAttributionCompareChart: document.querySelector("#quantumAttributionCompareChart"),
  quantumAttributionDelta: document.querySelector("#quantumAttributionDelta"),
  quantumAttributionCompareDelta: document.querySelector("#quantumAttributionCompareDelta"),
  quantumAttributionRecommendationSummary: document.querySelector("#quantumAttributionRecommendationSummary"),
  quantumAttributionRosterBody: document.querySelector("#quantumAttributionRosterBody"),
  quantumAttributionDescription: document.querySelector("#quantumAttributionDescription"),
  quantumMatrixSummary: document.querySelector("#quantumMatrixSummary"),
  quantumMatrixBody: document.querySelector("#quantumMatrixBody"),
  quantumRecommendedSummary: document.querySelector("#quantumRecommendedSummary"),
  quantumBundleSize: document.querySelector("#quantumBundleSize"),
  quantumBundleSha: document.querySelector("#quantumBundleSha"),
  quantumArchiveInventory: document.querySelector("#quantumArchiveInventory"),
  quantumLimitations: document.querySelector("#quantumLimitations"),
  quantumHarnessForm: document.querySelector("#quantumHarnessForm"),
  quantumShotsInput: document.querySelector("#quantumShotsInput"),
  quantumSeedInput: document.querySelector("#quantumSeedInput"),
  quantumReferenceToleranceInput: document.querySelector("#quantumReferenceToleranceInput"),
  quantumCompilationToleranceInput: document.querySelector("#quantumCompilationToleranceInput"),
  quantumMatrixScope: document.querySelector("#quantumMatrixScope"),
  quantumBasisGates: document.querySelector("#quantumBasisGates"),
  runQuantumValidationButton: document.querySelector("#runQuantumValidationButton"),
  quantumRunFeedback: document.querySelector("#quantumRunFeedback"),
  quantumRunName: document.querySelector("#quantumRunName"),
  quantumRunFreshness: document.querySelector("#quantumRunFreshness"),
  quantumRunStatus: document.querySelector("#quantumRunStatus"),
  quantumRunDuration: document.querySelector("#quantumRunDuration"),
  quantumRunPackageVersion: document.querySelector("#quantumRunPackageVersion"),
  quantumRunOutput: document.querySelector("#quantumRunOutput"),
  quantumRunVerification: document.querySelector("#quantumRunVerification"),
  quantumProgressSequence: document.querySelector("#quantumProgressSequence"),
  quantumRecommendationBody: document.querySelector("#quantumRecommendationBody"),
  configTemplate: document.querySelector("#configTemplate"),
  configContextTitle: document.querySelector("#configContextTitle"),
  configContextSummary: document.querySelector("#configContextSummary"),
  configLibraryCount: document.querySelector("#configLibraryCount"),
  configStudyType: document.querySelector("#configStudyType"),
  configModelSummary: document.querySelector("#configModelSummary"),
  configEvidenceFocus: document.querySelector("#configEvidenceFocus"),
  loadTemplateButton: document.querySelector("#loadTemplateButton"),
  labScenarioSelect: document.querySelector("#labScenarioSelect"),
  labFlowChoose: document.querySelector("#labFlowChoose"),
  labFlowRun: document.querySelector("#labFlowRun"),
  labFlowInspect: document.querySelector("#labFlowInspect"),
  labFlowVerify: document.querySelector("#labFlowVerify"),
  labFlowExport: document.querySelector("#labFlowExport"),
  labFlowChooseStatus: document.querySelector("#labFlowChooseStatus"),
  labFlowRunStatus: document.querySelector("#labFlowRunStatus"),
  labFlowInspectStatus: document.querySelector("#labFlowInspectStatus"),
  labFlowVerifyStatus: document.querySelector("#labFlowVerifyStatus"),
  labFlowExportStatus: document.querySelector("#labFlowExportStatus"),
  researchRunbookStatus: document.querySelector("#researchRunbookStatus"),
  researchRunbookSummary: document.querySelector("#researchRunbookSummary"),
  runbookStepDefine: document.querySelector("#runbookStepDefine"),
  runbookStepDefineSummary: document.querySelector("#runbookStepDefineSummary"),
  runbookStepDefineStatus: document.querySelector("#runbookStepDefineStatus"),
  runbookStepExecute: document.querySelector("#runbookStepExecute"),
  runbookStepExecuteSummary: document.querySelector("#runbookStepExecuteSummary"),
  runbookStepExecuteStatus: document.querySelector("#runbookStepExecuteStatus"),
  runbookStepInspect: document.querySelector("#runbookStepInspect"),
  runbookStepInspectSummary: document.querySelector("#runbookStepInspectSummary"),
  runbookStepInspectStatus: document.querySelector("#runbookStepInspectStatus"),
  runbookStepVerify: document.querySelector("#runbookStepVerify"),
  runbookStepVerifySummary: document.querySelector("#runbookStepVerifySummary"),
  runbookStepVerifyStatus: document.querySelector("#runbookStepVerifyStatus"),
  runbookStepCommunicate: document.querySelector("#runbookStepCommunicate"),
  runbookStepCommunicateSummary: document.querySelector("#runbookStepCommunicateSummary"),
  runbookStepCommunicateStatus: document.querySelector("#runbookStepCommunicateStatus"),
  evidenceAssistantContext: document.querySelector("#evidenceAssistantContext"),
  evidenceAssistantPromptGroup: document.querySelector("#evidenceAssistantPromptGroup"),
  evidenceAssistantResponseLabel: document.querySelector("#evidenceAssistantResponseLabel"),
  evidenceAssistantResponseTitle: document.querySelector("#evidenceAssistantResponseTitle"),
  evidenceAssistantResponseBody: document.querySelector("#evidenceAssistantResponseBody"),
  evidenceAssistantEvidenceList: document.querySelector("#evidenceAssistantEvidenceList"),
  evidenceAssistantMode: document.querySelector("#evidenceAssistantMode"),
  aiProviderStatus: document.querySelector("#aiProviderStatus"),
  aiProviderStatusTitle: document.querySelector("#aiProviderStatusTitle"),
  aiProviderStatusSummary: document.querySelector("#aiProviderStatusSummary"),
  aiDraftPanel: document.querySelector("#aiDraftPanel"),
  aiDraftStatus: document.querySelector("#aiDraftStatus"),
  aiDraftDisclosure: document.querySelector("#aiDraftDisclosure"),
  generateAiDraftButton: document.querySelector("#generateAiDraftButton"),
  aiDraftResult: document.querySelector("#aiDraftResult"),
  aiDraftTitle: document.querySelector("#aiDraftTitle"),
  aiDraftBody: document.querySelector("#aiDraftBody"),
  aiDraftFindings: document.querySelector("#aiDraftFindings"),
  aiDraftLimitations: document.querySelector("#aiDraftLimitations"),
  aiDraftActions: document.querySelector("#aiDraftActions"),
  aiDraftReviewer: document.querySelector("#aiDraftReviewer"),
  aiDraftEditedText: document.querySelector("#aiDraftEditedText"),
  aiReviewActions: document.querySelector("#aiReviewActions"),
  aiDraftProvenance: document.querySelector("#aiDraftProvenance"),
  aiDraftBundleLink: document.querySelector("#aiDraftBundleLink"),
  aiDraftFeedback: document.querySelector("#aiDraftFeedback"),
  demoPathStatus: document.querySelector("#demoPathStatus"),
  demoPathFeedback: document.querySelector("#demoPathFeedback"),
  demoRunStep: document.querySelector("#demoRunStep"),
  demoCompareStep: document.querySelector("#demoCompareStep"),
  demoExportStep: document.querySelector("#demoExportStep"),
  demoRunButton: document.querySelector("#demoRunButton"),
  demoCompareButton: document.querySelector("#demoCompareButton"),
  demoExportButton: document.querySelector("#demoExportButton"),
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
  labComparisonWorkbookLink: document.querySelector("#labComparisonWorkbookLink"),
  labComparisonWorkbookDownloadLink: document.querySelector(
    "#labComparisonWorkbookDownloadLink",
  ),
  labComparisonBundleLink: document.querySelector("#labComparisonBundleLink"),
  labComparisonJsonLink: document.querySelector("#labComparisonJsonLink"),
  labComparisonResults: document.querySelector("#labComparisonResults"),
  labComparisonResultsBody: document.querySelector("#labComparisonResultsBody"),
  labComparisonChart: document.querySelector("#labComparisonChart"),
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
  campaignStudyGuideTitle: document.querySelector("#campaignStudyGuideTitle"),
  campaignStudyGuideSummary: document.querySelector("#campaignStudyGuideSummary"),
  campaignStudyGuideChangedList: document.querySelector("#campaignStudyGuideChangedList"),
  campaignStudyGuideMetricList: document.querySelector("#campaignStudyGuideMetricList"),
  campaignStudyGuideNonClaimList: document.querySelector("#campaignStudyGuideNonClaimList"),
  campaignStudyGuideReviewPrompt: document.querySelector("#campaignStudyGuideReviewPrompt"),
  labExplorerStatus: document.querySelector("#labExplorerStatus"),
  labReportPreviewTitle: document.querySelector("#labReportPreviewTitle"),
  labReportPreviewBody: document.querySelector("#labReportPreviewBody"),
  labReportMetrics: document.querySelector("#labReportMetrics"),
  labDiagnosticSummary: document.querySelector("#labDiagnosticSummary"),
  labEnergyChart: document.querySelector("#labEnergyChart"),
  labNormChart: document.querySelector("#labNormChart"),
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
  workspaceExportStatus: document.querySelector("#workspaceExportStatus"),
  workspaceExportSummary: document.querySelector("#workspaceExportSummary"),
  workspaceCollaboratorName: document.querySelector("#workspaceCollaboratorName"),
  workspaceCollaboratorRole: document.querySelector("#workspaceCollaboratorRole"),
  workspaceCollaboratorAffiliation: document.querySelector("#workspaceCollaboratorAffiliation"),
  workspaceAnnotationText: document.querySelector("#workspaceAnnotationText"),
  exportWorkspaceButton: document.querySelector("#exportWorkspaceButton"),
  workspaceDownloadLink: document.querySelector("#workspaceDownloadLink"),
  workspaceImportInput: document.querySelector("#workspaceImportInput"),
  workspaceExportFeedback: document.querySelector("#workspaceExportFeedback"),
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
  runLaunchStatus: document.querySelector("#runLaunchStatus"),
  runLaunchState: document.querySelector("#runLaunchState"),
  runLaunchTitle: document.querySelector("#runLaunchTitle"),
  runLaunchMessage: document.querySelector("#runLaunchMessage"),
  runLaunchProgress: document.querySelector("#runLaunchProgress"),
  runLaunchResultActions: document.querySelector("#runLaunchResultActions"),
  runLaunchReviewBundle: document.querySelector("#runLaunchReviewBundle"),
  runLaunchStateBundle: document.querySelector("#runLaunchStateBundle"),
  runLaunchFullBundle: document.querySelector("#runLaunchFullBundle"),
  sweepForm: document.querySelector("#sweepForm"),
  sweepBaseConfig: document.querySelector("#sweepBaseConfig"),
  sweepParameter: document.querySelector("#sweepParameter"),
  sweepParameterDescription: document.querySelector("#sweepParameterDescription"),
  sweepValues: document.querySelector("#sweepValues"),
  sweepValidation: document.querySelector("#sweepValidation"),
  sweepPlannedCount: document.querySelector("#sweepPlannedCount"),
  sweepLaunchNote: document.querySelector("#sweepLaunchNote"),
  sweepInterpretationSummary: document.querySelector("#sweepInterpretationSummary"),
  sweepChanged: document.querySelector("#sweepChanged"),
  sweepHeldFixed: document.querySelector("#sweepHeldFixed"),
  sweepCompared: document.querySelector("#sweepCompared"),
  sweepScientificBoundary: document.querySelector("#sweepScientificBoundary"),
  sweepPreviewBody: document.querySelector("#sweepPreviewBody"),
  experimentNameInput: document.querySelector("#experimentNameInput"),
  launchSweepButton: document.querySelector("#launchSweepButton"),
  verifyButton: document.querySelector("#verifyButton"),
  replayButton: document.querySelector("#replayButton"),
  bundleLink: document.querySelector("#bundleLink"),
  reviewBundleLink: document.querySelector("#reviewBundleLink"),
  stateBundleLink: document.querySelector("#stateBundleLink"),
  openReportButton: document.querySelector("#openReportButton"),
  reportDialog: document.querySelector("#reportDialog"),
  reportFrame: document.querySelector("#reportFrame"),
  reportHeading: document.querySelector("#reportHeading"),
  artifactPreviewDialog: document.querySelector("#artifactPreviewDialog"),
  artifactPreviewHeading: document.querySelector("#artifactPreviewHeading"),
  artifactPreviewImage: document.querySelector("#artifactPreviewImage"),
  artifactPreviewFilename: document.querySelector("#artifactPreviewFilename"),
  artifactPreviewCallout: document.querySelector("#artifactPreviewCallout"),
  artifactPreviewWhy: document.querySelector("#artifactPreviewWhy"),
  artifactPreviewSourceLink: document.querySelector("#artifactPreviewSourceLink"),
  runsTableBody: document.querySelector("#runsTableBody"),
  comparisonTableBody: document.querySelector("#comparisonTableBody"),
  comparisonChart: document.querySelector("#comparisonChart"),
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
  experimentJobId: document.querySelector("#experimentJobId"),
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
  statusJobId: document.querySelector("#statusJobId"),
  statusJobBackend: document.querySelector("#statusJobBackend"),
  detailTitle: document.querySelector("#detailTitle"),
  detailChip: document.querySelector("#detailChip"),
  detailDigest: document.querySelector("#detailDigest"),
  jobProvenanceTitle: document.querySelector("#jobProvenanceTitle"),
  jobProvenanceSummary: document.querySelector("#jobProvenanceSummary"),
  jobProvenanceLifecycle: document.querySelector("#jobProvenanceLifecycle"),
  jobProvenanceArtifacts: document.querySelector("#jobProvenanceArtifacts"),
  jobProvenanceRegistry: document.querySelector("#jobProvenanceRegistry"),
  energyDriftValue: document.querySelector("#energyDriftValue"),
  normDriftValue: document.querySelector("#normDriftValue"),
  energyChart: document.querySelector("#energyChart"),
  normChart: document.querySelector("#normChart"),
  energyInitialValue: document.querySelector("#energyInitialValue"),
  energyFinalValue: document.querySelector("#energyFinalValue"),
  energyRangeValue: document.querySelector("#energyRangeValue"),
  normInitialValue: document.querySelector("#normInitialValue"),
  normFinalValue: document.querySelector("#normFinalValue"),
  normRangeValue: document.querySelector("#normRangeValue"),
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
  evidence_only: "is-warning",
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
  packageVersion: "0.13.2",
  releaseTag: "v0.13.2",
  conceptDoi: "10.5281/zenodo.20074924",
  releaseDoi: "10.5281/zenodo.21366910",
  releaseUrl: "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.13.2",
  pypiUrl: "https://pypi.org/project/qs-dmss/",
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

function formatBytes(value) {
  const bytes = Number(value);
  if (!Number.isFinite(bytes) || bytes < 0) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
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

function jobSummary(detailOrSummary) {
  if (!detailOrSummary) return null;
  if (detailOrSummary.summary) return detailOrSummary.summary;
  return detailOrSummary;
}

function jobLabel(job) {
  const summary = jobSummary(job);
  if (!summary?.job_id) return "No job";
  return `${shortRunId(summary.job_id)} / ${summary.state || "unknown"}`;
}

function jobBackendLabel(job) {
  const summary = jobSummary(job);
  if (!summary?.backend) return "-";
  return `${summary.backend}${summary.available === false ? " unavailable" : ""}`;
}

function jobCellMarkup(job) {
  const summary = jobSummary(job);
  if (!summary?.job_id) {
    return '<span class="job-provenance-chip is-empty">No job</span>';
  }
  return `
    <div class="job-provenance-mini">
      <strong>${escapeHtml(shortRunId(summary.job_id))}</strong>
      <span>${escapeHtml(summary.backend || "local")} / ${escapeHtml(summary.state || "unknown")}</span>
    </div>
  `;
}

function renderJobProvenance(jobDetail) {
  const summary = jobSummary(jobDetail);
  if (!summary?.job_id) {
    els.jobProvenanceTitle.textContent = "No execution job selected";
    els.jobProvenanceSummary.textContent =
      "Local executor job lifecycle and artifact roles appear after selecting a run.";
    els.jobProvenanceLifecycle.textContent = "-";
    els.jobProvenanceArtifacts.textContent = "-";
    els.jobProvenanceRegistry.textContent = "-";
    return;
  }

  const lifecycleStates = summary.lifecycle_states?.length
    ? summary.lifecycle_states.join(" -> ")
    : "Lifecycle unavailable";
  const artifactRoles = summary.artifact_roles?.length
    ? summary.artifact_roles.join(", ")
    : "Artifacts unavailable";
  els.jobProvenanceTitle.textContent = `${summary.backend || "local"} job ${shortRunId(summary.job_id)}`;
  els.jobProvenanceSummary.textContent = summary.available === false
    ? summary.message || "Local job record is not available for this run."
    : summary.message || "Local executor job record is available for this run.";
  els.jobProvenanceLifecycle.textContent = lifecycleStates;
  els.jobProvenanceArtifacts.textContent = artifactRoles;
  els.jobProvenanceRegistry.textContent = summary.registry_path || summary.url || "-";
}

function toast(title, body, tone = "neutral") {
  const node = document.createElement("div");
  const heading = document.createElement("strong");
  const message = document.createElement("span");
  node.className = "toast";
  heading.textContent = String(title ?? "");
  message.textContent = String(body ?? "");
  node.append(heading, message);
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
    cache: "no-store",
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
      } else if (Array.isArray(parsed.detail)) {
        message = parsed.detail
          .map((item) => item?.msg || item?.message)
          .filter(Boolean)
          .join("; ");
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

function hostedDemoEnabled() {
  return Boolean(state.hostedDemo?.enabled);
}

function hostedDemoBlocked(actionLabel) {
  if (!hostedDemoEnabled()) {
    return false;
  }
  toast(
    "Hosted demo uses curated paths",
    `${actionLabel} is local-only. Use Lab Mode, Guided Comparison, the Self-Interaction Sweep template, or install QS-DMSS locally for custom work.`,
    "danger",
  );
  return true;
}

function setControlsDisabled(container, disabled) {
  if (!container) {
    return;
  }
  container.querySelectorAll("button, input, select, textarea").forEach((control) => {
    control.disabled = disabled;
  });
}

function setActionLinkEnabled(link, enabled, href = null) {
  if (!link) {
    return;
  }
  link.classList.toggle("is-disabled", !enabled);
  if (enabled && href) {
    link.href = href;
    link.removeAttribute("aria-disabled");
    link.tabIndex = 0;
    return;
  }
  link.removeAttribute("href");
  link.setAttribute("aria-disabled", "true");
  link.tabIndex = -1;
}

function setupNavigation() {
  const links = Array.from(document.querySelectorAll('.rail-item[href^="#"]'));
  const pairs = links
    .map((link) => ({ link, target: document.querySelector(link.getAttribute("href")) }))
    .filter((item) => item.target);
  const skipLink = document.querySelector(".skip-link");
  const main = document.querySelector("#main-content");

  const setActive = (activeLink) => {
    links.forEach((link) => {
      const active = link === activeLink;
      link.classList.toggle("active", active);
      if (active) {
        link.setAttribute("aria-current", "location");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  };

  const syncActiveSection = () => {
    const visiblePairs = pairs.filter(({ link, target }) => {
      const linkStyle = window.getComputedStyle(link);
      const targetStyle = window.getComputedStyle(target);
      return linkStyle.display !== "none" && targetStyle.display !== "none";
    });
    if (!visiblePairs.length) {
      return;
    }
    const marker = window.innerWidth <= 900 ? 128 : Math.min(180, window.innerHeight * 0.24);
    let current = visiblePairs[0];
    visiblePairs.forEach((item) => {
      if (item.target.getBoundingClientRect().top <= marker) {
        current = item;
      }
    });
    const atPageEnd = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2;
    if (atPageEnd) {
      current = visiblePairs[visiblePairs.length - 1];
    }
    setActive(current.link);
  };

  let navigationFrame = null;
  const requestNavigationSync = () => {
    if (navigationFrame !== null) {
      return;
    }
    navigationFrame = window.requestAnimationFrame(() => {
      navigationFrame = null;
      syncActiveSection();
    });
  };

  links.forEach((link) =>
    link.addEventListener("click", (event) => {
      const target = document.querySelector(link.getAttribute("href"));
      if (!target) {
        return;
      }
      event.preventDefault();
      target.scrollIntoView({ behavior: "auto", block: "start" });
      window.history.pushState(null, "", link.hash);
      setActive(link);
    }),
  );
  window.addEventListener("scroll", requestNavigationSync, { passive: true });
  window.addEventListener("resize", requestNavigationSync);
  skipLink?.addEventListener("click", () => {
    window.requestAnimationFrame(() => main?.focus({ preventScroll: true }));
  });
  syncActiveSection();
}

function applyHostedDemoMode() {
  const enabled = hostedDemoEnabled();
  els.hostedDemoBanner.hidden = !enabled;
  els.railModeLabel.textContent = enabled ? "Hosted demo" : "Local-first";
  els.apiModePill.textContent = enabled ? "Hosted" : "Local";
  els.executionModeStatus.textContent = enabled ? "Curated demo" : "Local execution";
  document.body.classList.toggle("is-hosted-demo", enabled);
  window.dispatchEvent(new Event("resize"));
  if (!enabled) {
    return;
  }

  setControlsDisabled(els.launchForm, true);
  setControlsDisabled(els.sweepForm, true);
  setControlsDisabled(els.quantumHarnessForm, true);
  els.loadTemplateButton.disabled = true;
  els.launchButton.disabled = true;
  els.launchSweepButton.disabled = true;
  els.launchCampaignButton.disabled = true;
  els.launchCampaignStudioButton.disabled = true;
  els.saveCampaignStudyTemplateButton.disabled = true;
  els.importCampaignStudyTemplateInput.disabled = true;
  els.exportWorkspaceButton.disabled = true;
  els.workspaceImportInput.disabled = true;
  els.runQuantumValidationButton.disabled = true;
  els.quantumRunFeedback.textContent =
    "Hosted mode presents the verified packaged archive. Live compilation runs in the local full application.";
  els.workspaceExportSummary.textContent =
    "Workspace import/export is local-only in the public hosted demo. Compose a research-object export for shareable Markdown, or install QS-DMSS locally for portable workspace snapshots.";
  els.workspaceExportFeedback.textContent =
    "Hosted demo outputs are temporary. Do not upload sensitive collaborator, annotation, or workspace data.";
  if (!els.campaignStudioFeedback.textContent.includes("Hosted demo")) {
    els.campaignStudioFeedback.textContent =
      "Hosted demo runs the packaged Self-Interaction Sweep template. Editing and saving custom campaign designs is local-only.";
  }
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

function comparisonExportPayload(result) {
  if (!result) return null;
  const withoutExecutionJob = (item) => {
    const copy = { ...item };
    delete copy.execution_job;
    return copy;
  };
  const rows = (result.comparison?.rows || []).map(withoutExecutionJob);
  const runs = (result.runs || []).map(withoutExecutionJob);
  const summary = withoutExecutionJob(result.artifact?.summary || {});
  return {
    schema: "qs-dmss-guided-comparison-v1",
    generated_at: new Date().toISOString(),
    scenario: result.scenario,
    guide: result.guide,
    comparison: { ...result.comparison, rows },
    runs,
    artifact: {
      summary,
      evidence: result.artifact?.evidence || {},
      urls: result.artifact?.urls || {},
    },
  };
}

function setLabComparisonLinksEnabled(enabled, result = null) {
  if (state.comparisonDownloadUrl?.startsWith("blob:")) {
    URL.revokeObjectURL(state.comparisonDownloadUrl);
  }
  const exportPayload = comparisonExportPayload(result);
  state.comparisonDownloadUrl = enabled && exportPayload
    ? URL.createObjectURL(new Blob([`${JSON.stringify(exportPayload, null, 2)}\n`], { type: "application/json" }))
    : null;
  const experimentId = result?.artifact?.summary?.experiment_id || "guided-comparison";
  [
    [els.labComparisonReportLink, result?.urls?.report, "Open comparison report", "Report after run"],
    [
      els.labComparisonWorkbookLink,
      result?.urls?.workbook,
      "Open research workbook",
      "Workbook after run",
    ],
    [
      els.labComparisonWorkbookDownloadLink,
      result?.urls?.workbook_download,
      "Download workbook (.html)",
      "Download workbook",
    ],
    [els.labComparisonBundleLink, result?.urls?.bundle, "Download comparison bundle", "Bundle after run"],
    [els.labComparisonJsonLink, state.comparisonDownloadUrl, "Download comparison JSON", "JSON after run"],
  ].forEach(([link, href, readyLabel, disabledLabel]) => {
    if (enabled && href) {
      link.href = href;
      if (link === els.labComparisonBundleLink) {
        link.download = result?.artifact?.summary?.bundle_filename || `${experimentId}-comparison-bundle.zip`;
      } else if (link === els.labComparisonWorkbookDownloadLink) {
        link.download = `${experimentId}-research-workbook.html`;
      } else if (link === els.labComparisonJsonLink) {
        link.download = `${experimentId}-comparison.json`;
      }
      link.removeAttribute("aria-disabled");
      link.removeAttribute("tabindex");
      link.textContent = readyLabel;
      link.classList.remove("is-disabled");
    } else {
      link.removeAttribute("href");
      link.removeAttribute("download");
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
  els.demoRunButton.disabled = isRunning;
  els.demoRunButton.textContent = isRunning ? "Running showcase..." : "Run showcase";
}

function setLabComparisonProgress(isRunning, message) {
  els.launchLabComparisonButton.disabled = isRunning;
  els.launchLabComparisonButton.setAttribute("aria-busy", String(isRunning));
  els.launchLabComparisonButton.textContent = isRunning
    ? "Running Guided Comparison..."
    : "Run Guided Comparison";
  els.labComparisonProgressText.textContent = message;
  els.demoCompareButton.disabled = isRunning || !state.labResult;
  els.demoCompareButton.textContent = isRunning ? "Comparing variants..." : "Compare variants";
}

function setResearchRunbookStep(element, summary, status, details) {
  const { complete, current, available, summaryText, statusText } = details;
  element.classList.toggle("is-complete", complete);
  element.classList.toggle("is-current", current);
  element.classList.toggle("is-available", available);
  summary.textContent = summaryText;
  status.textContent = statusText;
}

function evidenceAssistantSources(scenario, result) {
  const sources = [];
  if (scenario) {
    sources.push(`Scenario contract · ${scenario.label || scenario.name || "packaged study"}`);
    const limitationCount = Array.isArray(scenario.limitations) ? scenario.limitations.length : 0;
    sources.push(
      limitationCount
        ? `Declared limitations · ${limitationCount} recorded`
        : "Declared limitations · review the scenario contract",
    );
  }

  const run = result?.run?.summary;
  if (run?.run_id) {
    sources.push(`Run ledger · ${run.run_id}`);
  }
  const evidence = result?.run?.evidence;
  if (evidence?.bundle_sha256) {
    sources.push(`Evidence bundle · SHA-256 ${evidence.bundle_sha256.slice(0, 12)}`);
  }
  const verification = result?.report?.verification;
  if (verification) {
    sources.push(
      verification.success
        ? `Manifest verification · ${verification.checked_files || 0} files passed`
        : "Manifest verification · requires review",
    );
  }
  const replay = result?.report?.replay;
  if (replay) {
    sources.push(
      replay.final_density_allclose
        ? "Deterministic replay · matched final density"
        : "Deterministic replay · requires review",
    );
  }
  const comparisonCount = state.labComparisonResult?.comparison?.rows?.length || 0;
  if (comparisonCount) {
    const comparisonId = state.labComparisonResult?.artifact?.summary?.experiment_id;
    sources.push(
      `Guided comparison · ${comparisonCount} recorded variants${comparisonId ? ` · ${comparisonId}` : ""}`,
    );
  }
  if (state.researchObject) {
    sources.push(`Research object · ${state.researchObject.fileName || "export composed"}`);
  }
  return sources;
}

function evidenceAssistantAnswer(scenario, result) {
  const intent = normalizedEvidenceAssistantIntent();
  const report = result?.report || {};
  const interpretation = report.interpretation || {};
  const verificationPassed = Boolean(report.verification?.success);
  const replayPassed = Boolean(report.replay?.final_density_allclose);
  const reproduced = verificationPassed && replayPassed;
  const limitations = Array.isArray(scenario?.limitations) ? scenario.limitations : [];
  const nonClaims = Array.isArray(interpretation.what_this_result_does_not_claim)
    ? interpretation.what_this_result_does_not_claim
    : [];
  const meanings = Array.isArray(interpretation.what_this_result_means)
    ? interpretation.what_this_result_means
    : [];
  const sources = evidenceAssistantSources(scenario, result);

  if (!scenario) {
    return {
      label: "Runbook guidance",
      title: "Choose a scenario to begin",
      body:
        "The next defensible action is to select a packaged scenario, review its purpose and limitations, and establish the scientific boundary before execution.",
      sources: ["Evidence basis will appear after a scenario is selected."],
    };
  }

  if (!result) {
    if (intent === "summary") {
      return {
        label: "Study contract",
        title: `Prepared scope: ${scenario.label || scenario.name}`,
        body:
          scenario.purpose ||
          scenario.description ||
          "The selected scenario has no recorded result yet; its contract defines the intended workflow rather than a scientific outcome.",
        sources,
      };
    }
    if (intent === "claim") {
      return {
        label: "Claim boundary",
        title: "No result claim is ready",
        body:
          limitations[0]
            ? `Before execution, retain this constraint: ${limitations[0]}`
            : "Before execution, the scenario contract—not an outcome—defines the available scientific boundary.",
        sources,
      };
    }
    if (intent === "comparison") {
      return {
        label: "Comparison readiness",
        title: "Record a run before comparing variants",
        body:
          "The packaged comparison becomes meaningful after the baseline run is recorded. Until then, review the declared comparison dimensions and limitations in the scenario contract.",
        sources,
      };
    }
    return {
      label: "Next best action",
      title: "Execute the declared scenario",
      body:
        "The scenario is selected. Launch one deterministic run to create the report, evidence manifest, replay record, and artifact set that the remaining runbook steps require.",
      sources,
    };
  }

  if (intent === "summary") {
    return {
      label: "Recorded evidence summary",
      title: `What ${report.scenario_title || scenario.label || scenario.name} recorded`,
      body:
        interpretation.plain_language_summary ||
        report.scenario_narrative ||
        "The recorded run is available for evidence inspection; read the report and diagnostics before interpreting the outcome.",
      sources,
    };
  }
  if (intent === "claim") {
    return {
      label: "Supportable reading",
      title: reproduced ? "Interpret within the recorded boundary" : "Verification gates are still open",
      body: reproduced
        ? meanings.slice(0, 2).join(" ") ||
          "The run supports only the documented numerical and workflow observations captured in its report."
        : "Do not promote this result to a supportable claim until manifest verification and deterministic replay are both recorded as passing.",
      sources: [...sources, ...nonClaims.slice(0, 1).map((item) => `Boundary · ${item}`)],
    };
  }
  if (intent === "comparison") {
    const comparison = state.labComparisonResult?.comparison;
    const guide = state.labComparisonResult?.guide;
    if (!comparison) {
      return {
        label: "Comparison critique",
        title: "No comparison evidence is recorded yet",
        body:
          "Run Guided Comparison to create controlled variant rows, metric deltas, a recommendation contract, and a comparison evidence bundle before critiquing tradeoffs.",
        sources,
      };
    }
    const rows = comparison.rows || [];
    const recommendedRunId = comparison.decision?.recommended_run_id;
    return {
      label: "Comparison critique",
      title: `${rows.length} controlled variants are ready for human review`,
      body:
        guide?.plain_language_summary ||
        `Compare every row against the baseline. ${recommendedRunId ? `The objective contract highlights ${recommendedRunId}, but that recommendation is not a scientific conclusion.` : "No objective-driven recommendation is available."}`,
      sources: [
        ...sources,
        ...(guide?.what_this_does_not_claim || nonClaims).slice(0, 2).map((item) => `Non-claim · ${item}`),
      ],
    };
  }

  if (!verificationPassed) {
    return {
      label: "Next best action",
      title: "Resolve manifest verification",
      body:
        "Inspect the evidence checklist and generated artifacts. A research object should not be communicated while file-manifest verification remains incomplete or failing.",
      sources,
    };
  }
  if (!replayPassed) {
    return {
      label: "Next best action",
      title: "Resolve deterministic replay",
      body:
        "Inspect the replay result and its run lineage before interpreting or exporting the run. Replay agreement is the runbook gate for reproducibility.",
      sources,
    };
  }
  if (!state.labComparisonResult) {
    return {
      label: "Next best action",
      title: "Inspect the evidence, then compare variants if needed",
      body:
        "The recorded run is verified and replayed. Review its report and diagnostics; use Guided Comparison when the research question requires a controlled, multi-variant attribution rather than a single-run reading.",
      sources,
    };
  }
  if (!state.researchObject) {
    return {
      label: "Next best action",
      title: "Compose the citable research object",
      body:
        "The runbook has recorded execution, evidence, reproducibility, and comparison context. Compose the export to package methods, citations, artifacts, evidence links, and non-claims for review.",
      sources,
    };
  }
  return {
    label: "Runbook state",
    title: "Evidence package ready for review",
    body:
      "The research object is composed. Before sharing, perform a human review of the report narrative, evidence links, limitations, and claim boundary; this assistant does not replace scientific review.",
    sources,
  };
}

function renderEvidenceAssistant(scenario) {
  const result = state.labResult;
  const answer = evidenceAssistantAnswer(scenario, result);
  const runId = result?.run?.summary?.run_id;
  els.evidenceAssistantContext.textContent = !scenario
    ? "No scenario is selected yet. The assistant will use the study contract and recorded evidence when they are available."
    : runId
      ? `Working from ${scenario.label || scenario.name}, recorded run ${shortRunId(runId)}, and its attached evidence lineage.`
      : `Working from the ${scenario.label || scenario.name} study contract. Run the scenario to attach evidence lineage.`;
  els.evidenceAssistantResponseLabel.textContent = answer.label;
  els.evidenceAssistantResponseTitle.textContent = answer.title;
  els.evidenceAssistantResponseBody.textContent = answer.body;
  renderPlainList(els.evidenceAssistantEvidenceList, answer.sources);
  els.evidenceAssistantPromptGroup
    .querySelectorAll("[data-evidence-assistant-intent]")
    .forEach((button) => {
      const isSelected =
        button.dataset.evidenceAssistantIntent === normalizedEvidenceAssistantIntent();
      button.setAttribute("aria-pressed", String(isSelected));
    });
  renderAiProviderStatus();
  renderAiDraft(scenario);
}

function aiDraftRequirement(scenario) {
  const intent = normalizedEvidenceAssistantIntent();
  if (!state.aiStatus?.available_in_current_mode) {
    return {
      available: false,
      message: "Configure an approved local or explicitly authorized remote model endpoint to generate AI drafts.",
    };
  }
  if (!scenario) {
    return { available: false, message: "Choose a packaged scenario first." };
  }
  if (["summary", "claim"].includes(intent) && !state.labResult) {
    return { available: false, message: "Record a verified run before requesting this draft." };
  }
  if (intent === "comparison" && !state.labComparisonResult) {
    return { available: false, message: "Run Guided Comparison before requesting a critique." };
  }
  return {
    available: true,
    message:
      state.aiStatus.endpoint_scope === "remote"
        ? "A remote endpoint is explicitly enabled. Only server-selected evidence fields will leave this environment."
        : "The configured local endpoint receives only server-selected evidence fields.",
  };
}

function clearAiDraft(message = "AI output is optional and never replaces deterministic guidance.") {
  state.aiDraft = null;
  state.aiDraftLoading = false;
  if (els.aiDraftFeedback) {
    els.aiDraftFeedback.textContent = message;
  }
}

function renderAiProviderStatus() {
  const status = state.aiStatus || {};
  const ready = Boolean(status.available_in_current_mode);
  els.aiProviderStatus.classList.toggle("is-ready", ready);
  els.aiProviderStatus.classList.toggle(
    "is-warning",
    !ready && ["configuration_error", "hosted_disabled"].includes(status.availability),
  );
  els.evidenceAssistantMode.textContent = ready ? "AI sidecar ready" : "Deterministic guidance";
  if (ready) {
    els.aiProviderStatusTitle.textContent = `${status.provider || "Configured provider"} · ${status.model || "model"}`;
    els.aiProviderStatusSummary.textContent =
      status.endpoint_scope === "remote"
        ? "Remote advisory endpoint · explicit operator authorization · no tools or run execution"
        : "Local advisory endpoint · evidence-bound context · no tools or run execution";
    return;
  }
  if (status.availability === "hosted_disabled") {
    els.aiProviderStatusTitle.textContent = "AI drafts disabled in hosted demo";
    els.aiProviderStatusSummary.textContent =
      "Use the local application with an explicitly configured provider; deterministic guidance remains active.";
    return;
  }
  if (status.availability === "configuration_error") {
    els.aiProviderStatusTitle.textContent = "AI provider configuration needs review";
    els.aiProviderStatusSummary.textContent = status.message || "Review the server-side AI configuration.";
    return;
  }
  els.aiProviderStatusTitle.textContent = "AI drafts disabled";
  els.aiProviderStatusSummary.textContent =
    "Recorded-context guidance remains available without a model provider.";
}

function aiDraftListMarkup(items, emptyMessage) {
  if (!Array.isArray(items) || !items.length) {
    return `<li>${escapeHtml(emptyMessage)}</li>`;
  }
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderAiDraft(scenario) {
  const requirement = aiDraftRequirement(scenario);
  const draft = state.aiDraft;
  els.generateAiDraftButton.disabled = !requirement.available || state.aiDraftLoading;
  els.generateAiDraftButton.textContent = state.aiDraftLoading
    ? "Generating evidence-bound draft..."
    : "Generate AI draft";
  els.aiDraftDisclosure.textContent = requirement.message;

  if (!draft) {
    els.aiDraftStatus.textContent = state.aiDraftLoading ? "Generating" : "Not generated";
    els.aiDraftResult.hidden = true;
    els.aiDraftBundleLink.hidden = true;
    return;
  }

  const response = draft.response || {};
  const review = draft.human_review || {};
  const reviewPending = review.status === "pending";
  els.aiDraftStatus.textContent = reviewPending
    ? "Human review required"
    : `Human ${review.status}`;
  els.aiDraftResult.hidden = false;
  els.aiDraftTitle.textContent = response.title || "AI advisory draft";
  els.aiDraftBody.textContent = response.draft || "";
  els.aiDraftFindings.innerHTML = (response.findings || [])
    .map(
      (finding) => `
        <li>
          ${escapeHtml(finding.statement)}
          <small>Sources: ${escapeHtml((finding.artifact_ids || []).join(", "))}</small>
        </li>
      `,
    )
    .join("") || "<li>No findings returned.</li>";
  els.aiDraftLimitations.innerHTML = aiDraftListMarkup(
    response.limitations,
    "No additional limitations returned.",
  );
  els.aiDraftActions.innerHTML = aiDraftListMarkup(
    response.proposed_actions,
    "No next action proposed.",
  );
  els.aiDraftEditedText.value = review.edited_draft || response.draft || "";
  els.aiDraftEditedText.disabled = !reviewPending;
  els.aiDraftReviewer.value = review.reviewer || els.aiDraftReviewer.value || "Local researcher";
  els.aiDraftReviewer.disabled = !reviewPending;
  els.aiReviewActions.querySelectorAll("button").forEach((button) => {
    button.disabled = !reviewPending;
  });
  const provenance = draft.provenance || {};
  const usage = provenance.usage || {};
  const tokenSummary = usage.total_tokens ? ` · ${usage.total_tokens} tokens` : "";
  els.aiDraftProvenance.textContent = `${provenance.provider || "Provider"} · ${provenance.model || "model"} · ${provenance.endpoint_scope || "endpoint"}${tokenSummary} · context ${String(provenance.context_sha256 || "unrecorded").slice(0, 12)}`;
  els.aiDraftBundleLink.href = draft.urls?.bundle || "#";
  els.aiDraftBundleLink.hidden = !draft.urls?.bundle;
  els.aiDraftFeedback.textContent = reviewPending
    ? "Review the artifact citations and wording, then accept, edit, or reject this draft."
    : `Review recorded as ${review.status} by ${review.reviewer || "the researcher"}.`;
}

async function handleGenerateAiDraft() {
  const scenario = showcaseByName(state.selectedShowcaseName);
  const requirement = aiDraftRequirement(scenario);
  if (!requirement.available || !scenario) {
    toast("AI draft unavailable", requirement.message, "danger");
    return;
  }
  state.aiDraftLoading = true;
  state.aiDraft = null;
  els.aiDraftFeedback.textContent =
    "Building an allowlisted evidence context and validating the provider response.";
  renderAiDraft(scenario);
  try {
    const intent = normalizedEvidenceAssistantIntent();
    const includeRun = ["summary", "claim", "next"].includes(intent);
    const includeComparison = ["comparison", "next"].includes(intent);
    const payload = await fetchJson("/api/ai/drafts", {
      method: "POST",
      body: JSON.stringify({
        intent,
        scenario_name: scenario.name,
        run_id: includeRun ? state.labResult?.run?.summary?.run_id || null : null,
        experiment_id: includeComparison
          ? state.labComparisonResult?.artifact?.summary?.experiment_id || null
          : null,
      }),
    });
    state.aiDraft = payload;
    els.aiDraftFeedback.textContent =
      "Draft generated and stored separately from measured evidence. Human review is required.";
    toast("AI advisory draft ready", "Review its citations before accepting any wording.", "success");
  } catch (error) {
    state.aiDraft = null;
    els.aiDraftFeedback.textContent = error.message;
    toast("AI draft rejected", error.message, "danger");
  } finally {
    state.aiDraftLoading = false;
    renderAiDraft(scenario);
  }
}

async function handleAiDraftReview(status) {
  const draft = state.aiDraft;
  if (!draft?.interaction_id) return;
  const editedDraft = els.aiDraftEditedText.value.trim();
  const reviewer = els.aiDraftReviewer.value.trim();
  if (!reviewer) {
    toast("Reviewer identity required", "Identify the researcher recording this disposition.", "danger");
    els.aiDraftReviewer.focus();
    return;
  }
  if (status === "edited" && !editedDraft) {
    toast("Edited draft required", "Add the human-reviewed wording before saving.", "danger");
    return;
  }
  els.aiDraftFeedback.textContent = "Recording the human disposition and rebuilding the advisory bundle.";
  els.aiReviewActions.querySelectorAll("button").forEach((button) => {
    button.disabled = true;
  });
  try {
    state.aiDraft = await fetchJson(draft.urls.review, {
      method: "POST",
      body: JSON.stringify({
        status,
        reviewer,
        edited_draft: status === "edited" ? editedDraft : null,
      }),
    });
    toast("Human review recorded", `AI draft marked ${status}.`, "success");
  } catch (error) {
    els.aiDraftFeedback.textContent = error.message;
    toast("Review was not recorded", error.message, "danger");
  }
  renderAiDraft(showcaseByName(state.selectedShowcaseName));
}

function renderResearchRunbook(scenario) {
  const result = state.labResult;
  const report = result?.report || {};
  const run = result?.run?.summary;
  const evidence = result?.run?.evidence;
  const hasScenario = Boolean(scenario);
  const hasRun = Boolean(run?.run_id);
  const inspected = Boolean(report?.scenario || report?.scenario_title || report?.interpretation);
  const verificationPassed = Boolean(report.verification?.success);
  const replayPassed = Boolean(report.replay?.final_density_allclose);
  const reproduced = verificationPassed && replayPassed;
  const hasExport = Boolean(state.researchObject);
  const limitationCount = Array.isArray(scenario?.limitations) ? scenario.limitations.length : 0;

  setResearchRunbookStep(
    els.runbookStepDefine,
    els.runbookStepDefineSummary,
    els.runbookStepDefineStatus,
    {
      complete: hasScenario,
      current: !hasScenario,
      available: true,
      summaryText: hasScenario
        ? `${scenario.label || scenario.name} selected with ${limitationCount || "documented"} limitation${limitationCount === 1 ? "" : "s"}.`
        : "Choose a scenario with a documented purpose and limitations.",
      statusText: hasScenario ? "Defined" : "Current",
    },
  );
  setResearchRunbookStep(
    els.runbookStepExecute,
    els.runbookStepExecuteSummary,
    els.runbookStepExecuteStatus,
    {
      complete: hasRun,
      current: hasScenario && !hasRun,
      available: hasScenario,
      summaryText: hasRun
        ? `Run ${shortRunId(run.run_id)} recorded with ${evidence?.file_count || 0} manifest files.`
        : hasScenario
          ? "The selected scenario is ready for one deterministic execution."
          : "Create a recorded run with versioned inputs and artifacts.",
      statusText: hasRun ? "Recorded" : hasScenario ? "Current" : "Queued",
    },
  );
  setResearchRunbookStep(
    els.runbookStepInspect,
    els.runbookStepInspectSummary,
    els.runbookStepInspectStatus,
    {
      complete: inspected,
      current: hasRun && !inspected,
      available: hasRun,
      summaryText: inspected
        ? "Report, diagnostics, artifacts, and the claim boundary are attached to the run."
        : hasRun
          ? "Open the recorded evidence before interpreting the outcome."
          : "Read the report, diagnostics, artifacts, and claim boundary.",
      statusText: inspected ? "Evidence loaded" : hasRun ? "Current" : "Locked",
    },
  );
  setResearchRunbookStep(
    els.runbookStepVerify,
    els.runbookStepVerifySummary,
    els.runbookStepVerifyStatus,
    {
      complete: reproduced,
      current: inspected && !reproduced,
      available: inspected,
      summaryText: reproduced
        ? "Manifest verification passed and deterministic replay matched the final density."
        : inspected
          ? "Review manifest verification and deterministic replay before drawing conclusions."
          : "Check the manifest and deterministic replay before interpretation.",
      statusText: reproduced ? "Reproduced" : inspected ? "Review" : "Locked",
    },
  );
  setResearchRunbookStep(
    els.runbookStepCommunicate,
    els.runbookStepCommunicateSummary,
    els.runbookStepCommunicateStatus,
    {
      complete: hasExport,
      current: reproduced && !hasExport,
      available: reproduced,
      summaryText: hasExport
        ? "Research object is composed with report, citations, evidence links, and non-claims."
        : reproduced
          ? "The reviewed evidence is ready to be composed into a citable research object."
          : "Export evidence, citations, methods, and stated non-claims.",
      statusText: hasExport ? "Ready for review" : reproduced ? "Current" : "Locked",
    },
  );

  const currentPhase = !hasScenario
    ? "Define scope"
    : !hasRun
      ? "Execute study"
      : !inspected
        ? "Inspect evidence"
        : !reproduced
          ? "Verify and replay"
          : !hasExport
            ? "Compose research object"
            : "Human review";
  els.researchRunbookStatus.textContent = currentPhase;
  els.researchRunbookSummary.textContent = hasScenario
    ? `The ${scenario.label || scenario.name} protocol keeps scope, execution, evidence, reproducibility, and responsible communication attached to one research object.`
    : "Select a packaged scenario to establish the scope, then execute, inspect, verify, and communicate one evidence-bound research object.";
  renderEvidenceAssistant(scenario);
}

function updateLabWorkflow() {
  const hasScenario = Boolean(els.labScenarioSelect.value || state.selectedShowcaseName);
  const hasRun = Boolean(state.labResult);
  const inspected = Boolean(state.labResult?.report);
  const verificationPassed = Boolean(state.labResult?.report?.verification?.success);
  const replayPassed = Boolean(state.labResult?.report?.replay?.final_density_allclose);
  const reproduced = verificationPassed && replayPassed;
  const hasExport = Boolean(state.researchObject);
  const steps = [
    {
      element: els.labFlowChoose,
      status: els.labFlowChooseStatus,
      complete: hasScenario,
      current: !hasScenario,
      available: true,
      label: hasScenario ? "Selected" : "Current",
    },
    {
      element: els.labFlowRun,
      status: els.labFlowRunStatus,
      complete: hasRun,
      current: hasScenario && !hasRun,
      available: hasScenario,
      label: hasRun ? "Complete" : hasScenario ? "Current" : "Queued",
    },
    {
      element: els.labFlowInspect,
      status: els.labFlowInspectStatus,
      complete: inspected,
      current: hasRun && !inspected,
      available: hasRun,
      label: inspected ? "Evidence loaded" : hasRun ? "Current" : "Locked",
    },
    {
      element: els.labFlowVerify,
      status: els.labFlowVerifyStatus,
      complete: reproduced,
      current: inspected && !reproduced,
      available: inspected,
      label: reproduced ? "Verified + replayed" : inspected ? "Review" : "Locked",
    },
    {
      element: els.labFlowExport,
      status: els.labFlowExportStatus,
      complete: hasExport,
      current: reproduced && !hasExport,
      available: reproduced,
      label: hasExport ? "Exported" : reproduced ? "Current" : "Locked",
    },
  ];

  steps.forEach(({ element, status, complete, current, available, label }) => {
    element.classList.toggle("is-complete", complete);
    element.classList.toggle("is-current", current);
    element.classList.toggle("is-available", available);
    status.textContent = label;
    const link = element.querySelector("a");
    if (current) link.setAttribute("aria-current", "step");
    else link.removeAttribute("aria-current");
  });
}

function updateDemoPath() {
  const hasRun = Boolean(state.labResult);
  const hasComparison = Boolean(state.labComparisonResult);
  const hasExport = Boolean(state.researchObject);
  const steps = [
    [els.demoRunStep, hasRun, !hasRun],
    [els.demoCompareStep, hasComparison, hasRun && !hasComparison],
    [els.demoExportStep, hasExport, hasComparison && !hasExport],
  ];
  steps.forEach(([element, complete, current]) => {
    element.classList.toggle("is-complete", complete);
    element.classList.toggle("is-current", current);
  });
  els.demoCompareButton.disabled = !hasRun;
  els.demoExportButton.disabled = !hasComparison;
  els.demoPathStatus.textContent = hasExport
    ? "Demo complete"
    : hasComparison
    ? "Step 3 of 3"
    : hasRun
    ? "Step 2 of 3"
    : "Step 1 of 3";
  els.demoPathFeedback.textContent = hasExport
    ? "Research object composed. Inspect the report surface and download the export below."
    : hasComparison
    ? "Three distinct variant bundles are ready. Inspect their metrics and SHA-256 identities, then compose the export."
    : hasRun
    ? "The showcase is verified and replayed. Continue with the three-variant comparison."
    : "Start with the packaged showcase. QS-DMSS will unlock each next action.";
  updateLabWorkflow();
}

function revealDemoResult(element) {
  element?.scrollIntoView({ behavior: "auto", block: "start" });
  window.requestAnimationFrame(() => element?.focus({ preventScroll: true }));
}

function renderLabComparisonResults(result) {
  const rows = result?.comparison?.rows || [];
  const summaries = new Map((result?.runs || []).map((run) => [run.run_id, run]));
  els.labComparisonResults.hidden = !rows.length;
  if (!rows.length) {
    els.labComparisonResultsBody.innerHTML = "";
    renderInteractiveComparisonChart(els.labComparisonChart, null, "lab");
    return;
  }
  renderInteractiveComparisonChart(els.labComparisonChart, result.comparison, "lab");
  els.labComparisonResultsBody.innerHTML = rows
    .map((row) => {
      const summary = summaries.get(row.run_id) || {};
      const parameters = (row.variant || [])
        .map((item) => `${item.label}: ${item.value_label}`)
        .join(" · ");
      const digest = summary.bundle_sha256 || "unavailable";
      const filename = summary.bundle_filename || `${row.run_id}-evidence-bundle.zip`;
      return `
        <tr>
          <td><strong>${escapeHtml(row.variant_label || row.parameter_value_label || "Variant")}</strong></td>
          <td>${escapeHtml(parameters)}</td>
          <td>${escapeHtml(formatScientific(row.energy_drift))}</td>
          <td>${escapeHtml(formatScientific(row.max_density))}</td>
          <td>
            <span class="comparison-evidence-id">
              <strong>${escapeHtml(digest.slice(0, 12))}</strong>
              <span>${escapeHtml(row.bundle_size_label || summary.bundle_size_label || "-")}</span>
            </span>
          </td>
          <td>
            <a
              class="comparison-bundle-link"
              href="/api/runs/${encodeURIComponent(row.run_id)}/bundle"
              download="${escapeHtml(filename)}"
            >Download ${escapeHtml(row.variant_label || "variant")}</a>
          </td>
        </tr>
      `;
    })
    .join("");
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
      detail: `${run.evidence.bundle_size_label} bundle with ${run.evidence.file_count} manifest files; SHA-256 ${run.evidence.bundle_sha256.slice(0, 12)}.`,
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

  els.labInterpretationTitle.textContent = `What ${report.scenario_title || report.scenario} is showing`;
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
    renderLabComparisonResults(null);
    updateDemoPath();
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
  renderLabComparisonResults(result);
  updateDemoPath();
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

async function fetchSvgPreviewText(url) {
  if (svgPreviewCache.has(url)) {
    return svgPreviewCache.get(url);
  }

  let lastError = null;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const svgText = await fetchText(url);
      if (!/<svg[\s>]/i.test(svgText)) {
        throw new Error("Artifact response is not an SVG document");
      }
      if (svgText.length > 2_000_000) {
        throw new Error("SVG preview exceeds the 2 MB cockpit preview limit");
      }
      svgPreviewCache.set(url, svgText);
      return svgText;
    } catch (error) {
      lastError = error;
      if (attempt === 0) {
        await new Promise((resolve) => window.setTimeout(resolve, 350));
      }
    }
  }
  throw lastError;
}

async function loadSvgPreview(item, index, runId) {
  const trigger = els.labArtifactPreview.querySelector(`[data-svg-index="${index}"]`);
  if (!trigger) return;
  const loading = trigger.querySelector("[data-svg-loading]");
  const image = trigger.querySelector("[data-svg-preview-image]");
  try {
    const svgText = await fetchSvgPreviewText(item.url);
    if (state.labResult?.run?.summary?.run_id !== runId) return;
    const previewUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgText)}`;
    image.src = previewUrl;
    image.hidden = false;
    loading.hidden = true;
    trigger.dataset.artifactPreviewUrl = previewUrl;
    trigger.disabled = false;
    trigger.setAttribute("aria-busy", "false");
  } catch (error) {
    if (state.labResult?.run?.summary?.run_id !== runId) return;
    loading.textContent = `Preview unavailable: ${error.message}. Use the artifact link above to open the source SVG.`;
    trigger.setAttribute("aria-busy", "false");
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
      const calloutData = calloutMap.get(item.key);
      const callout = artifactCalloutMarkup(calloutData);
      if (item.kind === "svg") {
        const encodedTitle = encodeURIComponent(item.label || item.name);
        const encodedName = encodeURIComponent(item.name || "Generated SVG");
        const encodedCallout = encodeURIComponent(
          calloutData?.callout || "Inspect axes, annotations, extrema, and the sampled diagnostic trajectory.",
        );
        const encodedWhy = encodeURIComponent(
          calloutData?.why_it_matters ||
            "The scalable source preserves labels and numerical structure for review and publication workflows.",
        );
        return `
          <figure class="lab-artifact-preview-item">
            <figcaption>
              <strong>${title}</strong>
              <span>${name}</span>
            </figcaption>
            ${callout}
            <button
              class="artifact-expand-button"
              type="button"
              data-artifact-preview-url="${escapeHtml(item.url)}"
              data-artifact-source-url="${escapeHtml(item.url)}"
              data-svg-index="${index}"
              data-artifact-preview-title="${encodedTitle}"
              data-artifact-preview-name="${encodedName}"
              data-artifact-preview-callout="${encodedCallout}"
              data-artifact-preview-why="${encodedWhy}"
              aria-label="Expand ${title} scientific figure"
              aria-busy="true"
              disabled
            >
              <span class="artifact-preview-loading" data-svg-loading>Preparing persistent SVG preview...</span>
              <img data-svg-preview-image alt="${title} preview" hidden />
            </button>
            <div class="artifact-science-strip">
              <span>Scalable vector diagnostic</span>
              <span>Axes + annotations + embedded metadata</span>
            </div>
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
    } else if (item.kind === "svg") {
      loadSvgPreview(item, index, runId);
    }
  });
}

function openArtifactPreview(trigger) {
  const url = trigger.dataset.artifactPreviewUrl;
  if (!url) return;

  artifactPreviewTrigger = trigger;
  const title = decodeURIComponent(trigger.dataset.artifactPreviewTitle || "Scientific figure");
  els.artifactPreviewHeading.textContent = title;
  els.artifactPreviewFilename.textContent = decodeURIComponent(
    trigger.dataset.artifactPreviewName || "Generated SVG",
  );
  els.artifactPreviewCallout.textContent = decodeURIComponent(
    trigger.dataset.artifactPreviewCallout || "Inspect the scientific figure at full scale.",
  );
  els.artifactPreviewWhy.textContent = decodeURIComponent(
    trigger.dataset.artifactPreviewWhy || "The figure is part of the generated evidence surface.",
  );
  els.artifactPreviewImage.src = url;
  els.artifactPreviewImage.alt = `${title} expanded scientific figure`;
  els.artifactPreviewSourceLink.href = trigger.dataset.artifactSourceUrl || url;
  els.artifactPreviewDialog.showModal();
}

function renderLabEvidenceExplorer(result) {
  if (!result) {
    els.labExplorerStatus.textContent = "Run showcase first";
    els.labReportPreviewTitle.textContent = "No showcase report yet";
    els.labReportPreviewBody.textContent =
      "Run Lab Mode to summarize the simulation narrative, claim boundary, and key numerical diagnostics directly inside the cockpit.";
    els.labReportMetrics.innerHTML = "";
    els.labDiagnosticSummary.textContent =
      "Energy and norm trajectories appear after the packaged run completes.";
    renderScientificTrace(els.labEnergyChart, [], "energy", {
      color: "#c45f28",
      title: "Relative energy change",
      description: "No recorded energy history yet.",
      yLabel: "Relative energy change",
    });
    renderScientificTrace(els.labNormChart, [], "norm", {
      color: "#237777",
      title: "Relative norm change",
      description: "No recorded norm history yet.",
      yLabel: "Relative norm change",
    });
    els.labEvidenceChecklist.innerHTML =
      "<li>Verification, replay, and bundle status appear after the showcase run.</li>";
    els.labArtifactPreview.innerHTML =
      "<p>SVG plots and CSV first rows appear here after Lab Mode completes.</p>";
    renderGuidedInterpretation(null);
    return;
  }

  const { report, run, artifact_links: artifactLinks } = result;
  els.labExplorerStatus.textContent = report.success ? "Research object ready" : "Needs review";
  els.labReportPreviewTitle.textContent = `${report.scenario} report summary`;
  els.labReportPreviewBody.textContent =
    `${report.scenario_narrative} The run preserved ${report.metrics.history_points} recorded diagnostic samples, ` +
    `a ${run.evidence.file_count}-file evidence manifest, deterministic replay status, and the scoped claim boundary: ${report.claim_boundary}`;
  renderGuidedInterpretation(report);
  renderMetricPreview(report.metrics);
  const history = run.metrics?.history || [];
  const energyTrace = renderScientificTrace(els.labEnergyChart, history, "energy", {
    color: "#c45f28",
    title: "Relative energy change for the packaged run",
    description: "Recorded energy history shown relative to the first solver sample.",
    yLabel: "Relative energy change",
  });
  const normTrace = renderScientificTrace(els.labNormChart, history, "norm", {
    color: "#237777",
    title: "Relative norm change for the packaged run",
    description: "Recorded norm history shown relative to the first solver sample.",
    yLabel: "Relative norm change",
  });
  els.labDiagnosticSummary.textContent =
    `${history.length} solver samples were recorded. Energy ended at ${formatSignedScientific(energyTrace?.finalRelative)} relative to its initial value; ` +
    `norm ended at ${formatSignedScientific(normTrace?.finalRelative)}. Peak absolute changes were ${formatScientific(energyTrace?.peakRelative)} and ${formatScientific(normTrace?.peakRelative)}, respectively. ` +
    "These trajectories are numerical conservation diagnostics, not physical validation.";
  renderEvidenceChecklist(result);
  renderArtifactPreviews(
    artifactLinks,
    result.run.summary.run_id,
    report.interpretation?.artifact_callouts || [],
  );
}

function clearResearchObject() {
  if (state.researchObjectDownloadUrl?.startsWith("blob:")) {
    URL.revokeObjectURL(state.researchObjectDownloadUrl);
  }
  state.researchObject = null;
  state.researchObjectDownloadUrl = null;
}

function setResearchObjectDownloadEnabled(enabled) {
  const link = els.researchObjectDownloadLink;
  if (enabled && state.researchObjectDownloadUrl && state.researchObject) {
    link.href = state.researchObjectDownloadUrl;
    link.download = state.researchObject.export?.file_name || state.researchObject.fileName;
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

function setWorkspaceDownloadEnabled(enabled) {
  const link = els.workspaceDownloadLink;
  if (enabled && state.workspaceDownloadUrl && state.workspaceExport) {
    const workspaceId = state.workspaceExport.summary?.workspace_id || "workspace";
    link.href = state.workspaceDownloadUrl;
    link.download = `${workspaceId}.json`;
    link.removeAttribute("aria-disabled");
    link.removeAttribute("tabindex");
    link.textContent = "Download Workspace JSON";
    link.classList.remove("is-disabled");
    return;
  }

  link.removeAttribute("href");
  link.removeAttribute("download");
  link.setAttribute("aria-disabled", "true");
  link.setAttribute("tabindex", "-1");
  link.textContent = "Download after export";
  link.classList.add("is-disabled");
}

function currentWorkspaceResourceIds() {
  const runIds = new Set(state.selectedRunIds || []);
  if (state.selectedRunId) runIds.add(state.selectedRunId);
  if (state.labResult?.run?.summary?.run_id) {
    runIds.add(state.labResult.run.summary.run_id);
  }
  if (state.lastCampaignStudioResult?.campaign?.run_ids) {
    state.lastCampaignStudioResult.campaign.run_ids.forEach((runId) => runIds.add(runId));
  }

  const experimentIds = new Set();
  if (state.selectedExperimentId) experimentIds.add(state.selectedExperimentId);
  if (state.selectedExperiment?.summary?.experiment_id) {
    experimentIds.add(state.selectedExperiment.summary.experiment_id);
  }
  if (state.labComparisonResult?.artifact?.summary?.experiment_id) {
    experimentIds.add(state.labComparisonResult.artifact.summary.experiment_id);
  }
  if (state.lastCampaignStudioResult?.artifact?.summary?.experiment_id) {
    experimentIds.add(state.lastCampaignStudioResult.artifact.summary.experiment_id);
  }

  const templateIds = new Set();
  if (state.selectedCampaignStudyTemplateId) {
    templateIds.add(state.selectedCampaignStudyTemplateId);
  }
  if (state.activeCampaignStudyTemplate?.template_id) {
    templateIds.add(state.activeCampaignStudyTemplate.template_id);
  }
  if (state.lastCampaignStudyTemplate?.template_id) {
    templateIds.add(state.lastCampaignStudyTemplate.template_id);
  }

  const researchObjectIds = new Set();
  if (state.researchObject?.export?.id) {
    researchObjectIds.add(state.researchObject.export.id);
  }

  return {
    run_ids: [...runIds].filter(Boolean),
    experiment_ids: [...experimentIds].filter(Boolean),
    campaign_study_template_ids: [...templateIds].filter(Boolean),
    research_object_ids: [...researchObjectIds].filter(Boolean),
  };
}

function buildWorkspacePayload() {
  const resourceIds = currentWorkspaceResourceIds();
  const collaboratorName = els.workspaceCollaboratorName.value.trim();
  const collaboratorRole = els.workspaceCollaboratorRole.value.trim() || "reviewer";
  const collaboratorAffiliation = els.workspaceCollaboratorAffiliation.value.trim();
  const collaborators = collaboratorName
    ? [
        {
          display_name: collaboratorName,
          role: collaboratorRole,
          ...(collaboratorAffiliation ? { affiliation: collaboratorAffiliation } : {}),
        },
      ]
    : [];

  const annotationText = els.workspaceAnnotationText.value.trim();
  const annotationTarget = resourceIds.experiment_ids[0]
    ? { target_type: "experiment", target_id: resourceIds.experiment_ids[0] }
    : resourceIds.run_ids[0]
      ? { target_type: "run", target_id: resourceIds.run_ids[0] }
      : { target_type: "workspace", target_id: "workspace" };
  const annotations = annotationText
    ? [
        {
          ...annotationTarget,
          text: annotationText,
          tags: ["cockpit", "handoff"],
        },
      ]
    : [];

  const title = state.lastCampaignStudioResult
    ? "QS-DMSS Campaign Studio workspace"
    : state.labComparisonResult
      ? "QS-DMSS guided comparison workspace"
      : state.labResult
        ? "QS-DMSS Lab Mode workspace"
        : "QS-DMSS workspace";

  return {
    title,
    description:
      "Portable QS-DMSS workspace snapshot with evidence references, collaborator metadata, and review annotations.",
    collaborators,
    annotations,
    ...resourceIds,
  };
}

function renderWorkspaceExport(detail) {
  state.workspaceExport = detail;
  state.workspaceDownloadUrl = detail?.urls?.download || detail?.summary?.urls?.download || null;
  setWorkspaceDownloadEnabled(Boolean(state.workspaceDownloadUrl));

  if (!detail?.summary) {
    els.workspaceExportStatus.textContent = "Not exported";
    els.workspaceExportSummary.textContent =
      "Export the current Lab Mode or Campaign Studio context as a portable JSON workspace with collaborator and annotation metadata.";
    return;
  }

  const summary = detail.summary;
  const resourceCount =
    summary.run_count +
    summary.experiment_count +
    summary.campaign_study_template_count +
    summary.research_object_count;
  const warningText = summary.warning_count
    ? ` ${summary.warning_count} stale reference(s) were skipped.`
    : "";
  els.workspaceExportStatus.textContent = "Workspace ready";
  els.workspaceExportSummary.textContent =
    `${summary.title} captures ${resourceCount} resource references, ${summary.collaborator_count} collaborator record(s), ${summary.annotation_count} annotation(s), and ${summary.job_count} job provenance record(s).${warningText}`;
  els.workspaceExportFeedback.textContent = summary.imported_from_workspace_id
    ? `Imported from ${shortRunId(summary.imported_from_workspace_id)}. Included campaign study templates were installed locally when available.`
    : `Exported ${summary.workspace_id}. Share the JSON to hand off the same study design and evidence context.${warningText}`;
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

function campaignStudyTemplateGuideFromSummary(item) {
  if (!item) return null;
  const interpretation = item.interpretation || {};
  return {
    title: `${item.label} guided interpretation`,
    plain_language_summary:
      interpretation.summary ||
      item.purpose ||
      item.description ||
      "Select or run this study template to inspect its campaign interpretation.",
    what_changed: interpretation.what_changed || [],
    metric_meanings:
      interpretation.metric_meanings ||
      (item.metrics || []).map((metric) => (
        `${metric.label || "Metric"}: ${metric.description || "No interpretation documented."}`
      )),
    what_this_does_not_claim:
      interpretation.what_this_does_not_claim ||
      item.non_claims ||
      [],
    review_prompt:
      interpretation.review_prompt ||
      "A useful review comment can focus on whether this study makes the campaign behavior understandable.",
  };
}

function renderCampaignStudyGuide(guide) {
  if (!guide) {
    els.campaignStudyGuideTitle.textContent = "Select a study template";
    els.campaignStudyGuideSummary.textContent =
      "Packaged study guidance appears here, including what changes, how to read the metrics, and what the result does not claim.";
    renderMetadataList(
      els.campaignStudyGuideChangedList,
      [],
      "Run or select a study template to inspect campaign changes.",
    );
    renderMetadataList(
      els.campaignStudyGuideMetricList,
      [],
      "Metric interpretation appears with packaged study metadata.",
    );
    renderMetadataList(
      els.campaignStudyGuideNonClaimList,
      [],
      "Scientific claim boundaries appear here.",
    );
    els.campaignStudyGuideReviewPrompt.textContent =
      "Run the study to generate a concrete review prompt.";
    return;
  }

  els.campaignStudyGuideTitle.textContent = guide.title || "Guided study interpretation";
  els.campaignStudyGuideSummary.textContent =
    guide.plain_language_summary || "No guided summary is documented yet.";
  renderMetadataList(
    els.campaignStudyGuideChangedList,
    guide.what_changed,
    "No changed-parameter guidance documented yet.",
  );
  renderMetadataList(
    els.campaignStudyGuideMetricList,
    guide.metric_meanings,
    "No metric guidance documented yet.",
  );
  renderMetadataList(
    els.campaignStudyGuideNonClaimList,
    guide.what_this_does_not_claim,
    "No non-claims documented yet.",
  );
  els.campaignStudyGuideReviewPrompt.textContent =
    guide.review_prompt || "Review the generated evidence before citing the result.";
}

function campaignStudyTemplateLastRunMarkup(item) {
  const lastRun = item.last_run;
  if (!lastRun) {
    return `
      <div class="campaign-study-template-last-run is-empty">
        <strong>No run provenance yet</strong>
        <span>Run this template to attach a recommendation, report, and bundle.</span>
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
  const importStatus = item.packaged
    ? "Packaged template"
    : item.imported
    ? `Imported from ${shortRunId(item.imported_from_template_id)}`
    : "Local template";
  const exportStatus = item.packaged
    ? "Packaged JSON"
    : item.exportable ? "Export-ready JSON" : "Export pending";
  const metrics = (item.metrics || [])
    .slice(0, 4)
    .map((metric) => metric.label || metric)
    .join(", ");
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
      <p>${escapeHtml(item.purpose || item.description || "Reusable Campaign Studio study template.")}</p>
      <dl class="campaign-study-template-meta">
        <div>
          <dt>Runtime</dt>
          <dd>${escapeHtml(item.expected_runtime || "Runtime not documented")}</dd>
        </div>
        <div>
          <dt>Metrics</dt>
          <dd>${escapeHtml(metrics || item.primary_metric || "Not documented")}</dd>
        </div>
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
      ${
        item.limitations?.length
          ? `
            <p><strong>Limitations:</strong> ${escapeHtml(item.limitations.slice(0, 2).join(" "))}</p>
          `
          : ""
      }
      ${
        item.non_claims?.length
          ? `
            <p><strong>Non-claims:</strong> ${escapeHtml(item.non_claims.slice(0, 2).join(" "))}</p>
          `
          : ""
      }
      ${campaignStudyTemplateLastRunMarkup(item)}
    </article>
  `;
}

function renderCampaignStudyTemplates() {
  const summaries = state.campaignStudyTemplates || [];
  const selected = selectedCampaignStudyTemplateSummary();
  const hostedDemo = hostedDemoEnabled();
  els.campaignStudyTemplateStatus.textContent = summaries.length
    ? `${summaries.length} ${summaries.length === 1 ? "template" : "templates"}`
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
  els.saveCampaignStudyTemplateButton.disabled = hostedDemo || !draft.valid;
  els.loadCampaignStudyTemplateButton.disabled = !selected;
  els.runCampaignStudyTemplateButton.disabled =
    !selected || (hostedDemo && selected.template_id !== "self-interaction-sweep");
  setCampaignStudyTemplateDownloadEnabled(selected);
  els.campaignStudyTemplateSummary.textContent = selected
    ? `${selected.label}: ${formatRunCount(selected.planned_run_count)} scored by ${selected.primary_metric} (${selected.goal}). ${selected.last_run ? `Last run recommended ${shortRunId(selected.last_run.recommended_run_id)}.` : "Run it once to attach provenance."}`
    : hostedDemo
      ? "Hosted demo offers packaged study templates only; install QS-DMSS locally to save or import custom campaign designs."
      : "Save edited grids and decision profiles as reusable local JSON templates that another user can import and rerun.";
  els.campaignStudyTemplateFeedback.textContent = selected
    ? hostedDemo
      ? `Selected template ${selected.template_id}. Hosted demo can run the packaged Self-Interaction Sweep and download its JSON for inspection.`
      : `Selected template ${selected.template_id}. Load it to edit, run it directly, or download portable JSON for another user.`
    : "Templates preserve the grid, scoring contract, launchable campaign config, and latest run provenance.";
  renderCampaignStudyGuide(
    state.lastCampaignStudyGuide || campaignStudyTemplateGuideFromSummary(selected),
  );
  applyHostedDemoMode();
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

function metricRowsForCampaignResearchObject(result) {
  const comparison = result?.comparison || {};
  const ranges = comparison.ranges || {};
  const decision = comparison.decision || {};
  const artifact = result?.artifact?.summary || {};
  return [
    ["Campaign runs", String(result?.runs?.length || artifact.run_count || 0)],
    ["Recommended run", shortRunId(decision.recommended_run_id || result?.campaign?.recommended_run_id)],
    ["Decision status", decision.status || "not available"],
    ["Energy drift span", formatScientific(ranges.energy_drift?.span)],
    ["Norm drift span", formatScientific(ranges.norm_drift?.span)],
    ["Max density span", formatScientific(ranges.max_density?.span)],
    ["Elapsed span", formatSeconds(ranges.elapsed_seconds?.span)],
  ];
}

function evidenceRowsForCampaignResearchObject(result) {
  const artifact = result?.artifact || {};
  const summary = artifact.summary || {};
  const evidence = artifact.evidence || {};
  const decision = result?.comparison?.decision || {};
  return [
    {
      label: "Campaign evidence bundle",
      status: artifact.urls?.bundle ? "available" : "missing",
      detail: artifact.urls?.bundle || "No campaign bundle URL available.",
    },
    {
      label: "Experiment report",
      status: artifact.urls?.report ? "available" : "missing",
      detail: artifact.urls?.report || "No campaign report URL available.",
    },
    {
      label: "Copied run evidence",
      status: evidence.file_count ? "captured" : "not counted",
      detail: `${evidence.file_count || 0} manifest entries across ${summary.run_count || 0} runs.`,
    },
    {
      label: "Decision recommendation",
      status: decision.available ? decision.status || "available" : "unavailable",
      detail: decision.reason || "No recommendation rationale available.",
    },
  ];
}

function artifactRowsForCampaignResearchObject(result) {
  const artifact = result?.artifact || {};
  const experimentId = artifact.summary?.experiment_id || result?.campaign?.id || "campaign";
  const rows = [];
  if (artifact.urls?.report) {
    rows.push({
      kind: "html",
      label: "Campaign report",
      name: `${experimentId}-report.html`,
      url: artifact.urls.report,
    });
  }
  if (artifact.urls?.bundle) {
    rows.push({
      kind: "zip",
      label: "Campaign evidence bundle",
      name: `${experimentId}-evidence-bundle.zip`,
      url: artifact.urls.bundle,
    });
  }
  return rows;
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

function buildLabResearchObject() {
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

function buildCampaignResearchObject() {
  const result = state.lastCampaignStudioResult;
  if (!result) {
    throw new Error("Run a Campaign Studio study before composing a campaign research object.");
  }
  const study = campaignStudyForResearchObject();
  const guide = state.lastCampaignStudyGuide || result.guide || {};
  const campaign = result.campaign || {};
  const artifact = result.artifact || {};
  const campaignId = campaign.id || artifact.summary?.experiment_id || "campaign-study";
  const researchObject = {
    generatedAt: new Date().toISOString(),
    scenario: {
      label: study.label || campaign.label || "Campaign Studio study",
      name: study.templateId || campaignId,
      description:
        study.description ||
        guide.plain_language_summary ||
        "Campaign Studio study exported with comparison evidence and recommendation rationale.",
    },
    runId: campaignId,
    claimBoundary:
      (guide.what_this_does_not_claim || [])[0] ||
      "This campaign demonstrates reproducible parameter-study workflow behavior; it is not peer-reviewed scientific validation.",
    status: "Ready",
    metrics: metricRowsForCampaignResearchObject(result),
    evidence: evidenceRowsForCampaignResearchObject(result),
    artifacts: artifactRowsForCampaignResearchObject(result),
    interpretation: {
      summary:
        guide.plain_language_summary ||
        "QS-DMSS ran a Campaign Studio study and preserved the comparison evidence, scoring contract, and recommendation rationale.",
      means: [
        ...(guide.what_changed || []),
        ...(guide.metric_meanings || []),
      ],
      nonClaims:
        guide.what_this_does_not_claim ||
        [
          "This campaign does not prove a scientifically correct parameter value.",
          "This campaign does not replace external validation or peer review.",
        ],
      reviewPrompt:
        guide.review_prompt ||
        "Review whether the campaign evidence makes parameter behavior understandable.",
    },
    comparison: {
      available: Boolean(result.comparison),
      summary:
        guide.plain_language_summary ||
        `${campaign.label || "Campaign Studio"} compared ${result.runs?.length || 0} variants.`,
      rows: comparisonRowsForResearchObject(result),
      reportUrl: artifact.urls?.report || "",
      bundleUrl: artifact.urls?.bundle || "",
    },
    campaignStudy: study,
    replayCommands: [
      "# In the cockpit, import or load the study template JSON.",
      "# Then run the saved Campaign Studio template to reproduce the campaign design.",
      `qs-dmss experiments list --output-root "runs"`,
      `qs-dmss verify "<selected-run-dir-from-${campaignId}>"`,
    ],
  };
  const fileStem = `${researchObject.scenario.name}-${shortRunId(campaignId)}-research-object`;
  researchObject.fileName = `${fileStem}.md`;
  researchObject.markdown = buildResearchObjectMarkdown(researchObject);
  return researchObject;
}

function buildResearchObject() {
  if (state.labResult) {
    return buildLabResearchObject();
  }
  return buildCampaignResearchObject();
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
    <div class="research-object-comparison-chart" data-research-comparison-chart></div>
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
  const exportJob = jobSummary(researchObject.executionJob);
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
      <section class="research-object-card research-object-summary-card">
        <p class="artifact-list-title">Scenario</p>
        <h5>${escapeHtml(researchObject.scenario.label)}</h5>
        <p>${escapeHtml(researchObject.scenario.description)}</p>
        <p class="research-object-boundary">${escapeHtml(researchObject.claimBoundary)}</p>
      </section>
      <section class="research-object-card research-object-metrics-card">
        <p class="artifact-list-title">Metrics</p>
        <dl class="lab-report-metrics">${researchObjectMetricsMarkup(researchObject)}</dl>
      </section>
      <section class="research-object-card research-object-evidence-card">
        <p class="artifact-list-title">Evidence And Replay</p>
        <ul class="research-object-evidence-list">${researchObjectEvidenceMarkup(researchObject)}</ul>
      </section>
      <section class="research-object-card research-object-artifacts-card">
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
      <section class="research-object-card research-object-replay-card">
        <p class="artifact-list-title">Replay Instructions</p>
        <pre><code>${escapeHtml(researchObject.replayCommands.join("\n"))}</code></pre>
      </section>
      <section class="research-object-card research-object-citation-card">
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
      <section class="research-object-card research-object-provenance-card">
        <p class="artifact-list-title">Export Provenance</p>
        ${
          exportJob
            ? `
              <div>${jobCellMarkup(exportJob)}</div>
              <p>
                Persisted as ${escapeHtml(researchObject.export?.file_name || researchObject.fileName)}
                with job lifecycle and artifact roles in the local registry.
              </p>
            `
            : "<p>Compose the research object to persist export job provenance.</p>"
        }
      </section>
    </div>
  `;
  const comparison = state.labComparisonResult?.comparison || state.lastCampaignStudioResult?.comparison;
  renderInteractiveComparisonChart(
    els.researchObjectSurface.querySelector("[data-research-comparison-chart]"),
    comparison,
    "research",
  );
}

function renderResearchObjectComposer() {
  const hasLabResult = Boolean(state.labResult);
  const hasCampaignResult = Boolean(state.lastCampaignStudioResult);
  const hasResearchMaterial = hasLabResult || hasCampaignResult;
  els.composeResearchObjectButton.disabled = !hasResearchMaterial;
  els.composeResearchObjectButton.textContent = state.researchObject
    ? "Recompose Research Object"
    : "Compose Research Object";
  els.researchObjectCta.hidden = !state.researchObject;
  setResearchObjectDownloadEnabled(Boolean(state.researchObject));
  updateDemoPath();

  if (!hasResearchMaterial) {
    els.researchObjectStatus.textContent = "Run showcase or campaign first";
    els.researchObjectStatus.className = "selection-chip";
    els.researchObjectLede.textContent =
      "Compose a shareable research object after Lab Mode or Campaign Studio generates evidence, comparison, artifact, and citation metadata.";
    els.researchObjectSurface.innerHTML = `
      <p>
        Your publication-grade summary will appear here after export, including metrics,
        figure or campaign links, evidence status, replay instructions, and citation metadata.
      </p>
    `;
    return;
  }

  if (!state.researchObject) {
    els.researchObjectStatus.textContent = state.labComparisonResult || hasCampaignResult
      ? "Ready with comparison"
      : "Ready to compose";
    els.researchObjectStatus.className = "selection-chip";
    els.researchObjectLede.textContent = hasCampaignResult && !hasLabResult
      ? "Campaign Studio is ready. Compose a research object with the study template, scoring contract, recommendation rationale, report, and bundle links."
      : state.labComparisonResult
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

async function handleComposeResearchObject() {
  if (!state.labResult && !state.lastCampaignStudioResult) {
    return;
  }
  clearResearchObject();
  const researchObject = buildResearchObject();
  els.composeResearchObjectButton.disabled = true;
  els.composeResearchObjectButton.textContent = "Exporting...";

  try {
    const payload = await fetchJson("/api/research-objects/export", {
      method: "POST",
      body: JSON.stringify({ research_object: researchObject }),
    });
    state.researchObject = payload.research_object;
    state.researchObject.executionJob = payload.execution_job;
    state.researchObject.export = payload.export;
    state.researchObjectDownloadUrl = payload.export.download_url;
    renderResearchObjectComposer();
    revealDemoResult(els.researchObjectSurface);
    toast(
      "Research object exported",
      `Markdown persisted with job ${shortRunId(payload.execution_job?.summary?.job_id)}.`,
      "success",
    );
  } catch (error) {
    clearResearchObject();
    renderResearchObjectComposer();
    toast("Research object export failed", error.message, "danger");
  }
}

async function handleExportWorkspace() {
  if (hostedDemoBlocked("Workspace export")) {
    return;
  }
  const payload = buildWorkspacePayload();
  els.exportWorkspaceButton.disabled = true;
  els.exportWorkspaceButton.textContent = "Exporting...";
  els.workspaceExportStatus.textContent = "Exporting";

  try {
    const response = await fetchJson("/api/workspaces/export", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderWorkspaceExport(response);
    toast(
      "Workspace exported",
      `${response.summary.workspace_id} is ready to download or hand off.`,
      "success",
    );
  } catch (error) {
    els.workspaceExportStatus.textContent = "Export failed";
    toast("Workspace export failed", error.message, "danger");
  } finally {
    els.exportWorkspaceButton.disabled = false;
    els.exportWorkspaceButton.textContent = "Export Workspace";
  }
}

async function handleImportWorkspace(event) {
  if (hostedDemoBlocked("Workspace import")) {
    event.target.value = "";
    return;
  }
  const [file] = event.target.files || [];
  if (!file) {
    return;
  }
  els.workspaceExportStatus.textContent = "Importing";

  try {
    const parsed = JSON.parse(await file.text());
    const workspace = parsed.workspace || parsed;
    const payload = await fetchJson("/api/workspaces/import", {
      method: "POST",
      body: JSON.stringify({ workspace }),
    });
    renderWorkspaceExport(payload);
    await refreshCampaignStudyTemplates();
    toast(
      "Workspace imported",
      `${payload.summary.workspace_id} installed ${payload.imported_campaign_studies?.length || 0} study template(s).`,
      "success",
    );
  } catch (error) {
    els.workspaceExportStatus.textContent = "Import failed";
    toast("Workspace import failed", error.message, "danger");
  } finally {
    event.target.value = "";
  }
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

function campaignStudioPreviewFromTemplate(template) {
  const config = template?.config || {};
  const campaign = template?.campaign || config.campaign || {};
  const objective = config.objective || template?.objective || {};
  const constraints = {
    require_verification: true,
    ...(config.constraints || template?.constraints || {}),
  };
  const ranking = config.ranking || template?.ranking || {};
  return {
    available: Boolean(config.campaign || template?.campaign),
    title: "Campaign Studio",
    source_config_name: template?.source_config_name || "campaign-study.yaml",
    label: campaign.label || template?.label || "Campaign Studio study",
    strategy: campaign.strategy || "grid",
    max_runs: campaign.max_runs || campaign.planned_run_count || 2,
    planned_run_count: campaign.planned_run_count || 0,
    dimension_count: campaign.dimension_count || (campaign.dimensions || []).length,
    dimensions: campaign.dimensions || [],
    objective: {
      name: objective.name || "No objective",
      summary: objective.summary || template?.description || "No objective summary provided.",
      primary_metric: objective.primary_metric,
      goal: objective.goal,
      target_value: objective.target_value,
      supported_metrics: decisionMetricOptions,
      supported_goals: objectiveGoalOptions,
    },
    constraint_values: constraints,
    constraints: Object.entries(constraints).map(([name, value]) => ({ name, value })),
    ranking: {
      primary_metric_weight: ranking.primary_metric_weight,
      weights: ranking.weights || {},
    },
    readiness_badges: [
      { label: template?.packaged ? "Packaged template" : "Saved template", status: "ready" },
      { label: "Grid editor", status: "ready" },
      { label: "Objective scoring", status: "ready" },
      { label: "Research export", status: "ready" },
    ],
    summary:
      template?.purpose ||
      template?.description ||
      "Reusable Campaign Studio study template with a launchable scoring contract.",
    current_boundary:
      (template?.non_claims || [])[0] ||
      "This campaign ranks reproducible variants under an explicit scoring contract; it is not a scientific verdict.",
    next_capabilities: template?.limitations || [],
    launch_endpoint: "/api/campaigns",
  };
}

function campaignStudioBaseConfig() {
  if (state.activeCampaignStudyTemplate?.config) {
    return state.activeCampaignStudyTemplate.config;
  }
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
  state.campaignStudio = campaignStudioPreviewFromTemplate(template);
  state.campaignStudioValues = Object.fromEntries(
    config.campaign.dimensions.map((dimension) => [
      dimension.path,
      (dimension.values || []).map(String).join(", "),
    ]),
  );
  state.campaignStudioDecisionValues = campaignStudyDecisionValuesFromConfig(config);
  state.activeCampaignStudyTemplate = template;
  state.lastCampaignStudyGuide = campaignStudyTemplateGuideFromSummary(
    {
      ...template,
      ...template.summary,
    },
  );
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
    description:
      template?.purpose ||
      template?.description ||
      "Campaign Studio design used for objective-driven comparison.",
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
  els.launchCampaignStudioButton.disabled = hostedDemoEnabled() || !draft.valid;
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
  renderResearchRunbook(scenario);
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
  els.launchCampaignButton.disabled = hostedDemoEnabled() || plannedRuns < 2;
}

function renderConfigOptions() {
  els.configTemplate.innerHTML = state.configs
    .map(
      (item) =>
        `<option value="${item.name}" ${item.name === state.selectedTemplateName ? "selected" : ""}>${item.label}</option>`,
    )
    .join("");
  renderConfigContext(configByName(state.selectedTemplateName));
}

function renderConfigContext(item) {
  if (!item) {
    els.configContextTitle.textContent = "No configuration available";
    els.configContextSummary.textContent = "Add a valid YAML study configuration to the local library.";
    els.configLibraryCount.textContent = "0 configurations";
    els.configStudyType.textContent = "—";
    els.configModelSummary.textContent = "—";
    els.configEvidenceFocus.textContent = "—";
    return;
  }
  const engine = item.config?.engine || {};
  const grid = Array.isArray(engine.grid_shape) ? engine.grid_shape.join(" × ") : "unspecified grid";
  els.configContextTitle.textContent = item.label;
  els.configContextSummary.textContent = item.summary || "Versioned deterministic study configuration.";
  els.configLibraryCount.textContent = `${state.configs.length} curated configurations`;
  els.configStudyType.textContent = item.study_type || "Deterministic study";
  els.configModelSummary.textContent = `${engine.backend || "local"} · ${grid} · ${engine.num_steps || 0} steps`;
  els.configEvidenceFocus.textContent = item.evidence_focus || "Metrics, provenance, verification, and replay.";
}

function setRunLaunchStatus(stateName, detail = null, message = "") {
  const stateCopy = {
    idle: ["Ready", "Ready for local execution", "is-idle"],
    running: ["Running", "Local simulation in progress", "is-warning"],
    complete: ["Complete", "Evidence package ready", "is-success"],
    error: ["Action required", "Run launch failed", "is-danger"],
  }[stateName] || ["Review", "Run state changed", "is-warning"];
  els.runLaunchStatus.className = `run-launch-status is-${stateName}`;
  els.runLaunchState.textContent = stateCopy[0];
  els.runLaunchState.className = `status-badge ${stateCopy[2]}`;
  els.runLaunchTitle.textContent = stateCopy[1];
  els.runLaunchMessage.textContent = message || (
    stateName === "running"
      ? "Executing the solver, recording diagnostics, verifying the manifest, and packaging evidence."
      : "Review the selected study contract, then launch a deterministic run."
  );
  els.runLaunchProgress.hidden = stateName !== "running";
  els.runLaunchResultActions.hidden = stateName !== "complete" || !detail;
  const links = [
    [els.runLaunchReviewBundle, detail?.urls?.review_bundle],
    [els.runLaunchStateBundle, detail?.urls?.state_bundle],
    [els.runLaunchFullBundle, detail?.urls?.bundle],
  ];
  links.forEach(([link, url]) => {
    setActionLinkEnabled(link, Boolean(url), url);
    if (url) link.setAttribute("download", "");
    else link.removeAttribute("download");
  });
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
  els.openExperimentReportButton.textContent = !enabled || state.selectedExperiment?.urls?.workbook
    ? "Open Research Workbook"
    : "Open Experiment Report";
  setActionLinkEnabled(
    els.experimentBundleLink,
    enabled,
    enabled ? state.selectedExperiment?.urls?.bundle : null,
  );
}

function renderRunsTable() {
  if (!state.runs.length) {
    els.runsTableBody.innerHTML = `
      <tr>
        <td colspan="9">No runs yet. Launch the first deterministic run from the cockpit.</td>
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
            <input
              class="run-select"
              type="checkbox"
              data-run-check="${run.run_id}"
              aria-label="Select run ${escapeHtml(run.run_id)} for comparison"
              ${checked}
            />
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
          <td>${jobCellMarkup(run.execution_job)}</td>
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
        <td colspan="7">No experiments saved yet.</td>
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
          <td>${jobCellMarkup(experiment.execution_job)}</td>
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

function formatAxisValue(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "-";
  if (numeric === 0) return "0";
  if (Math.abs(numeric) >= 1000 || Math.abs(numeric) < 0.001) {
    return numeric.toExponential(1);
  }
  const formatted = numeric.toPrecision(3);
  return formatted.includes(".") ? formatted.replace(/0+$/, "").replace(/\.$/, "") : formatted;
}

const comparisonMetricDefinitions = {
  energy_drift: {
    label: "Energy drift",
    shortLabel: "Energy",
    description: "Absolute final-minus-initial energy drift recorded by each run.",
    formatter: formatScientific,
  },
  norm_drift: {
    label: "Norm drift",
    shortLabel: "Norm",
    description: "Absolute final-minus-initial norm drift recorded by each run.",
    formatter: formatScientific,
  },
  max_density: {
    label: "Maximum density",
    shortLabel: "Density",
    description: "Largest final density value recorded for each run.",
    formatter: formatScientific,
  },
  elapsed_seconds: {
    label: "Elapsed time",
    shortLabel: "Elapsed",
    description: "Observed local execution time; environment and workload affect this metric.",
    formatter: formatSeconds,
  },
};

function comparisonVariantLabel(row, index) {
  return (
    row.variant_label ||
    row.parameter_value_label ||
    (index === 0 ? "Baseline" : row.config_name) ||
    `Variant ${index + 1}`
  );
}

function comparisonMarkerMarkup(index, x, y, color) {
  const shape = index % 4;
  if (shape === 1) {
    return `<rect x="${x - 7}" y="${y - 7}" width="14" height="14" rx="2" fill="${color}" />`;
  }
  if (shape === 2) {
    return `<path d="M ${x} ${y - 9} L ${x + 9} ${y} L ${x} ${y + 9} L ${x - 9} ${y} Z" fill="${color}" />`;
  }
  if (shape === 3) {
    return `<path d="M ${x} ${y - 9} L ${x + 9} ${y + 7} L ${x - 9} ${y + 7} Z" fill="${color}" />`;
  }
  return `<circle cx="${x}" cy="${y}" r="8" fill="${color}" />`;
}

function renderInteractiveComparisonChart(container, comparison, scope = "main") {
  if (!container) return;
  const rows = (comparison?.rows || []).filter((row) => row && row.run_id);
  if (rows.length < 2) {
    container.innerHTML = `
      <p class="comparison-chart-placeholder">
        Compare at least two runs to activate the metric explorer. The evidence table remains the complete numerical fallback.
      </p>
    `;
    return;
  }

  const metricKey = comparisonMetricDefinitions[state.comparisonMetrics[scope]]
    ? state.comparisonMetrics[scope]
    : "energy_drift";
  const metric = comparisonMetricDefinitions[metricKey];
  const validRows = rows
    .map((row, index) => ({ row, index, value: Number(row[metricKey]) }))
    .filter((item) => Number.isFinite(item.value));
  if (validRows.length < 2) {
    container.innerHTML = `<p class="comparison-chart-placeholder">${escapeHtml(metric.label)} is unavailable for this comparison.</p>`;
    return;
  }

  const baseline = validRows.find((item) => item.row.run_id === comparison.baseline_run_id) || validRows[0];
  const values = validRows.map((item) => item.value);
  let domainMin = Math.min(...values);
  let domainMax = Math.max(...values);
  if (["energy_drift", "norm_drift"].includes(metricKey)) {
    domainMin = Math.min(0, domainMin);
    domainMax = Math.max(0, domainMax);
  }
  const rawSpan = domainMax - domainMin;
  const padding = rawSpan ? rawSpan * 0.1 : Math.max(Math.abs(domainMax) * 0.2, 1e-12);
  domainMin -= padding;
  domainMax += padding;

  const width = 900;
  const height = 132 + validRows.length * 64;
  const plotLeft = 218;
  const plotRight = 670;
  const plotTop = 78;
  const plotBottom = height - 48;
  const xScale = (value) =>
    plotLeft + ((value - domainMin) / Math.max(domainMax - domainMin, Number.EPSILON)) * (plotRight - plotLeft);
  const palette = ["#237777", "#c45f28", "#78844c", "#3d5a80", "#9b5f78"];
  const axisTicks = Array.from({ length: 5 }, (_, index) => {
    const fraction = index / 4;
    const value = domainMin + (domainMax - domainMin) * fraction;
    const x = plotLeft + (plotRight - plotLeft) * fraction;
    return `
      <line x1="${x}" y1="${plotTop}" x2="${x}" y2="${plotBottom}" stroke="rgba(21,57,61,.1)" />
      <text x="${x}" y="${height - 21}" text-anchor="middle" fill="#627176" font-size="11">${escapeHtml(formatAxisValue(value))}</text>
    `;
  }).join("");
  const baselineX = xScale(baseline.value);
  const marks = validRows
    .map(({ row, index, value }, visibleIndex) => {
      const y = 112 + visibleIndex * 64;
      const x = xScale(value);
      const color = palette[index % palette.length];
      const label = comparisonVariantLabel(row, index);
      const code = index === baseline.index ? "B" : `V${index}`;
      const delta = value - baseline.value;
      const deltaLabel = index === baseline.index
        ? "baseline"
        : `${delta >= 0 ? "+" : ""}${metric.formatter(delta)} vs baseline`;
      const accessibleLabel = `${label}, ${metric.label} ${metric.formatter(value)}, ${deltaLabel}`;
      return `
        <line x1="${plotLeft}" y1="${y}" x2="${plotRight}" y2="${y}" stroke="rgba(21,57,61,.08)" />
        <text x="26" y="${y - 4}" fill="#17383c" font-size="13" font-weight="800">${escapeHtml(code)} · ${escapeHtml(label.slice(0, 24))}</text>
        <text x="26" y="${y + 15}" fill="#627176" font-size="10">${escapeHtml(shortRunId(row.run_id))}</text>
        <g class="comparison-chart-point" tabindex="0" role="img" aria-label="${escapeHtml(accessibleLabel)}" data-chart-readout="${escapeHtml(accessibleLabel)}">
          <circle class="chart-hit-target" cx="${x}" cy="${y}" r="18" fill="transparent" />
          ${comparisonMarkerMarkup(index, x, y, color)}
          <circle class="comparison-focus-ring" cx="${x}" cy="${y}" r="13" fill="none" stroke="${color}" stroke-width="2" />
          <title>${escapeHtml(accessibleLabel)}</title>
        </g>
        <text x="696" y="${y - 3}" fill="#17383c" font-size="12" font-weight="800">${escapeHtml(metric.formatter(value))}</text>
        <text x="696" y="${y + 15}" fill="#627176" font-size="10">${escapeHtml(deltaLabel)}</text>
      `;
    })
    .join("");
  const spread = Math.max(...values) - Math.min(...values);
  const summary = `${metric.label} spans ${metric.formatter(spread)} across ${validRows.length} runs. Baseline ${comparisonVariantLabel(baseline.row, baseline.index)} is ${metric.formatter(baseline.value)}. Each metric uses its own labeled scale.`;

  container.innerHTML = `
    <div class="comparison-chart-head">
      <div>
        <p class="artifact-list-title">Interactive Metric Explorer</p>
        <h3>${escapeHtml(metric.label)} across variants</h3>
        <p>${escapeHtml(metric.description)}</p>
      </div>
      <div class="comparison-metric-toolbar" role="toolbar" aria-label="Choose comparison metric">
        ${Object.entries(comparisonMetricDefinitions)
          .map(
            ([key, definition]) => `
              <button type="button" data-comparison-metric="${key}" aria-pressed="${String(key === metricKey)}">
                ${escapeHtml(definition.shortLabel)}
              </button>
            `,
          )
          .join("")}
      </div>
    </div>
    <div class="comparison-chart-viewport">
      <svg class="comparison-chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(metric.label)} dot plot for ${validRows.length} compared runs">
        <title>${escapeHtml(metric.label)} comparison</title>
        <desc>${escapeHtml(summary)} Focus a marker for its run value and baseline delta.</desc>
        ${axisTicks}
        <line x1="${baselineX}" y1="${plotTop}" x2="${baselineX}" y2="${plotBottom}" stroke="#d7a33d" stroke-width="2" stroke-dasharray="5 5" />
        <text x="${Math.min(baselineX + 6, plotRight - 70)}" y="${plotTop - 12}" fill="#8a651d" font-size="10" font-weight="800">BASELINE</text>
        ${marks}
        <text x="${(plotLeft + plotRight) / 2}" y="${height - 4}" text-anchor="middle" fill="#40575c" font-size="11" font-weight="800">${escapeHtml(metric.label)} · direct recorded values</text>
      </svg>
    </div>
    <p class="comparison-chart-readout" aria-live="polite">${escapeHtml(summary)}</p>
  `;

  const readout = container.querySelector(".comparison-chart-readout");
  container.querySelectorAll(".comparison-chart-point").forEach((point) => {
    const update = () => {
      readout.textContent = point.dataset.chartReadout;
    };
    point.addEventListener("pointerenter", update);
    point.addEventListener("focus", update);
    point.addEventListener("click", update);
  });
  container.querySelectorAll("[data-comparison-metric]").forEach((button) => {
    button.addEventListener("click", () => {
      state.comparisonMetrics[scope] = button.dataset.comparisonMetric;
      renderInteractiveComparisonChart(container, comparison, scope);
    });
  });
}

function renderScientificTrace(svg, history, key, options) {
  const width = 720;
  const height = 300;
  const margin = { top: 28, right: 32, bottom: 54, left: 82 };
  svg.innerHTML = "";
  const readout = svg.parentElement?.querySelector("[data-chart-readout]");

  const samples = (history || [])
    .map((item, index) => ({
      step: Number.isFinite(Number(item.step)) ? Number(item.step) : index,
      value: Number(item[key]),
    }))
    .filter((item) => Number.isFinite(item.step) && Number.isFinite(item.value));
  if (!samples.length) {
    if (readout) readout.textContent = "No recorded samples are available for this diagnostic.";
    return null;
  }

  const initial = samples[0].value;
  const denominator = Math.abs(initial) || 1;
  const relative = samples.map((item) => ({
    ...item,
    delta: (item.value - initial) / denominator,
  }));
  const xMin = Math.min(...relative.map((item) => item.step));
  const xMax = Math.max(...relative.map((item) => item.step));
  const rawYMin = Math.min(0, ...relative.map((item) => item.delta));
  const rawYMax = Math.max(0, ...relative.map((item) => item.delta));
  const rawSpan = rawYMax - rawYMin;
  const yPadding = rawSpan ? rawSpan * 0.14 : Math.max(Math.abs(rawYMax) * 0.2, 1e-12);
  const yMin = rawYMin - yPadding;
  const yMax = rawYMax + yPadding;
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const xScale = (value) =>
    margin.left + ((value - xMin) / Math.max(xMax - xMin, 1)) * plotWidth;
  const yScale = (value) =>
    margin.top + ((yMax - value) / Math.max(yMax - yMin, Number.EPSILON)) * plotHeight;
  const coordinates = relative.map((item) => ({
    ...item,
    x: xScale(item.step),
    y: yScale(item.delta),
  }));
  const linePoints = coordinates.map((item) => `${item.x.toFixed(2)},${item.y.toFixed(2)}`).join(" ");
  const zeroY = yScale(0);
  const areaPoints = [
    `${coordinates[0].x.toFixed(2)},${zeroY.toFixed(2)}`,
    ...coordinates.map((item) => `${item.x.toFixed(2)},${item.y.toFixed(2)}`),
    `${coordinates.at(-1).x.toFixed(2)},${zeroY.toFixed(2)}`,
  ].join(" ");
  const peak = coordinates.reduce((current, item) =>
    Math.abs(item.delta) > Math.abs(current.delta) ? item : current,
  );
  const final = coordinates.at(-1);
  const gradientId = `${svg.id}-area-gradient`;

  const xTicks = Array.from({ length: 5 }, (_, index) => {
    const fraction = index / 4;
    const value = xMin + (xMax - xMin) * fraction;
    const x = margin.left + plotWidth * fraction;
    return `
      <line x1="${x}" y1="${margin.top}" x2="${x}" y2="${height - margin.bottom}" stroke="rgba(21,57,61,0.09)" stroke-width="1" />
      <text x="${x}" y="${height - margin.bottom + 22}" text-anchor="middle" fill="#627176" font-size="11">${formatAxisValue(value)}</text>
    `;
  }).join("");
  const yTicks = Array.from({ length: 5 }, (_, index) => {
    const fraction = index / 4;
    const value = yMax - (yMax - yMin) * fraction;
    const y = margin.top + plotHeight * fraction;
    return `
      <line x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" stroke="rgba(21,57,61,0.1)" stroke-width="1" />
      <text x="${margin.left - 12}" y="${y + 4}" text-anchor="end" fill="#627176" font-size="11">${formatAxisValue(value)}</text>
    `;
  }).join("");
  const points = coordinates
    .map(
      (item) => `
        <g
          class="trace-point"
          tabindex="0"
          role="img"
          aria-label="Step ${formatAxisValue(item.step)}: ${escapeHtml(key)} ${formatScientific(item.value)}, relative change ${formatScientific(item.delta)}"
          data-chart-readout="Step ${formatAxisValue(item.step)} · ${escapeHtml(key)} ${formatScientific(item.value)} · relative change ${formatSignedScientific(item.delta)}"
        >
          <circle class="chart-hit-target" cx="${item.x}" cy="${item.y}" r="12" fill="transparent" />
          <circle class="trace-visible-point" cx="${item.x}" cy="${item.y}" r="4" fill="#fffdf8" stroke="${options.color}" stroke-width="2" />
          <title>Step ${formatAxisValue(item.step)}: ${key} ${formatScientific(item.value)}, relative change ${formatScientific(item.delta)}</title>
        </g>
      `,
    )
    .join("");
  const annotationX = Math.min(peak.x + 12, width - margin.right - 150);
  const annotationY = Math.max(margin.top + 18, peak.y - 12);

  svg.innerHTML = `
    <title>${escapeHtml(options.title)}</title>
    <desc>${escapeHtml(options.description)} Relative values use the first recorded sample as the reference.</desc>
    <defs>
      <linearGradient id="${gradientId}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${options.color}" stop-opacity="0.22" />
        <stop offset="100%" stop-color="${options.color}" stop-opacity="0.02" />
      </linearGradient>
    </defs>
    ${xTicks}
    ${yTicks}
    <line x1="${margin.left}" y1="${zeroY}" x2="${width - margin.right}" y2="${zeroY}" stroke="#334f54" stroke-width="1.4" stroke-dasharray="5 5" />
    <polygon points="${areaPoints}" fill="url(#${gradientId})" />
    <polyline points="${linePoints}" fill="none" stroke="${options.color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
    ${points}
    <line x1="${peak.x}" y1="${peak.y}" x2="${annotationX}" y2="${annotationY}" stroke="${options.color}" stroke-width="1" />
    <text x="${annotationX + 4}" y="${annotationY - 4}" fill="#263f43" font-size="11" font-weight="700">Peak |change| ${formatScientific(Math.abs(peak.delta))}</text>
    <text x="${width / 2}" y="${height - 12}" text-anchor="middle" fill="#40575c" font-size="12" font-weight="700">Simulation step</text>
    <text x="18" y="${height / 2}" transform="rotate(-90 18 ${height / 2})" text-anchor="middle" fill="#40575c" font-size="12" font-weight="700">${escapeHtml(options.yLabel)}</text>
    <text x="${width - margin.right}" y="${margin.top + 2}" text-anchor="end" fill="#627176" font-size="10" font-weight="700">Diagnostic trajectory · ${coordinates.length} samples</text>
  `;

  if (readout) {
    if (!readout.id) readout.id = `${svg.id}-readout`;
    svg.setAttribute("aria-describedby", readout.id);
    readout.textContent = `Final step ${formatAxisValue(final.step)} · ${key} ${formatScientific(final.value)} · relative change ${formatSignedScientific(final.delta)}. Peak absolute change ${formatScientific(Math.abs(peak.delta))}.`;
    svg.querySelectorAll(".trace-point").forEach((point) => {
      const update = () => {
        readout.textContent = point.dataset.chartReadout;
      };
      point.addEventListener("pointerenter", update);
      point.addEventListener("focus", update);
      point.addEventListener("click", update);
    });
  }

  return {
    initial,
    final: final.value,
    finalRelative: final.delta,
    peakRelative: Math.abs(peak.delta),
  };
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
  els.bundleSizeValue.textContent = `${detail.evidence.bundle_size_label} · SHA ${detail.evidence.bundle_sha256.slice(0, 12)}`;
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

function renderReleaseIdentity(release = {}) {
  const version = String(release.version || citationMetadata.packageVersion).replace(/^v/i, "");
  const archivedTag = String(release.latest_archived_release_tag || citationMetadata.releaseTag);
  const archivedDoi = release.archived_release_doi || "10.5281/zenodo.21366910";
  const archivedDoiUrl = release.archived_release_doi_url || `https://doi.org/${archivedDoi}`;
  const projectDoi = release.project_doi || "10.5281/zenodo.20074924";
  const projectDoiUrl = release.project_doi_url || `https://doi.org/${projectDoi}`;

  els.releaseVersion.textContent = `Build v${version}`;
  els.releaseDoi.textContent = `Latest archive ${archivedTag} DOI ${archivedDoi}`;
  els.releaseDoi.href = archivedDoiUrl;
  els.releaseDoi.title = `Open archived QS-DMSS ${archivedTag} release`;
  els.projectDoi.textContent = `Project DOI ${projectDoi}`;
  els.projectDoi.href = projectDoiUrl;
  els.projectDoi.title = `Project DOI ${projectDoi}`;
}

function renderOverviewResearchObject(detail = null) {
  if (!detail?.summary?.run_id) {
    els.overviewObjectType.textContent = "No object selected";
    els.overviewResearchObjectTitle.textContent = "Run a packaged or quantum study";
    els.overviewObjectId.textContent = "—";
    els.overviewObjectStatus.textContent = "Awaiting execution";
    els.overviewObjectCreated.textContent = "—";
    els.overviewObjectMethod.textContent = "—";
    els.overviewObjectEvidence.textContent = "Open run ledger";
    els.overviewObjectEvidence.href = "#runs";
    els.overviewResearchObjectSummary.textContent = "No research object selected.";
    return;
  }

  const verification = detail.verification?.success
    ? `verified across ${detail.verification.checked_files} evidence files`
    : "verification pending";
  els.overviewObjectType.textContent = detail.run_record?.experiment ? "Study run" : "Local simulation";
  els.overviewResearchObjectTitle.textContent = detail.summary.name || shortRunId(detail.summary.run_id);
  els.overviewObjectId.textContent = shortRunId(detail.summary.run_id);
  els.overviewObjectStatus.textContent = detail.verification?.success ? "✓ Evidence ready" : "Verification pending";
  els.overviewObjectCreated.textContent = formatTimestamp(detail.summary.finished_at);
  els.overviewObjectMethod.textContent = "Deterministic local execution";
  els.overviewObjectEvidence.textContent = "Open evidence package ↗";
  els.overviewObjectEvidence.href = "#evidence";
  els.overviewResearchObjectSummary.textContent =
    `${shortRunId(detail.summary.run_id)} · ${verification} · finished ${formatTimestamp(detail.summary.finished_at)}.`;
}

function renderOverviewQuantumObject(payload) {
  if (payload?.source !== "live_local_run" || !payload.run?.run_id) return;
  els.overviewObjectType.textContent = "Quantum validation";
  els.overviewResearchObjectTitle.textContent = "Fractal SSFM compilation matrix";
  els.overviewObjectId.textContent = shortRunId(payload.run.run_id);
  els.overviewObjectStatus.textContent = payload.status === "pass" ? "✓ Evidence ready" : "Review required";
  els.overviewObjectCreated.textContent = formatTimestamp(payload.run.completed_at || payload.generated_at);
  els.overviewObjectMethod.textContent = "Live local ideal simulator";
  els.overviewObjectEvidence.textContent = "Open evidence package ↗";
  els.overviewObjectEvidence.href = payload.downloads?.summary || "#quantum-validation";
  els.overviewResearchObjectSummary.textContent = `${payload.run.run_id} · ${payload.validation?.rows_passing || 0}/${payload.validation?.row_count || 0} rows pass.`;
}

function renderSelectedRun(detail) {
  state.selectedRun = detail;
  state.selectedRunId = detail.summary.run_id;
  renderOverviewResearchObject(detail);

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
  els.statusJobId.textContent = jobLabel(detail.execution_job);
  els.statusJobBackend.textContent = jobBackendLabel(detail.execution_job);

  const runVariantLabel = detail.run_record.experiment?.parameter_value_label;
  els.detailTitle.textContent = runVariantLabel ? `${runVariantLabel} run` : detail.summary.name;
  els.detailChip.textContent = shortRunId(detail.summary.run_id);
  els.detailDigest.textContent = detail.summary.config_digest;
  const energyTrace = renderScientificTrace(
    els.energyChart,
    detail.metrics.history,
    "energy",
    {
      color: "#c45f28",
      title: "Relative energy change over simulation steps",
      description: "Recorded energy history shown as change relative to the initial value.",
      yLabel: "Relative energy change",
    },
  );
  const normTrace = renderScientificTrace(
    els.normChart,
    detail.metrics.history,
    "norm",
    {
      color: "#237777",
      title: "Relative norm change over simulation steps",
      description: "Recorded norm history shown as change relative to the initial value.",
      yLabel: "Relative norm change",
    },
  );
  els.energyDriftValue.textContent = formatSignedScientific(energyTrace?.finalRelative);
  els.energyInitialValue.textContent = formatScientific(energyTrace?.initial);
  els.energyFinalValue.textContent = formatScientific(energyTrace?.final);
  els.energyRangeValue.textContent = formatScientific(energyTrace?.peakRelative);
  els.normDriftValue.textContent = formatSignedScientific(normTrace?.finalRelative);
  els.normInitialValue.textContent = formatScientific(normTrace?.initial);
  els.normFinalValue.textContent = formatScientific(normTrace?.final);
  els.normRangeValue.textContent = formatScientific(normTrace?.peakRelative);

  els.bundleLink.href = detail.urls.bundle;
  els.bundleLink.setAttribute("download", "");
  setActionLinkEnabled(els.bundleLink, true, detail.urls.bundle);
  [
    [els.reviewBundleLink, detail.urls.review_bundle],
    [els.stateBundleLink, detail.urls.state_bundle],
  ].forEach(([link, url]) => {
    setActionLinkEnabled(link, Boolean(url), url);
    if (url) link.setAttribute("download", "");
  });
  els.verifyButton.disabled = false;
  els.replayButton.disabled = false;
  els.openReportButton.disabled = false;
  els.reportFrame.src = detail.urls.report;
  els.reportHeading.textContent = `Evidence Report - ${detail.summary.run_id}`;

  renderJobProvenance(detail.execution_job);
  renderEvidence(detail);
  renderRunsTable();
}

function renderRecommendation(decision, rows = []) {
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
    const mixedProfiles = decision.objective_profile_status === "mixed";
    els.recommendationLabel.textContent = "Evidence-only comparison";
    els.recommendationRun.textContent = mixedProfiles
      ? "No cross-profile winner"
      : "No ranked winner";
    els.recommendationReason.textContent = decision.reason;
    els.recommendationStatus.textContent = mixedProfiles
      ? `${decision.profile_count || 0} objective profiles`
      : decision.status || "Evidence only";
    els.recommendationStatus.className = `status-badge ${toneForStatus(decision.status)}`;
    els.recommendationScore.textContent = "Not scored";
    return;
  }

  els.recommendationLabel.textContent = decision.profile.objective.name;
  const recommendedRow = rows.find((row) => row.run_id === decision.recommended_run_id);
  const recommendedLabel =
    recommendedRow?.parameter_value_label || recommendedRow?.config_name || "Recommended run";
  els.recommendationRun.textContent = `${recommendedLabel} · ${shortRunId(decision.recommended_run_id)}`;
  els.recommendationReason.textContent = decision.reason;
  els.recommendationStatus.textContent = decision.status;
  els.recommendationStatus.className = `status-badge ${toneForStatus(decision.status)}`;
  els.recommendationScore.textContent = `Score ${formatScore(decision.recommended_score)}`;
}

function renderComparison(comparison) {
  state.comparison = comparison;
  renderRecommendation(comparison?.decision || null, comparison?.rows || []);

  if (!comparison) {
    els.compareTitle.textContent = "Run Comparison";
    els.compareContext.textContent = "Select two or more runs";
    els.compareEnergySpan.textContent = "-";
    els.compareNormSpan.textContent = "-";
    els.compareDensitySpan.textContent = "-";
    els.compareFastestRun.textContent = "-";
    els.comparisonTableBody.innerHTML = `
      <tr>
        <td colspan="10">Select at least two runs to compare.</td>
      </tr>
    `;
    renderInteractiveComparisonChart(els.comparisonChart, null, "main");
    return;
  }

  const shared = comparison.shared_experiment;
  els.compareTitle.textContent = shared ? shared.label : "Run Comparison";
  const comparisonContext = shared
    ? sharedExperimentContext(shared)
    : `${comparison.rows.length} runs selected`;
  els.compareContext.textContent = `${comparisonContext}${
    comparison.decision?.mode === "evidence_only" ? " | evidence-only" : ""
  }`;
  els.compareEnergySpan.textContent = formatScientific(comparison.ranges.energy_drift.span);
  els.compareNormSpan.textContent = formatScientific(comparison.ranges.norm_drift.span);
  els.compareDensitySpan.textContent = formatScientific(comparison.ranges.max_density.span);
  els.compareFastestRun.textContent = shortRunId(comparison.ranges.elapsed_seconds.min_run_id);
  renderInteractiveComparisonChart(els.comparisonChart, comparison, "main");

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
        <td>${jobCellMarkup(row.execution_job)}</td>
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
    renderOverviewResearchObject();
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

const sweepDefaultValues = {
  "engine.g_int": "0.02, 0.05, 0.08",
  "engine.time_step": "0.01, 0.02, 0.03",
  "engine.num_steps": "4, 6, 8",
  "initial.amplitude": "0.8, 1.0, 1.2",
  "initial.width": "0.18, 0.22, 0.28",
  "run.seed": "7, 17, 27",
};

function validateSweepValues(parameter, text) {
  const entries = parseSweepValues(text);
  if (!parameter) {
    return { valid: false, values: [], message: "Choose a supported parameter." };
  }
  if (entries.length < 2) {
    return {
      valid: false,
      values: [],
      message: "Enter at least two comma-separated values to create a comparison.",
    };
  }

  const values = entries.map((entry) => Number(entry));
  if (values.some((value) => !Number.isFinite(value))) {
    return {
      valid: false,
      values: [],
      message: `${parameter.label} accepts numeric values only.`,
    };
  }
  if (parameter.value_type === "int" && values.some((value) => !Number.isInteger(value))) {
    return {
      valid: false,
      values: [],
      message: `${parameter.label} requires whole numbers.`,
    };
  }
  if (
    parameter.minimum !== null
    && parameter.minimum !== undefined
    && values.some((value) => value < Number(parameter.minimum))
  ) {
    return {
      valid: false,
      values: [],
      message: `${parameter.label} values must be at least ${parameter.minimum}.`,
    };
  }
  if (new Set(values.map((value) => String(value))).size !== values.length) {
    return {
      valid: false,
      values: [],
      message: "Remove duplicate values so every planned run represents a distinct comparison point.",
    };
  }
  return {
    valid: true,
    values,
    message: `Preflight passed: ${values.length} distinct ${parameter.value_type === "int" ? "integer" : "numeric"} values.`,
  };
}

function updateSweepContract({ applyDefault = false } = {}) {
  const parameter = sweepParameterByPath(els.sweepParameter.value);
  if (applyDefault && parameter && !els.sweepValues.value.trim()) {
    els.sweepValues.value = sweepDefaultValues[parameter.path] || "";
  }

  const validation = validateSweepValues(parameter, els.sweepValues.value);
  const activeConfig = configByName(els.configTemplate.value);
  const config = currentConfig();
  const seed = Number.isFinite(config.run?.seed) ? config.run.seed : "-";
  const grid = Array.isArray(config.engine?.grid_shape) ? config.engine.grid_shape.join(" × ") : "-";
  const hosted = hostedDemoEnabled();

  els.sweepBaseConfig.options[0].textContent = activeConfig?.label || activeConfig?.name || "Active configuration";
  els.sweepParameterDescription.textContent = parameter?.description || "Choose the single variable under test.";
  els.sweepInterpretationSummary.textContent = parameter
    ? `${parameter.description} Review metric movement across distinct deterministic evidence objects; the recommended row is a workflow result, not physical calibration.`
    : "Select a parameter to see what changes, what stays controlled, and which diagnostics support interpretation.";
  els.sweepChanged.textContent = parameter ? `${parameter.label} · ${parameter.path}` : "One declared parameter";
  els.sweepHeldFixed.textContent =
    "Every other active configuration field, plus the solver, initial-state, and evidence contracts";
  els.sweepCompared.textContent =
    "Energy drift, norm drift, peak density, runtime, verification, and evidence identity";
  els.sweepValidation.textContent = hosted
    ? "Custom sweeps are local-only. Use the packaged Self-Interaction Sweep in hosted mode."
    : validation.message;
  els.sweepValidation.classList.toggle("is-valid", validation.valid && !hosted);
  els.sweepValidation.classList.toggle("is-invalid", !validation.valid || hosted);
  els.sweepValues.setAttribute("aria-invalid", String(!validation.valid));
  els.sweepPlannedCount.textContent = validation.valid
    ? `${validation.values.length} planned runs`
    : "Preflight required";
  els.launchSweepButton.disabled = hosted || !validation.valid;
  els.launchSweepButton.textContent = validation.valid
    ? `Launch ${validation.values.length}-run sweep`
    : "Launch Sweep";
  els.sweepLaunchNote.textContent = hosted
    ? "Hosted mode preserves this contract for review; custom execution remains local-only."
    : validation.valid
      ? `${validation.values.length} deterministic local runs; each receives an evidence bundle, verification result, and shared experiment identifier.`
      : "Complete preflight to create verified runs with a shared experiment identifier.";

  els.sweepPreviewBody.innerHTML = validation.valid
    ? validation.values
      .map(
        (value, index) => `
          <tr>
            <td>${index + 1}</td>
            <td><strong>${escapeHtml(value)}</strong></td>
            <td>${escapeHtml(seed)}</td>
            <td>${escapeHtml(grid)}</td>
            <td><span class="quantum-table-chip">Planned</span></td>
          </tr>
        `,
      )
      .join("")
    : '<tr><td colspan="5">Enter at least two valid, distinct values to preview the run plan.</td></tr>';

  return validation;
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
  els.experimentBundleSize.textContent = `${detail.summary.bundle_size_label} · SHA ${detail.summary.bundle_sha256.slice(0, 12)}`;
  els.experimentJobId.textContent = jobLabel(detail.execution_job || detail.summary.execution_job);
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
  els.experimentJobId.textContent = "-";
  setExperimentActionsEnabled(false);
  renderExperimentRegistry();
}

function restoreInitialHashPosition() {
  if (!window.location.hash) {
    return;
  }
  const target = document.querySelector(window.location.hash);
  if (!target) {
    return;
  }
  window.requestAnimationFrame(() => {
    target.scrollIntoView({ block: "start" });
  });
}

function quantumPayloadRunId(payload) {
  return payload?.run?.run_id || payload?.showcase_id || "packaged-reference";
}

function quantumResourceDelta(currentValue, previousValue) {
  const current = Number(currentValue);
  const previous = Number(previousValue);
  if (!Number.isFinite(current) || !Number.isFinite(previous) || current === previous) return null;
  const delta = current - previous;
  return `${delta > 0 ? "+" : ""}${delta}`;
}

function topologyResourceChanges(rows, previousRows) {
  const previousByOptimization = new Map(
    (previousRows || []).map((row) => [row.optimization_level, row]),
  );
  const changes = [];
  rows.forEach((row) => {
    const previous = previousByOptimization.get(row.optimization_level);
    if (!previous) return;
    [
      ["depth", "depth"],
      ["two_qubit_gates", "CX"],
    ].forEach(([key, label]) => {
      const delta = quantumResourceDelta(row.resources?.[key], previous.resources?.[key]);
      if (delta !== null) changes.push({ optimization: row.optimization_level, key, label, delta });
    });
  });
  return changes;
}

function quantumTopologyChartMarkup(topologyLabel, rows, previousRows, hasPreviousResult) {
  const sortedRows = [...rows].sort(
    (first, second) => first.optimization_level - second.optimization_level,
  );
  const previousByOptimization = new Map(
    (previousRows || []).map((row) => [row.optimization_level, row]),
  );
  const changes = topologyResourceChanges(sortedRows, previousRows);
  const maxValue = Math.max(
    1,
    ...sortedRows.flatMap((row) => [row.resources?.depth || 0, row.resources?.two_qubit_gates || 0]),
  );
  const chartLeft = 44;
  const chartRight = 318;
  const chartTop = 24;
  const chartBottom = 132;
  const xFor = (index) => chartLeft + (index * (chartRight - chartLeft)) / Math.max(1, sortedRows.length - 1);
  const yFor = (value) => chartBottom - (Number(value) / maxValue) * (chartBottom - chartTop);
  const depthPoints = sortedRows
    .map((row, index) => `${xFor(index)},${yFor(row.resources?.depth || 0)}`)
    .join(" ");
  const cxPoints = sortedRows
    .map((row, index) => `${xFor(index)},${yFor(row.resources?.two_qubit_gates || 0)}`)
    .join(" ");
  const grid = [0, 0.5, 1]
    .map((ratio) => {
      const y = chartBottom - ratio * (chartBottom - chartTop);
      const label = Math.round(maxValue * ratio);
      return `
        <line x1="${chartLeft}" y1="${y}" x2="${chartRight}" y2="${y}" class="quantum-chart-grid" />
        <text x="${chartLeft - 8}" y="${y + 4}" text-anchor="end" class="quantum-axis-label">${label}</text>
      `;
    })
    .join("");
  const points = sortedRows
    .map((row, index) => {
      const x = xFor(index);
      const depth = row.resources?.depth || 0;
      const cx = row.resources?.two_qubit_gates || 0;
      const previous = previousByOptimization.get(row.optimization_level);
      const depthDelta = quantumResourceDelta(depth, previous?.resources?.depth);
      const cxDelta = quantumResourceDelta(cx, previous?.resources?.two_qubit_gates);
      const depthY = yFor(depth);
      const cxY = yFor(cx);
      return `
        <circle cx="${x}" cy="${depthY}" r="5" class="quantum-depth-point${depthDelta !== null ? " is-changed" : ""}" data-value="${depth}" data-optimization="${escapeHtml(row.optimization_level)}" />
        <text x="${x}" y="${Math.max(14, depthY - 8)}" text-anchor="middle" class="quantum-point-label quantum-depth-label${depthDelta !== null ? " is-changed" : ""}" data-value="${depth}">${depth}</text>
        <rect x="${x - 4.5}" y="${cxY - 4.5}" width="9" height="9" rx="1" class="quantum-cx-point${cxDelta !== null ? " is-changed" : ""}" data-value="${cx}" data-optimization="${escapeHtml(row.optimization_level)}" />
        <text x="${x}" y="${Math.min(151, cxY + 15)}" text-anchor="middle" class="quantum-point-label quantum-cx-label${cxDelta !== null ? " is-changed" : ""}" data-value="${cx}">${cx}</text>
        <text x="${x}" y="173" text-anchor="middle" class="quantum-axis-label">Opt ${escapeHtml(row.optimization_level)}</text>
      `;
    })
    .join("");
  const refreshText = !hasPreviousResult
    ? `${sortedRows.length * 2} resource values bound from this result.`
    : changes.length
      ? `Recomputed: ${changes.length} of ${sortedRows.length * 2} values changed — ${changes.map((item) => `Opt ${item.optimization} ${item.label} ${item.delta}`).join(" · ")}.`
      : `Recomputed: all ${sortedRows.length * 2} values match the previous result.`;

  return `
    <article class="quantum-topology-card${hasPreviousResult ? (changes.length ? " is-updated" : " is-recomputed") : ""}">
      <div class="quantum-topology-card-head">
        <h4>${escapeHtml(topologyLabel)}</h4>
        <div class="quantum-chart-key" aria-label="Chart key">
          <span><i class="is-depth" aria-hidden="true"></i>Depth</span>
          <span><i class="is-cx" aria-hidden="true"></i>CX gates</span>
        </div>
      </div>
      <svg viewBox="0 0 340 184" role="img" aria-label="${escapeHtml(topologyLabel)} depth and CX count by optimization level">
        ${grid}
        <polyline points="${depthPoints}" class="quantum-depth-line" />
        <polyline points="${cxPoints}" class="quantum-cx-line" />
        ${points}
      </svg>
      <p class="quantum-chart-refresh${changes.length ? " has-changes" : ""}">${escapeHtml(refreshText)}</p>
    </article>
  `;
}

function renderQuantumTopologyCharts(payload, previousPayload = null) {
  const rows = payload.matrix || [];
  const topologies = payload.matrix_definition?.topologies || [];
  const previousRows = previousPayload?.matrix || [];
  const hasPreviousResult = Boolean(previousRows.length) && quantumPayloadRunId(previousPayload) !== quantumPayloadRunId(payload);
  els.quantumTopologyCharts.innerHTML = topologies
    .map((topology) =>
      quantumTopologyChartMarkup(
        topology.label,
        rows.filter((row) => row.topology_id === topology.profile_id),
        previousRows.filter((row) => row.topology_id === topology.profile_id),
        hasPreviousResult,
      ),
    )
    .join("");
  const changeCount = hasPreviousResult
    ? topologies.reduce(
      (total, topology) => total + topologyResourceChanges(
        rows.filter((row) => row.topology_id === topology.profile_id),
        previousRows.filter((row) => row.topology_id === topology.profile_id),
      ).length,
      0,
    )
    : null;
  const valueCount = rows.length * 2;
  const runId = quantumPayloadRunId(payload);
  els.quantumTopologyCharts.dataset.runId = runId;
  els.quantumTopologyCharts.dataset.resourceFingerprint = payload.visualization?.resource_fingerprint || "";
  els.quantumTopologySource.textContent = hasPreviousResult
    ? changeCount
      ? `Live ${shortRunId(runId)} · ${changeCount}/${valueCount} values changed`
      : `Live ${shortRunId(runId)} · recomputed, deterministic match`
    : `${payload.source === "live_local_run" ? "Live harness" : "Reference"} · ${shortRunId(runId)} · ${valueCount} values bound`;
  const figure = els.quantumTopologyCharts.closest(".quantum-figure");
  figure.dataset.runId = runId;
  figure.classList.remove("is-updated", "is-recomputed");
  void figure.offsetWidth;
  figure.classList.add(hasPreviousResult && changeCount ? "is-updated" : "is-recomputed");
}

function renderQuantumVisualProvenance(payload) {
  const isLive = payload.source === "live_local_run";
  const parameters = payload.run?.parameters || {};
  const runId = payload.run?.run_id || payload.showcase_id || "packaged-reference";
  const generated = formatTimestamp(payload.run?.completed_at || payload.generated_at);
  const sourceLabel = isLive ? `Live harness · ${shortRunId(runId)}` : "Packaged reference · not a fresh run";
  els.quantumVisualProvenance.classList.toggle("is-live", isLive);
  els.quantumVisualProvenance.classList.toggle("is-reference", !isLive);
  els.quantumVisualSourceBadge.textContent = isLive ? "Live harness result" : "Packaged reference";
  els.quantumVisualSourceBadge.className = `quantum-source-badge ${isLive ? "is-live" : "is-reference"}`;
  els.quantumVisualProvenanceTitle.textContent = isLive
    ? `Figures redrawn from ${shortRunId(runId)}`
    : "Figures drawn from the packaged reference payload";
  els.quantumVisualProvenanceSummary.textContent = isLive
    ? `Completed ${generated}. Every point, bar, recommendation, and table row below uses this persisted local harness result.`
    : `Generated ${generated}. Run the local harness to replace this reference with a newly identified result.`;
  els.quantumVisualRunId.textContent = shortRunId(runId);
  els.quantumVisualRunId.title = runId;
  els.quantumVisualParameters.textContent = isLive
    ? `${Number(parameters.shots || 0).toLocaleString()} shots · seed ${parameters.seed ?? "—"} · tol ${formatScientific(parameters.reference_tolerance)} / ${formatScientific(parameters.compilation_tolerance)}`
    : "Packaged validation parameters";
  const dataFingerprint = payload.visualization?.resource_fingerprint;
  els.quantumVisualDataDigest.textContent = dataFingerprint
    ? `${dataFingerprint.slice(0, 16)}…`
    : "—";
  els.quantumVisualDataDigest.title = dataFingerprint || "Chart data fingerprint unavailable";
  els.quantumVisualProvenance.dataset.resourceFingerprint = dataFingerprint || "";
  els.quantumTopologySource.textContent = sourceLabel;
  els.quantumAttributionSource.textContent = sourceLabel;
}

const quantumAttributionComponents = [
  ["state_preparation", "State preparation"],
  ["ssfm_evolution", "SSFM evolution"],
  ["measurement", "Measurement"],
  ["full_experiment", "Full circuit"],
];

function quantumAttributionRowKey(row) {
  return `${row?.topology_id || "unknown"}::${row?.optimization_level ?? "unknown"}`;
}

function quantumAttributionRowLabel(row, topologyLabels) {
  return `${topologyLabels.get(row.topology_id) || row.topology_label || row.topology_id || "Unknown topology"} · Opt ${row.optimization_level ?? "—"}`;
}

function quantumAttributionForRow(row, recommended) {
  if (row?.attribution) return row.attribution;
  return quantumAttributionRowKey(row) === quantumAttributionRowKey(recommended)
    ? recommended.attribution || {}
    : {};
}

function quantumAttributionChartData(row, previousRow, recommended) {
  const attribution = quantumAttributionForRow(row, recommended);
  const previousAttribution = previousRow?.attribution || {};
  return quantumAttributionComponents.map(([key, label]) => ({
    key,
    label,
    ...(attribution[key] || {}),
    previous: previousAttribution[key] || null,
  }));
}

function renderQuantumAttributionChart({
  svg,
  status,
  label,
  row,
  previousRow,
  recommended,
  topologyLabels,
  payload,
  hasPreviousResult,
  maxValue,
  slot,
}) {
  const components = quantumAttributionChartData(row, previousRow, recommended);
  const barStart = 178;
  const barWidth = 440;
  const rowHeight = 61;
  const markup = components
    .map((component, index) => {
      const y = 42 + index * rowHeight;
      const depthWidth = ((component.depth || 0) / maxValue) * barWidth;
      const cxWidth = ((component.two_qubit_gates || 0) / maxValue) * barWidth;
      const depthDelta = quantumResourceDelta(component.depth, component.previous?.depth);
      const cxDelta = quantumResourceDelta(
        component.two_qubit_gates,
        component.previous?.two_qubit_gates,
      );
      return `
        <g class="quantum-attribution-row${depthDelta !== null || cxDelta !== null ? " is-changed" : ""}" data-component="${escapeHtml(component.key)}">
          <text x="8" y="${y + 15}" class="quantum-attribution-label">${escapeHtml(component.label)}</text>
          <rect x="${barStart}" y="${y}" width="${barWidth}" height="12" rx="6" class="quantum-bar-track" />
          <rect x="${barStart}" y="${y}" width="${depthWidth}" height="12" rx="6" class="quantum-depth-bar${depthDelta !== null ? " is-changed" : ""}" data-value="${component.depth || 0}" />
          <text x="${Math.min(716, barStart + depthWidth + 9)}" y="${y + 10}" class="quantum-bar-value quantum-depth-label${depthDelta !== null ? " is-changed" : ""}" data-value="${component.depth || 0}">${component.depth || 0}</text>
          <rect x="${barStart}" y="${y + 19}" width="${barWidth}" height="12" rx="6" class="quantum-bar-track" />
          <rect x="${barStart}" y="${y + 19}" width="${cxWidth}" height="12" rx="6" class="quantum-cx-bar${cxDelta !== null ? " is-changed" : ""}" data-value="${component.two_qubit_gates || 0}" />
          <text x="${Math.min(716, barStart + cxWidth + 9)}" y="${y + 29}" class="quantum-bar-value quantum-cx-label${cxDelta !== null ? " is-changed" : ""}" data-value="${component.two_qubit_gates || 0}">${component.two_qubit_gates || 0}</text>
        </g>
      `;
    })
    .join("");
  const sourceDescription = payload.source === "live_local_run"
    ? `Live local harness run ${payload.run?.run_id || "unknown"}`
    : "Packaged validation reference";
  const rowLabel = quantumAttributionRowLabel(row, topologyLabels);
  const titleId = slot === "A" ? "quantumAttributionTitle" : "quantumAttributionCompareTitle";
  const descriptionId = slot === "A" ? "quantumAttributionDescription" : "quantumAttributionCompareDescription";
  svg.innerHTML = `
    <title id="${titleId}">Configuration ${slot}: ${escapeHtml(rowLabel)} resource attribution</title>
    <desc id="${descriptionId}">${escapeHtml(sourceDescription)}. Depth and CX gate counts for ${escapeHtml(rowLabel)} across state preparation, SSFM evolution, measurement, and the full circuit.</desc>
    <g class="quantum-attribution-key" aria-hidden="true">
      <rect x="178" y="10" width="12" height="12" rx="3" class="quantum-depth-bar" />
      <text x="198" y="20">Depth</text>
      <rect x="270" y="10" width="12" height="12" rx="3" class="quantum-cx-bar" />
      <text x="290" y="20">CX gates</text>
    </g>
    ${markup}
  `;
  const changes = components.flatMap((component) => [
    [component.label, "depth", quantumResourceDelta(component.depth, component.previous?.depth)],
    [component.label, "CX", quantumResourceDelta(component.two_qubit_gates, component.previous?.two_qubit_gates)],
  ]).filter((item) => item[2] !== null);
  const valueCount = components.length * 2;
  const runId = quantumPayloadRunId(payload);
  const recommendedKey = quantumAttributionRowKey(recommended);
  const isRecommended = quantumAttributionRowKey(row) === recommendedKey;
  svg.dataset.runId = runId;
  svg.dataset.configurationKey = quantumAttributionRowKey(row);
  svg.dataset.resourceFingerprint = payload.visualization?.resource_fingerprint || "";
  label.textContent = `${rowLabel}${isRecommended ? " · Recommended" : ""}`;
  status.textContent = !hasPreviousResult
    ? `${valueCount} attribution values bound from ${shortRunId(runId)}${isRecommended ? "; recommendation highlighted" : ""}.`
    : changes.length
      ? `Recomputed: ${changes.length} of ${valueCount} values changed — ${changes.map(([component, metric, delta]) => `${component} ${metric} ${delta}`).join(" · ")}.`
      : `Recomputed from ${shortRunId(runId)}: all ${valueCount} attribution values are a deterministic match to the previous result.`;
  status.classList.toggle("has-changes", changes.length > 0);
  return { changes, valueCount, isRecommended };
}

function renderQuantumAttribution(payload, previousPayload = null) {
  const rows = payload.matrix || [];
  const recommended = payload.recommended_configuration || {};
  const topologyLabels = new Map(
    (payload.matrix_definition?.topologies || []).map((item) => [item.profile_id, item.label]),
  );
  const recommendedKey = quantumAttributionRowKey(recommended);
  const rowKeys = new Set(rows.map(quantumAttributionRowKey));
  if (!rowKeys.has(state.quantumAttributionPrimaryKey)) {
    state.quantumAttributionPrimaryKey = rowKeys.has(recommendedKey)
      ? recommendedKey
      : quantumAttributionRowKey(rows[0]);
  }
  if (
    !rowKeys.has(state.quantumAttributionCompareKey)
    || state.quantumAttributionCompareKey === state.quantumAttributionPrimaryKey
  ) {
    const alternative = rows.find(
      (row) => row.pareto_optimal && quantumAttributionRowKey(row) !== state.quantumAttributionPrimaryKey,
    ) || rows.find((row) => quantumAttributionRowKey(row) !== state.quantumAttributionPrimaryKey);
    state.quantumAttributionCompareKey = quantumAttributionRowKey(alternative);
  }
  const primaryRow = rows.find(
    (row) => quantumAttributionRowKey(row) === state.quantumAttributionPrimaryKey,
  ) || rows[0];
  const compareRow = rows.find(
    (row) => quantumAttributionRowKey(row) === state.quantumAttributionCompareKey,
  ) || rows.find((row) => row !== primaryRow) || primaryRow;
  if (!primaryRow || !compareRow) return;

  const optionMarkup = rows.map((row) => {
    const key = quantumAttributionRowKey(row);
    const suffix = key === recommendedKey ? " — Recommended" : "";
    return `<option value="${escapeHtml(key)}">${escapeHtml(quantumAttributionRowLabel(row, topologyLabels) + suffix)}</option>`;
  }).join("");
  els.quantumAttributionPrimarySelect.innerHTML = optionMarkup;
  els.quantumAttributionCompareSelect.innerHTML = optionMarkup;
  els.quantumAttributionPrimarySelect.value = state.quantumAttributionPrimaryKey;
  els.quantumAttributionCompareSelect.value = state.quantumAttributionCompareKey;

  const previousRowsByKey = new Map(
    (previousPayload?.matrix || []).map((row) => [quantumAttributionRowKey(row), row]),
  );
  const hasPreviousResult = Boolean(previousPayload)
    && quantumPayloadRunId(previousPayload) !== quantumPayloadRunId(payload);
  const primaryComponents = quantumAttributionChartData(
    primaryRow,
    previousRowsByKey.get(state.quantumAttributionPrimaryKey),
    recommended,
  );
  const compareComponents = quantumAttributionChartData(
    compareRow,
    previousRowsByKey.get(state.quantumAttributionCompareKey),
    recommended,
  );
  const maxValue = Math.max(
    1,
    ...[...primaryComponents, ...compareComponents].flatMap(
      (component) => [component.depth || 0, component.two_qubit_gates || 0],
    ),
  );
  const primaryResult = renderQuantumAttributionChart({
    svg: els.quantumAttributionChart,
    status: els.quantumAttributionDelta,
    label: els.quantumAttributionPrimaryLabel,
    row: primaryRow,
    previousRow: previousRowsByKey.get(state.quantumAttributionPrimaryKey),
    recommended,
    topologyLabels,
    payload,
    hasPreviousResult,
    maxValue,
    slot: "A",
  });
  const compareResult = renderQuantumAttributionChart({
    svg: els.quantumAttributionCompareChart,
    status: els.quantumAttributionCompareDelta,
    label: els.quantumAttributionCompareLabel,
    row: compareRow,
    previousRow: previousRowsByKey.get(state.quantumAttributionCompareKey),
    recommended,
    topologyLabels,
    payload,
    hasPreviousResult,
    maxValue,
    slot: "B",
  });

  const recommendedRow = rows.find((row) => quantumAttributionRowKey(row) === recommendedKey);
  els.quantumAttributionRecommendationSummary.textContent = recommendedRow
    ? `Highlighted recommendation: ${quantumAttributionRowLabel(recommendedRow, topologyLabels)} · depth ${recommendedRow.resources?.depth ?? "—"} · ${recommendedRow.resources?.two_qubit_gates ?? "—"} CX. Selection remains unrestricted.`
    : "No recommendation is available; every evidence row remains selectable.";
  els.quantumAttributionRosterBody.innerHTML = rows.map((row) => {
    const key = quantumAttributionRowKey(row);
    const isPrimary = key === state.quantumAttributionPrimaryKey;
    const isComparison = key === state.quantumAttributionCompareKey;
    const isRecommended = key === recommendedKey;
    const roles = [
      isRecommended ? '<span class="quantum-table-chip is-recommended">Recommended</span>' : "",
      isPrimary ? '<span class="quantum-table-chip is-slot-a">A</span>' : "",
      isComparison ? '<span class="quantum-table-chip is-slot-b">B</span>' : "",
    ].filter(Boolean).join(" ") || "—";
    return `
      <tr class="${[isRecommended ? "is-recommended" : "", isPrimary ? "is-primary" : "", isComparison ? "is-comparison" : ""].filter(Boolean).join(" ")}">
        <td><strong>${escapeHtml(topologyLabels.get(row.topology_id) || row.topology_label || row.topology_id)}</strong></td>
        <td>${escapeHtml(row.optimization_level)}</td>
        <td>${escapeHtml(String(row.semantics?.acceptance_class || "—").replaceAll("_", " "))}</td>
        <td>${escapeHtml(row.resources?.depth ?? "—")}</td>
        <td>${escapeHtml(row.resources?.two_qubit_gates ?? "—")}</td>
        <td>${escapeHtml(formatScientific(row.semantics?.state_l2_error))}</td>
        <td>${roles}</td>
        <td><span class="attribution-assign-actions"><button type="button" data-attribution-slot="primary" data-attribution-key="${escapeHtml(key)}" aria-pressed="${isPrimary}" aria-label="Assign ${escapeHtml(quantumAttributionRowLabel(row, topologyLabels))} to Configuration A">A</button><button type="button" data-attribution-slot="compare" data-attribution-key="${escapeHtml(key)}" aria-pressed="${isComparison}" aria-label="Assign ${escapeHtml(quantumAttributionRowLabel(row, topologyLabels))} to Configuration B">B</button></span></td>
      </tr>
    `;
  }).join("");

  const runId = quantumPayloadRunId(payload);
  const totalChanges = primaryResult.changes.length + compareResult.changes.length;
  els.quantumAttributionSource.textContent = `${payload.source === "live_local_run" ? "Live" : "Reference"} ${shortRunId(runId)} · A/B comparison · ${rows.length} configurations available`;
  const figure = els.quantumAttributionChart.closest(".quantum-figure");
  figure.dataset.runId = runId;
  figure.dataset.primaryConfiguration = state.quantumAttributionPrimaryKey;
  figure.dataset.compareConfiguration = state.quantumAttributionCompareKey;
  figure.classList.remove("is-updated", "is-recomputed");
  void figure.offsetWidth;
  figure.classList.add(hasPreviousResult && totalChanges ? "is-updated" : "is-recomputed");
}

function setQuantumAttributionSelection(slot, key) {
  if (!state.quantumValidation) return;
  if (slot === "primary") {
    const previousPrimary = state.quantumAttributionPrimaryKey;
    state.quantumAttributionPrimaryKey = key;
    if (state.quantumAttributionCompareKey === key) {
      state.quantumAttributionCompareKey = previousPrimary;
    }
  } else {
    const previousComparison = state.quantumAttributionCompareKey;
    state.quantumAttributionCompareKey = key;
    if (state.quantumAttributionPrimaryKey === key) {
      state.quantumAttributionPrimaryKey = previousComparison;
    }
  }
  renderQuantumAttribution(state.quantumValidation, state.previousQuantumValidation);
}

function renderQuantumMatrix(payload) {
  const rows = payload.matrix || [];
  els.quantumMatrixBody.innerHTML = rows
    .map((row) => {
      const semantics = row.semantics || {};
      return `
        <tr${row.pareto_optimal ? ' class="is-pareto"' : ""}>
          <td><strong>${escapeHtml(row.topology_label || row.topology_id)}</strong></td>
          <td>${escapeHtml(row.optimization_level)}</td>
          <td>${escapeHtml(String(semantics.acceptance_class || "-").replaceAll("_", " "))}</td>
          <td>${escapeHtml(row.resources?.depth ?? "-")}</td>
          <td>${escapeHtml(row.resources?.two_qubit_gates ?? "-")}</td>
          <td>${escapeHtml(formatScientific(semantics.state_l2_error))}</td>
          <td>${escapeHtml(Number(semantics.state_fidelity || 0).toFixed(9))}</td>
          <td>${row.pareto_optimal ? '<span class="quantum-table-chip is-pareto">Pareto</span>' : "-"}</td>
          <td><span class="quantum-table-chip ${row.success ? "is-pass" : "is-review"}">${row.success ? "PASS" : "REVIEW"}</span></td>
        </tr>
      `;
    })
    .join("");
  els.quantumMatrixSummary.textContent = `${payload.validation?.rows_passing || 0} of ${payload.validation?.row_count || rows.length} rows pass; ${payload.validation?.reference_exact_rows || 0} preserve the reference exactly and ${payload.validation?.bounded_approximation_rows || 0} remain within the configured approximation tolerance. Scroll inside the matrix to inspect every row.`;
}

function renderQuantumRuntime(runtime = {}) {
  state.quantumRuntime = runtime;
  const defaults = runtime.defaults || {};
  const scope = runtime.matrix_scope || {};
  if (defaults.shots) els.quantumShotsInput.value = defaults.shots;
  if (defaults.seed !== undefined) els.quantumSeedInput.value = defaults.seed;
  if (defaults.reference_tolerance) els.quantumReferenceToleranceInput.value = defaults.reference_tolerance;
  if (defaults.compilation_tolerance) els.quantumCompilationToleranceInput.value = defaults.compilation_tolerance;
  els.quantumMatrixScope.textContent = `${scope.topology_count || 3} generic topologies × ${(scope.optimization_levels || [0, 1, 2, 3]).length} optimization levels = ${scope.row_count || 12} configurations`;
  els.quantumBasisGates.textContent = `Basis gates: ${(scope.basis_gates || ["rz", "sx", "x", "cx"]).join(", ")}`;

  const executable = Boolean(runtime.live_execution) && !hostedDemoEnabled();
  setControlsDisabled(els.quantumHarnessForm, !executable);
  els.runQuantumValidationButton.disabled = !executable;
  if (executable) {
    els.quantumRunFeedback.textContent = "Ready for a fresh local simulator run.";
  } else if (hostedDemoEnabled()) {
    els.quantumRunFeedback.textContent = "Hosted mode is a read-only evidence archive. Use the local full application to execute the harness.";
  } else {
    els.quantumRunFeedback.textContent = `Simulator stack unavailable. ${runtime.install_command || "Install the quantum optional dependency."}`;
  }
}

function setQuantumProgress(stateName) {
  els.quantumProgressSequence.className = `quantum-progress-sequence is-${stateName}`;
}

function renderQuantumRecommendation(payload) {
  const topologyLabels = new Map(
    (payload.matrix_definition?.topologies || []).map((item) => [item.profile_id, item.label]),
  );
  const candidates = (payload.matrix || [])
    .filter((row) => row.success && row.pareto_optimal)
    .sort((left, right) => (
      (left.resources?.two_qubit_gates || 0) - (right.resources?.two_qubit_gates || 0)
      || (left.resources?.depth || 0) - (right.resources?.depth || 0)
    ))
    .slice(0, 4);
  const recommended = payload.recommended_configuration || {};
  const rows = candidates.length ? candidates : [{
    topology_id: recommended.topology_id,
    optimization_level: recommended.optimization_level,
    resources: { depth: recommended.depth, two_qubit_gates: recommended.two_qubit_gates },
    semantics: { acceptance_class: recommended.acceptance_class },
  }];
  els.quantumRecommendationBody.innerHTML = rows.map((row, index) => `
    <tr${index === 0 ? ' class="is-recommended"' : ""}>
      <td>${escapeHtml(topologyLabels.get(row.topology_id) || row.topology_label || row.topology_id || "-")}</td>
      <td>${escapeHtml(row.optimization_level ?? "-")}</td>
      <td>${escapeHtml(row.resources?.depth ?? "-")}</td>
      <td>${escapeHtml(row.resources?.two_qubit_gates ?? "-")}</td>
      <td>${escapeHtml(String(row.semantics?.acceptance_class || "-").replaceAll("_", " "))}</td>
    </tr>
  `).join("");
}

function renderQuantumValidation(payload) {
  if (!payload || payload.error) {
    els.quantumValidationStatus.textContent = "Snapshot unavailable";
    els.quantumValidationStatus.className = "status-badge is-danger";
    els.quantumMatrixBody.innerHTML = '<tr><td colspan="9">The packaged validation snapshot could not be loaded.</td></tr>';
    [els.quantumBundleLink, els.quantumSummaryLink, els.quantumMatrixLink, els.quantumReportLink]
      .forEach((link) => setActionLinkEnabled(link, false));
    return;
  }

  const previousQuantumValidation = state.quantumValidation;
  if (
    previousQuantumValidation
    && quantumPayloadRunId(previousQuantumValidation) !== quantumPayloadRunId(payload)
  ) {
    state.previousQuantumValidation = previousQuantumValidation;
  }
  state.quantumValidation = payload;
  renderQuantumRuntime(payload.runtime || {});
  const validation = payload.validation || {};
  const policy = payload.execution_policy || {};
  const recommended = payload.recommended_configuration || {};
  const archive = validation.archive || {};
  const downloads = payload.downloads || {};
  const topology = (payload.matrix_definition?.topologies || []).find(
    (item) => item.profile_id === recommended.topology_id,
  );

  const isLive = payload.source === "live_local_run";
  const recordedPackageVersion = payload.run?.package_version;
  const currentPackageVersion = payload.runtime?.package_version;
  const recordedBuildIsCurrent = recordedPackageVersion === currentPackageVersion;
  if (isLive) {
    const parameters = payload.run?.parameters || {};
    if (parameters.shots !== undefined) els.quantumShotsInput.value = parameters.shots;
    if (parameters.seed !== undefined) els.quantumSeedInput.value = parameters.seed;
    if (parameters.reference_tolerance !== undefined) {
      els.quantumReferenceToleranceInput.value = parameters.reference_tolerance;
    }
    if (parameters.compilation_tolerance !== undefined) {
      els.quantumCompilationToleranceInput.value = parameters.compilation_tolerance;
    }
    els.quantumRunFeedback.textContent =
      "Latest persisted evidence loaded. Run the harness again to create a new, independently identified evidence package.";
  }
  els.quantumValidationStatus.textContent = payload.status === "pass"
    ? (isLive ? "PASS / fresh evidence" : (payload.runtime?.live_execution ? "Simulator stack ready" : "PASS / archive ready"))
    : "Review required";
  els.quantumValidationStatus.className = `status-badge ${payload.status === "pass" ? "is-success" : "is-warning"}`;
  els.quantumRowsPassing.textContent = `${validation.rows_passing || 0} / ${validation.row_count || 0}`;
  els.quantumReferenceExact.textContent = String(validation.reference_exact_rows || 0);
  els.quantumBoundedApproximation.textContent = String(validation.bounded_approximation_rows || 0);
  els.quantumExecutionMode.textContent = policy.local_simulation_only ? "Local simulator" : "Review";
  els.quantumAuthorizedSpend.textContent = `$${Number(policy.max_authorized_cost_usd || 0).toFixed(2)}`;
  els.quantumSnapshotDate.textContent = formatTimestamp(payload.generated_at);
  els.quantumSnapshotId.textContent = payload.showcase_id || "packaged evidence";
  els.quantumRunName.textContent = payload.run?.name || "Packaged reference snapshot";
  els.quantumRunFreshness.textContent = isLive
    ? recordedBuildIsCurrent
      ? `Fresh local run · current build v${currentPackageVersion}`
      : recordedPackageVersion
        ? `Live run · build v${recordedPackageVersion}; current app v${currentPackageVersion || "unknown"} — rerun recommended`
        : "Live run · build version not recorded — rerun recommended"
    : payload.runtime?.live_execution
      ? "Reference only · local run required"
      : "Reference archive · local execution unavailable";
  els.quantumRunStatus.textContent = payload.status === "pass"
    ? (isLive ? "✓ PASS / evidence ready" : "Verified reference · run to refresh")
    : "Review required";
  els.quantumRunDuration.textContent = payload.run?.duration_seconds !== undefined
    ? formatSeconds(payload.run.duration_seconds)
    : "Precomputed";
  els.quantumRunPackageVersion.textContent = isLive
    ? recordedPackageVersion
      ? `QS-DMSS v${recordedPackageVersion}`
      : "Version not recorded"
    : payload.showcase_id || "Packaged reference";
  els.quantumRunOutput.textContent = payload.run?.output_directory || "Bundled application asset";
  els.quantumRunVerification.textContent = archive.readable ? "✓ Verified" : "Review required";
  els.quantumBundleSize.textContent = formatBytes(payload.bundle?.size_bytes);
  els.quantumBundleSha.textContent = payload.bundle?.sha256
    ? `${payload.bundle.sha256.slice(0, 16)}...`
    : "-";
  els.quantumArchiveInventory.textContent = archive.readable
    ? `${archive.file_count || 0} files; manifest and JSON report present`
    : "Archive requires review";
  els.quantumRecommendedSummary.textContent = `${topology?.label || recommended.topology_id || "The recommended generic target"}, optimization level ${recommended.optimization_level ?? "-"}, is the minimum-CX tolerance-passing Pareto result: depth ${recommended.depth ?? "-"}, ${recommended.two_qubit_gates ?? "-"} CX gates, and state L2 error ${formatScientific(recommended.state_l2_error)}.`;
  els.quantumLimitations.innerHTML = (payload.limitations || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  [
    [els.quantumBundleLink, downloads.bundle],
    [els.quantumSummaryLink, downloads.summary],
    [els.quantumMatrixLink, downloads.matrix],
    [els.quantumReportLink, downloads.report],
  ].forEach(([link, url]) => setActionLinkEnabled(link, Boolean(url), url));
  renderQuantumVisualProvenance(payload);
  renderQuantumTopologyCharts(payload, state.previousQuantumValidation);
  renderQuantumAttribution(payload, state.previousQuantumValidation);
  renderQuantumMatrix(payload);
  renderQuantumRecommendation(payload);
  setQuantumProgress(isLive ? "complete" : "reference");
  renderOverviewQuantumObject(payload);
}

async function hydrate() {
  const [
    healthPayload,
    quantumValidationPayload,
    latestQuantumValidationPayload,
    configPayload,
    sweepPayload,
    showcasePayload,
    experimentPayload,
    campaignStudyPayload,
    aiStatusPayload,
  ] = await Promise.all([
    fetchJson("/api/health"),
    fetchJson("/api/quantum-validation").catch((error) => ({ error: error.message })),
    fetchJson("/api/quantum-validation/runs/latest").catch(() => ({ available: false })),
    fetchJson("/api/configs"),
    fetchJson("/api/sweeps/parameters"),
    fetchJson("/api/showcases"),
    fetchJson("/api/experiments"),
    fetchJson("/api/campaign-studies"),
    fetchJson("/api/ai/status").catch(() => ({
      enabled: false,
      configured: false,
      availability: "disabled",
      available_in_current_mode: false,
    })),
  ]);
  state.hostedDemo = healthPayload.hosted_demo || null;
  renderReleaseIdentity(healthPayload.release || { version: healthPayload.version });
  renderQuantumValidation(
    latestQuantumValidationPayload.available
      ? latestQuantumValidationPayload.result
      : quantumValidationPayload,
  );
  state.configs = configPayload.items;
  state.sweepParameters = sweepPayload.items;
  state.showcases = showcasePayload.items;
  state.campaignStudio = showcasePayload.campaign_studio || null;
  state.experiments = experimentPayload.items;
  state.campaignStudyTemplates = campaignStudyPayload.items || [];
  state.aiStatus = aiStatusPayload;
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
    updateSweepContract({ applyDefault: true });
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
  applyHostedDemoMode();
  restoreInitialHashPosition();
}

async function handleLaunch(event) {
  event.preventDefault();
  if (hostedDemoBlocked("Custom run launch")) {
    return;
  }
  els.launchButton.disabled = true;
  els.launchForm.setAttribute("aria-busy", "true");
  els.launchButton.innerHTML = '<span class="button-spinner" aria-hidden="true"></span>Running locally…';
  setRunLaunchStatus("running");
  els.runLaunchStatus.focus({ preventScroll: true });
  toast("Run started", "Local deterministic execution is now in progress.", "success");

  try {
    const detail = await fetchJson("/api/runs", {
      method: "POST",
      body: JSON.stringify({
        config: currentConfig(),
        source_name: els.configTemplate.value || "cockpit.yaml",
      }),
    });
    toast("Run complete", `Created ${detail.summary.run_id}`, "success");
    setRunLaunchStatus(
      "complete",
      detail,
      `${shortRunId(detail.summary.run_id)} completed in ${formatSeconds(detail.summary.elapsed_seconds)}; ${detail.verification.checked_files} evidence files verified. Choose a purpose-built package below or inspect the full run detail.`,
    );
    state.runs = [detail.summary, ...state.runs.filter((item) => item.run_id !== detail.summary.run_id)];
    renderSelectedRun(detail);
  } catch (error) {
    toast("Launch failed", error.message, "danger");
    setRunLaunchStatus("error", null, error.message);
  } finally {
    els.launchForm.removeAttribute("aria-busy");
    els.launchButton.disabled = false;
    els.launchButton.textContent = "Launch Run";
  }
}

async function handleQuantumValidationRun(event) {
  event.preventDefault();
  if (hostedDemoBlocked("Live quantum validation")) return;

  const payload = {
    shots: Number(els.quantumShotsInput.value),
    seed: Number(els.quantumSeedInput.value),
    reference_tolerance: Number(els.quantumReferenceToleranceInput.value),
    compilation_tolerance: Number(els.quantumCompilationToleranceInput.value),
  };
  const invalid = (
    !Number.isInteger(payload.shots)
    || payload.shots < 128
    || payload.shots > 100000
    || !Number.isInteger(payload.seed)
    || payload.seed < 0
    || !Number.isFinite(payload.reference_tolerance)
    || payload.reference_tolerance <= 0
    || !Number.isFinite(payload.compilation_tolerance)
    || payload.compilation_tolerance <= 0
  );
  if (invalid) {
    els.quantumRunFeedback.textContent = "Correct the harness inputs before execution: shots 128–100000, non-negative integer seed, and positive tolerances.";
    toast("Quantum preflight failed", "Review the declared shots, seed, and tolerance values.", "danger");
    return;
  }

  setControlsDisabled(els.quantumHarnessForm, true);
  els.runQuantumValidationButton.disabled = true;
  els.runQuantumValidationButton.innerHTML = '<span class="run-icon" aria-hidden="true">◌</span>Running local harness…';
  els.quantumRunFeedback.textContent = "Compiling 12 target configurations, checking semantic equivalence, verifying the manifest, and packaging evidence.";
  els.quantumValidationStatus.textContent = "RUNNING / local simulator";
  els.quantumValidationStatus.className = "status-badge is-warning";
  setQuantumProgress("running");

  try {
    const result = await fetchJson("/api/quantum-validation/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const latest = await fetchJson("/api/quantum-validation/runs/latest").catch(() => ({ available: false }));
    const persistedResult = latest.available ? latest.result : result;
    renderQuantumValidation(persistedResult);
    els.quantumRunFeedback.textContent = `Fresh persisted evidence package completed in ${formatSeconds(persistedResult.run?.duration_seconds)}. No provider, credential, remote API, or QPU was used.`;
    toast("Quantum validation complete", `${persistedResult.validation?.rows_passing || 0}/${persistedResult.validation?.row_count || 0} compilation rows passed.`, "success");
  } catch (error) {
    els.quantumValidationStatus.textContent = "RUN FAILED / review required";
    els.quantumValidationStatus.className = "status-badge is-danger";
    els.quantumRunFeedback.textContent = error.message;
    setQuantumProgress("error");
    toast("Quantum validation failed", error.message, "danger");
  } finally {
    const executable = Boolean(state.quantumRuntime?.live_execution) && !hostedDemoEnabled();
    setControlsDisabled(els.quantumHarnessForm, !executable);
    els.runQuantumValidationButton.disabled = !executable;
    els.runQuantumValidationButton.innerHTML = '<span class="run-icon" aria-hidden="true">▶</span>Run validation harness';
  }
}

async function handleLaunchLabMode() {
  const scenarioName = els.labScenarioSelect.value || state.selectedShowcaseName;
  if (!scenarioName) {
    toast("No showcase selected", "Choose a packaged showcase scenario first.", "danger");
    return;
  }

  clearAiDraft("A new run is being created; generate a fresh AI draft after evidence is recorded.");

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
    clearAiDraft(
      "Evidence recorded. Choose an approved task and generate a fresh draft from this run.",
    );
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

  clearAiDraft("A new comparison is being created; generate a fresh critique from its evidence rows.");

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
    clearAiDraft(
      "Comparison evidence recorded. Select Comparison critique to review every variant row.",
    );
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
    revealDemoResult(els.labComparisonResults);
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
    state.lastCampaignStudyGuide = payload.guide || campaignStudyTemplateGuideFromSummary(
      payload.study_template?.summary || studyTemplate,
    );
    state.lastCampaignStudioResult = payload;
    toast(successTitle, `Created ${payload.runs.length} scored campaign runs`, "success");
    state.selectedRunIds = payload.campaign.run_ids;
    await refreshRuns();
    await refreshExperiments();
    if (payload.study_template) {
      await refreshCampaignStudyTemplates();
    }
    renderCampaignStudyGuide(state.lastCampaignStudyGuide);
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
  if (hostedDemoBlocked("Edited Campaign Studio launch")) {
    return;
  }
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
  if (hostedDemoBlocked("Saving custom study templates")) {
    return;
  }
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
    if (
      hostedDemoEnabled() &&
      payload.summary.template_id !== "self-interaction-sweep"
    ) {
      toast(
        "Hosted demo uses curated paths",
        "Only the packaged Self-Interaction Sweep template can run in hosted mode.",
        "danger",
      );
      return;
    }
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
  if (hostedDemoBlocked("Importing study templates")) {
    event.target.value = "";
    return;
  }
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
  if (hostedDemoBlocked("Custom sweep launch")) {
    return;
  }
  const selectedParameter = sweepParameterByPath(els.sweepParameter.value);
  const validation = updateSweepContract();
  if (!selectedParameter || !validation.valid) {
    toast("Sweep preflight failed", validation.message, "danger");
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
        values: validation.values,
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
    updateSweepContract();
  }
}

async function handleLaunchCampaign() {
  if (hostedDemoBlocked("Generic campaign launch")) {
    return;
  }
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
  const workbookUrl = state.selectedExperiment.urls.workbook;
  openReport(
    workbookUrl || state.selectedExperiment.urls.report,
    workbookUrl
      ? `Research Workbook - ${state.selectedExperiment.summary.experiment_id}`
      : `Experiment Report - ${state.selectedExperiment.summary.experiment_id}`,
  );
}

function bindEvents() {
  els.demoRunButton.addEventListener("click", () => els.launchLabButton.click());
  els.demoCompareButton.addEventListener("click", () => els.launchLabComparisonButton.click());
  els.demoExportButton.addEventListener("click", () => els.composeResearchObjectButton.click());
  els.evidenceAssistantPromptGroup.addEventListener("click", (event) => {
    const button = event.target.closest("[data-evidence-assistant-intent]");
    if (!button) return;
    state.evidenceAssistantIntent = button.dataset.evidenceAssistantIntent;
    clearAiDraft("Intent changed. Generate a new draft from the selected evidence context.");
    renderResearchRunbook(showcaseByName(state.selectedShowcaseName));
  });
  els.generateAiDraftButton.addEventListener("click", handleGenerateAiDraft);
  els.aiReviewActions.addEventListener("click", (event) => {
    const button = event.target.closest("[data-ai-review-status]");
    if (!button) return;
    handleAiDraftReview(button.dataset.aiReviewStatus);
  });
  els.labScenarioSelect.addEventListener("change", (event) => {
    state.selectedShowcaseName = event.target.value;
    state.labResult = null;
    state.labComparisonResult = null;
    clearAiDraft("Scenario changed. Select an approved task after recording the relevant evidence.");
    clearResearchObject();
    renderLabMode();
  });

  els.launchLabButton.addEventListener("click", handleLaunchLabMode);
  els.launchLabComparisonButton.addEventListener("click", handleLaunchLabComparison);
  els.labArtifactPreview.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-artifact-preview-url]");
    if (trigger) openArtifactPreview(trigger);
  });
  els.artifactPreviewDialog.addEventListener("close", () => {
    els.artifactPreviewImage.removeAttribute("src");
    artifactPreviewTrigger?.focus();
    artifactPreviewTrigger = null;
  });
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
    state.lastCampaignStudyGuide = null;
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
    state.lastCampaignStudyGuide = null;
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
    state.lastCampaignStudyGuide = null;
    renderCampaignStudyTemplates();
  });
  els.saveCampaignStudyTemplateButton.addEventListener("click", handleSaveCampaignStudyTemplate);
  els.loadCampaignStudyTemplateButton.addEventListener("click", handleLoadCampaignStudyTemplate);
  els.runCampaignStudyTemplateButton.addEventListener("click", handleRunCampaignStudyTemplate);
  els.importCampaignStudyTemplateInput.addEventListener("change", handleImportCampaignStudyTemplate);
  els.composeResearchObjectButton.addEventListener("click", handleComposeResearchObject);
  els.exportWorkspaceButton.addEventListener("click", handleExportWorkspace);
  els.workspaceImportInput.addEventListener("change", handleImportWorkspace);
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
      renderConfigContext(selected);
      updateSweepContract();
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
      renderConfigContext(selected);
      setRunLaunchStatus("idle");
      updateSweepContract();
    }
  });

  els.sweepParameter.addEventListener("change", () => {
    const parameter = sweepParameterByPath(els.sweepParameter.value);
    els.sweepValues.value = sweepDefaultValues[parameter?.path] || "";
    updateSweepContract();
  });
  els.sweepValues.addEventListener("input", () => updateSweepContract());
  els.launchForm.addEventListener("input", () => updateSweepContract());

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
  els.quantumAttributionPrimarySelect.addEventListener("change", (event) => {
    setQuantumAttributionSelection("primary", event.target.value);
  });
  els.quantumAttributionCompareSelect.addEventListener("change", (event) => {
    setQuantumAttributionSelection("compare", event.target.value);
  });
  els.quantumAttributionRosterBody.addEventListener("click", (event) => {
    const button = event.target.closest("[data-attribution-slot][data-attribution-key]");
    if (!button) return;
    setQuantumAttributionSelection(button.dataset.attributionSlot, button.dataset.attributionKey);
  });
  els.quantumHarnessForm.addEventListener("submit", handleQuantumValidationRun);
  els.launchForm.addEventListener("submit", handleLaunch);
  els.sweepForm.addEventListener("submit", handleLaunchSweep);
  els.verifyButton.addEventListener("click", handleVerify);
  els.replayButton.addEventListener("click", handleReplay);
  els.openReportButton.addEventListener("click", openRunReport);
  els.openExperimentReportButton.addEventListener("click", openExperimentReport);
}

setupNavigation();
bindEvents();

hydrate().catch((error) => {
  toast("Cockpit failed to load", error.message, "danger");
});
