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

    navigation_labels = [
        "Lab Mode",
        "Quantum Validation",
        "Run Setup",
        "Configuration",
        "Run Detail",
        "Run Ledger",
        "Experiments",
        "Evidence",
    ]
    positions = [html.index(f"<span>{label}</span>") for label in navigation_labels]
    assert positions == sorted(positions)
    assert 'href="#lab-mode" aria-current="location"' in html
    assert 'id="demoPathTitle"' in html
    assert 'id="demoRunButton"' in html
    assert 'id="demoCompareButton"' in html
    assert 'id="demoExportButton"' in html
    assert '<table aria-label="Guided comparison variant evidence">' in html
    assert '<table aria-label="Quantum compilation validation matrix">' in html
    assert 'aria-labelledby="quantumValidationTitle"' in html
    assert 'aria-label="Quantum validation gate summary"' in html
    assert re.search(
        r'class="table-wrap quantum-table-wrap"\s+'
        r'role="region"\s+'
        r'aria-labelledby="quantumMatrixTitle"\s+'
        r'tabindex="0"',
        html,
    )
    assert 'role="img"' in _element_tag(html, "quantumAttributionChart")
    assert ">Open Polished Report</a>" in html


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

    assert "--rail-width: 220px" in css
    assert ".skip-link:focus" in css
    assert 'input[type="checkbox"]:not(.visually-hidden-input)' in css
    assert "min-width: 24px" in css
    assert "@media (forced-colors: active)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "scroll-margin-top: 78px" in css
    assert "scroll-margin-top: 96px" in css
    assert ".demo-path-steps" in css
    assert ".comparison-results" in css
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
    assert "function renderScientificTrace(" in script
    assert "function openArtifactPreview(" in script
    assert "const svgPreviewCache = new Map()" in script
    assert "async function fetchSvgPreviewText(" in script
    assert 'data-artifact-source-url="${escapeHtml(item.url)}"' in script
    assert "data:image/svg+xml;charset=utf-8" in script
    assert "artifact-expand-label" not in script
    assert "state.selectedExperiment.urls.workbook" in script
    assert "Research Workbook - ${state.selectedExperiment.summary.experiment_id}" in script
    assert "function renderQuantumValidation(" in script
    assert "function renderQuantumTopologyCharts(" in script
    assert "function renderQuantumAttribution(" in script
    assert 'fetchJson("/api/quantum-validation")' in script
    assert 'aria-label="Select run ${escapeHtml(run.run_id)} for comparison"' in script
    assert "setupNavigation();" in script
    assert "restoreInitialHashPosition();" in script
