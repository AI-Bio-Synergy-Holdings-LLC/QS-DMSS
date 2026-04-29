from __future__ import annotations

import os
from pathlib import Path

from qs_dmss.cli import main


def test_cli_campaigns_run_demo(tmp_path: Path, capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    previous_cwd = Path.cwd()
    try:
        os.chdir(repo_root)
        exit_code = main(["campaigns", "run-demo", "--output-root", str(tmp_path / "runs")])
    finally:
        os.chdir(previous_cwd)

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Campaign saved:" in output
    assert "Planned runs: 6" in output
    assert "Recommended run:" in output

    experiments_dir = tmp_path / "experiments"
    assert experiments_dir.exists()
    assert any(path.is_dir() for path in experiments_dir.iterdir())
