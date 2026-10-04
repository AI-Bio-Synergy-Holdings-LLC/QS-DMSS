"""Exercise the local recorded-result pilot from an installed candidate wheel."""

from __future__ import annotations

import argparse
import json
import zipfile
from copy import deepcopy
from pathlib import Path

from fastapi import HTTPException

from qs_dmss.cockpit.api import CockpitService, LaunchCampaignRequest
from qs_dmss.cockpit.robustness import CockpitRobustnessService
from qs_dmss.robustness import RobustnessRequest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, type=Path)
    root = parser.parse_args().output_root.resolve()
    cockpit = CockpitService.create(
        repo_root=root, output_root=root / "runs", hosted_demo=False
    )
    service = CockpitRobustnessService(cockpit.experiments_root)
    assert service.analyses() == {"items": []}
    assert not service._analysis_root().exists()
    config = deepcopy(
        cockpit.get_campaign_study_template("self-interaction-sweep")["template"][
            "config"
        ]
    )
    config["campaign"]["max_runs"] = 2
    config["campaign"]["dimensions"] = [{"path": "engine.g_int", "values": [0.0, 0.1]}]
    campaign = cockpit.launch_campaign(LaunchCampaignRequest(config=config))
    identifier = campaign["artifact"]["summary"]["experiment_id"]
    assert service.analyses() == {"items": []}
    assert not service._analysis_root().exists()
    source = service.source(identifier)
    payload = RobustnessRequest.model_validate(
        {
            "experiment_id": identifier,
            "source_fingerprint": source["source_fingerprint"],
            "profile": source["comparison"]["decision"]["profile"],
            "preferred_run_id": source["comparison"]["decision"]["recommended_run_id"],
            "weight_values": [0.0, 1.0, 4.0],
        }
    )
    preview = service.preview(payload)
    assert preview["current"]["rows"] == source["comparison"]["rows"]
    saved = service.save(payload)
    assert service.load(saved["analysis_id"]) == saved
    assert [item["analysis_id"] for item in service.analyses()["items"]] == [
        saved["analysis_id"]
    ]
    assert saved["sensitivity"]["case_count"] == 3
    with zipfile.ZipFile(service.bundle(saved["analysis_id"])) as archive:
        assert f"{saved['analysis_id']}/source/comparison.json" in archive.namelist()
    assert (
        service.source(identifier)["source_fingerprint"] == source["source_fingerprint"]
    )
    hosted = CockpitRobustnessService(cockpit.experiments_root, True)
    try:
        hosted.save(payload)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("Hosted robustness pilot must stay disabled")
    print(
        json.dumps(
            {
                "campaign": identifier,
                "analysis": saved["analysis_id"],
                "original_scores_preserved": True,
                "empty_saved_list_supported": True,
                "saved_reopened_exported": True,
                "hosted_disabled": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
