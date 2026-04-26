from __future__ import annotations

import argparse
from pathlib import Path

from fastapi import HTTPException

from qs_dmss.app import execute_run_from_path, replay_run
from qs_dmss.evidence.verify import verify_run_path
from qs_dmss.paths import demo_config_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qs-dmss",
        description="QS-DMSS CLI for deterministic runs, evidence bundling, and verification.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a config and emit an evidence bundle.")
    run_parser.add_argument("config", help="Path to a YAML config file.")
    run_parser.add_argument(
        "--output-root",
        help="Optional output directory override for generated runs.",
    )

    demo_parser = subparsers.add_parser(
        "run-demo",
        help="Run the bundled demo config from the installed package or repo checkout.",
    )
    demo_parser.add_argument(
        "--output-root",
        help="Optional output directory override for generated runs.",
    )

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a run directory or evidence bundle zip.",
    )
    verify_parser.add_argument("path", help="Path to a run directory or evidence bundle zip.")

    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay a prior run using the captured config and seed.",
    )
    replay_parser.add_argument("path", help="Path to an existing run directory.")
    replay_parser.add_argument(
        "--output-root",
        help="Optional output directory override for replayed runs.",
    )

    cockpit_parser = subparsers.add_parser(
        "cockpit",
        help="Start the local QS-DMSS browser cockpit.",
    )
    cockpit_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind the cockpit server to.",
    )
    cockpit_parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind the cockpit server to.",
    )
    cockpit_parser.add_argument(
        "--output-root",
        help="Optional run output directory override for the cockpit.",
    )

    experiments_parser = subparsers.add_parser(
        "experiments",
        help="List and export experiment-level comparison bundles.",
    )
    experiments_subparsers = experiments_parser.add_subparsers(
        dest="experiments_command",
        required=True,
    )

    experiments_list_parser = experiments_subparsers.add_parser(
        "list",
        help="List persisted experiment artifacts.",
    )
    experiments_list_parser.add_argument(
        "--output-root",
        help="Optional run output directory override used to locate sibling experiments.",
    )

    experiments_export_parser = experiments_subparsers.add_parser(
        "export",
        help="Persist selected runs as an experiment evidence bundle.",
    )
    experiments_export_parser.add_argument(
        "run_ids",
        nargs="+",
        help="Run IDs to include in the saved experiment artifact.",
    )
    experiments_export_parser.add_argument(
        "--label",
        help="Optional experiment label override.",
    )
    experiments_export_parser.add_argument(
        "--output-root",
        help="Optional run output directory override used to locate sibling experiments.",
    )

    return parser


def _print_verification_result(path: Path) -> int:
    result = verify_run_path(path)
    if result.success:
        print(f"Verification passed for {path}")
        print(f"Checked files: {result.checked_files}")
        return 0

    print(f"Verification failed for {path}")
    for error in result.errors:
        print(f"- {error}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        outputs = execute_run_from_path(
            config_path=args.config,
            output_root=args.output_root,
        )
        print(f"Run complete: {outputs.run_dir}")
        print(f"Evidence bundle: {outputs.bundle_path}")
        return _print_verification_result(outputs.run_dir)

    if args.command == "run-demo":
        demo_path = demo_config_path()
        outputs = execute_run_from_path(
            config_path=demo_path,
            output_root=args.output_root,
        )
        print(f"Demo config: {demo_path}")
        print(f"Run complete: {outputs.run_dir}")
        print(f"Evidence bundle: {outputs.bundle_path}")
        return _print_verification_result(outputs.run_dir)

    if args.command == "verify":
        return _print_verification_result(Path(args.path).resolve())

    if args.command == "replay":
        outputs = replay_run(
            run_dir=args.path,
            output_root=args.output_root,
        )
        print(f"Replay complete: {outputs.run_dir}")
        print(f"Evidence bundle: {outputs.bundle_path}")
        return _print_verification_result(outputs.run_dir)

    if args.command == "cockpit":
        from qs_dmss.cockpit.server import run_cockpit_server

        print(f"Starting QS-DMSS cockpit at http://{args.host}:{args.port}")
        return run_cockpit_server(
            host=args.host,
            port=args.port,
            output_root=args.output_root,
        )

    if args.command == "experiments":
        from qs_dmss.cockpit.api import CockpitService, CreateExperimentRequest

        service = CockpitService.create(output_root=args.output_root)

        if args.experiments_command == "list":
            items = service.list_experiments()
            if not items:
                print(f"No experiment artifacts found under {service.experiments_root}")
                return 0

            print(f"Experiment artifacts under {service.experiments_root}:")
            for item in items:
                print(
                    f"- {item['experiment_id']} | {item['label']} | "
                    f"{item['run_count']} runs | {item['bundle_size_label']}"
                )
            return 0

        if args.experiments_command == "export":
            try:
                detail = service.create_experiment(
                    CreateExperimentRequest(
                        run_ids=args.run_ids,
                        label=args.label,
                    )
                )
            except HTTPException as exc:
                print(exc.detail)
                return 1

            print(f"Experiment saved: {detail['summary']['experiment_id']}")
            print(f"Label: {detail['summary']['label']}")
            print(f"Bundle: {service.experiments_root / detail['summary']['experiment_id'] / 'evidence_bundle.zip'}")
            return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
