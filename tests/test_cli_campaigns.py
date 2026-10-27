from __future__ import annotations

import os
from pathlib import Path

import pytest

from qs_dmss.cli import main


@pytest.mark.parametrize("arguments", [["run-demo"], ["campaigns", "run-demo"]])
def test_demo_outputs_stay_in_nested_working_directory(tmp_path, monkeypatch, arguments):
    checkout = tmp_path / "checkout"
    (checkout / "src" / "qs_dmss").mkdir(parents=True)
    (checkout / "pyproject.toml").write_text("# Synthetic repository marker\n")
    working = checkout / "researcher" / "study"
    working.mkdir(parents=True)
    monkeypatch.chdir(working)

    assert main(arguments) == 0
    assert any((working / "runs").iterdir())
    assert not (checkout / "runs").exists()
    assert not (checkout / "experiments").exists()
    if arguments[0] == "campaigns":
        assert any((working / "experiments").iterdir())


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


def test_cli_campaigns_run_demo_defaults_to_current_working_directory(
    tmp_path: Path,
    capsys,
) -> None:
    previous_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        exit_code = main(["campaigns", "run-demo"])
    finally:
        os.chdir(previous_cwd)

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Campaign saved:" in output
    assert "Planned runs: 6" in output

    assert (tmp_path / "runs").exists()
    assert (tmp_path / "experiments").exists()
    assert any(path.is_dir() for path in (tmp_path / "experiments").iterdir())
