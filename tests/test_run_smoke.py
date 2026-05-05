from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from qs_dmss.app import execute_run_from_path, replay_run
from qs_dmss.cli import main
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.paths import demo_config_path


def test_run_bundle_and_replay_are_reproducible(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "configs" / "demo.yaml"

    first_run = execute_run_from_path(
        config_path=config_path,
        output_root=tmp_path / "runs",
    )
    assert first_run.run_dir.exists()
    assert first_run.bundle_path.exists()

    first_result = verify_run_path(first_run.run_dir)
    assert first_result.success, first_result.errors

    bundle_result = verify_run_path(first_run.bundle_path)
    assert bundle_result.success, bundle_result.errors

    replayed_run = replay_run(
        run_dir=first_run.run_dir,
        output_root=tmp_path / "replays",
    )
    replay_result = verify_run_path(replayed_run.run_dir)
    assert replay_result.success, replay_result.errors

    first_density = np.load(first_run.run_dir / "artifacts" / "final_density.npy")
    replay_density = np.load(replayed_run.run_dir / "artifacts" / "final_density.npy")
    np.testing.assert_allclose(first_density, replay_density)

    first_record = json.loads((first_run.run_dir / "run.json").read_text(encoding="utf-8"))
    replay_record = json.loads((replayed_run.run_dir / "run.json").read_text(encoding="utf-8"))
    assert replay_record["replayed_from"] == first_record["run_id"]
    assert first_record["decision_profile"]["objective"]["name"] == "Stability-first recommendation"

    report_html = (first_run.run_dir / "report.html").read_text(encoding="utf-8")
    assert "Decision Profile" in report_html
    assert "Stability-first recommendation" in report_html


def test_bundled_demo_config_and_cli_entrypoint(tmp_path: Path) -> None:
    demo_path = demo_config_path(tmp_path)
    assert demo_path.exists()
    assert "assets" in str(demo_path)

    previous_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        exit_code = main(["run-demo", "--output-root", str(tmp_path / "runs")])
    finally:
        os.chdir(previous_cwd)
    assert exit_code == 0

    run_dirs = [path for path in (tmp_path / "runs").iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    verification = verify_run_path(run_dirs[0])
    assert verification.success, verification.errors

    run_record = json.loads((run_dirs[0] / "run.json").read_text(encoding="utf-8"))
    assert run_record["decision_profile"]["objective"]["primary_metric"] == "energy_drift"


def test_run_demo_defaults_to_current_working_directory(tmp_path: Path) -> None:
    demo_path = demo_config_path(tmp_path)
    previous_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        exit_code = main(["run-demo"])
    finally:
        os.chdir(previous_cwd)
    assert exit_code == 0

    runs_root = tmp_path / "runs"
    assert runs_root.exists()
    run_dirs = [path for path in runs_root.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    verification = verify_run_path(run_dirs[0])
    assert verification.success, verification.errors
    assert not (demo_path.parent / "runs").exists()
