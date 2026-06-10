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
    }
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


def _scale_points(
    points: list[tuple[float, float]],
    *,
    width: int,
    height: int,
    margin: int,
) -> tuple[list[tuple[float, float]], tuple[float, float], tuple[float, float]]:
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    if x_min == x_max:
        x_min -= 1.0
        x_max += 1.0
    if y_min == y_max:
        padding = max(abs(y_min) * 0.1, 1.0)
        y_min -= padding
        y_max += padding

    plot_width = width - (2 * margin)
    plot_height = height - (2 * margin)
    scaled = [
        (
            margin + ((x - x_min) / (x_max - x_min)) * plot_width,
            height - margin - ((y - y_min) / (y_max - y_min)) * plot_height,
        )
        for x, y in points
    ]
    return scaled, (x_min, x_max), (y_min, y_max)


def _write_line_plot_svg(
    path: Path,
    *,
    title: str,
    x_label: str,
    y_label: str,
    points: list[tuple[float, float]],
    stroke: str,
) -> None:
    width = 720
    height = 360
    margin = 56
    scaled, x_domain, y_domain = _scale_points(
        points,
        width=width,
        height=height,
        margin=margin,
    )
    polyline = " ".join(f"{x:.3f},{y:.3f}" for x, y in scaled)
    circles = "\n".join(
        f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3.5" fill="{stroke}" />'
        for x, y in scaled
    )

    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="{margin}" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#111827">{html.escape(title)}</text>
  <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#334155" stroke-width="1" />
  <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#334155" stroke-width="1" />
  <polyline points="{polyline}" fill="none" stroke="{stroke}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" />
  {circles}
  <text x="{width / 2:.0f}" y="{height - 16}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#334155">{html.escape(x_label)}</text>
  <text x="18" y="{height / 2:.0f}" transform="rotate(-90 18 {height / 2:.0f})" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#334155">{html.escape(y_label)}</text>
  <text x="{margin}" y="{height - margin + 22}" font-family="Arial, sans-serif" font-size="11" fill="#64748b">{x_domain[0]:.4g}</text>
  <text x="{width - margin}" y="{height - margin + 22}" text-anchor="end" font-family="Arial, sans-serif" font-size="11" fill="#64748b">{x_domain[1]:.4g}</text>
  <text x="{margin - 8}" y="{height - margin}" text-anchor="end" font-family="Arial, sans-serif" font-size="11" fill="#64748b">{y_domain[0]:.4g}</text>
  <text x="{margin - 8}" y="{margin + 4}" text-anchor="end" font-family="Arial, sans-serif" font-size="11" fill="#64748b">{y_domain[1]:.4g}</text>
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
    cell_size = 24
    margin = 56
    nx, ny = slice_data.shape
    width = margin * 2 + nx * cell_size
    height = margin * 2 + ny * cell_size + 24
    minimum = float(np.min(slice_data))
    maximum = float(np.max(slice_data))
    cells = []
    for x_index in range(nx):
        for y_index in range(ny):
            x = margin + x_index * cell_size
            y = margin + (ny - y_index - 1) * cell_size
            color = _density_color(float(slice_data[x_index, y_index]), minimum, maximum)
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}" stroke="#f8fafc" stroke-width="1" />'
            )

    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Final density midplane heatmap">
  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="{margin}" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#111827">Final Density Midplane</text>
  {"".join(cells)}
  <text x="{margin}" y="{height - 18}" font-family="Arial, sans-serif" font-size="12" fill="#334155">min density {minimum:.4g}</text>
  <text x="{width - margin}" y="{height - 18}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#334155">max density {maximum:.4g}</text>
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

    _write_line_plot_svg(
        energy_svg,
        title="Energy History",
        x_label="simulation step",
        y_label="energy",
        points=[(float(row["step"]), float(row["energy"])) for row in history_rows],
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
        "# QS-DMSS Canonical Simulation Showcase",
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
        "scenario_narrative": (
            "The scenario evolves a compact Gaussian scalar-field packet with a "
            "deterministic random phase through the NumPy split-step "
            "Schrodinger-Poisson reference solver. It is intentionally small "
            "enough for reviewer laptops while still producing inspectable "
            "field-density, energy-history, and replay artifacts."
        ),
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
