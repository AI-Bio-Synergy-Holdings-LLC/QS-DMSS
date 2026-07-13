from __future__ import annotations

import hashlib
import html
import json
import platform
import zipfile
from collections.abc import Iterable
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_entries(
    root_dir: Path,
    excluded_paths: Iterable[str],
) -> list[dict]:
    excluded = set(excluded_paths)
    entries = []
    for file_path in sorted(path for path in root_dir.rglob("*") if path.is_file()):
        relative_path = file_path.relative_to(root_dir).as_posix()
        if relative_path in excluded:
            continue
        entries.append(
            {
                "path": relative_path,
                "sha256": _file_sha256(file_path),
                "size_bytes": file_path.stat().st_size,
            }
        )
    return entries


def build_environment_lock() -> dict:
    packages: dict[str, str] = {}
    for package_name in ("numpy", "PyYAML", "qs-dmss"):
        try:
            packages[package_name] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            continue

    return {
        "schema_version": 1,
        "captured_at": _utc_now(),
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "packages": packages,
    }


def _run_trace_series(metrics: dict, key: str) -> list[dict]:
    samples = [
        {
            "step": float(item.get("step", index)),
            "value": float(item[key]),
        }
        for index, item in enumerate(metrics.get("history") or [])
        if item.get(key) is not None
    ]
    if not samples:
        return []
    initial = samples[0]["value"]
    denominator = abs(initial) or 1.0
    return [
        {
            **sample,
            "relative": (sample["value"] - initial) / denominator,
        }
        for sample in samples
    ]


def _run_diagnostic_svg(metrics: dict) -> str:
    width = 920
    height = 570
    plot_left = 104
    plot_right = 868
    plot_width = plot_right - plot_left
    panels = (
        ("energy", "Relative energy change", "#c45f28", 104),
        ("norm", "Relative norm change", "#237777", 344),
    )
    panel_markup: list[str] = []
    descriptions: list[str] = []

    for key, label, color, top in panels:
        series = _run_trace_series(metrics, key)
        if not series:
            continue
        panel_height = 154
        steps = [item["step"] for item in series]
        values = [item["relative"] for item in series]
        x_min = min(steps)
        x_max = max(steps)
        y_min = min(0.0, min(values))
        y_max = max(0.0, max(values))
        y_span = y_max - y_min
        padding = y_span * 0.14 if y_span else max(abs(y_max) * 0.2, 1e-12)
        y_min -= padding
        y_max += padding

        def x_scale(value: float) -> float:
            return plot_left + ((value - x_min) / max(x_max - x_min, 1.0)) * plot_width

        def y_scale(value: float) -> float:
            return top + ((y_max - value) / max(y_max - y_min, 1e-18)) * panel_height

        points = " ".join(
            f'{x_scale(item["step"]):.2f},{y_scale(item["relative"]):.2f}'
            for item in series
        )
        zero_y = y_scale(0.0)
        peak = max(series, key=lambda item: abs(item["relative"]))
        final = series[-1]
        peak_x = x_scale(peak["step"])
        peak_y = y_scale(peak["relative"])
        final_x = x_scale(final["step"])
        final_y = y_scale(final["relative"])
        grid = "".join(
            f'<line x1="{plot_left}" y1="{top + panel_height * fraction:.2f}" '
            f'x2="{plot_right}" y2="{top + panel_height * fraction:.2f}" stroke="#e3e9e7" />'
            for fraction in (0, 0.5, 1)
        )
        x_ticks = "".join(
            f'<text x="{plot_left + plot_width * fraction:.2f}" y="{top + panel_height + 26}" '
            f'text-anchor="middle" font-size="10" fill="#627176">'
            f'{_format_scientific(x_min + (x_max - x_min) * fraction)}</text>'
            for fraction in (0, 0.25, 0.5, 0.75, 1)
        )
        y_labels = "".join(
            f'<text x="{plot_left - 12}" y="{y_scale(value) + 4:.2f}" text-anchor="end" '
            f'font-size="10" fill="#627176">{_format_scientific(value)}</text>'
            for value in (y_max, 0.0, y_min)
        )
        descriptions.append(
            f"{label} ends at {_format_scientific(final['relative'])}; "
            f"peak absolute change {_format_scientific(abs(peak['relative']))}."
        )
        panel_markup.append(
            f"""
    <g>
      <text x="34" y="{top - 32}" font-size="16" font-weight="700" fill="#17383c">{html.escape(label)}</text>
      <text x="{plot_right}" y="{top - 32}" text-anchor="end" font-size="10" fill="#627176">{len(series)} recorded samples</text>
      {grid}
      <line x1="{plot_left}" y1="{zero_y:.2f}" x2="{plot_right}" y2="{zero_y:.2f}" stroke="#40575c" stroke-dasharray="5 5" />
      <polyline points="{points}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="{peak_x:.2f}" cy="{peak_y:.2f}" r="6" fill="#fffdf8" stroke="{color}" stroke-width="3" />
      <circle cx="{final_x:.2f}" cy="{final_y:.2f}" r="5" fill="{color}" />
      <text x="{min(peak_x + 10, plot_right - 164):.2f}" y="{max(peak_y - 10, top + 14):.2f}" font-size="10" font-weight="700" fill="#40575c">peak |change| {_format_scientific(abs(peak['relative']))}</text>
      {x_ticks}
      {y_labels}
    </g>"""
        )

    metadata = html.escape(
        json.dumps(
            {
                "figure_type": "run_conservation_diagnostics",
                "reference": "first recorded sample",
                "sample_count": len(metrics.get("history") or []),
                "claim_boundary": "numerical conservation diagnostics; not physical validation",
            },
            sort_keys=True,
        )
    )
    description = " ".join(descriptions) or "No diagnostic history was recorded."
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="run-diagnostic-title run-diagnostic-desc">
  <title id="run-diagnostic-title">Run conservation diagnostics</title>
  <desc id="run-diagnostic-desc">{html.escape(description)} Relative values use the first recorded sample as reference.</desc>
  <metadata>{metadata}</metadata>
  <rect width="100%" height="100%" rx="22" fill="#fffdf8" />
  <text x="34" y="38" font-family="Georgia,serif" font-size="23" font-weight="700" fill="#17383c">Conservation evidence plate</text>
  <text x="34" y="62" font-size="11" fill="#627176">Recorded solver history · relative to initial value · diagnostic only</text>
  {''.join(panel_markup)}
  <text x="{width / 2:.0f}" y="556" text-anchor="middle" font-size="11" font-weight="700" fill="#40575c">Simulation step</text>
</svg>"""


def _run_interpretation_markup(metrics: dict) -> str:
    energy = _run_trace_series(metrics, "energy")
    norm = _run_trace_series(metrics, "norm")
    history = metrics.get("history") or []
    if not energy or not norm:
        return "<p>No step history was recorded, so conservation trajectories could not be interpreted.</p>"
    energy_peak = max(abs(item["relative"]) for item in energy)
    norm_peak = max(abs(item["relative"]) for item in norm)
    density_values = [float(item["max_density"]) for item in history if item.get("max_density") is not None]
    density_peak = max(density_values) if density_values else float(metrics.get("max_density", 0.0))
    return f"""
    <div class="insight-grid">
      <article><span>Trajectory coverage</span><strong>{len(history)} samples</strong><p>Recorded from step {_format_scientific(energy[0]['step'])} through {_format_scientific(energy[-1]['step'])}.</p></article>
      <article><span>Energy behavior</span><strong>{_format_scientific(energy[-1]['relative'])} final relative change</strong><p>Peak absolute relative change: {_format_scientific(energy_peak)}.</p></article>
      <article><span>Norm behavior</span><strong>{_format_scientific(norm[-1]['relative'])} final relative change</strong><p>Peak absolute relative change: {_format_scientific(norm_peak)}.</p></article>
      <article><span>Density envelope</span><strong>{_format_scientific(density_peak)} peak</strong><p>Largest sampled maximum-density value in the recorded history.</p></article>
    </div>
    <p class="interpretation-note"><strong>Interpretation:</strong> These traces document numerical conservation behavior for this configuration and execution. They support reproducibility review; they do not establish physical calibration, peer-reviewed validation, or quantum advantage.</p>
    """


def write_report(
    run_dir: Path,
    run_record: dict,
    metrics: dict,
    decision: dict | None = None,
) -> None:
    report_path = run_dir / "report.html"
    diagnostic_svg = _run_diagnostic_svg(metrics)
    interpretation_markup = _run_interpretation_markup(metrics)
    rows = "\n".join(
        "<tr>"
        f"<td>{snapshot['step']}</td>"
        f"<td>{snapshot['norm']}</td>"
        f"<td>{snapshot['energy']}</td>"
        f"<td>{snapshot['max_density']}</td>"
        "</tr>"
        for snapshot in metrics["history"]
    )
    experiment = run_record.get("experiment")
    experiment_markup = ""
    if experiment:
        kind = str(experiment.get("kind", "sweep"))
        dimensions = experiment.get("dimensions") or []
        variant = experiment.get("variant") or []
        dimension_rows = "".join(
            f"<li>{html.escape(str(item.get('label') or item.get('path')))} (<code>{html.escape(str(item.get('path')))}</code>)</li>"
            for item in dimensions
        )
        variant_rows = "".join(
            f"<li>{html.escape(str(item.get('label') or item.get('path')))}: <code>{html.escape(str(item.get('value_label', '-')))}</code></li>"
            for item in variant
        )
        context_rows = f"""
      <li>Experiment ID: <code>{html.escape(str(experiment['id']))}</code></li>
      <li>Label: {html.escape(str(experiment['label']))}</li>
      <li>Kind: {html.escape(kind)}</li>
      <li>Ordinal: {experiment['ordinal']} of {experiment['total_runs']}</li>
"""
        if experiment.get("strategy"):
            context_rows += (
                f"      <li>Strategy: {html.escape(str(experiment['strategy']))}</li>\n"
            )
        if experiment.get("variant_label"):
            context_rows += (
                f"      <li>Variant: {html.escape(str(experiment['variant_label']))}</li>\n"
            )
        experiment_markup = f"""
    <h2>Experiment Context</h2>
    <ul>
{context_rows}    </ul>
    <h3>Search Dimensions</h3>
    <ul>
      {dimension_rows}
    </ul>
    <h3>Variant Values</h3>
    <ul>
      {variant_rows}
    </ul>
"""

    decision_markup = ""
    decision_profile = run_record.get("decision_profile")
    if decision_profile:
        objective = decision_profile["objective"]
        constraints = decision_profile["constraints"]
        ranking = decision_profile["ranking"]
        constraint_rows = "".join(
            f"<li>{html.escape(str(label))}: <code>{html.escape(str(value))}</code></li>"
            for label, value in constraints.items()
        )
        ranking_rows = "".join(
            f"<li>{html.escape(str(metric))}: {weight}</li>"
            for metric, weight in ranking["weights"].items()
        )
        evaluation_markup = ""
        if decision:
            checks = "".join(
                f"<li>{'PASS' if check['passed'] else 'FAIL'} - {html.escape(check['label'])} ({html.escape(check['actual_display'])})</li>"
                for check in decision["constraints"]["checks"]
            )
            primary = decision["primary_objective"]
            evaluation_markup = f"""
    <h3>Assessment</h3>
    <ul>
      <li>Status: {html.escape(decision['status'])}</li>
      <li>Reason: {html.escape(decision['reason'])}</li>
      <li>Primary metric: {html.escape(primary['label'])} = <code>{html.escape(primary['actual_display'])}</code></li>
    </ul>
    <h3>Constraint Checks</h3>
    <ul>
      {checks}
    </ul>
"""

        decision_markup = f"""
    <h2>Decision Profile</h2>
    <ul>
      <li>Objective: {html.escape(str(objective['name']))}</li>
      <li>Summary: {html.escape(str(objective.get('summary', '')) or 'No summary provided.')}</li>
      <li>Primary metric: {html.escape(str(objective['primary_metric']))}</li>
      <li>Goal: {html.escape(str(objective['goal']))}</li>
      <li>Target value: <code>{html.escape(str(objective.get('target_value', '-')))}</code></li>
    </ul>
    <h3>Constraints</h3>
    <ul>
      {constraint_rows}
    </ul>
    <h3>Ranking Weights</h3>
    <ul>
      <li>Primary metric boost: {ranking['primary_metric_weight']}</li>
      {ranking_rows}
    </ul>
    {evaluation_markup}
"""

    html_body = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>QS-DMSS Evidence Report</title>
    <style>
      :root {{ --ink:#17383c; --muted:#627176; --line:#dce4e2; --paper:#fffdf8; --teal:#237777; --copper:#c45f28; }}
      * {{ box-sizing:border-box; }}
      body {{ margin:0; background:#edf0ea; color:var(--ink); font-family:Manrope,"Segoe UI",sans-serif; line-height:1.55; }}
      main {{ width:min(1180px,calc(100% - 32px)); margin:28px auto; padding:clamp(24px,4vw,52px); border:1px solid var(--line); border-radius:28px; background:var(--paper); box-shadow:0 28px 80px rgba(24,56,61,.12); }}
      h1,h2,h3 {{ font-family:Georgia,serif; line-height:1.14; }}
      h1 {{ max-width:18ch; margin:.2rem 0 .7rem; font-size:clamp(2.4rem,5vw,4.4rem); }}
      h2 {{ margin:2.2rem 0 .8rem; font-size:clamp(1.45rem,3vw,2.1rem); }}
      .eyebrow {{ margin:0; color:var(--copper); font-size:.76rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }}
      .lede {{ max-width:78ch; color:var(--muted); font-size:1.02rem; }}
      .run-meta,.metric-grid,.insight-grid {{ display:grid; gap:12px; }}
      .run-meta {{ grid-template-columns:repeat(2,minmax(0,1fr)); padding:18px; border:1px solid var(--line); border-radius:18px; background:#f8faf6; }}
      .run-meta p {{ margin:0; overflow-wrap:anywhere; }}
      .metric-grid,.insight-grid {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
      .metric,.insight-grid article {{ min-width:0; padding:16px; border:1px solid var(--line); border-radius:18px; background:#f8faf6; }}
      .metric span,.insight-grid span {{ color:var(--muted); font-size:.72rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }}
      .metric strong,.insight-grid strong {{ display:block; margin-top:7px; font-family:Georgia,serif; font-size:1.15rem; overflow-wrap:anywhere; }}
      .insight-grid p {{ margin:7px 0 0; color:var(--muted); font-size:.86rem; }}
      .interpretation-note,.boundary {{ padding:15px 17px; border-radius:13px; }}
      .interpretation-note {{ border-left:4px solid var(--teal); background:#eef6f3; }}
      .boundary {{ border-left:4px solid var(--copper); background:#fff4ea; font-weight:700; }}
      figure {{ margin:22px 0; padding:12px; overflow:auto; border:1px solid var(--line); border-radius:22px; background:white; }}
      figure svg {{ display:block; width:100%; min-width:760px; height:auto; }}
      figcaption {{ padding:10px 8px 2px; color:var(--muted); font-size:.86rem; }}
      .table-shell {{ overflow:auto; border:1px solid var(--line); border-radius:18px; }}
      table {{ border-collapse:collapse; width:100%; min-width:720px; }}
      th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:left; }}
      th {{ background:#edf5f2; color:#365257; font-size:.72rem; letter-spacing:.07em; text-transform:uppercase; }}
      code {{ padding:2px 5px; border-radius:6px; background:#edf1ef; overflow-wrap:anywhere; }}
      @media(max-width:760px) {{ main {{ width:calc(100% - 16px); margin:8px auto; padding:20px; border-radius:20px; }} .run-meta,.metric-grid,.insight-grid {{ grid-template-columns:1fr; }} }}
      @media print {{ body {{ background:white; }} main {{ width:100%; margin:0; padding:20px; border:0; box-shadow:none; }} figure {{ break-inside:avoid; }} }}
    </style>
  </head>
  <body><main>
    <p class="eyebrow">QS-DMSS · Inspectable research object</p>
    <h1>QS-DMSS Evidence Report</h1>
    <p class="lede">A deterministic run record with numerical diagnostics, configuration identity, experiment context, and complete step history.</p>
    <div class="run-meta">
      <p><strong>Run ID</strong><br><code>{html.escape(run_record['run_id'])}</code></p>
      <p><strong>Name</strong><br>{html.escape(run_record['name'])}</p>
      <p><strong>Backend</strong><br>{html.escape(run_record['backend'])}</p>
      <p><strong>Config digest</strong><br><code>{html.escape(run_record['config_digest'])}</code></p>
    </div>
    <p class="boundary">Numerical workflow evidence only. Interpret conservation trajectories inside the documented configuration and do not treat this report as physical calibration or peer-reviewed validation.</p>
    <h2>Executive diagnostic summary</h2>
    <div class="metric-grid">
      <article class="metric"><span>Norm drift</span><strong>{_format_scientific(metrics['norm_drift'])}</strong></article>
      <article class="metric"><span>Energy drift</span><strong>{_format_scientific(metrics['energy_drift'])}</strong></article>
      <article class="metric"><span>Maximum density</span><strong>{_format_scientific(metrics.get('max_density'))}</strong></article>
      <article class="metric"><span>Elapsed time</span><strong>{float(metrics['elapsed_seconds']):.3f} s</strong></article>
    </div>
    {interpretation_markup}
    <figure>{diagnostic_svg}<figcaption>Energy and norm use independent labeled scales and the first recorded sample as reference. Peak and final values are directly annotated; the table below remains the complete numerical record.</figcaption></figure>
    {experiment_markup}
    {decision_markup}
    <h2>Step History</h2>
    <div class="table-shell"><table>
      <thead>
        <tr>
          <th>Step</th>
          <th>Norm</th>
          <th>Energy</th>
          <th>Max Density</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table></div>
  </main></body>
</html>
"""
    report_path.write_text(html_body, encoding="utf-8")


_COMPARISON_MARKERS = (
    {"code": "A", "color": "#237777", "shape": "circle"},
    {"code": "B", "color": "#c45f28", "shape": "square"},
    {"code": "C", "color": "#78844c", "shape": "diamond"},
    {"code": "D", "color": "#3d5a80", "shape": "triangle"},
    {"code": "E", "color": "#9b5f78", "shape": "circle"},
)


def _comparison_variant_label(row: dict, index: int) -> str:
    return str(
        row.get("variant_label")
        or row.get("parameter_value_label")
        or ("Baseline" if index == 0 else row.get("config_name"))
        or f"Variant {index + 1}"
    )


def _format_scientific(value: object) -> str:
    try:
        return f"{float(value):.3e}"
    except (TypeError, ValueError):
        return "-"


def _marker_svg(marker: dict[str, str], x: float, y: float, size: float = 7) -> str:
    color = marker["color"]
    shape = marker["shape"]
    if shape == "square":
        return (
            f'<rect x="{x - size:.2f}" y="{y - size:.2f}" width="{size * 2:.2f}" '
            f'height="{size * 2:.2f}" rx="2" fill="{color}" />'
        )
    if shape == "diamond":
        return (
            f'<path d="M {x:.2f} {y - size:.2f} L {x + size:.2f} {y:.2f} '
            f'L {x:.2f} {y + size:.2f} L {x - size:.2f} {y:.2f} Z" fill="{color}" />'
        )
    if shape == "triangle":
        return (
            f'<path d="M {x:.2f} {y - size:.2f} L {x + size:.2f} {y + size:.2f} '
            f'L {x - size:.2f} {y + size:.2f} Z" fill="{color}" />'
        )
    return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{size:.2f}" fill="{color}" />'


def _comparison_visual_svg(comparison: dict) -> str:
    rows = comparison["rows"]
    width = 1240
    height = max(500, 260 + len(rows) * 58)
    left = 182
    top = 130
    panel_width = 220
    panel_gap = 42
    legend_x = left + 3 * (panel_width + panel_gap) + 10
    decision = comparison.get("decision") or {}
    recommended_run_id = decision.get("recommended_run_id")
    decision_available = bool(decision.get("available"))
    metric_specs = [
        ("energy_drift", "Energy drift", "Lower |value| preferred"),
        ("max_density", "Maximum density", "Response metric"),
    ]
    metric_specs.append(
        ("decision_score", "Decision score", "Higher weighted score")
        if decision_available
        else ("norm_drift", "Norm drift", "Evidence-only metric")
    )
    metric_markup: list[str] = []
    for metric_index, (key, label, subtitle) in enumerate(metric_specs):
        x_start = left + metric_index * (panel_width + panel_gap)
        values = [float(row.get(key) or 0.0) for row in rows]
        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum
        if span == 0:
            span = max(abs(maximum), 1.0)
            minimum -= span * 0.5
            maximum += span * 0.5
            span = maximum - minimum
        metric_markup.extend(
            [
                f'<text x="{x_start}" y="88" font-size="16" font-weight="700" fill="#18383d">{html.escape(label)}</text>',
                f'<text x="{x_start}" y="108" font-size="11" fill="#607176">{html.escape(subtitle)}</text>',
            ]
        )
        for tick_index in range(3):
            fraction = tick_index / 2
            tick_x = x_start + fraction * panel_width
            tick_value = minimum + fraction * span
            tick_anchor = (
                "start" if tick_index == 0 else "end" if tick_index == 2 else "middle"
            )
            tick_label_x = (
                tick_x + 4
                if tick_index == 0
                else tick_x - 4
                if tick_index == 2
                else tick_x
            )
            metric_markup.append(
                f'<line x1="{tick_x:.2f}" y1="{top - 15}" x2="{tick_x:.2f}" '
                f'y2="{top + len(rows) * 58 - 17}" stroke="#dce4e2" stroke-width="1" />'
            )
            metric_markup.append(
                f'<text x="{tick_label_x:.2f}" y="{top + len(rows) * 58 + 5}" '
                f'text-anchor="{tick_anchor}" font-size="10" fill="#607176">{_format_scientific(tick_value)}</text>'
            )
        for row_index, row in enumerate(rows):
            value = float(row.get(key) or 0.0)
            marker = _COMPARISON_MARKERS[row_index % len(_COMPARISON_MARKERS)]
            position = (value - minimum) / span
            x = x_start + position * panel_width
            y = top + row_index * 58
            if row.get("run_id") == recommended_run_id:
                metric_markup.append(
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="13" fill="none" '
                    'stroke="#d7a33d" stroke-width="2.5" />'
                )
            metric_markup.append(_marker_svg(marker, x, y))
            value_anchor = (
                "start"
                if position <= 0.12
                else "end"
                if position >= 0.88
                else "middle"
            )
            value_label_x = (
                x + 10
                if position <= 0.12
                else x - 10
                if position >= 0.88
                else x
            )
            metric_markup.append(
                f'<text x="{value_label_x:.2f}" y="{y - 14:.2f}" text-anchor="{value_anchor}" '
                f'font-size="10" font-weight="700" fill="#42575b">{_format_scientific(value)}</text>'
            )

    row_labels: list[str] = []
    legend_rows: list[str] = []
    for row_index, row in enumerate(rows):
        marker = _COMPARISON_MARKERS[row_index % len(_COMPARISON_MARKERS)]
        label = _comparison_variant_label(row, row_index)
        y = top + row_index * 58
        recommended = row.get("run_id") == recommended_run_id
        row_labels.append(
            f'<text x="{left - 18}" y="{y + 4:.2f}" text-anchor="end" font-size="12" '
            f'font-weight="700" fill="#2d474c">{marker["code"]} · {html.escape(label[:22])}</text>'
        )
        legend_y = 145 + row_index * 54
        legend_rows.append(_marker_svg(marker, legend_x + 10, legend_y, 7))
        legend_rows.append(
            f'<text x="{legend_x + 28}" y="{legend_y - 2}" font-size="12" font-weight="700" '
            f'fill="#2d474c">{marker["code"]} · {html.escape(label[:25])}</text>'
        )
        legend_rows.append(
            f'<text x="{legend_x + 28}" y="{legend_y + 15}" font-size="10" fill="#607176">'
            f'{"Recommended · " if recommended else ""}{html.escape(str(row.get("run_id", ""))[-8:])}</text>'
        )

    metadata = html.escape(
        json.dumps(
            {
                "figure_type": "comparison_small_multiples",
                "variant_count": len(rows),
                "metrics": [item[0] for item in metric_specs],
                "recommended_run_id": recommended_run_id,
                "claim_boundary": "diagnostic workflow comparison; not scientific validation",
            },
            sort_keys=True,
        )
    )
    visual_description = (
        "Small-multiple plots compare energy drift, maximum density, and decision score. "
        "A sidecar key identifies each shape and color. A gold halo marks the recommended run."
        if decision_available
        else "Small-multiple plots compare energy drift, maximum density, and norm drift. "
        "A sidecar key identifies each shape and color. No recommendation is shown because the selected runs do not share one scoring contract."
    )
    recommendation_key = (
        f'<circle cx="{legend_x + 10}" cy="{height - 52}" r="12" fill="none" '
        'stroke="#d7a33d" stroke-width="2.5" />'
        f'<text x="{legend_x + 30}" y="{height - 48}" font-size="11" fill="#607176">Recommended by active scoring contract</text>'
        if decision_available
        else f'<text x="{legend_x}" y="{height - 48}" font-size="11" fill="#607176">Evidence-only: no shared scoring contract</text>'
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="comparison-visual-title comparison-visual-desc">
  <title id="comparison-visual-title">Variant metric comparison</title>
  <desc id="comparison-visual-desc">{html.escape(visual_description)}</desc>
  <metadata>{metadata}</metadata>
  <rect width="100%" height="100%" rx="22" fill="#fffdf8" />
  <text x="34" y="35" font-family="Georgia, serif" font-size="22" font-weight="700" fill="#17383c">Variant evidence plate</text>
  <text x="34" y="61" font-size="12" fill="#607176">Direct values · independent metric scales · diagnostic workflow comparison</text>
  {''.join(metric_markup)}
  {''.join(row_labels)}
  <line x1="{legend_x - 18}" y1="38" x2="{legend_x - 18}" y2="{height - 36}" stroke="#dce4e2" />
  <text x="{legend_x}" y="88" font-size="13" font-weight="700" fill="#18383d">Marker key</text>
  <text x="{legend_x}" y="106" font-size="10" fill="#607176">Shape + color remain redundant</text>
  {''.join(legend_rows)}
  {recommendation_key}
</svg>"""


def _experiment_report_styles() -> str:
    return """
      :root { --ink:#18383d; --muted:#607176; --line:#d9e1df; --paper:#fffdf8; --teal:#237777; --copper:#c45f28; --gold:#d7a33d; }
      * { box-sizing: border-box; }
      body { margin:0; background:#edf0ea; color:var(--ink); font-family:Manrope,"Segoe UI",sans-serif; line-height:1.55; }
      main { width:min(1480px,calc(100% - 32px)); margin:28px auto; padding:clamp(24px,4vw,54px); border:1px solid var(--line); border-radius:28px; background:var(--paper); box-shadow:0 28px 80px rgba(24,56,61,.12); }
      h1,h2,h3 { font-family:Georgia,serif; line-height:1.12; }
      h1 { max-width:18ch; margin:.2rem 0 .75rem; font-size:clamp(2.2rem,5vw,4.7rem); }
      h2 { margin:2.2rem 0 .8rem; font-size:clamp(1.5rem,3vw,2.2rem); }
      p { max-width:78ch; }
      .eyebrow { margin:0; color:var(--copper); font-size:.76rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }
      .lede { color:var(--muted); font-size:1.05rem; }
      .actions { display:flex; flex-wrap:wrap; gap:10px; margin:22px 0; }
      .actions a,.actions button { display:inline-flex; min-height:44px; align-items:center; justify-content:center; padding:0 16px; border:1px solid var(--line); border-radius:14px; background:white; color:var(--teal); font:inherit; font-weight:800; text-decoration:none; cursor:pointer; }
      .actions .primary { border-color:var(--teal); background:var(--teal); color:white; }
      .metric-grid,.readiness-grid,.insight-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
      .metric,.readiness-card,.insight-card { min-width:0; padding:16px; border:1px solid var(--line); border-radius:18px; background:#f8faf6; }
      .metric span,.readiness-card span,.insight-card span { color:var(--muted); font-size:.74rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
      .metric strong { display:block; margin-top:7px; font-family:Georgia,serif; font-size:1.28rem; overflow-wrap:anywhere; }
      .readiness-card strong { display:block; margin:7px 0; }
      .insight-card strong { display:block; margin:7px 0; font-family:Georgia,serif; font-size:1.05rem; overflow-wrap:anywhere; }
      .readiness-card p,.insight-card p { margin:0; color:var(--muted); font-size:.9rem; }
      .recommendation { padding:22px; border:1px solid rgba(215,163,61,.45); border-radius:22px; background:linear-gradient(135deg,rgba(215,163,61,.13),rgba(35,119,119,.07)); }
      .recommendation h2 { margin:0 0 8px; }
      figure { margin:22px 0; padding:12px; border:1px solid var(--line); border-radius:22px; background:white; overflow:auto; }
      figure svg { display:block; width:100%; min-width:820px; height:auto; }
      figcaption { padding:10px 8px 2px; color:var(--muted); font-size:.86rem; }
      .table-shell { overflow:auto; border:1px solid var(--line); border-radius:18px; }
      table { width:100%; border-collapse:collapse; min-width:960px; }
      th,td { padding:12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
      th { background:#edf5f2; color:#365257; font-size:.72rem; letter-spacing:.07em; text-transform:uppercase; }
      code { padding:2px 5px; border-radius:6px; background:#edf1ef; overflow-wrap:anywhere; }
      .boundary { padding:14px 16px; border-left:4px solid var(--copper); border-radius:12px; background:#fff4ea; font-weight:700; }
      .tab-list { display:flex; flex-wrap:wrap; gap:8px; margin:18px 0; }
      [role=tab] { min-height:44px; padding:0 15px; border:1px solid var(--line); border-radius:999px; background:white; color:var(--ink); font:inherit; font-weight:800; cursor:pointer; }
      [role=tab][aria-selected=true] { border-color:var(--teal); background:var(--teal); color:white; }
      [role=tabpanel][hidden] { display:none; }
      pre { padding:16px; overflow:auto; border-radius:16px; background:#152e32; color:#eff8f6; font-size:.82rem; }
      @media(max-width:760px) { main { width:min(100% - 16px,1480px); margin:8px auto; padding:20px; border-radius:20px; } .metric-grid,.readiness-grid,.insight-grid { grid-template-columns:1fr; } figure svg { min-width:720px; } }
      @media print { body { background:white; } main { width:100%; margin:0; padding:20px; border:0; box-shadow:none; } .actions,.tab-list { display:none; } [role=tabpanel][hidden] { display:block; } figure { break-inside:avoid; } }
    """


def _comparison_rows_markup(comparison: dict) -> str:
    return "\n".join(
        "<tr>"
        f"<td><strong>{html.escape(_comparison_variant_label(row, index))}</strong><br><code>{html.escape(str(row['run_id']))}</code></td>"
        f"<td>{html.escape(str(row.get('decision_rank', '-')))}</td>"
        f"<td>{html.escape(str(row.get('decision_score', '-')))}</td>"
        f"<td>{'-' if row.get('decision_qualified') is None else 'yes' if row['decision_qualified'] else 'no'}</td>"
        f"<td>{_format_scientific(row['energy_drift'])}</td>"
        f"<td>{_format_scientific(row['norm_drift'])}</td>"
        f"<td>{_format_scientific(row['max_density'])}</td>"
        f"<td>{float(row['elapsed_seconds']):.3f}</td>"
        f"<td>{'verified' if row['verification_success'] else 'pending'}</td>"
        "</tr>"
        for index, row in enumerate(comparison["rows"])
    )


def _readiness_markup(comparison: dict) -> str:
    verified_count = sum(bool(row.get("verification_success")) for row in comparison["rows"])
    run_count = len(comparison["rows"])
    return f"""
    <div class="readiness-grid">
      <article class="readiness-card"><span>Evidence verification</span><strong>{verified_count}/{run_count} variants verified</strong><p>Manifest checks completed for the comparison inputs.</p></article>
      <article class="readiness-card"><span>Replay</span><strong>Scenario path available</strong><p>Use the packaged showcase replay path for deterministic reproduction checks.</p></article>
      <article class="readiness-card"><span>Validation spine</span><strong>Separate numerical gate</strong><p><code>qs-dmss validation fractal-ssfm</code> remains diagnostics-only and is not implied by this comparison.</p></article>
      <article class="readiness-card"><span>Dry-run Slurm</span><strong>Review-only handoff</strong><p><code>qs-dmss executors slurm-dry-run</code> generates scheduler artifacts and never submits a job.</p></article>
    </div>
    """


def _recommendation_markup(comparison: dict) -> str:
    decision = comparison.get("decision") or {}
    if not decision.get("available"):
        reason = html.escape(
            str(
                decision.get("reason")
                or "No ranked result is available under a shared scoring contract."
            )
        )
        return (
            '<section class="recommendation evidence-only">'
            '<p class="eyebrow">Evidence-only comparison</p>'
            '<h2>No cross-profile winner</h2>'
            f'<p>{reason}</p>'
            '<p><strong>Next step:</strong> select runs with one shared objective profile to enable ranking.</p>'
            '</section>'
        )
    recommended = next(
        (row for row in comparison["rows"] if row["run_id"] == decision["recommended_run_id"]),
        {},
    )
    label = _comparison_variant_label(recommended, 0) if recommended else "Recommended run"
    return f"""
    <section class="recommendation">
      <p class="eyebrow">Recommendation · Objective-driven ranking</p>
      <h2>{html.escape(label)}</h2>
      <p>{html.escape(str(decision.get('reason', 'Ranked by the active decision profile.')))}</p>
      <p><strong>Score:</strong> {_format_scientific(decision.get('recommended_score'))} · <strong>Status:</strong> {html.escape(str(decision.get('status', '-')))}</p>
    </section>
    """


def _comparison_metric_cards(experiment_record: dict, comparison: dict) -> str:
    cards = (
        ("Variants", str(experiment_record["run_count"])),
        ("Energy drift span", _format_scientific(comparison["ranges"]["energy_drift"]["span"])),
        ("Density span", _format_scientific(comparison["ranges"]["max_density"]["span"])),
        ("Fastest run", str(comparison["ranges"]["elapsed_seconds"]["min_run_id"])[-8:]),
    )
    return "".join(
        f'<article class="metric"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></article>'
        for label, value in cards
    )


def _comparison_insights_markup(comparison: dict) -> str:
    rows = comparison.get("rows") or []
    if not rows:
        return "<p>No comparison rows are available for interpretation.</p>"
    indexed_rows = list(enumerate(rows))
    energy_row = min(indexed_rows, key=lambda item: abs(float(item[1]["energy_drift"])))
    norm_row = min(indexed_rows, key=lambda item: abs(float(item[1]["norm_drift"])))
    density_row = max(indexed_rows, key=lambda item: float(item[1]["max_density"]))
    elapsed_row = min(indexed_rows, key=lambda item: float(item[1]["elapsed_seconds"]))

    def label(indexed_row: tuple[int, dict]) -> str:
        return _comparison_variant_label(indexed_row[1], indexed_row[0])

    decision = comparison.get("decision") or {}
    decision_note = (
        f"The active shared scoring contract recommends {html.escape(str(decision.get('recommended_run_id', ''))[-8:])}. "
        "That recommendation is contract-dependent and should be reviewed alongside the individual metric tradeoffs."
        if decision.get("available")
        else "No shared scoring contract is available, so the report presents evidence without naming a cross-profile winner."
    )
    return f"""
    <h2>Interpretive comparison summary</h2>
    <div class="insight-grid">
      <article class="insight-card"><span>Smallest |energy drift|</span><strong>{html.escape(label(energy_row))}</strong><p>{_format_scientific(energy_row[1]['energy_drift'])} recorded drift.</p></article>
      <article class="insight-card"><span>Smallest |norm drift|</span><strong>{html.escape(label(norm_row))}</strong><p>{_format_scientific(norm_row[1]['norm_drift'])} recorded drift.</p></article>
      <article class="insight-card"><span>Highest max density</span><strong>{html.escape(label(density_row))}</strong><p>{_format_scientific(density_row[1]['max_density'])} recorded maximum.</p></article>
      <article class="insight-card"><span>Fastest observed run</span><strong>{html.escape(label(elapsed_row))}</strong><p>{float(elapsed_row[1]['elapsed_seconds']):.3f} seconds in the captured environment.</p></article>
    </div>
    <p class="boundary"><strong>Decision context:</strong> {decision_note} Runtime is environment-sensitive, and all numerical metrics remain workflow diagnostics rather than external scientific validation.</p>
    """


def _comparison_figure_caption(comparison: dict) -> str:
    decision = comparison.get("decision") or {}
    if decision.get("available"):
        return (
            "Each metric uses its own labeled scale. Marker shape and color identify "
            "variants; the gold halo identifies the recommendation."
        )
    return (
        "Each metric uses its own labeled scale. Marker shape and color identify variants. "
        "Norm drift replaces decision score because the selected runs do not share one "
        "objective profile."
    )


def write_experiment_workbook(
    experiment_dir: Path,
    experiment_record: dict,
    comparison: dict,
) -> None:
    workbook_path = experiment_dir / "workbook.html"
    rows = _comparison_rows_markup(comparison)
    comparison_json = html.escape(json.dumps(comparison, indent=2, sort_keys=True))
    workbook_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QS-DMSS Comparison Research Workbook</title><style>{_experiment_report_styles()}</style></head>
<body><main>
  <p class="eyebrow">Portable comparison research object</p>
  <h1>QS-DMSS Research Workbook</h1>
  <p class="lede">{html.escape(experiment_record['label'])} · generated {html.escape(experiment_record['created_at'])}</p>
  <div class="actions"><button class="primary" type="button" onclick="window.print()">Print / save PDF</button><a href="./workbook/download">Download workbook (.html)</a><a href="./report">Open concise report</a><a href="./bundle">Download evidence bundle</a></div>
  <p class="boundary">This workbook compares reproducible workflow outputs. It does not claim peer-reviewed physical validation.</p>
  <div class="tab-list" role="tablist" aria-label="Workbook sections">
    <button role="tab" id="tab-overview" aria-controls="panel-overview" aria-selected="true">Overview</button>
    <button role="tab" id="tab-variants" aria-controls="panel-variants" aria-selected="false">Variant matrix</button>
    <button role="tab" id="tab-readiness" aria-controls="panel-readiness" aria-selected="false">Evidence & handoff</button>
    <button role="tab" id="tab-data" aria-controls="panel-data" aria-selected="false">Embedded data</button>
  </div>
  <section role="tabpanel" id="panel-overview" aria-labelledby="tab-overview">
    <div class="metric-grid">{_comparison_metric_cards(experiment_record, comparison)}</div>
    {_recommendation_markup(comparison)}
    {_comparison_insights_markup(comparison)}
    <figure>{_comparison_visual_svg(comparison)}<figcaption>{html.escape(_comparison_figure_caption(comparison))}</figcaption></figure>
  </section>
  <section role="tabpanel" id="panel-variants" aria-labelledby="tab-variants" hidden>
    <h2>Variant matrix</h2><div class="table-shell"><table><thead><tr><th>Variant / run</th><th>Rank</th><th>Score</th><th>Qualified</th><th>Energy drift</th><th>Norm drift</th><th>Max density</th><th>Seconds</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></div>
  </section>
  <section role="tabpanel" id="panel-readiness" aria-labelledby="tab-readiness" hidden>
    <h2>Evidence, validation, and HPC handoff</h2>{_readiness_markup(comparison)}
    <h2>Reproduction commands</h2><pre>pip install qs-dmss
qs-dmss showcase run --output-root simulation-showcase
qs-dmss validation fractal-ssfm --output-root fractal-ssfm-validation
qs-dmss executors slurm-dry-run configs/demo.yaml --request-root dry-run-jobs --job-name qs-demo</pre>
  </section>
  <section role="tabpanel" id="panel-data" aria-labelledby="tab-data" hidden><h2>Embedded comparison data</h2><pre>{comparison_json}</pre></section>
</main>
<script>const tabs=[...document.querySelectorAll('[role=tab]')];tabs.forEach(tab=>tab.addEventListener('click',()=>{{tabs.forEach(item=>{{const selected=item===tab;item.setAttribute('aria-selected',String(selected));document.getElementById(item.getAttribute('aria-controls')).hidden=!selected;}});}}));</script>
</body></html>""",
        encoding="utf-8",
    )


def write_experiment_report(
    experiment_dir: Path,
    experiment_record: dict,
    comparison: dict,
) -> None:
    report_path = experiment_dir / "report.html"
    shared = experiment_record.get("shared_experiment")
    shared_markup = ""
    if shared:
        kind = str(shared.get("kind", "comparison"))
        dimensions = shared.get("dimensions") or []
        dimension_rows = "".join(
            f"<li>{html.escape(str(item.get('label') or item.get('path')))} (<code>{html.escape(str(item.get('path')))}</code>)</li>"
            for item in dimensions
        )
        shared_rows = f"""
      <li>Experiment ID: <code>{html.escape(str(shared["id"]))}</code></li>
      <li>Label: {html.escape(str(shared["label"]))}</li>
      <li>Kind: {html.escape(kind)}</li>
"""
        if shared.get("strategy"):
            shared_rows += f"      <li>Strategy: {html.escape(str(shared['strategy']))}</li>\n"
        if shared.get("dimension_count") is not None:
            shared_rows += f"      <li>Dimension count: {html.escape(str(shared['dimension_count']))}</li>\n"
        if shared.get("parameter_label") and shared.get("parameter_path"):
            shared_rows += (
                f"      <li>Primary parameter: {html.escape(str(shared['parameter_label']))} "
                f"(<code>{html.escape(str(shared['parameter_path']))}</code>)</li>\n"
            )
        shared_heading = "Shared Campaign Context" if kind == "campaign" else "Shared Sweep Context"
        shared_markup = f"""
    <h2>{shared_heading}</h2>
    <ul>
{shared_rows}    </ul>
    <h3>Dimensions</h3>
    <ul>
      {dimension_rows}
    </ul>
"""

    rows = _comparison_rows_markup(comparison)
    html_body = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>QS-DMSS Comparison Report</title>
    <style>{_experiment_report_styles()}</style>
  </head>
  <body><main>
    <p class="eyebrow">QS-DMSS Experiment Report · Comparison research object</p>
    <h1>{html.escape(experiment_record['label'])}</h1>
    <p class="lede">{experiment_record['run_count']} deterministic variants · {html.escape(experiment_record['created_at'])} · baseline <code>{html.escape(str(comparison['baseline_run_id'])[-8:])}</code></p>
    <div class="actions"><a class="primary" href="./workbook" target="_blank" rel="noreferrer">Open research workbook</a><a href="./workbook/download">Download workbook (.html)</a><a href="./bundle">Download evidence bundle</a></div>
    <p class="boundary">Diagnostic workflow comparison only. This report does not claim peer-reviewed physical validation.</p>
    <div class="metric-grid">{_comparison_metric_cards(experiment_record, comparison)}</div>
    {_recommendation_markup(comparison)}
    {_comparison_insights_markup(comparison)}
    <figure>{_comparison_visual_svg(comparison)}<figcaption>{html.escape(_comparison_figure_caption(comparison))}</figcaption></figure>
    {shared_markup}
    <h2>Evidence, validation, and HPC handoff</h2>
    {_readiness_markup(comparison)}
    <h2>Variant evidence</h2>
    <div class="table-shell"><table>
      <thead>
        <tr>
          <th>Variant / Run</th>
          <th>Rank</th>
          <th>Score</th>
          <th>Qualified</th>
          <th>Energy Drift</th>
          <th>Norm Drift</th>
          <th>Max Density</th>
          <th>Elapsed Seconds</th>
          <th>Verification</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table></div>
  </main></body>
</html>
"""
    report_path.write_text(html_body, encoding="utf-8")
    write_experiment_workbook(experiment_dir, experiment_record, comparison)


def write_manifest_for_directory(
    root_dir: Path,
    *,
    manifest_name: str = "manifest.sha256.json",
    bundle_name: str = "evidence_bundle.zip",
) -> Path:
    manifest_path = root_dir / manifest_name
    entries = _manifest_entries(root_dir, {manifest_name, bundle_name})

    manifest = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "algorithm": "sha256",
        "files": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def write_manifest(run_dir: Path) -> Path:
    return write_manifest_for_directory(run_dir)


def create_bundle_zip_for_directory(
    root_dir: Path,
    *,
    bundle_name: str = "evidence_bundle.zip",
) -> Path:
    bundle_path = root_dir / bundle_name
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(path for path in root_dir.rglob("*") if path.is_file()):
            if file_path == bundle_path:
                continue
            archive.write(
                file_path,
                arcname=(Path(root_dir.name) / file_path.relative_to(root_dir)).as_posix(),
            )
    return bundle_path


def create_bundle_zip(run_dir: Path) -> Path:
    return create_bundle_zip_for_directory(run_dir)
