"""Installed-candidate synthetic acceptance; no CERN download or scientific claim."""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from qs_dmss.cli import main as core_cli
from qs_dmss.external_data.storage import json_bytes, sha256


def capture(arguments):
    output = io.StringIO()
    with redirect_stdout(output):
        code = core_cli(arguments)
    return code, json.loads(output.getvalue())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=False)
    # Original synthetic, back-to-back four-vectors; exactly 3 GeV pair mass.
    raw = (
        "Run,Event,type1,E1,px1,py1,pz1,pt1,eta1,phi1,Q1,type2,E2,px2,py2,pz2,pt2,eta2,phi2,Q2\n"
        "1,1,G,1.5,0.5,0,0,0.5,0,0,1,T,1.5,-0.5,0,0,0.5,0,3.14159265,-1\n"
    ).encode("ascii")
    source = root / "synthetic.csv"
    source.write_bytes(raw)
    arguments = [
        "external-data",
        "dimuon",
        "--input",
        str(source),
        "--output",
        str(root / "analysis"),
        "--input-kind",
        "synthetic",
        "--expected-sha256",
        sha256(raw),
    ]
    code, result = capture(arguments)
    assert code == 0 and result["selected_events"] == 1, result
    code, checked = capture(
        ["external-data", "verify", result["bundle"], "--recompute"]
    )
    assert code == 0 and checked["recomputation"] == "MATCHED_CURRENT_IMPLEMENTATION", (
        checked
    )
    assert result["bundle_sha256"] == checked["bundle_sha256"]
    analysis = json.loads((root / "analysis/analysis.json").read_bytes())
    assert analysis["mass_summary_GeV"]["mean"] == 3
    assert analysis["scientific_validation_status"] == "NOT_ESTABLISHED"
    assert analysis["human_disposition"] == "PENDING"
    assert analysis["ai_advice"] is None
    assert source.read_bytes() == raw == (root / "analysis/input.csv").read_bytes()
    before = Path(result["bundle"]).read_bytes()
    code, refused = capture(arguments)
    assert code == 1 and refused["success"] is False
    assert Path(result["bundle"]).read_bytes() == before
    summary = {
        "success": True,
        "input_kind": "synthetic",
        "bundle_sha256": checked["bundle_sha256"],
        "recomputation": checked["recomputation"],
        "source_preserved": True,
        "no_overwrite": True,
        "scientific_validation_status": "NOT_ESTABLISHED",
    }
    (root / "smoke.json").write_bytes(json_bytes(summary))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
