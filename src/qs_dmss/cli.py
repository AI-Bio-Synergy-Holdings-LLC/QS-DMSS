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

    benchmarks_parser = subparsers.add_parser(
        "benchmarks",
        help="List and validate packaged benchmark scenarios.",
    )
    benchmarks_subparsers = benchmarks_parser.add_subparsers(
        dest="benchmarks_command",
        required=True,
    )

    benchmarks_subparsers.add_parser(
        "list",
        help="List packaged benchmark scenario names.",
    )

    benchmarks_validate_parser = benchmarks_subparsers.add_parser(
        "validate",
        help="Run benchmark scenarios and validate evidence, metrics, and replay.",
    )
    benchmarks_validate_parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="Scenario name to validate. Repeat to validate multiple scenarios.",
    )
    benchmarks_validate_parser.add_argument(
        "--output-root",
        help="Directory for benchmark run, replay, and summary outputs.",
    )
    benchmarks_validate_parser.add_argument(
        "--skip-replay",
        action="store_true",
        help="Skip replay validation and only check fresh benchmark runs.",
    )

    showcase_parser = subparsers.add_parser(
        "showcase",
        help="Run reviewer-facing canonical simulation showcase scenarios.",
    )
    showcase_subparsers = showcase_parser.add_subparsers(
        dest="showcase_command",
        required=True,
    )

    showcase_subparsers.add_parser(
        "list",
        help="List packaged simulation showcase scenario names.",
    )

    showcase_run_parser = showcase_subparsers.add_parser(
        "run",
        help="Run the canonical simulation showcase and write reviewer artifacts.",
    )
    showcase_run_parser.add_argument(
        "--scenario",
        default="canonical-simulation",
        help="Packaged showcase scenario name to run.",
    )
    showcase_run_parser.add_argument(
        "--output-root",
        help="Directory for showcase run, replay, plot, table, and report outputs.",
    )
    showcase_run_parser.add_argument(
        "--skip-replay",
        action="store_true",
        help="Skip replay validation and only generate fresh-run showcase artifacts.",
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

    campaigns_parser = subparsers.add_parser(
        "campaigns",
        help="Launch template-defined decision campaigns.",
    )
    campaigns_subparsers = campaigns_parser.add_subparsers(
        dest="campaigns_command",
        required=True,
    )

    campaigns_run_parser = campaigns_subparsers.add_parser(
        "run",
        help="Launch the campaign defined in a YAML config file.",
    )
    campaigns_run_parser.add_argument("config", help="Path to a YAML config file.")
    campaigns_run_parser.add_argument(
        "--output-root",
        help="Optional run output directory override used for generated campaign runs.",
    )

    campaigns_demo_parser = campaigns_subparsers.add_parser(
        "run-demo",
        help="Launch the bundled demo decision campaign.",
    )
    campaigns_demo_parser.add_argument(
        "--output-root",
        help="Optional run output directory override used for generated campaign runs.",
    )

    executors_parser = subparsers.add_parser(
        "executors",
        help="Generate review-only executor request artifacts.",
    )
    executors_subparsers = executors_parser.add_subparsers(
        dest="executors_command",
        required=True,
    )

    slurm_dry_run_parser = executors_subparsers.add_parser(
        "slurm-dry-run",
        help="Generate a Slurm request bundle without submitting to a scheduler.",
    )
    slurm_dry_run_parser.add_argument("config", help="Path to a YAML config file.")
    slurm_dry_run_parser.add_argument(
        "--request-root",
        help="Optional directory for the dry-run job registry and request bundle.",
    )
    slurm_dry_run_parser.add_argument(
        "--job-name",
        default="qs-dmss-dry-run",
        help="SBATCH job name for the generated script.",
    )
    slurm_dry_run_parser.add_argument(
        "--time",
        dest="time_limit",
        default="00:10:00",
        help="SBATCH time limit for the generated script.",
    )
    slurm_dry_run_parser.add_argument(
        "--nodes",
        type=int,
        default=1,
        help="SBATCH node count for the generated script.",
    )
    slurm_dry_run_parser.add_argument(
        "--ntasks",
        type=int,
        default=1,
        help="SBATCH task count for the generated script.",
    )
    slurm_dry_run_parser.add_argument(
        "--cpus-per-task",
        type=int,
        default=1,
        help="SBATCH CPUs per task for the generated script.",
    )
    slurm_dry_run_parser.add_argument(
        "--mem",
        default="2G",
        help="SBATCH memory directive for the generated script.",
    )
    slurm_dry_run_parser.add_argument(
        "--partition",
        help="Optional SBATCH partition directive.",
    )
    slurm_dry_run_parser.add_argument(
        "--account",
        help="Optional SBATCH account directive.",
    )
    slurm_dry_run_parser.add_argument(
        "--qos",
        help="Optional SBATCH QoS directive.",
    )
    slurm_dry_run_parser.add_argument(
        "--python-module",
        help="Optional environment module to load before running qs-dmss.",
    )
    slurm_dry_run_parser.add_argument(
        "--qs-dmss-command",
        default="qs-dmss",
        help="Command used inside the generated Slurm script.",
    )
    slurm_dry_run_parser.add_argument(
        "--slurm-output-root",
        default="runs",
        help="Output root argument embedded in the generated Slurm script.",
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

    if args.command == "benchmarks":
        from qs_dmss.benchmarks import (
            list_benchmark_scenarios,
            validate_benchmark_scenarios,
        )

        if args.benchmarks_command == "list":
            for scenario_name in list_benchmark_scenarios():
                print(scenario_name)
            return 0

        if args.benchmarks_command == "validate":
            try:
                report = validate_benchmark_scenarios(
                    scenarios=args.scenarios,
                    output_root=args.output_root,
                    replay=not args.skip_replay,
                )
            except (FileNotFoundError, ValueError) as exc:
                print(exc)
                return 1

            for scenario in report["scenarios"]:
                status = "passed" if scenario["success"] else "failed"
                print(f"Benchmark {status}: {scenario['scenario']}")
                for check in scenario["checks"]:
                    if not check["success"]:
                        print(f"- {check['name']}: {check['detail']}")
            print(f"Report: {report['report_path']}")
            print(f"Reviewer summary: {report['markdown_report_path']}")
            return 0 if report["success"] else 1

    if args.command == "showcase":
        from qs_dmss.showcase import (
            list_showcase_scenarios,
            run_simulation_showcase,
        )

        if args.showcase_command == "list":
            for scenario_name in list_showcase_scenarios():
                print(scenario_name)
            return 0

        if args.showcase_command == "run":
            try:
                report = run_simulation_showcase(
                    output_root=args.output_root,
                    scenario=args.scenario,
                    replay=not args.skip_replay,
                )
            except (FileNotFoundError, ValueError) as exc:
                print(exc)
                return 1

            status = "passed" if report["success"] else "failed"
            print(f"Simulation showcase {status}: {report['scenario']}")
            print(f"Run complete: {report['run']['run_dir']}")
            print(f"Evidence bundle: {report['run']['bundle_path']}")
            if report.get("replay"):
                print(f"Replay complete: {report['replay']['run_dir']}")
            print(f"Report: {report['report_path']}")
            print(f"Reviewer summary: {report['markdown_report_path']}")
            return 0 if report["success"] else 1

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
                recommendation = ""
                if item.get("decision_available"):
                    recommendation = (
                        f" | recommended {item.get('recommended_run_id')} "
                        f"({item.get('decision_status')})"
                    )
                print(
                    f"- {item['experiment_id']} | {item['label']} | "
                    f"{item['run_count']} runs | {item['bundle_size_label']}{recommendation}"
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
            if detail.get("decision", {}).get("available"):
                print(f"Recommended run: {detail['decision']['recommended_run_id']}")
                print(f"Decision status: {detail['decision']['status']}")
                print(f"Reason: {detail['decision']['reason']}")
            print(f"Bundle: {service.experiments_root / detail['summary']['experiment_id'] / 'evidence_bundle.zip'}")
            return 0

    if args.command == "campaigns":
        from qs_dmss.cockpit.api import CockpitService, LaunchCampaignRequest
        from qs_dmss.io.config import load_config

        service = CockpitService.create(output_root=args.output_root)
        if args.campaigns_command == "run":
            config_path = Path(args.config).resolve()
        elif args.campaigns_command == "run-demo":
            config_path = demo_config_path()
        else:
            parser.error(f"Unsupported campaigns command: {args.campaigns_command}")
            return 2

        try:
            payload = service.launch_campaign(
                LaunchCampaignRequest(
                    config=load_config(config_path).to_dict(),
                    source_name=config_path.name,
                )
            )
        except (HTTPException, ValueError, FileNotFoundError) as exc:
            detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
            if isinstance(detail, dict):
                print(detail.get("message", "Campaign failed"))
                if detail.get("error"):
                    print(f"Error: {detail['error']}")
                if detail.get("experiment_id"):
                    print(f"Failed campaign artifact: {detail['experiment_id']}")
                if detail.get("bundle"):
                    print(f"Bundle: {detail['bundle']}")
            else:
                print(detail)
            return 1

        print(f"Campaign saved: {payload['campaign']['id']}")
        print(f"Label: {payload['campaign']['label']}")
        print(f"Planned runs: {payload['campaign']['planned_run_count']}")
        if payload.get("comparison", {}).get("decision", {}).get("available"):
            print(f"Recommended run: {payload['comparison']['decision']['recommended_run_id']}")
            print(f"Decision status: {payload['comparison']['decision']['status']}")
            print(f"Reason: {payload['comparison']['decision']['reason']}")
        print(f"Bundle: {service.experiments_root / payload['campaign']['id'] / 'evidence_bundle.zip'}")
        return 0

    if args.command == "executors":
        if args.executors_command == "slurm-dry-run":
            from qs_dmss.execution import (
                DryRunSlurmExecutor,
                ExecutionJobSpec,
                LocalJobRegistry,
                SlurmDryRunOptions,
            )
            from qs_dmss.io.config import load_config

            config_path = Path(args.config).resolve()
            try:
                config = load_config(config_path)
            except (FileNotFoundError, ValueError) as exc:
                print(exc)
                return 1

            request_root = (
                Path(args.request_root).resolve()
                if args.request_root
                else Path.cwd() / "jobs"
            )
            executor = DryRunSlurmExecutor(
                LocalJobRegistry(request_root),
                options=SlurmDryRunOptions(
                    job_name=args.job_name,
                    time_limit=args.time_limit,
                    nodes=args.nodes,
                    ntasks=args.ntasks,
                    cpus_per_task=args.cpus_per_task,
                    memory=args.mem,
                    partition=args.partition,
                    account=args.account,
                    qos=args.qos,
                    python_module=args.python_module,
                    qs_dmss_command=args.qs_dmss_command,
                    output_root=args.slurm_output_root,
                ),
            )
            handle = executor.submit(
                ExecutionJobSpec(
                    config=config.to_dict(),
                    source_name=config_path.name,
                    output_root=Path(args.slurm_output_root),
                    labels=("dry-run", "slurm"),
                    metadata={"source_config_path": str(config_path)},
                )
            )
            result = executor.collect(handle)
            request_bundle = next(
                artifact
                for artifact in result.artifacts
                if artifact.role == "request_bundle" and artifact.path is not None
            )
            request_dir = request_bundle.path.parent
            print("Slurm dry-run request bundle created.")
            print("No scheduler job was submitted.")
            print(f"Job ID: {handle.job_id}")
            print(f"Job record: {handle.status_uri}")
            print(f"Request bundle: {request_bundle.path}")
            print(f"Review directory: {request_dir}")
            print(f"Review script before any manual submission: {request_dir / 'slurm-job.sh'}")
            return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
