from __future__ import annotations

import html
from pathlib import Path
from typing import Any


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _scientific(value: object) -> str:
    try:
        return f"{float(value):.3e}"
    except (TypeError, ValueError):
        return "-"


def _resource_chart(
    items: list[tuple[str, int, int]],
    *,
    title: str,
    description: str,
) -> str:
    chart_id = "-".join(
        part for part in "".join(
            character.lower() if character.isalnum() else " " for character in title
        ).split()
    )
    maximum = max((max(depth, cx_count) for _, depth, cx_count in items), default=1)
    width = 940
    label_width = 285
    plot_width = 520
    row_height = 76
    height = 78 + row_height * len(items)
    rows: list[str] = []
    for index, (label, depth, cx_count) in enumerate(items):
        top = 58 + index * row_height
        depth_width = max(2.0, plot_width * depth / maximum)
        cx_width = max(2.0, plot_width * cx_count / maximum)
        rows.append(
            f"""
            <g>
              <text class="chart-label" x="12" y="{top + 17}">{_escape(label)}</text>
              <rect class="bar-track" x="{label_width}" y="{top}" width="{plot_width}" height="18" rx="9" />
              <rect class="bar-depth" x="{label_width}" y="{top}" width="{depth_width:.2f}" height="18" rx="9" />
              <text class="chart-value" x="{label_width + depth_width + 9:.2f}" y="{top + 14}">{depth} depth</text>
              <rect class="bar-track" x="{label_width}" y="{top + 30}" width="{plot_width}" height="12" rx="6" />
              <rect class="bar-cx" x="{label_width}" y="{top + 30}" width="{cx_width:.2f}" height="12" rx="6" />
              <text class="chart-value" x="{label_width + cx_width + 9:.2f}" y="{top + 40}">{cx_count} CX</text>
            </g>
            """
        )
    return f"""
      <svg class="resource-chart" viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title-{chart_id} chart-desc-{chart_id}">
        <title id="chart-title-{chart_id}">{_escape(title)}</title>
        <desc id="chart-desc-{chart_id}">{_escape(description)}</desc>
        <g class="chart-key" transform="translate(286 20)">
          <rect class="bar-depth" width="18" height="10" rx="5" /><text x="27" y="10">Circuit depth</text>
          <rect class="bar-cx" x="156" width="18" height="10" rx="5" /><text x="183" y="10">CX gates</text>
        </g>
        {''.join(rows)}
      </svg>
    """


def render_quantum_compilation_html(report: dict[str, Any]) -> str:
    matrix = list(report.get("matrix") or [])
    passing = [row for row in matrix if row.get("success")]
    exact = [
        row
        for row in matrix
        if row.get("semantics", {}).get("acceptance_class") == "reference_exact"
    ]
    approximate = [
        row
        for row in matrix
        if row.get("semantics", {}).get("acceptance_class")
        == "bounded_approximation"
    ]
    recommended = report.get("recommended_configuration") or {}
    recommended_key = (
        recommended.get("topology_id"),
        recommended.get("optimization_level"),
    )
    topology_labels = {
        row.get("topology_id"): row.get("topology_label") or row.get("topology_id")
        for row in matrix
    }

    topology_items: list[tuple[str, int, int]] = []
    for topology_id, label in topology_labels.items():
        candidates = [
            row
            for row in passing
            if row.get("topology_id") == topology_id
        ]
        if not candidates:
            continue
        selected = min(
            candidates,
            key=lambda row: (
                row.get("resources", {}).get("two_qubit_gates", 0),
                row.get("resources", {}).get("depth", 0),
            ),
        )
        resources = selected.get("resources", {})
        topology_items.append(
            (
                str(label),
                int(resources.get("depth", 0)),
                int(resources.get("two_qubit_gates", 0)),
            )
        )

    attribution_items = [
        (
            str(name).replace("_", " ").title(),
            int(resources.get("depth", 0)),
            int(resources.get("two_qubit_gates", 0)),
        )
        for name, resources in (recommended.get("attribution") or {}).items()
    ]

    matrix_rows: list[str] = []
    for row in matrix:
        semantics = row.get("semantics", {})
        resources = row.get("resources", {})
        is_recommended = (
            row.get("topology_id"),
            row.get("optimization_level"),
        ) == recommended_key
        classes = []
        if row.get("pareto_optimal"):
            classes.append("pareto-row")
        if is_recommended:
            classes.append("recommended-row")
        class_attribute = f' class="{" ".join(classes)}"' if classes else ""
        acceptance = str(semantics.get("acceptance_class") or "-").replace("_", " ")
        matrix_rows.append(
            f"""
            <tr{class_attribute}>
              <td><strong>{_escape(row.get('topology_label') or row.get('topology_id'))}</strong></td>
              <td>{_escape(row.get('optimization_level', '-'))}</td>
              <td><span class="class-chip">{_escape(acceptance)}</span></td>
              <td>{_escape(resources.get('depth', '-'))}</td>
              <td>{_escape(resources.get('two_qubit_gates', '-'))}</td>
              <td><code>{_scientific(semantics.get('state_l2_error'))}</code></td>
              <td><code>{float(semantics.get('state_fidelity', 0.0)):.9f}</code></td>
              <td>{'<span class="pareto-chip">Pareto</span>' if row.get('pareto_optimal') else '-'}</td>
              <td><span class="status-chip {'pass' if row.get('success') else 'review'}">{'PASS' if row.get('success') else 'REVIEW'}</span></td>
            </tr>
            """
        )

    acceptance = report.get("acceptance") or {}
    execution = report.get("execution_policy") or {}
    status = "PASS" if report.get("success") else "REVIEW"
    status_class = "pass" if report.get("success") else "review"
    recommendation_markup = (
        f"""
        <div class="recommendation-grid">
          <div><span>Generic target</span><strong>{_escape(topology_labels.get(recommended.get('topology_id'), recommended.get('topology_id', '-')))}</strong></div>
          <div><span>Optimization</span><strong>Level {_escape(recommended.get('optimization_level', '-'))}</strong></div>
          <div><span>Depth</span><strong>{_escape(recommended.get('depth', '-'))}</strong></div>
          <div><span>CX gates</span><strong>{_escape(recommended.get('two_qubit_gates', '-'))}</strong></div>
          <div><span>State L2 error</span><strong>{_scientific(recommended.get('state_l2_error'))}</strong></div>
          <div><span>Semantic class</span><strong>{_escape(str(recommended.get('acceptance_class', '-')).replace('_', ' '))}</strong></div>
        </div>
        <p class="selection-rule"><strong>Selection rule:</strong> {_escape(recommended.get('selection_rule', 'No passing recommendation was available.'))}</p>
        """
        if recommended
        else "<p>No matrix row passed the declared semantic acceptance gate.</p>"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="QS-DMSS simulator-only quantum compilation validation and resource attribution report.">
  <title>QS-DMSS Quantum Compilation Validation</title>
  <style>
    :root {{ --ink:#173335; --muted:#587071; --paper:#fbfaf5; --canvas:#e9e4d8; --line:#d7d2c4; --teal:#246f72; --teal-soft:#dceceb; --orange:#d76b2a; --orange-soft:#fae7d8; --green:#3f7141; --green-soft:#e4eee0; --gold:#b89035; }}
    * {{ box-sizing:border-box; }}
    html {{ max-width:100%; overflow-x:hidden; background:var(--canvas); color:var(--ink); font-family:Aptos, "Segoe UI", sans-serif; line-height:1.55; }}
    body {{ max-width:100%; margin:0; overflow-x:hidden; }}
    a {{ color:var(--teal); text-underline-offset:3px; }}
    :focus-visible {{ outline:3px solid var(--orange); outline-offset:3px; }}
    .page {{ width:min(1180px, calc(100% - 32px)); margin:32px auto; background:var(--paper); border:1px solid var(--line); border-radius:28px; box-shadow:0 24px 60px rgba(31,48,45,.13); overflow:hidden; }}
    .masthead {{ padding:42px 48px 38px; color:#f8f5e9; background:radial-gradient(circle at 88% 5%, rgba(216,154,62,.25), transparent 31%), linear-gradient(135deg,#113d40,#1d5554 62%,#143b3d); }}
    .eyebrow {{ margin:0 0 12px; color:#f1c56f; font-size:.78rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }}
    h1,h2,h3 {{ font-family:Georgia, "Times New Roman", serif; line-height:1.12; }}
    h1 {{ max-width:820px; margin:0; overflow-wrap:anywhere; font-size:clamp(2.35rem,5vw,4.7rem); letter-spacing:-.045em; }}
    .lede {{ max-width:770px; margin:20px 0 0; color:#dce9e5; font-size:1.08rem; }}
    .mast-meta {{ display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-top:28px; }}
    .status-chip,.pareto-chip,.class-chip {{ display:inline-flex; align-items:center; border-radius:999px; font-weight:800; white-space:nowrap; }}
    .status-chip {{ padding:5px 10px; font-size:.73rem; letter-spacing:.06em; }}
    .status-chip.pass {{ color:#315d34; background:var(--green-soft); }}
    .status-chip.review {{ color:#88441d; background:var(--orange-soft); }}
    .masthead .status-chip {{ padding:8px 14px; color:#153d32; background:#d9eccf; }}
    .meta-item {{ min-width:0; overflow-wrap:anywhere; color:#d7e4e1; font-size:.9rem; }}
    .content {{ padding:42px 48px 56px; }}
    .content .eyebrow {{ color:var(--teal); }}
    .metric-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-bottom:42px; }}
    .metric {{ min-height:126px; padding:20px; background:#f1f0e9; border:1px solid #dedbd0; border-radius:18px; }}
    .metric span {{ display:block; color:var(--muted); font-size:.75rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; }}
    .metric strong {{ display:block; margin-top:10px; font-family:Georgia,serif; font-size:2rem; }}
    .metric small {{ color:var(--muted); }}
    section {{ margin-top:48px; }}
    .section-head {{ display:flex; justify-content:space-between; gap:24px; align-items:end; margin-bottom:18px; }}
    .section-head h2 {{ margin:0; font-size:2rem; }}
    .section-head p {{ max-width:560px; margin:0; color:var(--muted); }}
    .recommendation {{ padding:26px; border:1px solid #cfcbc0; border-left:6px solid var(--orange); border-radius:18px; background:linear-gradient(135deg,#fffdf7,#f5efe3); }}
    .recommendation-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    .recommendation-grid div {{ padding:14px 16px; background:rgba(255,255,255,.66); border:1px solid #e1dccf; border-radius:13px; }}
    .recommendation-grid span {{ display:block; color:var(--muted); font-size:.72rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }}
    .recommendation-grid strong {{ display:block; margin-top:5px; }}
    .selection-rule {{ margin:18px 2px 0; color:var(--muted); }}
    .chart-card {{ min-width:0; max-width:100%; padding:20px; overflow:hidden; border:1px solid var(--line); border-radius:18px; background:#fffefa; }}
    .resource-chart {{ display:block; width:100%; min-width:680px; height:auto; }}
    .bar-track {{ fill:#e7e7df; }} .bar-depth {{ fill:var(--teal); }} .bar-cx {{ fill:var(--orange); }}
    .chart-label {{ fill:var(--ink); font-size:15px; font-weight:700; }} .chart-value {{ fill:var(--muted); font-size:12px; font-weight:700; }}
    .chart-key text {{ fill:var(--muted); font-size:12px; font-weight:700; }}
    .table-scroll {{ min-width:0; max-width:100%; overflow:auto; border:1px solid var(--line); border-radius:18px; background:white; }}
    table {{ width:100%; min-width:980px; border-collapse:collapse; font-size:.9rem; }}
    th,td {{ padding:13px 14px; border-bottom:1px solid #e5e2d9; text-align:left; vertical-align:middle; }}
    th {{ position:sticky; top:0; z-index:1; color:#395254; background:#eeeee7; font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; }}
    tr:last-child td {{ border-bottom:0; }} tr.recommended-row {{ background:#fff3e8; }} tr.pareto-row td:first-child {{ box-shadow:inset 4px 0 0 var(--gold); }}
    code {{ font-family:"Cascadia Mono",Consolas,monospace; font-size:.86em; }}
    .class-chip {{ padding:4px 9px; color:#3c595a; background:#e7efed; font-size:.72rem; font-weight:700; }}
    .pareto-chip {{ padding:4px 9px; color:#755a17; background:#f3e8c5; font-size:.72rem; }}
    .two-column {{ display:grid; grid-template-columns:1.12fr .88fr; gap:18px; }}
    .note {{ padding:24px; border-radius:18px; background:#f1f0e9; border:1px solid #dedbd0; }}
    .note h3 {{ margin:0 0 12px; font-size:1.35rem; }} .note p,.note li {{ color:var(--muted); }} .note ul {{ margin:10px 0 0; padding-left:20px; }}
    .boundary {{ background:#193f42; color:#f8f5e9; border-color:#193f42; }} .boundary p {{ color:#d7e5e1; }}
    .artifact-links {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; }}
    .artifact-links a {{ display:block; padding:14px; border:1px solid var(--line); border-radius:13px; background:white; font-weight:750; text-decoration:none; }}
    footer {{ margin-top:46px; padding-top:20px; border-top:1px solid var(--line); color:var(--muted); font-size:.84rem; }}
    @media (max-width:850px) {{ .page {{ width:100%; max-width:100%; margin:0; border:0; border-radius:0; }} .masthead,.content,section {{ min-width:0; max-width:100%; }} .masthead,.content {{ padding:32px 22px; }} .metric-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .recommendation-grid,.two-column,.artifact-links {{ grid-template-columns:1fr; }} .section-head {{ display:block; }} .section-head p {{ margin-top:8px; }} .chart-card {{ overflow:auto; }} }}
    @media (max-width:560px) {{ .metric-grid {{ grid-template-columns:1fr; }} .mast-meta {{ align-items:flex-start; flex-direction:column; }} .recommendation {{ padding:20px 14px; }} h1 {{ font-size:2.35rem; }} }}
    @media print {{ html {{ background:white; }} .page {{ width:100%; margin:0; border:0; box-shadow:none; }} .masthead {{ background:#173f42 !important; print-color-adjust:exact; }} .content {{ padding:28px 0; }} .table-scroll,.chart-card {{ overflow:visible; }} table {{ min-width:0; font-size:8pt; }} th,td {{ padding:6px; }} .artifact-links {{ display:none; }} section {{ break-inside:avoid; }} }}
  </style>
</head>
<body>
  <main class="page">
    <header class="masthead">
      <p class="eyebrow">QS-DMSS / Evidence-first quantum readiness</p>
      <h1>Quantum Compilation Validation</h1>
      <p class="lede">A deterministic, simulator-only view of semantic preservation and circuit resource growth across fixed generic five-qubit topologies.</p>
      <div class="mast-meta"><span class="status-chip {status_class}">{status}</span><span class="meta-item">Generated {_escape(report.get('generated_at','-'))}</span><span class="meta-item">No provider submission or authorized spend</span></div>
    </header>
    <div class="content">
      <div class="metric-grid" aria-label="Validation summary">
        <article class="metric"><span>Passing rows</span><strong>{len(passing)} / {len(matrix)}</strong><small>Declared tolerance gate</small></article>
        <article class="metric"><span>Reference exact</span><strong>{len(exact)}</strong><small>Strict source tolerance</small></article>
        <article class="metric"><span>Bounded approximation</span><strong>{len(approximate)}</strong><small>Compilation tolerance</small></article>
        <article class="metric"><span>Authorized cost</span><strong>${float(execution.get('max_authorized_cost_usd',0)):.2f}</strong><small>Local ideal simulators only</small></article>
      </div>

      <section aria-labelledby="recommendation-heading">
        <div class="section-head"><div><p class="eyebrow">Resource frontier</p><h2 id="recommendation-heading">Recommended generic configuration</h2></div><p>This is a software-target recommendation under the declared rule, not a hardware or provider recommendation.</p></div>
        <div class="recommendation">{recommendation_markup}</div>
      </section>

      <section aria-labelledby="topology-heading">
        <div class="section-head"><div><p class="eyebrow">Topology sensitivity</p><h2 id="topology-heading">Minimum-cost passing rows</h2></div><p>Depth and CX counts reveal how connectivity changes routing cost for the same logical experiment.</p></div>
        <div class="chart-card">{_resource_chart(topology_items, title='Minimum-cost passing resource counts by generic topology', description='Horizontal bars compare circuit depth and CX gate count for the lowest-CX passing row in each topology.')}</div>
      </section>

      <section aria-labelledby="attribution-heading">
        <div class="section-head"><div><p class="eyebrow">Cost attribution</p><h2 id="attribution-heading">Where the recommended circuit grows</h2></div><p>Direct component counts distinguish state preparation, SSFM evolution, measurement, and the complete experiment.</p></div>
        <div class="chart-card">{_resource_chart(attribution_items, title='Recommended configuration resource attribution', description='Horizontal bars compare circuit depth and CX gates by experiment component.')}</div>
      </section>

      <section aria-labelledby="matrix-heading">
        <div class="section-head"><div><p class="eyebrow">Validation matrix</p><h2 id="matrix-heading">All compilation results</h2></div><p>Gold edge marks Pareto rows; the warm row is the resource-minimizing recommendation.</p></div>
        <div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable quantum compilation validation matrix">
          <table><thead><tr><th>Topology</th><th>Opt</th><th>Class</th><th>Depth</th><th>CX</th><th>State L2</th><th>Fidelity</th><th>Frontier</th><th>Gate</th></tr></thead><tbody>{''.join(matrix_rows)}</tbody></table>
        </div>
      </section>

      <section class="two-column" aria-label="Method and scientific boundary">
        <article class="note"><p class="eyebrow">Acceptance contract</p><h3>What PASS means</h3><ul><li>Reference tolerance: <code>{_scientific(acceptance.get('reference_tolerance'))}</code></li><li>Compilation tolerance: <code>{_scientific(acceptance.get('compilation_tolerance'))}</code></li><li>Checks: state L2 error, state fidelity, density total-variation distance, and unused-qubit leakage.</li><li>Global phase is aligned before logical-state comparison.</li></ul></article>
        <article class="note boundary"><p class="eyebrow">Scientific boundary</p><h3>What this does not claim</h3><p>{_escape(report.get('claim_boundary','No claim boundary was recorded.'))}</p><p>No provider, credential, remote API, QPU, or authorized spend was used.</p></article>
      </section>

      <section aria-labelledby="artifacts-heading">
        <div class="section-head"><div><p class="eyebrow">Research object</p><h2 id="artifacts-heading">Evidence companions</h2></div><p>The HTML is the human-facing surface; machine-readable and integrity artifacts remain authoritative companions.</p></div>
        <nav class="artifact-links" aria-label="Validation evidence files"><a href="quantum-compilation-validation.json" download>JSON report</a><a href="quantum-compilation-matrix.csv" download>Matrix CSV</a><a href="manifest.sha256.json" download>SHA-256 manifest</a><a href="quantum-compilation-evidence.zip" download>Evidence ZIP</a></nav>
      </section>
      <footer>QS-DMSS compilation snapshot. Simulator-first quantum readiness; no QPU execution, provider authorization, quantum-advantage claim, or peer-reviewed scientific validation.</footer>
    </div>
  </main>
</body>
</html>
"""


def write_quantum_compilation_html_report(
    path: Path,
    report: dict[str, Any],
) -> None:
    rendered = render_quantum_compilation_html(report)
    normalized = "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"
    path.write_text(normalized, encoding="utf-8")
