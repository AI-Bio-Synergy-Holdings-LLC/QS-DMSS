"""Isolated external-data CLI: no network acquisition or hosted execution."""

from __future__ import annotations

import json

from qs_dmss.external_data.contracts import AnalysisProfile, EvidenceError
from qs_dmss.external_data.evidence import run_analysis, verify_bundle


def register_commands(subparsers) -> None:
    root = subparsers.add_parser(
        "external-data", help="Bounded local educational-data evidence workflows."
    )
    commands = root.add_subparsers(dest="external_command", required=True)
    run = commands.add_parser(
        "dimuon",
        help="Import a local record-5203-format CSV and retain an analysis bundle.",
    )
    run.add_argument(
        "--input",
        required=True,
        help="Local literal CSV file; no URLs or automatic download.",
    )
    run.add_argument(
        "--output", required=True, help="New output directory under an existing parent."
    )
    run.add_argument(
        "--input-kind", required=True, choices=("synthetic", "cms-record-5203")
    )
    run.add_argument(
        "--expected-sha256", help="Optional caller-pinned input SHA-256 (recommended)."
    )
    run.add_argument("--bins", type=int, default=60)
    run.add_argument("--mass-min", type=float, default=2.0)
    run.add_argument("--mass-max", type=float, default=5.0)
    run.add_argument("--pt-min", type=float, default=0.0)
    run.add_argument(
        "--source-commit",
        help="Caller-declared full source commit; not independently verified.",
    )
    run.add_argument(
        "--candidate-wheel-sha256", help="Caller-declared full candidate wheel hash."
    )
    verify = commands.add_parser(
        "verify", help="Verify a bounded evidence ZIP without extracting it."
    )
    verify.add_argument("bundle")
    verify.add_argument(
        "--recompute",
        action="store_true",
        help="Also rerun the bounded analysis using the current implementation.",
    )


def dispatch(args) -> int:
    try:
        if args.external_command == "verify":
            result = verify_bundle(args.bundle, recompute=args.recompute)
        else:
            result = run_analysis(
                args.input,
                args.output,
                kind=args.input_kind,
                profile=AnalysisProfile(
                    args.bins, args.mass_min, args.mass_max, args.pt_min
                ),
                expected_sha256=args.expected_sha256,
                source_commit=args.source_commit,
                candidate_wheel_sha256=args.candidate_wheel_sha256,
            )
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except EvidenceError as exc:
        print(json.dumps({"success": False, "error": str(exc)}))
        return 1
