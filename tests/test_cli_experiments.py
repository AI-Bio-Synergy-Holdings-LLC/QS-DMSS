from __future__ import annotations

from pathlib import Path

from qs_dmss.app import execute_run_from_path, replay_run
from qs_dmss.cli import main
from qs_dmss.paths import demo_config_path


def test_cli_experiments_export_and_list(tmp_path: Path, capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_root = tmp_path / "runs"
    config_path = demo_config_path(repo_root)

    first_run = execute_run_from_path(config_path, output_root=output_root)
    replayed_run = replay_run(first_run.run_dir, output_root=output_root)

    exit_code = main(
        [
            "experiments",
            "export",
            first_run.run_id,
            replayed_run.run_id,
            "--label",
            "cli comparison",
            "--output-root",
            str(output_root),
        ]
    )
    assert exit_code == 0
    export_output = capsys.readouterr().out
    assert "Experiment saved:" in export_output
    assert "cli comparison" in export_output

    exit_code = main(
        [
            "experiments",
            "list",
            "--output-root",
            str(output_root),
        ]
    )
    assert exit_code == 0
    list_output = capsys.readouterr().out
    assert "cli comparison" in list_output
