from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from qs_dmss.app import execute_run_from_path, replay_run
from qs_dmss.evidence.verify import verify_run_path


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
