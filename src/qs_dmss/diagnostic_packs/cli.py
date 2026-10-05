"""Isolated command family; no new cockpit routes or hosted capability."""

from __future__ import annotations

import json

from qs_dmss.diagnostic_packs.admission import PackError, admit_pack
from qs_dmss.diagnostic_packs.evidence import export_result, verify_bundle
from qs_dmss.diagnostic_packs.fft import evaluate_pack


def register_commands(subparsers) -> None:
    packs = subparsers.add_parser(
        "diagnostic-packs", help="Inspect and run closed data-only diagnostic packs."
    )
    commands = packs.add_subparsers(dest="pack_command", required=True)
    for command in ("inspect", "run"):
        child = commands.add_parser(command)
        child.add_argument(
            "--pack",
            help="Literal pack directory; defaults to bundled FFT reference pack.",
        )
        if command == "run":
            child.add_argument(
                "--output",
                required=True,
                help="New output directory; parent must exist.",
            )
            child.add_argument(
                "--source-commit", help="Caller-declared 40-character candidate commit."
            )
            child.add_argument(
                "--candidate-wheel-sha256", help="Caller-declared candidate wheel hash."
            )
    verify = commands.add_parser(
        "verify", help="Verify exported content hashes without rerunning diagnostics."
    )
    verify.add_argument("bundle")


def dispatch(args) -> int:
    try:
        if args.pack_command == "verify":
            result = verify_bundle(args.bundle)
        else:
            pack = admit_pack(args.pack)
            if args.pack_command == "inspect":
                result = {**pack.summary(), "cases": pack.cases.model_dump(mode="json")}
            else:
                result = export_result(
                    pack,
                    evaluate_pack(pack),
                    args.output,
                    source_commit=args.source_commit,
                    candidate_wheel_sha256=args.candidate_wheel_sha256,
                )
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
        return 0 if result.get("all_cases_pass", True) else 1
    except PackError as exc:
        print(json.dumps({"success": False, "error": str(exc)}))
        return 1
