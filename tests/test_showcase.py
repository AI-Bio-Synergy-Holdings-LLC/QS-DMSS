from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from qs_dmss.cli import main
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.showcase import (
    list_showcase_scenarios,
    run_simulation_showcase,
)


def test_simulation_showcase_generates_reviewer_artifacts(tmp_path: Path) -> None:
    report = run_simulation_showcase(output_root=tmp_path / "simulation-showcase")

    assert report["success"], report
    assert report["scenario"] == "canonical-simulation"
    assert report["claim_boundary"].endswith("not peer-reviewed scientific validation.")

    run_dir = Path(report["run"]["run_dir"])
    replay_dir = Path(report["replay"]["run_dir"])
    assert verify_run_path(run_dir).success
    assert verify_run_path(replay_dir).success
    assert report["replay"]["final_density_allclose"] is True

    report_path = tmp_path / "simulation-showcase" / "simulation-showcase.json"
    markdown_path = tmp_path / "simulation-showcase" / "simulation-showcase.md"
    saved_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved_report["success"] is True
    assert saved_report["metrics"]["history_points"] == 11

    markdown_text = markdown_path.read_text(encoding="utf-8")
    assert "# QS-DMSS Canonical Simulation Showcase" in markdown_text
    assert "not peer-reviewed scientific validation" in markdown_text
    assert "Radial density" in markdown_text or "radial-density-profile.csv" in markdown_text

    artifact_paths = report["artifacts"].values()
    for artifact_path in artifact_paths:
        assert Path(artifact_path).exists()

    energy_svg = Path(report["artifacts"]["energy_history_svg"]).read_text(
        encoding="utf-8"
    )
    radial_svg = Path(report["artifacts"]["radial_density_svg"]).read_text(
        encoding="utf-8"
    )
    density_svg = Path(report["artifacts"]["midplane_density_svg"]).read_text(
        encoding="utf-8"
    )
    for line_svg in (energy_svg, radial_svg):
        ET.fromstring(line_svg)
        assert 'data-scientific-figure="line-diagnostic"' in line_svg
        assert "<title>" in line_svg
        assert "<desc>" in line_svg
        assert "<metadata>" in line_svg
        assert 'class="grid-line"' in line_svg
        assert "Peak" in line_svg
        assert "Final" in line_svg
    assert 'data-scientific-figure="density-heatmap"' in density_svg
    ET.fromstring(density_svg)
    assert "density (solver units)" in density_svg
    assert "Peak cell" in density_svg
    assert "<metadata>" in density_svg


def test_cli_showcase_list_and_run(tmp_path: Path, capsys) -> None:
    assert set(list_showcase_scenarios()) >= {
        "canonical-simulation",
        "self-interaction-response",
        "fractal-quadrant-validation-preview",
    }

    list_exit_code = main(["showcase", "list"])
    assert list_exit_code == 0
    assert "canonical-simulation" in capsys.readouterr().out

    run_exit_code = main(
        [
            "showcase",
            "run",
            "--output-root",
            str(tmp_path / "cli-simulation-showcase"),
        ]
    )
    assert run_exit_code == 0
    output = capsys.readouterr().out
    assert "Simulation showcase passed: canonical-simulation" in output
    assert "simulation-showcase.json" in output
    assert "Reviewer summary:" in output
    assert "simulation-showcase.md" in output


def test_expanded_packaged_showcase_scenarios_run(tmp_path: Path) -> None:
    expectations = {
        "self-interaction-response": "Self-Interaction Response Study",
        "fractal-quadrant-validation-preview": "Fractal SSFM Validation Preview",
    }
    for scenario, title in expectations.items():
        report = run_simulation_showcase(
            output_root=tmp_path / scenario,
            scenario=scenario,
            replay=False,
        )
        assert report["success"], report
        assert report["scenario_title"] == title
        assert report["scenario_narrative"]
        assert Path(report["artifacts"]["energy_history_svg"]).exists()
