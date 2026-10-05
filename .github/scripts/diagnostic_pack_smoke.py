"""Installed-candidate contract smoke; never run against published v0.13.2."""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from qs_dmss.cli import main as core_cli
from qs_dmss.diagnostic_packs.admission import (
    PackError,
    admit_bytes,
    admit_pack,
    bundled_pack_path,
    sha256,
)
from qs_dmss.diagnostic_packs.evidence import json_bytes


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
    pack = admit_pack()
    input_hashes = pack.summary()["input_sha256"]
    code, inspected = capture(["diagnostic-packs", "inspect"])
    assert code == 0 and inspected["case_count"] == 12
    code, result = capture(
        ["diagnostic-packs", "run", "--output", str(root / "result")]
    )
    assert code == 0 and result["all_cases_pass"]
    code, integrity = capture(["diagnostic-packs", "verify", result["bundle"]])
    assert code == 0 and integrity["checked_files"] == 4
    bundle_hash = sha256(Path(result["bundle"]).read_bytes())
    assert bundle_hash == result["bundle_sha256"] == integrity["bundle_sha256"]
    code, rejected = capture(
        ["diagnostic-packs", "run", "--output", str(root / "result")]
    )
    assert code == 1 and rejected["success"] is False
    assert sha256(Path(result["bundle"]).read_bytes()) == bundle_hash
    assert admit_pack().summary()["input_sha256"] == input_hashes
    for name, data in (
        ("manifest.json", pack.manifest_bytes),
        ("cases.json", pack.cases_bytes),
    ):
        assert (root / "result/pack" / name).read_bytes() == data
        assert (bundled_pack_path() / name).read_bytes() == data
    invalid = pack.manifest.model_dump(mode="json")
    invalid["entry_point"] = "arbitrary.module:function"
    try:
        admit_bytes(json_bytes(invalid), pack.cases_bytes)
    except PackError:
        pass
    else:
        raise AssertionError("Executable actions must not be admitted.")
    saved = json.loads((root / "result/result.json").read_bytes())
    assert saved["numerical_outcome"] == "NOT_FALSIFIED_WITHIN_SCOPE"
    assert saved["scientific_validation_status"] == "NOT_ESTABLISHED"
    assert saved["human_disposition"] == "PENDING"
    assert saved["execution_policy"]["solver_evolution_called"] is False
    summary = {
        "success": True,
        "cases": 12,
        "bundle_sha256": bundle_hash,
        "data_only_admission": True,
        "source_bytes_preserved": True,
        "no_overwrite": True,
        "scientific_validation_status": "NOT_ESTABLISHED",
    }
    (root / "smoke.json").write_bytes(json_bytes(summary))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
