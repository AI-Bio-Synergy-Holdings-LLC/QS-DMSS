from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "src" / "qs_dmss" / "cockpit" / "static"


def _element_tag(source: str, element_id: str) -> str:
    match = re.search(
        rf"<[^>]+\bid=[\"']{re.escape(element_id)}[\"'][^>]*>",
        source,
        flags=re.IGNORECASE,
    )
    assert match is not None, f"Missing element #{element_id}"
    return match.group(0)


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_cockpit_shell_has_accessible_navigation_and_landmarks() -> None:
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")

    assert '<a class="skip-link" href="#main-content">Skip to main content</a>' in html
    assert '<aside class="rail" aria-label="Application navigation">' in html
    assert '<nav class="rail-nav" aria-labelledby="primaryNavigationLabel">' in html
    assert '<main class="workspace" id="main-content" tabindex="-1">' in html
    assert '<meta name="application-version" content="0.12.0" />' in html
    assert '<meta name="citation_doi" content="10.5281/zenodo.21329711" />' in html
    assert '<link rel="cite-as" href="https://doi.org/10.5281/zenodo.21329711" />' in html
    assert 'id="releaseVersion"' in html
    assert 'id="releaseDoi"' in html
    assert 'id="projectDoi"' in html
    assert "Release DOI 10.5281/zenodo.21329711" in html
    assert "Project DOI 10.5281/zenodo.20074924" in html

    navigation_labels = [
        "Overview",
        "Run Lab",
        "Quantum Validation",
        "Run Setup",
        "Run Ledger",
        "Studies",
        "Evidence",
    ]
    positions = [html.index(f"<span>{label}</span>") for label in navigation_labels]
    assert positions == sorted(positions)
    assert 'href="#overview" aria-current="location"' in html
    assert 'aria-labelledby="overviewTitle"' in html
    assert 'aria-label="Research posture summary"' in html
    assert 'id="demoPathTitle"' in html
    assert 'id="demoRunButton"' in html
    assert 'id="demoCompareButton"' in html
    assert 'id="demoExportButton"' in html
    assert '<table aria-label="Guided comparison variant evidence">' in html
    assert '<table aria-label="Quantum compilation validation matrix">' in html
    assert '<table aria-label="Recommended quantum compilation configuration">' in html
    assert '<table aria-label="Planned parameter sweep runs">' in html
    assert 'id="quantumHarnessForm"' in html
    assert 'id="runQuantumValidationButton"' in html
    assert 'id="quantumVisualProvenance"' in html
    assert 'id="quantumTopologySource"' in html
    assert 'id="quantumAttributionSource"' in html
    assert 'id="quantumVisualDataDigest"' in html
    assert 'id="quantumFigureScopeNote"' in html
    assert 'id="quantumAttributionDelta"' in html
    assert 'id="quantumAttributionPrimarySelect"' in html
    assert 'id="quantumAttributionCompareSelect"' in html
    assert 'id="quantumAttributionCompareChart"' in html
    assert 'id="quantumAttributionRosterBody"' in html
    assert '<table aria-label="Quantum attribution configuration comparison">' in html
    assert "Recommendation is a highlighted result, not a selection constraint" in html
    assert "Shots and tolerances change validation evidence and acceptance gates" in html
    assert 'id="runSetupTitle"' in html
    assert 'id="configContext"' in html
    assert 'id="runLaunchStatus"' in html
    assert 'id="reviewBundleLink"' in html
    assert 'id="stateBundleLink"' in html
    assert 'aria-labelledby="quantumValidationTitle"' in html
    assert 'aria-label="Quantum validation gate summary"' in html
    assert html.count('class="rail-icon') == 7
    assert html.count('class="signal-icon"') == 3
    assert html.count('class="method-icon"') == 3
    for semantic_icon in (
        "claim-boundary",
        "reproduced-traces",
        "validated-quantum-circuit",
        "interactive-controls",
        "precomputed-result",
        "local-locked-workstation",
    ):
        assert f'data-icon="{semantic_icon}"' in html
    assert re.search(
        r'class="table-wrap quantum-table-wrap"\s+'
        r'role="region"\s+'
        r'aria-labelledby="quantumMatrixTitle"\s+'
        r'tabindex="0"',
        html,
    )
    assert 'role="img"' in _element_tag(html, "quantumAttributionChart")
    assert 'role="img"' in _element_tag(html, "quantumAttributionCompareChart")
    assert ">Open polished report</a>" in html


def test_cockpit_static_research_surfaces_are_named() -> None:
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")

    for label in (
        "Recent simulation runs",
        "Run comparison metrics",
        "Saved experiment registry",
    ):
        assert f'<table aria-label="{label}">' in html

    assert '<dialog class="report-modal" id="reportDialog" aria-labelledby="reportHeading">' in html
    assert 'class="panel detail-panel run-overview-panel reveal"' in html
    assert 'aria-label="Relative energy change over simulation steps"' in html
    assert 'aria-label="Relative norm change over simulation steps"' in html
    assert 'id="artifactPreviewDialog"' in html
    assert 'id="artifactPreviewImage"' in html
    assert 'id="labComparisonWorkbookLink"' in html
    assert 'id="labComparisonWorkbookDownloadLink"' in html
    assert "Open Research Workbook" in html


def test_unavailable_actions_are_not_keyboard_traps() -> None:
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")

    for button_id in (
        "verifyButton",
        "replayButton",
        "saveExperimentButton",
        "openExperimentReportButton",
        "openReportButton",
    ):
        assert "disabled" in _element_tag(html, button_id)

    for link_id in ("bundleLink", "experimentBundleLink"):
        tag = _element_tag(html, link_id)
        assert "href=" not in tag
        assert 'aria-disabled="true"' in tag
        assert 'tabindex="-1"' in tag

    workspace_import = _element_tag(html, "workspaceImportInput")
    assert 'class="visually-hidden-input"' in workspace_import
    assert " hidden" not in workspace_import


def test_cockpit_styles_encode_wcag_interaction_baseline() -> None:
    css = (STATIC_ROOT / "styles.css").read_text(encoding="utf-8")

    assert "--rail-width: 120px" in css
    assert ".skip-link:focus" in css
    assert ".visually-hidden {" in css
    assert 'input[type="checkbox"]:not(.visually-hidden-input)' in css
    assert "min-width: 24px" in css
    assert "@media (forced-colors: active)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "scroll-margin-top: 78px" in css
    assert "scroll-margin-top: 96px" in css
    assert ".demo-path-steps" in css
    assert ".comparison-results" in css
    assert ".lab-flow-step.is-current" in css
    assert ".interactive-comparison-figure" in css
    assert ".comparison-chart-point:focus" in css
    assert ".trace-point:focus" in css
    assert ".lab-diagnostic-charts" in css
    assert ".lab-comparison-actions > :is(button, a, label)" in css
    assert ".run-overview-panel," in css
    assert ".scientific-chart-stack" in css
    assert ".artifact-expand-button" in css
    assert ".artifact-preview-modal-grid" in css
    assert "width: min(1480px, calc(100vw - 32px))" in css
    assert "grid-template-columns: repeat(12, minmax(0, 1fr))" in css
    assert ".lab-report-metrics dd" in css
    assert ".quantum-validation-panel" in css
    assert ".quantum-topology-charts" in css
    assert ".quantum-attribution-chart" in css
    assert ".quantum-table-wrap" in css
    assert ".research-runbook-grid" in css
    assert ".research-runbook-step.is-current" in css
    assert ".evidence-assistant-prompts" in css
    assert '.evidence-assistant-prompts button[aria-pressed="true"]' in css
    assert ".research-runbook-head .selection-chip" in css
    assert "@media (max-width: 1050px)" in css
    quantum_table_wrap = re.search(
        r"\.quantum-table-wrap\s*\{(?P<rules>.*?)\}",
        css,
        flags=re.DOTALL,
    )
    assert quantum_table_wrap is not None
    quantum_table_rules = quantum_table_wrap.group("rules")
    assert "overflow: auto" in quantum_table_rules
    assert "overscroll-behavior: contain" in quantum_table_rules
    assert "scrollbar-gutter: stable" in quantum_table_rules
    assert ".quantum-table-wrap:focus-visible" in css
    assert ".quantum-recommendation .table-wrap" in css
    assert "overflow-x: auto" in css

    foreground = "#fff8ef"
    action_colors = [
        re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{6}})", css).group(1)
        for name in ("copper-action", "copper-action-dark")
    ]
    assert all(_contrast_ratio(foreground, color) >= 4.5 for color in action_colors)


def test_cockpit_navigation_and_dynamic_controls_preserve_semantics() -> None:
    script = (STATIC_ROOT / "app.js").read_text(encoding="utf-8")

    assert "function setupNavigation()" in script
    assert "function restoreInitialHashPosition()" in script
    assert 'setAttribute("aria-current", "location")' in script
    assert "target.offsetTop" not in script
    assert "atPageEnd" in script
    assert "function setActionLinkEnabled(" in script
    assert "function renderLabComparisonResults(" in script
    assert "function comparisonExportPayload(" in script
    assert "function updateDemoPath()" in script
    assert "function updateLabWorkflow()" in script
    assert "function renderResearchRunbook(" in script
    assert "function renderEvidenceAssistant(" in script
    assert "function evidenceAssistantAnswer(" in script
    assert "function evidenceAssistantSources(" in script
    assert "data-evidence-assistant-intent" in script
    assert "function renderScientificTrace(" in script
    assert "function renderInteractiveComparisonChart(" in script
    assert 'data-comparison-metric="${key}"' in script
    assert 'point.addEventListener("focus", update)' in script
    assert "function openArtifactPreview(" in script
    assert "const svgPreviewCache = new Map()" in script
    assert "async function fetchSvgPreviewText(" in script
    assert 'data-artifact-source-url="${escapeHtml(item.url)}"' in script
    assert "data:image/svg+xml;charset=utf-8" in script
    assert "artifact-expand-label" not in script
    assert "state.selectedExperiment.urls.workbook" in script
    assert "Research Workbook - ${state.selectedExperiment.summary.experiment_id}" in script
    assert "function renderQuantumValidation(" in script
    assert "function renderReleaseIdentity(" in script
    assert "renderReleaseIdentity(healthPayload.release" in script
    assert "function renderQuantumTopologyCharts(" in script
    assert "function renderQuantumAttribution(" in script
    assert 'fetchJson("/api/quantum-validation")' in script
    assert 'fetchJson("/api/quantum-validation/runs/latest")' in script
    assert 'fetchJson("/api/quantum-validation/runs", {' in script
    assert "async function handleQuantumValidationRun(" in script
    assert "function validateSweepValues(" in script
    assert "function updateSweepContract(" in script
    assert 'setAttribute("aria-invalid"' in script
    assert "heading.textContent = String(title" in script
    assert "message.textContent = String(body" in script
    assert "node.innerHTML = `<strong>${title}" not in script
    assert 'aria-label="Select run ${escapeHtml(run.run_id)} for comparison"' in script
    assert "setupNavigation();" in script
    assert "restoreInitialHashPosition();" in script


def test_lab_workflow_and_live_chart_surfaces_are_semantic() -> None:
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")

    assert '<ol class="lab-flow" id="labWorkflow"' in html
    for step_id in (
        "labFlowChoose",
        "labFlowRun",
        "labFlowInspect",
        "labFlowVerify",
        "labFlowExport",
    ):
        assert f'id="{step_id}"' in html
    assert 'id="researchRunbook"' in html
    assert 'aria-labelledby="researchRunbookTitle"' in html
    assert 'id="evidenceAssistantTitle"' in html
    assert 'id="evidenceAssistantPromptGroup"' in html
    assert 'id="evidenceAssistantResponseTitle"' in html
    assert 'id="evidenceAssistantEvidenceList"' in html
    assert 'data-evidence-assistant-intent="summary"' in html
    assert 'data-evidence-assistant-intent="claim"' in html
    assert 'data-evidence-assistant-intent="review"' in html
    assert 'data-evidence-assistant-intent="next"' in html
    assert "It does not create evidence" in html
    assert 'id="labComparisonChart"' in html
    assert 'id="comparisonChart"' in html
    assert 'id="labEnergyChart"' in html
    assert 'id="labNormChart"' in html
    assert html.count("data-chart-readout") >= 4
