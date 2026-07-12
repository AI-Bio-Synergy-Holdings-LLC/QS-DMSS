from __future__ import annotations

import csv
import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from qs_dmss.app import execute_run_from_path, replay_run
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.io.config import SimulationConfig, load_config
from qs_dmss.paths import bundled_assets_root, contained_path, safe_filename


SHOWCASE_REPORT_SCHEMA_VERSION = 1
SHOWCASE_JSON_REPORT = "simulation-showcase.json"
SHOWCASE_MARKDOWN_REPORT = "simulation-showcase.md"
STEP_HISTORY_CSV = "step-history.csv"
RADIAL_PROFILE_CSV = "radial-density-profile.csv"
MIDPLANE_SLICE_CSV = "density-midplane.csv"
ENERGY_SVG = "energy-history.svg"
RADIAL_DENSITY_SVG = "radial-density-profile.svg"
MIDPLANE_SVG = "density-midplane.svg"
DEFAULT_SHOWCASE_NAME = "canonical-simulation"

SHOWCASE_SCENARIO_METADATA: dict[str, dict[str, Any]] = {
    DEFAULT_SHOWCASE_NAME: {
        "title": "Canonical Simulation Showcase",
        "purpose": (
            "Demonstrate the full QS-DMSS research-object loop with a compact "
            "Gaussian scalar-field packet: run, verify, replay, inspect CSV/SVG "
            "artifacts, compare variants, and export a citable report."
        ),
        "expected_runtime": "Fast smoke scenario; usually under 30 seconds on a laptop.",
        "output_artifacts": [
            {
                "label": "Evidence bundle",
                "description": "ZIP bundle with config, run record, metrics, manifest, report, and environment lock.",
            },
            {
                "label": "CSV diagnostics",
                "description": "Step history, radial density profile, and final midplane density samples.",
            },
            {
                "label": "SVG figures",
                "description": "Energy history, radial density profile, and final-density midplane visualizations.",
            },
            {
                "label": "Replay comparison",
                "description": "Deterministic replay evidence with final-density agreement status.",
            },
        ],
        "limitations": [
            "Small educational/reference scenario, not a peer-reviewed scientific validation claim.",
            "Optimized for fast inspection rather than high-resolution production physics.",
            "Uses packaged parameters; domain experts should add calibrated scenarios before scientific use.",
        ],
        "readiness_badges": [
            {"label": "Packaged", "status": "ready"},
            {"label": "Deterministic", "status": "ready"},
            {"label": "Replayable", "status": "ready"},
            {"label": "Report-ready", "status": "ready"},
        ],
        "next_actions": [
            "Run the showcase to create the single-scenario research object.",
            "Run Guided Comparison to inspect baseline, wider-packet, and stronger-interaction variants.",
            "Use Campaign Studio as the next builder lane for editable parameter-grid studies.",
        ],
        "scenario_narrative": (
            "A compact Gaussian scalar-field packet evolves through the NumPy "
            "split-step Schrodinger-Poisson reference solver. The small grid keeps "
            "the full run, replay, and evidence path suitable for reviewer laptops."
        ),
    },
    "self-interaction-response": {
        "title": "Self-Interaction Response Study",
        "purpose": (
            "Inspect how a stronger configured nonlinear interaction changes density "
            "response and conservation diagnostics while preserving the same evidence, "
            "replay, comparison, and publication workflow."
        ),
        "expected_runtime": "Compact hosted study; usually under 30 seconds per run.",
        "output_artifacts": [
            {"label": "Response diagnostics", "description": "Relative energy, norm, and density trajectories."},
            {"label": "Spatial evidence", "description": "Radial profile and density-midplane SVG/CSV pairs."},
            {"label": "Replay evidence", "description": "Deterministic final-density comparison and verified bundles."},
        ],
        "limitations": [
            "Exploratory parameter-response workflow, not a calibrated physical self-interaction model.",
            "The packaged grid and duration are selected for review speed, not production inference.",
            "A recommendation reflects the configured scoring contract, not a scientific verdict.",
        ],
        "readiness_badges": [
            {"label": "Packaged", "status": "ready"},
            {"label": "Comparative", "status": "ready"},
            {"label": "Replayable", "status": "ready"},
            {"label": "Exploratory", "status": "warning"},
        ],
        "next_actions": [
            "Run the scenario and inspect the relative conservation traces.",
            "Compare the packaged width and interaction variants in the research workbook.",
            "Adapt the study locally before making domain-specific claims.",
        ],
        "scenario_narrative": (
            "This study raises the configured nonlinear interaction while retaining a "
            "compact Gaussian initial state. It is designed to make parameter-response "
            "differences visible and evidence-bundled, not to calibrate a physical model."
        ),
    },
    "fractal-quadrant-validation-preview": {
        "title": "Fractal SSFM Validation Preview",
        "purpose": (
            "Preview the experimental NumPy Fractal/Quadrant SSFM backend with a fuzzy "
            "effective potential, conservation diagnostics, replay evidence, and a clear "
            "route to the separate validation harness."
        ),
        "expected_runtime": "Compact CPU preview; usually under 45 seconds per run.",
        "output_artifacts": [
            {"label": "Spectral run evidence", "description": "Run report, metrics, arrays, manifest, and bundle."},
            {"label": "Geometry preview", "description": "Final density heatmap and radial diagnostic exports."},
            {"label": "Validation handoff", "description": "Workbook guidance for the separate Fractal SSFM validation command."},
        ],
        "limitations": [
            "Experimental fuzzy-potential backend preview; not exact fractal-boundary PDE solving.",
            "Does not represent atomic-void modeling or peer-reviewed physical validation.",
            "Use the separate validation harness for convergence and conservation review.",
        ],
        "readiness_badges": [
            {"label": "CPU reference", "status": "ready"},
            {"label": "Fuzzy potential", "status": "ready"},
            {"label": "Validation companion", "status": "warning"},
            {"label": "Experimental", "status": "warning"},
        ],
        "next_actions": [
            "Run the preview and inspect conservation plus spatial diagnostics.",
            "Run qs-dmss validation fractal-ssfm for the separate validation spine.",
            "Review the dry-run Slurm handoff before considering remote execution.",
        ],
        "scenario_narrative": (
            "An experimental pseudo-spectral nonlinear wave path evolves a Gaussian field "
            "inside a quadrant-weighted fuzzy fractal effective potential. This is a compact "
            "backend preview paired with, but not equivalent to, the validation harness."
        ),
    },
}


@dataclass(frozen=True)
class ShowcaseScenario:
    name: str
    config_path: Path


def showcase_assets_root() -> Path:
    root = bundled_assets_root() / "showcases"
    if not root.exists():
        raise FileNotFoundError(f"Showcase assets not found at {root}")
    return root


def list_showcase_scenarios() -> list[str]:
    return sorted(path.stem for path in showcase_assets_root().glob("*.yaml"))


def showcase_scenario_metadata(name: str = DEFAULT_SHOWCASE_NAME) -> dict[str, Any]:
    scenario_name = safe_filename(name, default=DEFAULT_SHOWCASE_NAME, suffixes=(".yaml",))
    scenario_stem = Path(scenario_name).stem
    metadata = SHOWCASE_SCENARIO_METADATA.get(scenario_stem, {})
    label = scenario_stem.replace("-", " ").title()
    return {
        "title": metadata.get("title", label),
        "purpose": metadata.get(
            "purpose",
            "Packaged QS-DMSS scenario for creating a reproducible simulation artifact.",
        ),
        "expected_runtime": metadata.get("expected_runtime", "Runtime target not documented yet."),
        "output_artifacts": list(metadata.get("output_artifacts", [])),
        "limitations": list(metadata.get("limitations", [])),
        "readiness_badges": list(metadata.get("readiness_badges", [])),
        "next_actions": list(metadata.get("next_actions", [])),
        "scenario_narrative": metadata.get(
            "scenario_narrative",
            "Packaged QS-DMSS simulation scenario with reproducible evidence outputs.",
        ),
    }


def resolve_showcase_scenario(name: str = DEFAULT_SHOWCASE_NAME) -> ShowcaseScenario:
    scenario_name = safe_filename(name, default=DEFAULT_SHOWCASE_NAME, suffixes=(".yaml",))
    scenario_stem = Path(scenario_name).stem
    config_path = contained_path(showcase_assets_root(), f"{scenario_stem}.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Showcase scenario not found: {scenario_stem}")
    return ShowcaseScenario(name=scenario_stem, config_path=config_path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _coordinate_axes(config: SimulationConfig) -> list[np.ndarray]:
    return [
        np.linspace(
            -config.engine.box_size / 2.0,
            config.engine.box_size / 2.0,
            axis_size,
            endpoint=False,
        )
        for axis_size in config.engine.grid_shape
    ]


def _radial_density_profile(
    density: np.ndarray,
    config: SimulationConfig,
) -> list[dict[str, Any]]:
    axes = _coordinate_axes(config)
    x, y, z = np.meshgrid(*axes, indexing="ij")
    radius = np.sqrt(x**2 + y**2 + z**2)
    bin_count = max(4, min(config.engine.grid_shape) // 2)
    edges = np.linspace(0.0, float(np.max(radius)), bin_count + 1)

    rows: list[dict[str, Any]] = []
    for index in range(bin_count):
        lower = edges[index]
        upper = edges[index + 1]
        if index == bin_count - 1:
            mask = (radius >= lower) & (radius <= upper)
        else:
            mask = (radius >= lower) & (radius < upper)

        samples = int(np.count_nonzero(mask))
        values = density[mask]
        rows.append(
            {
                "bin": index,
                "radius_min": round(float(lower), 12),
                "radius_max": round(float(upper), 12),
                "radius_mid": round(float((lower + upper) / 2.0), 12),
                "mean_density": round(float(np.mean(values)) if samples else 0.0, 12),
                "max_density": round(float(np.max(values)) if samples else 0.0, 12),
                "sample_count": samples,
            }
        )
    return rows


def _midplane_density_slice(
    density: np.ndarray,
    config: SimulationConfig,
) -> tuple[list[dict[str, Any]], np.ndarray]:
    axes = _coordinate_axes(config)
    z_index = config.engine.grid_shape[2] // 2
    slice_data = density[:, :, z_index]
    rows: list[dict[str, Any]] = []
    for x_index, x_value in enumerate(axes[0]):
        for y_index, y_value in enumerate(axes[1]):
            rows.append(
                {
                    "x_index": x_index,
                    "y_index": y_index,
                    "z_index": z_index,
                    "x": round(float(x_value), 12),
                    "y": round(float(y_value), 12),
                    "density": round(float(slice_data[x_index, y_index]), 12),
                }
            )
    return rows, slice_data


def _tick_values(minimum: float, maximum: float, count: int = 6) -> list[float]:
    if count < 2:
        return [minimum]
    return [minimum + (maximum - minimum) * index / (count - 1) for index in range(count)]


def _write_line_plot_svg(
    path: Path,
    *,
    title: str,
    x_label: str,
    y_label: str,
    points: list[tuple[float, float]],
    stroke: str,
) -> None:
    width = 960
    height = 540
    left = 96
    right = 44
    top = 92
    bottom = 78
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    if x_min == x_max:
        x_min -= 1.0
        x_max += 1.0
    if y_min == y_max:
        padding = max(abs(y_min) * 0.1, 1e-12)
    else:
        padding = (y_max - y_min) * 0.08
    y_min -= padding
    y_max += padding
    plot_width = width - left - right
    plot_height = height - top - bottom
    scaled = [
        (
            left + ((x - x_min) / (x_max - x_min)) * plot_width,
            top + ((y_max - y) / (y_max - y_min)) * plot_height,
        )
        for x, y in points
    ]
    polyline = " ".join(f"{x:.3f},{y:.3f}" for x, y in scaled)
    circles = "\n".join(
        (
            f'<circle cx="{scaled_x:.3f}" cy="{scaled_y:.3f}" r="4" '
            f'fill="#fffdf8" stroke="{stroke}" stroke-width="2">'
            f'<title>{html.escape(x_label)} {x_value:.6g}; '
            f'{html.escape(y_label)} {y_value:.6g}</title></circle>'
        )
        for (x_value, y_value), (scaled_x, scaled_y) in zip(points, scaled, strict=True)
    )
    x_grid = "\n".join(
        (
            f'<line class="grid-line" x1="{left + (value - x_min) / (x_max - x_min) * plot_width:.3f}" '
            f'y1="{top}" x2="{left + (value - x_min) / (x_max - x_min) * plot_width:.3f}" '
            f'y2="{height - bottom}" stroke="#d8e0df" stroke-width="1" />'
            f'<text x="{left + (value - x_min) / (x_max - x_min) * plot_width:.3f}" '
            f'y="{height - bottom + 24}" text-anchor="middle" font-family="Arial, sans-serif" '
            f'font-size="12" fill="#53666a">{value:.4g}</text>'
        )
        for value in _tick_values(x_min, x_max)
    )
    y_grid = "\n".join(
        (
            f'<line class="grid-line" x1="{left}" '
            f'y1="{top + (y_max - value) / (y_max - y_min) * plot_height:.3f}" '
            f'x2="{width - right}" y2="{top + (y_max - value) / (y_max - y_min) * plot_height:.3f}" '
            f'stroke="#d8e0df" stroke-width="1" />'
            f'<text x="{left - 12}" y="{top + (y_max - value) / (y_max - y_min) * plot_height + 4:.3f}" '
            f'text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#53666a">{value:.3g}</text>'
        )
        for value in _tick_values(y_min, y_max)
    )
    peak_index = int(np.argmax(np.asarray(y_values)))
    peak_x, peak_y = scaled[peak_index]
    peak_value = points[peak_index]
    final_x, final_y = scaled[-1]
    metadata = html.escape(
        json.dumps(
            {
                "figure_type": "sampled_line_diagnostic",
                "sample_count": len(points),
                "x_domain": [x_min, x_max],
                "y_domain": [y_min, y_max],
                "peak_sample": list(peak_value),
                "final_sample": list(points[-1]),
                "claim_boundary": "diagnostic workflow artifact; not scientific validation",
            },
            sort_keys=True,
        )
    )

    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}" data-scientific-figure="line-diagnostic">
  <title>{html.escape(title)}</title>
  <desc>Sampled {html.escape(y_label)} plotted against {html.escape(x_label)} with direct axis labels, grid lines, peak and final-sample annotations. Diagnostic workflow artifact; not scientific validation.</desc>
  <metadata>{metadata}</metadata>
  <rect width="100%" height="100%" fill="#fffdf8" />
  <text x="{left}" y="38" font-family="Georgia, serif" font-size="24" font-weight="700" fill="#17383c">{html.escape(title)}</text>
  <text x="{left}" y="62" font-family="Arial, sans-serif" font-size="12" fill="#607176">{len(points)} sampled values · diagnostic workflow artifact</text>
  {x_grid}
  {y_grid}
  <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#334f54" stroke-width="1.5" />
  <line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#334f54" stroke-width="1.5" />
  <polyline points="{polyline}" fill="none" stroke="{stroke}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke" />
  {circles}
  <line x1="{peak_x:.3f}" y1="{peak_y:.3f}" x2="{min(peak_x + 52, width - right - 128):.3f}" y2="{max(peak_y - 30, top + 18):.3f}" stroke="{stroke}" stroke-width="1.25" />
  <text x="{min(peak_x + 56, width - right - 124):.3f}" y="{max(peak_y - 34, top + 14):.3f}" font-family="Arial, sans-serif" font-size="11" font-weight="700" fill="#31494d">Peak {peak_value[1]:.4g}</text>
  <circle cx="{final_x:.3f}" cy="{final_y:.3f}" r="7" fill="none" stroke="#d96d2e" stroke-width="2" />
  <text x="{max(final_x - 8, left + 70):.3f}" y="{min(final_y + 24, height - bottom - 8):.3f}" text-anchor="end" font-family="Arial, sans-serif" font-size="11" font-weight="700" fill="#9b4c20">Final {points[-1][1]:.4g}</text>
  <text x="{width / 2:.0f}" y="{height - 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#334f54">{html.escape(x_label)}</text>
  <text x="24" y="{top + plot_height / 2:.0f}" transform="rotate(-90 24 {top + plot_height / 2:.0f})" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#334f54">{html.escape(y_label)}</text>
</svg>
""",
        encoding="utf-8",
    )


def _density_color(value: float, minimum: float, maximum: float) -> str:
    if maximum <= minimum:
        fraction = 0.0
    else:
        fraction = (value - minimum) / (maximum - minimum)
    low = np.array([239, 246, 255], dtype=float)
    mid = np.array([45, 212, 191], dtype=float)
    high = np.array([15, 23, 42], dtype=float)
    if fraction < 0.55:
        local = fraction / 0.55
        rgb = low + (mid - low) * local
    else:
        local = (fraction - 0.55) / 0.45
        rgb = mid + (high - mid) * local
    return "#" + "".join(f"{int(round(channel)):02x}" for channel in rgb)


def _write_density_slice_svg(path: Path, slice_data: np.ndarray) -> None:
    width = 900
    height = 700
    left = 92
    top = 94
    plot_size = 500
    nx, ny = slice_data.shape
    cell_width = plot_size / nx
    cell_height = plot_size / ny
    minimum = float(np.min(slice_data))
    maximum = float(np.max(slice_data))
    cells = []
    for x_index in range(nx):
        for y_index in range(ny):
            x = left + x_index * cell_width
            y = top + (ny - y_index - 1) * cell_height
            value = float(slice_data[x_index, y_index])
            color = _density_color(value, minimum, maximum)
            cells.append(
                f'<rect x="{x:.3f}" y="{y:.3f}" width="{cell_width + 0.2:.3f}" height="{cell_height + 0.2:.3f}" fill="{color}">'
                f'<title>x index {x_index}; y index {y_index}; density {value:.6g}</title></rect>'
            )
    x_ticks = "\n".join(
        f'<text x="{left + index / 4 * plot_size:.3f}" y="{top + plot_size + 24}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#53666a">{round(index / 4 * (nx - 1))}</text>'
        for index in range(5)
    )
    y_ticks = "\n".join(
        f'<text x="{left - 14}" y="{top + plot_size - index / 4 * plot_size + 4:.3f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#53666a">{round(index / 4 * (ny - 1))}</text>'
        for index in range(5)
    )
    peak_index = np.unravel_index(int(np.argmax(slice_data)), slice_data.shape)
    peak_x = left + (peak_index[0] + 0.5) * cell_width
    peak_y = top + (ny - peak_index[1] - 0.5) * cell_height
    midpoint = minimum + (maximum - minimum) / 2
    metadata = html.escape(
        json.dumps(
            {
                "figure_type": "density_midplane_heatmap",
                "shape": [nx, ny],
                "minimum": minimum,
                "maximum": maximum,
                "peak_index": [int(index) for index in peak_index],
                "claim_boundary": "diagnostic workflow artifact; not scientific validation",
            },
            sort_keys=True,
        )
    )

    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Final density midplane heatmap" data-scientific-figure="density-heatmap">
  <title>Final Density Midplane</title>
  <desc>Final solver density on the central grid plane with indexed axes, an explicit color scale, cell tooltips, and the peak cell annotated. Diagnostic workflow artifact; not scientific validation.</desc>
  <metadata>{metadata}</metadata>
  <defs>
    <linearGradient id="density-scale" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0%" stop-color="{_density_color(minimum, minimum, maximum)}" />
      <stop offset="55%" stop-color="{_density_color(midpoint, minimum, maximum)}" />
      <stop offset="100%" stop-color="{_density_color(maximum, minimum, maximum)}" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="#fffdf8" />
  <text x="{left}" y="38" font-family="Georgia, serif" font-size="24" font-weight="700" fill="#17383c">Final Density Midplane</text>
  <text x="{left}" y="62" font-family="Arial, sans-serif" font-size="12" fill="#607176">Central solver plane · {nx} × {ny} indexed cells · diagnostic workflow artifact</text>
  {"".join(cells)}
  <rect x="{left}" y="{top}" width="{plot_size}" height="{plot_size}" fill="none" stroke="#334f54" stroke-width="1.5" />
  {x_ticks}
  {y_ticks}
  <text x="{left + plot_size / 2}" y="{top + plot_size + 54}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#334f54">x grid index</text>
  <text x="24" y="{top + plot_size / 2}" transform="rotate(-90 24 {top + plot_size / 2})" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#334f54">y grid index</text>
  <circle cx="{peak_x:.3f}" cy="{peak_y:.3f}" r="{max(min(cell_width, cell_height) * 0.42, 7):.3f}" fill="none" stroke="#f7c96b" stroke-width="3" />
  <line x1="{peak_x:.3f}" y1="{peak_y:.3f}" x2="{left + plot_size + 62}" y2="{top + 54}" stroke="#d96d2e" stroke-width="1.5" />
  <text x="{left + plot_size + 72}" y="{top + 50}" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#9b4c20">Peak cell ({peak_index[0]}, {peak_index[1]})</text>
  <text x="{left + plot_size + 72}" y="{top + 68}" font-family="Arial, sans-serif" font-size="12" fill="#53666a">density {maximum:.4g}</text>
  <rect x="{left + plot_size + 72}" y="{top + 116}" width="28" height="260" fill="url(#density-scale)" stroke="#334f54" stroke-width="1" />
  <text x="{left + plot_size + 112}" y="{top + 126}" font-family="Arial, sans-serif" font-size="12" fill="#53666a">{maximum:.3g}</text>
  <text x="{left + plot_size + 112}" y="{top + 250}" font-family="Arial, sans-serif" font-size="12" fill="#53666a">{midpoint:.3g}</text>
  <text x="{left + plot_size + 112}" y="{top + 376}" font-family="Arial, sans-serif" font-size="12" fill="#53666a">{minimum:.3g}</text>
  <text x="{left + plot_size + 72}" y="{top + 406}" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#334f54">density (solver units)</text>
</svg>
""",
        encoding="utf-8",
    )


def _write_showcase_artifacts(
    output_root: Path,
    run_dir: Path,
    config: SimulationConfig,
) -> dict[str, str]:
    artifacts_root = output_root / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    metrics = _read_json(run_dir / "metrics.json")
    density = np.load(run_dir / "artifacts" / "final_density.npy")
    history_rows = [
        {
            "step": item["step"],
            "norm": item["norm"],
            "energy": item["energy"],
            "max_density": item["max_density"],
        }
        for item in metrics["history"]
    ]
    radial_rows = _radial_density_profile(density, config)
    midplane_rows, midplane_slice = _midplane_density_slice(density, config)

    step_history_csv = artifacts_root / STEP_HISTORY_CSV
    radial_profile_csv = artifacts_root / RADIAL_PROFILE_CSV
    midplane_csv = artifacts_root / MIDPLANE_SLICE_CSV
    energy_svg = artifacts_root / ENERGY_SVG
    radial_svg = artifacts_root / RADIAL_DENSITY_SVG
    midplane_svg = artifacts_root / MIDPLANE_SVG

    _write_csv(
        step_history_csv,
        ["step", "norm", "energy", "max_density"],
        history_rows,
    )
    _write_csv(
        radial_profile_csv,
        [
            "bin",
            "radius_min",
            "radius_max",
            "radius_mid",
            "mean_density",
            "max_density",
            "sample_count",
        ],
        radial_rows,
    )
    _write_csv(
        midplane_csv,
        ["x_index", "y_index", "z_index", "x", "y", "density"],
        midplane_rows,
    )

    initial_energy = float(history_rows[0]["energy"])
    energy_scale = abs(initial_energy) or 1.0
    _write_line_plot_svg(
        energy_svg,
        title="Relative Energy Change",
        x_label="simulation step",
        y_label="(energy - initial energy) / |initial energy|",
        points=[
            (
                float(row["step"]),
                (float(row["energy"]) - initial_energy) / energy_scale,
            )
            for row in history_rows
        ],
        stroke="#0f766e",
    )
    _write_line_plot_svg(
        radial_svg,
        title="Radial Density Profile",
        x_label="radius",
        y_label="mean density",
        points=[
            (float(row["radius_mid"]), float(row["mean_density"]))
            for row in radial_rows
        ],
        stroke="#1d4ed8",
    )
    _write_density_slice_svg(midplane_svg, midplane_slice)

    return {
        "step_history_csv": str(step_history_csv),
        "radial_profile_csv": str(radial_profile_csv),
        "midplane_slice_csv": str(midplane_csv),
        "energy_history_svg": str(energy_svg),
        "radial_density_svg": str(radial_svg),
        "midplane_density_svg": str(midplane_svg),
    }


def _compare_replay(run_dir: Path, replay_dir: Path) -> dict[str, Any]:
    original_density = np.load(run_dir / "artifacts" / "final_density.npy")
    replay_density = np.load(replay_dir / "artifacts" / "final_density.npy")
    absolute_delta = np.abs(original_density - replay_density)
    return {
        "final_density_allclose": bool(
            np.allclose(original_density, replay_density, rtol=1e-10, atol=1e-12)
        ),
        "max_abs_density_delta": round(float(np.max(absolute_delta)), 18),
    }


def _metrics_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    initial_norm = float(metrics["initial_norm"])
    initial_energy = float(metrics["initial_energy"])
    norm_drift = float(metrics["norm_drift"])
    energy_drift = float(metrics["energy_drift"])
    return {
        "initial_norm": initial_norm,
        "final_norm": metrics["final_norm"],
        "norm_drift": norm_drift,
        "relative_norm_drift": (
            0.0
            if initial_norm == 0.0
            else round(abs(norm_drift) / abs(initial_norm), 18)
        ),
        "initial_energy": initial_energy,
        "final_energy": metrics["final_energy"],
        "energy_drift": energy_drift,
        "relative_energy_drift": (
            0.0
            if initial_energy == 0.0
            else round(abs(energy_drift) / abs(initial_energy), 18)
        ),
        "max_density": metrics["max_density"],
        "elapsed_seconds": metrics["elapsed_seconds"],
        "history_points": len(metrics["history"]),
    }


def _showcase_guided_interpretation(
    metrics: dict[str, Any],
    verification: Any,
    replay_report: dict[str, Any] | None,
) -> dict[str, Any]:
    norm_message = (
        "The norm drift is effectively zero for this small deterministic run, "
        "which is a useful sanity check for the numerical workflow."
        if abs(float(metrics["relative_norm_drift"])) <= 1e-12
        else "The norm drift is visible enough to deserve reviewer attention."
    )
    replay_message = (
        "Replay reproduced the final density array, so the generated evidence can be re-run "
        "through the same deterministic path."
        if replay_report is not None and replay_report["final_density_allclose"]
        else "Replay was skipped or did not match final density, so the result should be reviewed before sharing."
    )
    verification_message = (
        f"Evidence verification checked {verification.checked_files} files from the run directory."
        if verification.success
        else "Evidence verification reported errors; inspect the JSON report before trusting this run."
    )
    return {
        "plain_language_summary": (
            "This showcase starts with a compact scalar-field density packet and evolves it "
            "through the packaged reference solver. The goal is not to prove a scientific "
            "claim; the goal is to show that QS-DMSS can run a scenario, preserve evidence, "
            "replay the result, and expose interpretable artifacts."
        ),
        "what_this_result_means": [
            norm_message,
            "The energy-history and density artifacts give reviewers a compact view of how the simulated field evolves over the configured steps.",
            verification_message,
            replay_message,
        ],
        "what_this_result_does_not_claim": [
            "It does not establish peer-reviewed dark-matter, cosmology, or quantum-gravity conclusions.",
            "It does not prove the solver is valid for production scientific inference beyond this packaged reference workflow.",
            "It should be treated as a reproducible workflow demonstration and a starting point for external review.",
        ],
        "artifact_callouts": [
            {
                "artifact_key": "energy_history_svg",
                "title": "Energy history plot",
                "callout": "Use this plot to see whether the run changes smoothly across simulation steps.",
                "why_it_matters": "Abrupt jumps would be a useful signal for reviewers to inspect timestep, grid, or solver assumptions.",
            },
            {
                "artifact_key": "radial_density_svg",
                "title": "Radial density profile",
                "callout": "Use this profile to understand how density concentrates from the center outward.",
                "why_it_matters": "It turns the final 3D field into a compact shape reviewers can compare across scenarios.",
            },
            {
                "artifact_key": "midplane_density_svg",
                "title": "Midplane density heatmap",
                "callout": "Use this heatmap to inspect the spatial structure of the final density slice.",
                "why_it_matters": "It makes the simulated field visible without opening binary array artifacts.",
            },
            {
                "artifact_key": "step_history_csv",
                "title": "Step history table",
                "callout": "Use the CSV to inspect norm, energy, and max-density values step by step.",
                "why_it_matters": "The table is the machine-readable companion to the plotted run history.",
            },
            {
                "artifact_key": "radial_profile_csv",
                "title": "Radial profile table",
                "callout": "Use the CSV when you want to replot or independently analyze the radial profile.",
                "why_it_matters": "It keeps the visual summary reproducible outside the cockpit.",
            },
            {
                "artifact_key": "midplane_slice_csv",
                "title": "Midplane slice table",
                "callout": "Use the CSV to inspect exact coordinates and density values behind the heatmap.",
                "why_it_matters": "It lets reviewers audit the plotted density slice numerically.",
            },
        ],
        "review_prompt": (
            "A useful review comment can focus on whether these artifacts make the simulated behavior "
            "understandable, whether the claim boundary is clear, or which diagnostic would make the "
            "scenario more trustworthy."
        ),
    }


def write_showcase_markdown_report(report: dict[str, Any], path: Path) -> None:
    metrics = report["metrics"]
    verification = report["verification"]
    replay = report.get("replay")
    artifacts = report["artifacts"]
    interpretation = report["interpretation"]
    artifact_callout_lines = []
    for item in interpretation["artifact_callouts"]:
        artifact_callout_lines.extend(
            [
                f"### {item['title']}",
                "",
                item["callout"],
                "",
                f"Why it matters: {item['why_it_matters']}",
                "",
            ]
        )
    replay_lines = [
        "| Replay evidence verification | skipped | Replay was disabled. |",
        "| Replay density comparison | skipped | Replay was disabled. |",
    ]
    if replay is not None:
        replay_status = "PASS" if replay["verification_success"] else "FAIL"
        density_status = "PASS" if replay["final_density_allclose"] else "FAIL"
        replay_lines = [
            f"| Replay evidence verification | {replay_status} | `{replay['run_dir']}` |",
            f"| Replay density comparison | {density_status} | max abs delta `{replay['max_abs_density_delta']}` |",
        ]

    lines = [
        f"# QS-DMSS {report.get('scenario_title', 'Simulation Showcase')}",
        "",
        "This generated report is a reviewer-facing simulation walkthrough for the",
        "packaged QS-DMSS reference solver.",
        "",
        report["claim_boundary"],
        "",
        "## Scenario",
        "",
        f"- Name: `{report['scenario']}`",
        f"- Config: `{report['config_path']}`",
        f"- Output root: `{report['output_root']}`",
        "",
        report["scenario_narrative"],
        "",
        "## Guided Interpretation",
        "",
        interpretation["plain_language_summary"],
        "",
        "### What This Result Means",
        "",
        *[f"- {item}" for item in interpretation["what_this_result_means"]],
        "",
        "### What This Result Does Not Claim",
        "",
        *[f"- {item}" for item in interpretation["what_this_result_does_not_claim"]],
        "",
        "### Artifact Callouts",
        "",
        *artifact_callout_lines,
        "### Reviewer Prompt",
        "",
        interpretation["review_prompt"],
        "",
        "## Reproduce This Showcase",
        "",
        "```powershell",
        f"qs-dmss showcase run --output-root \"{report['output_root']}\"",
        f"qs-dmss verify \"{report['run']['run_dir']}\"",
        "```",
        "",
        "The generated run can also be replayed directly:",
        "",
        "```powershell",
        f"qs-dmss replay \"{report['run']['run_dir']}\" --output-root \"{Path(report['output_root']) / 'manual-replays'}\"",
        "```",
        "",
        "## Simulation Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Initial norm | {metrics['initial_norm']} |",
        f"| Final norm | {metrics['final_norm']} |",
        f"| Norm drift | {metrics['norm_drift']} |",
        f"| Relative norm drift | {metrics['relative_norm_drift']} |",
        f"| Initial energy | {metrics['initial_energy']} |",
        f"| Final energy | {metrics['final_energy']} |",
        f"| Energy drift | {metrics['energy_drift']} |",
        f"| Relative energy drift | {metrics['relative_energy_drift']} |",
        f"| Final max density | {metrics['max_density']} |",
        f"| Elapsed seconds | {metrics['elapsed_seconds']} |",
        f"| History points | {metrics['history_points']} |",
        "",
        "## Verification And Replay",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
        (
            "| Evidence verification | PASS | "
            f"`{report['run']['run_dir']}` checked files: {verification['checked_files']} |"
            if verification["success"]
            else "| Evidence verification | FAIL | See `simulation-showcase.json` errors. |"
        ),
        *replay_lines,
        "",
        "## Reviewer Artifacts",
        "",
        "| Artifact | Purpose |",
        "| --- | --- |",
        f"| `{report['run']['run_dir']}` | Full run directory with config, metrics, arrays, HTML report, manifest, and bundle. |",
        f"| `{report['run']['bundle_path']}` | Portable evidence bundle for the canonical run. |",
        f"| `{artifacts['step_history_csv']}` | Step-by-step norm, energy, and max-density table. |",
        f"| `{artifacts['radial_profile_csv']}` | Radial density summary derived from the final density array. |",
        f"| `{artifacts['midplane_slice_csv']}` | Final-density midplane values for independent plotting. |",
        f"| `{artifacts['energy_history_svg']}` | Lightweight energy-history plot. |",
        f"| `{artifacts['radial_density_svg']}` | Lightweight radial-density profile plot. |",
        f"| `{artifacts['midplane_density_svg']}` | Lightweight final-density midplane heatmap. |",
        "",
        "## What To Review",
        "",
        "- Does the showcase make the simulated field evolution understandable without reading source code?",
        "- Are the generated CSV/SVG artifacts enough to inspect the actual simulation output?",
        "- Does the evidence bundle plus replay check make the result easier to trust?",
        "- Is the claim boundary clear enough for scientific and JOSS-style review?",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_simulation_showcase(
    output_root: str | Path | None = None,
    *,
    scenario: str = DEFAULT_SHOWCASE_NAME,
    replay: bool = True,
    runs_output_root: str | Path | None = None,
    replay_output_root: str | Path | None = None,
) -> dict[str, Any]:
    output_path = (
        Path(output_root).resolve()
        if output_root is not None
        else (Path.cwd() / "simulation-showcase").resolve()
    )
    output_path.mkdir(parents=True, exist_ok=True)
    run_root = (
        Path(runs_output_root).resolve()
        if runs_output_root is not None
        else output_path / "runs"
    )
    replay_root = (
        Path(replay_output_root).resolve()
        if replay_output_root is not None
        else output_path / "replays"
    )

    selected = resolve_showcase_scenario(scenario)
    scenario_metadata = showcase_scenario_metadata(selected.name)
    config = load_config(selected.config_path)
    outputs = execute_run_from_path(
        selected.config_path,
        output_root=run_root,
    )
    verification = verify_run_path(outputs.run_dir)
    metrics = _read_json(outputs.run_dir / "metrics.json")
    metrics_summary = _metrics_summary(metrics)
    artifacts = _write_showcase_artifacts(output_path, outputs.run_dir, config)

    replay_report = None
    if replay:
        replay_outputs = replay_run(
            outputs.run_dir,
            output_root=replay_root,
        )
        replay_verification = verify_run_path(replay_outputs.run_dir)
        replay_comparison = _compare_replay(outputs.run_dir, replay_outputs.run_dir)
        replay_report = {
            "run_id": replay_outputs.run_id,
            "run_dir": str(replay_outputs.run_dir),
            "bundle_path": str(replay_outputs.bundle_path),
            "verification_success": replay_verification.success,
            "verification_errors": replay_verification.errors,
            **replay_comparison,
        }

    report = {
        "schema_version": SHOWCASE_REPORT_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "scenario": selected.name,
        "scenario_title": scenario_metadata["title"],
        "scenario_narrative": scenario_metadata["scenario_narrative"],
        "claim_boundary": (
            "This demonstrates the QS-DMSS workflow and simulation behavior; "
            "it is not peer-reviewed scientific validation."
        ),
        "output_root": str(output_path),
        "config_path": str(selected.config_path),
        "run": {
            "run_id": outputs.run_id,
            "run_dir": str(outputs.run_dir),
            "bundle_path": str(outputs.bundle_path),
        },
        "verification": {
            "success": verification.success,
            "checked_files": verification.checked_files,
            "errors": verification.errors,
        },
        "replay": replay_report,
        "metrics": metrics_summary,
        "interpretation": _showcase_guided_interpretation(
            metrics_summary,
            verification,
            replay_report,
        ),
        "artifacts": artifacts,
    }
    report["success"] = bool(
        verification.success
        and (
            replay_report is None
            or (
                replay_report["verification_success"]
                and replay_report["final_density_allclose"]
            )
        )
    )

    report_path = output_path / SHOWCASE_JSON_REPORT
    markdown_report_path = output_path / SHOWCASE_MARKDOWN_REPORT
    report["report_path"] = str(report_path)
    report["markdown_report_path"] = str(markdown_report_path)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_showcase_markdown_report(report, markdown_report_path)
    return report
