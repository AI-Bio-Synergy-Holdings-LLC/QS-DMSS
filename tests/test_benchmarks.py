from __future__ import annotations

import json
from pathlib import Path

from qs_dmss.benchmarks import (
    list_benchmark_scenarios,
    validate_benchmark_scenarios,
)
from qs_dmss.cli import main
from qs_dmss.evidence.verify import verify_run_path


def test_packaged_benchmark_validation_smoke(tmp_path: Path) -> None:
    report = validate_benchmark_scenarios(
        scenarios=["demo-baseline"],
        output_root=tmp_path / "benchmark-validation",
    )

    assert report["success"], report
    assert report["scenarios"][0]["scenario"] == "demo-baseline"

    run_dir = Path(report["scenarios"][0]["run_dir"])
    replay_run_dir = Path(report["scenarios"][0]["replay_run_dir"])
    assert verify_run_path(run_dir).success
    assert verify_run_path(replay_run_dir).success

    report_path = tmp_path / "benchmark-validation" / "benchmark-validation.json"
    saved_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved_report["success"] is True
    assert saved_report["scenarios"][0]["metrics"]["energy_drift"] > 0


def test_cli_benchmark_list_and_validate(tmp_path: Path, capsys) -> None:
    assert "demo-baseline" in list_benchmark_scenarios()

    list_exit_code = main(["benchmarks", "list"])
    assert list_exit_code == 0
    assert "demo-baseline" in capsys.readouterr().out

    validate_exit_code = main(
        [
            "benchmarks",
            "validate",
            "--scenario",
            "demo-baseline",
            "--output-root",
            str(tmp_path / "cli-benchmark-validation"),
        ]
    )
    assert validate_exit_code == 0
    output = capsys.readouterr().out
    assert "Benchmark passed: demo-baseline" in output
    assert "benchmark-validation.json" in output
