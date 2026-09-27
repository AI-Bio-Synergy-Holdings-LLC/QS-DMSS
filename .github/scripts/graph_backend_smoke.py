"""Verify the experimental backend from an installed candidate, outside the checkout."""

import argparse
import json
import zipfile
from importlib.resources import files
from pathlib import Path

import numpy as np
from fastapi import HTTPException

from qs_dmss.app import execute_run_from_path, replay_run
from qs_dmss.cockpit.api import CockpitService
from qs_dmss.cockpit.artifacts import CockpitArtifactService
from qs_dmss.evidence.verify import verify_run_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, type=Path)
    root = parser.parse_args().output_root.resolve()
    config = files("qs_dmss.assets").joinpath("configs/sierpinski_graph_spectral.yaml")
    run = execute_run_from_path(str(config), root / "runs")
    replay = replay_run(run.run_dir, root / "replays")
    assert verify_run_path(run.bundle_path).success
    assert verify_run_path(replay.bundle_path).success
    density = np.load(run.run_dir / "artifacts/final_density.npy", allow_pickle=False)
    assert density.shape == (120,)
    np.testing.assert_allclose(
        density, np.load(replay.run_dir / "artifacts/final_density.npy", allow_pickle=False)
    )
    metrics = json.loads((run.run_dir / "metrics.json").read_text(encoding="utf-8"))
    json.dumps(metrics, allow_nan=False)
    assert metrics["energy_diagnostic_convention"] == "graph_mass_stiffness_v1"
    assert metrics["diagnostics"]["device"] == "cpu"
    assert abs(metrics["diagnostics"]["relative_norm_error"]) < 1e-10
    with np.load(run.run_dir / "artifacts/graph_operator.npz", allow_pickle=False) as arrays:
        assert arrays["fractal_stiffness"].shape == (120, 120)
        assert arrays["fractal_mass_weights"].shape == (120,)
        active = arrays["fractal_active_vertex_ids"]
        np.testing.assert_array_equal(arrays["fractal_lattice_coordinates"],
                                      arrays["fractal_full_lattice_coordinates"][active])
    artifacts = CockpitArtifactService(root / "runs", root / "experiments")
    for profile in ("review", "state"):
        with zipfile.ZipFile(artifacts.run_bundle_profile_path(run.run_id, profile)) as archive:
            assert "artifacts/graph_operator.npz" in archive.namelist()
    local = CockpitService.create(output_root=root / "runs", hosted_demo=False)
    assert "sierpinski_graph_spectral.yaml" not in {c["name"] for c in local.list_configs()}
    hosted = CockpitService.create(output_root=root / "runs", hosted_demo=True)
    assert "sierpinski_graph_spectral.yaml" not in {c["name"] for c in hosted.list_configs()}
    try:
        hosted.replay_run(run.run_id)
    except HTTPException as exc:
        assert exc.status_code == 403 and "local-only" in exc.detail
    else:
        raise AssertionError("Hosted graph replay must be rejected")
    print(json.dumps({"run_dir": str(run.run_dir), "replay_dir": str(replay.run_dir),
                      "bundle_verified": True, "replay_verified": True,
                      "hosted_graph_disabled": True,
                      "rectangular_setup_graph_hidden": True}, indent=2))


if __name__ == "__main__":
    main()
