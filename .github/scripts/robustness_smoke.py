"""Exercise the local recorded-result pilot from an installed candidate wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

import qs_dmss.cockpit.robustness as robustness
from qs_dmss.cockpit.api import (
    BASELINE_SECURITY_HEADERS,
    CockpitService,
    LaunchCampaignRequest,
)
from qs_dmss.cockpit.robustness import CockpitRobustnessService
from qs_dmss.evidence.html_security import MAX_REPORT_CSP_BYTES, report_preview_headers
from qs_dmss.robustness import RobustnessRequest


def assert_streamed_bundle_ceiling(service, identifier):
    """Model growth in memory, without changing the generated campaign ZIP."""
    bundle = (service.experiments_root / identifier / "evidence_bundle.zip").resolve()
    original_open, original_stat = Path.open, Path.stat

    class CountedStream(BytesIO):
        consumed = 0

        def read(self, size=-1):
            chunk = super().read(size)
            self.consumed += len(chunk)
            return chunk

    stream = CountedStream(b"x" * 12)

    def opened(path, *args, **kwargs):
        return stream if path == bundle else original_open(path, *args, **kwargs)

    def stat(path, *args, **kwargs):
        return (
            SimpleNamespace(st_size=4)
            if path == bundle
            else original_stat(path, *args, **kwargs)
        )

    with (
        patch.object(robustness, "MAX_BUNDLE_BYTES", 8),
        patch.object(Path, "open", opened),
        patch.object(Path, "stat", stat),
    ):
        try:
            service.source(identifier)
        except ValueError as exc:
            assert str(exc) == "Source bundle exceeds the robustness resource limit"
        else:
            raise AssertionError(
                "A source growing beyond the byte ceiling was accepted"
            )
    assert stream.consumed == 9 and stream.closed


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
    items = service.analyses()["items"]
    assert [item["analysis_id"] for item in items] == [saved["analysis_id"]]
    assert items[0]["integrity_scope"] == "analysis_json_only"
    assert saved["sensitivity"]["case_count"] == 3
    with zipfile.ZipFile(service.bundle(saved["analysis_id"])) as archive:
        assert f"{saved['analysis_id']}/source/comparison.json" in archive.namelist()
    snapshot = service.bundle_snapshot(saved["analysis_id"])
    assert hashlib.sha256(snapshot).hexdigest() == saved["bundle_sha256"]
    with zipfile.ZipFile(BytesIO(snapshot)) as archive:
        assert f"{saved['analysis_id']}/analysis.json" in archive.namelist()
    assert (
        service.source(identifier)["source_fingerprint"] == source["source_fingerprint"]
    )
    assert_streamed_bundle_ceiling(service, identifier)
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
    malformed_report = root / "malformed-preview-fixture.html"
    malformed_bytes = b"<style>body{color:red}</style>\xff"
    malformed_report.write_bytes(malformed_bytes)
    headers = report_preview_headers(malformed_report, BASELINE_SECURITY_HEADERS)
    styles = next(
        directive.strip()
        for directive in headers["Content-Security-Policy"].split(";")
        if directive.strip().startswith("style-src")
    )
    assert styles == "style-src 'self' https://fonts.googleapis.com"
    assert malformed_report.read_bytes() == malformed_bytes
    unclosed_report = root / "unclosed-style-preview-fixture.html"
    unclosed_bytes = b"<style>" * 4096
    unclosed_report.write_bytes(unclosed_bytes)
    unclosed_headers = report_preview_headers(
        unclosed_report, BASELINE_SECURITY_HEADERS
    )
    assert unclosed_headers == headers
    assert unclosed_report.read_bytes() == unclosed_bytes
    for repeated in (True, False):
        report = root / f"style-budget-fixture-{repeated}.html"
        payload = (
            b"<style>x</style>" * 4096
            if repeated
            else b"".join(f"<style>/*{i}*/</style>".encode() for i in range(4096))
        )
        report.write_bytes(payload)
        policy = report_preview_headers(report, BASELINE_SECURITY_HEADERS)[
            "Content-Security-Policy"
        ]
        assert len(policy.encode("utf-8")) <= MAX_REPORT_CSP_BYTES == 8 * 1024
        style_policy = next(
            part.strip()
            for part in policy.split(";")
            if part.strip().startswith("style-src")
        )
        if repeated:
            assert style_policy.count("'sha256-") == 1
        else:
            assert style_policy == styles
        assert report.read_bytes() == payload
    print(
        json.dumps(
            {
                "campaign": identifier,
                "analysis": saved["analysis_id"],
                "original_scores_preserved": True,
                "empty_saved_list_supported": True,
                "summary_scope_explicit": True,
                "invalid_utf8_preview_fail_closed": True,
                "report_csp_budget_enforced": True,
                "unclosed_style_preview_fail_closed": True,
                "verified_bundle_snapshot": True,
                "source_bundle_stream_limit_enforced": True,
                "saved_reopened_exported": True,
                "hosted_disabled": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
