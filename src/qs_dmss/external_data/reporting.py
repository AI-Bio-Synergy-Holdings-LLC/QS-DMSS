"""Script-free, responsive local report with table alternatives to every figure."""

from __future__ import annotations

import html
import json

from qs_dmss.external_data.contracts import LIMITATIONS

STYLE = """:root { color-scheme: light; font-family: system-ui, sans-serif; color: #183b3d; background: #f4f6f4; }
* { box-sizing: border-box; } body { margin: 0; } main { max-width: 1080px; margin: auto; padding: 36px 24px; }
h1 { font: 600 clamp(1.8rem, 5vw, 2.8rem)/1.15 Georgia, serif; margin: 12px 0; }
h2 { font-size: 1.3rem; margin: 0 0 12px; } p, li { line-height: 1.6; } a { color: #075b62; }
.kicker { letter-spacing: .08em; font-size: .8rem; font-weight: 700; } .notice { border-left: 4px solid #a34b17; padding: 12px 18px; background: #fff4e9; }
section { background: white; border: 1px solid #d4dddd; border-radius: 8px; padding: 24px; margin-top: 20px; }
.summary { font-size: 1.1rem; } .muted { color: #476264; } figure { margin: 16px 0; } svg { display: block; width: 100%; height: auto; }
.mobile-chart { display: none; } table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { padding: 10px 8px; border-bottom: 1px solid #d4dddd; text-align: right; overflow-wrap: anywhere; }
th:first-child, td:first-child { text-align: left; } caption { text-align: left; font-weight: 600; padding-bottom: 12px; }
th:not(:first-child), td:not(:first-child) { min-width: 4.5rem; white-space: nowrap; }
summary { cursor: pointer; padding: 14px 0; font-weight: 600; } summary:focus-visible, a:focus-visible { outline: 3px solid #a34b17; outline-offset: 3px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: .85rem; line-height: 1.55; }
code, strong { overflow-wrap: anywhere; } footer { padding: 24px 0; } .chart-text { font: 12px system-ui, sans-serif; fill: #183b3d; }
@media (max-width: 600px) { main { padding: 24px 14px; } section { padding: 16px; } .desktop-chart { display: none; } .mobile-chart { display: block; } th, td { padding: 10px 4px; font-size: .9rem; } }
@media print { body { background: white; } main { padding: 0; } section { break-inside: avoid; } details { display: block; } }
"""


def _escape(value) -> str:
    return html.escape(str(value), quote=True)


def _histogram(histogram: dict, *, mobile: bool) -> str:
    width, height = (320, 250) if mobile else (840, 300)
    left, right, top, bottom = 48, 12, 30, 48
    plot_width, plot_height = width - left - right, height - top - bottom
    counts, edges = histogram["counts"], histogram["edges"]
    maximum = max(max(counts), 1)
    suffix = "mobile" if mobile else "desktop"
    parts = [
        f'<svg class="{suffix}-chart" role="img" aria-labelledby="title-{suffix} desc-{suffix}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<title id="title-{suffix}">Recomputed dimuon invariant-mass distribution</title>',
        f'<desc id="desc-{suffix}">Unweighted selected-event counts. Exact bin intervals and counts follow in the histogram table. This preselected sample cannot establish a discovery.</desc>',
        '<g class="chart-text">',
        f'<text x="{left}" y="16">Events per bin</text>',
    ]
    for fraction in (0, 0.5, 1):
        value = maximum * fraction
        y = top + plot_height * (1 - fraction)
        parts.extend(
            [
                f'<line x1="{left}" y1="{y}" x2="{width - right}" y2="{y}" stroke="#d4dddd" stroke-width="0.75" shape-rendering="crispEdges"/>',
                f'<text x="{left - 8}" y="{y + 4}" text-anchor="end">{value:g}</text>',
            ]
        )
    bar_width = plot_width / len(counts)
    for index, count in enumerate(counts):
        h = plot_height * count / maximum
        parts.append(
            f'<rect x="{left + index * bar_width:.3f}" y="{top + plot_height - h:.3f}" width="{bar_width:.3f}" height="{h:.3f}" fill="#176c73"/>'
        )
    for fraction in (0, 0.5, 1):
        value = edges[0] + (edges[-1] - edges[0]) * fraction
        parts.append(
            f'<text x="{left + plot_width * fraction}" y="{height - 28}" text-anchor="middle">{value:g}</text>'
        )
    parts.append(
        f'<text x="{left + plot_width / 2}" y="{height - 5}" text-anchor="middle">Dimuon mass (GeV, c=1)</text></g></svg>'
    )
    return "".join(parts)


def render_report(result: dict, profile: dict, source: dict) -> bytes:
    histogram = result["histogram"]
    labels = {
        "input_rows": "Input rows",
        "valid_values": "Valid numeric values, categories and identifiers",
        "nonnegative_mass_squared_with_roundoff_policy": "Nonnegative mass squared (declared roundoff policy)",
        "source_both_abs_eta_below_2_4": "Source: both |eta| < 2.4",
        "source_at_least_one_global_muon": "Source: at least one global muon",
        "source_opposite_sign": "Source: opposite-sign charges",
        "source_strict_mass_2_to_5_GeV": "Source: 2 < recomputed mass < 5 GeV",
        "analysis_both_pt_minimum": "Analysis: both muons meet pt minimum",
        "analysis_strict_mass_window": "Analysis: strict mass window",
    }
    cut_rows = "".join(
        f'<tr><th scope="row">{_escape(labels.get(row["stage"], row["stage"]))}</th><td>{row["remaining"]}</td><td>{row["rejected"]}</td></tr>'
        for row in result["cut_flow"]
    )
    bin_rows = "".join(
        f'<tr><th scope="row">{histogram["edges"][i]!r} to {histogram["edges"][i + 1]!r}</th><td>{count}</td></tr>'
        for i, count in enumerate(histogram["counts"])
    )
    limits = "".join(f"<li>{_escape(item)}</li>" for item in LIMITATIONS)
    provenance = _escape(json.dumps(source, indent=2, allow_nan=False))
    method = _escape(json.dumps(profile, indent=2, allow_nan=False))
    quality = _escape(
        json.dumps(
            {
                "invalid_rows_first_failure": result["invalid_rows_first_failure"],
                "roundoff_clamped_rows_before_cuts": result[
                    "roundoff_clamped_rows_before_cuts"
                ],
                "mass_summary_GeV": result["mass_summary_GeV"],
            },
            indent=2,
            allow_nan=False,
        )
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>CERN Dimuon Evidence Lab — local analysis</title><style>{STYLE}</style></head>
<body><main><header><p class="kicker">QS-DMSS · external-data pilot · local only</p>
<h1>CERN Dimuon Evidence Lab</h1><p class="summary">{result["selected_events"]:,} {"event" if result["selected_events"] == 1 else "events"} retained after declared source and analysis cuts.</p>
<p><strong>{_escape(source["observation_label"])}</strong></p>
<p class="notice">Scientific validation: NOT_ESTABLISHED. Independent scientific review: PENDING. Human disposition: PENDING. No scientific approval is implied by this report.</p></header>
<section aria-labelledby="distribution"><h2 id="distribution">Recomputed invariant-mass distribution</h2>
<p>Unweighted event counts; no fit, smoothing or uncertainty estimate. The source was already selected near J/psi: a peak is not an independent discovery.</p>
<figure>{_histogram(histogram, mobile=False)}{_histogram(histogram, mobile=True)}
<figcaption class="muted">Strict analysis window {_escape(profile["mass_min"])} &lt; mass &lt; {_escape(profile["mass_max"])} GeV; both muons require pt ≥ {_escape(profile["pt_min"])} GeV. Empty selection is reported, not treated as a failed physics test.</figcaption></figure>
<details><summary>Inspect exact histogram counts</summary><table><caption>Mass-bin counts (last bin includes its upper edge; selected window is strict)</caption><thead><tr><th scope="col">Mass interval (GeV)</th><th scope="col">Events</th></tr></thead><tbody>{bin_rows}</tbody></table></details></section>
<section aria-labelledby="cuts"><h2 id="cuts">Selection and data quality</h2><table><caption>Sequential cut flow; rejected counts apply at each stage</caption><thead><tr><th scope="col">Stage</th><th scope="col">Retained</th><th scope="col">Rejected</th></tr></thead><tbody>{cut_rows}</tbody></table>
<details><summary>Inspect exclusions and descriptive statistics</summary><pre>{quality}</pre></details></section>
<section aria-labelledby="method"><h2 id="method">Method and provenance</h2><p>Mass is reconstructed from the summed four-vector in natural units (c=1). Exact profile, input hash and provider-reference metadata are retained in the evidence bundle.</p>
<p>Provider reference: <a href="https://opendata.cern.ch/record/5203" rel="noreferrer">CERN Open Data record 5203</a>. CC0-1.0 data; neither CMS nor CERN endorses this work.</p>
<details><summary>Exact analysis profile</summary><pre>{method}</pre></details><details><summary>Input identity and provider-reference metadata</summary><pre>{provenance}</pre></details></section>
<section aria-labelledby="limitations"><h2 id="limitations">Interpretation boundaries</h2><ul>{limits}</ul></section>
<footer class="muted">Read alongside analysis.json, profile.json, source.json and receipt.json. Verification checks retained content; it is not scientific validation. Historical evidence and gate #183 are unchanged.</footer>
</main></body></html>"""
    return document.encode("utf-8")
