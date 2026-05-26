from __future__ import annotations

import json
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


def test_cli_showcase_list_and_run(tmp_path: Path, capsys) -> None:
    assert "canonical-simulation" in list_showcase_scenarios()

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
