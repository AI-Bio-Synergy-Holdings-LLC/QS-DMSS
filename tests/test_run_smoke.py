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
    assert first_run.job_id is not None
    assert first_run.job_record_path == tmp_path / "jobs" / first_run.job_id / "job.json"
    assert first_run.job_record_path.exists()

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
    assert first_record["execution_job"]["job_id"] == first_run.job_id
    assert first_record["execution_job"]["backend"] == "local"
    assert first_record["execution_job"]["registry_path"] == str(first_run.job_record_path)
    assert replay_record["execution_job"]["job_id"] == replayed_run.job_id

    first_job_record = json.loads(first_run.job_record_path.read_text(encoding="utf-8"))
    assert first_job_record["state"] == "succeeded"
    assert first_job_record["backend"] == "local"
    assert first_job_record["spec"]["source_name"] == "demo.yaml"
    assert first_job_record["spec"]["labels"] == ["run"]
    assert first_job_record["result"]["run_id"] == first_run.run_id
    assert first_job_record["result"]["run_dir"] == str(first_run.run_dir)
    assert {
        artifact["role"] for artifact in first_job_record["result"]["artifacts"]
    } >= {
        "run_directory",
        "evidence_bundle",
        "report",
        "metrics",
        "manifest",
    }
    assert [
        event["state"] for event in first_job_record["lifecycle"]
    ] == [
        "submitted",
        "running",
        "collecting",
        "succeeded",
    ]

    replay_job_record = json.loads(replayed_run.job_record_path.read_text(encoding="utf-8"))
    assert replay_job_record["spec"]["labels"] == ["run", "replay"]
    assert replay_job_record["spec"]["metadata"]["replayed_from"] == first_run.run_id

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


def test_cli_slurm_dry_run_generates_request_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "configs" / "demo.yaml"
    request_root = tmp_path / "dry-run-jobs"

    exit_code = main(
        [
            "executors",
            "slurm-dry-run",
            str(config_path),
            "--request-root",
            str(request_root),
            "--job-name",
            "qs-demo",
            "--partition",
            "debug",
            "--time",
            "00:03:00",
            "--cpus-per-task",
            "2",
            "--mem",
            "4G",
            "--slurm-output-root",
            "hpc-runs",
        ]
    )

    assert exit_code == 0
    job_dirs = [path for path in request_root.iterdir() if path.is_dir()]
    assert len(job_dirs) == 1
    job_dir = job_dirs[0]
    request_dir = job_dir / "request-bundle"
    request_bundle_path = request_dir / "request-bundle.json"
    script_path = request_dir / "slurm-job.sh"
    record_path = job_dir / "job.json"
    assert request_bundle_path.exists()
    assert script_path.exists()
    assert (request_dir / "README.md").exists()
    assert (request_dir / "config.yaml").exists()

    record = json.loads(record_path.read_text(encoding="utf-8"))
    request_bundle = json.loads(request_bundle_path.read_text(encoding="utf-8"))
    script = script_path.read_text(encoding="utf-8")

    assert record["state"] == "draft"
    assert record["backend"] == "dry-run-slurm"
    assert record["metadata"]["submission_policy"] == "never_submit"
    assert request_bundle["submission_policy"]["submitted"] is False
    assert request_bundle["submission_policy"]["manual_review_required"] is True
    assert request_bundle["slurm_options"]["job_name"] == "qs-demo"
    assert request_bundle["slurm_options"]["partition"] == "debug"
    assert "#SBATCH --job-name=qs-demo" in script
    assert "#SBATCH --partition=debug" in script
    assert "qs-dmss run config.yaml --output-root hpc-runs" in script
    assert not any(line.strip().startswith("sbatch") for line in script.splitlines())
