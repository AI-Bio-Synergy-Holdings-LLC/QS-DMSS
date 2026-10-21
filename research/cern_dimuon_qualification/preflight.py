"""Synthetic preflight only. No --input, dataset downloader or pilot runner."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path

from .contract import (
    BUCKETS,
    INPUT_SHA256,
    LOG_BYTES,
    SCIENTIFIC,
    TOTAL_BYTES,
    Hold,
    checked_protocol,
    json_bytes,
)
from .retention import Store, digest, read_regular
from .supervision import run_worker


def synthetic_csv():
    # Original fixture, never a copied CMS event or relabelled real snapshot.
    header = "Run,Event,type1,E1,px1,py1,pz1,pt1,eta1,phi1,Q1,type2,E2,px2,py2,pz2,pt2,eta2,phi2,Q2"
    rows = [
        "1,1,G,1.5,0.5,0,0,0.5,0,0,1,T,1.5,-0.5,0,0,0.5,0,3,-1",
        "1,2,G,2,0.5,0,0,0.5,0,0,1,T,2,-0.5,0,0,0.5,0,3,-1",
        "1,3,G,1.5,0.5,0,0,0.5,2.4,0,1,T,1.5,-0.5,0,0,0.5,0,3,-1",
    ]
    raw = (header + "\n" + "\n".join(rows) + "\n").encode("ascii")
    if hashlib.sha256(raw).hexdigest() == INPUT_SHA256:
        raise Hold("Actual snapshot is forbidden in synthetic preflight.")
    return raw


def worker(mode):
    if mode == "timeout":
        print("synthetic timeout control started", flush=True)
        time.sleep(10)
    elif mode == "overflow":
        sys.stdout.buffer.write(b"X" * (LOG_BYTES + 1))
        sys.stdout.buffer.flush()
    elif mode == "drift":
        # Only the explicitly created disposable copy, never tracked code.
        target = Path("drift-target.txt")
        if target.read_bytes() != b"synthetic drift input\n":
            raise Hold("Synthetic drift fixture identity changed prematurely.")
        target.write_bytes(b"synthetic drift changed\n")
        print("synthetic source drift exercised", flush=True)
    elif mode == "normal":
        from .candidate import probe
        from .comparison import compare
        from .reference import parse

        raw = synthetic_csv()
        if read_regular(Path("synthetic.csv"), 4096) != raw:
            raise Hold("Retained synthetic fixture differs from the built-in control.")
        result, views = probe(raw, "synthetic")
        comparison = compare(parse(raw), result, views)
        print(
            json_bytes(
                {
                    "observation_label": "SYNTHETIC_NOT_COLLISION_DATA",
                    "synthetic_input_sha256": hashlib.sha256(raw).hexdigest(),
                    "qualification_outcome": "NOT_EXECUTED",
                    "comparison": comparison,
                }
            ).decode(),
            end="",
        )
        if comparison["comparison_outcome"] != "MATCH":
            return 1
    return 0


def copy_helpers(store):
    source = Path(__file__).resolve().parent
    repository = source.parents[1]
    before = {}
    paths = [
        path for path in sorted(source.iterdir()) if path.suffix in {".py", ".json"}
    ]
    paths.extend(
        repository / name
        for name in (
            "docs/cern-dimuon-numerical-reconciliation.md",
            "tests/test_cern_dimuon_qualification.py",
        )
    )
    for path in paths:
        data = read_regular(path, BUCKETS["records/source"])
        name = path.relative_to(repository).as_posix()
        before[name] = hashlib.sha256(data).hexdigest()
        store.write("records/source", name, data)
    if any(
        digest(repository / name, BUCKETS["records/source"]) != value
        for name, value in before.items()
    ):
        raise Hold("Original helpers drifted during snapshot creation.")
    store.write("records/source", "drift-target.txt", b"synthetic drift input\n")
    store.write("records/source", "drift-before.txt", b"synthetic drift input\n")
    store.write("records/source", "synthetic.csv", synthetic_csv())
    return before


def run_preflight(output, candidate_wheel=None):
    store = Store(output)
    try:
        protocol_identity = checked_protocol()
        sources = copy_helpers(store)
        identity = {"state": "NOT_CHECKED"}
        if candidate_wheel is not None:
            from .candidate import wheel_identity

            repository = Path(__file__).resolve().parents[2]
            identity = {
                "state": "CHECKED",
                **wheel_identity(candidate_wheel, repository),
            }
            store.write(
                "wheel",
                "candidate.whl",
                read_regular(Path(candidate_wheel), BUCKETS["wheel"]),
            )
        environment = {
            "python": sys.version,
            "interpreter_path": sys.executable,
            "interpreter_prefix": sys.prefix,
            "numpy_installation_root": str(
                importlib.metadata.distribution("numpy").locate_file("")
            ),
            "platform": platform.system(),
            "numpy": importlib.metadata.version("numpy"),
            "interpreter_and_dependency_caches": "Outside evidence-root budget; not copied or claimed as retained evidence",
            "future_pilot_environment_lock": "NOT_FROZEN",
        }
        store.write("records/source", "environment.json", json_bytes(environment))
        controls = {}
        for mode in ("normal", "timeout", "overflow", "drift"):
            controls[mode] = run_worker(
                store, mode, timeout_seconds=1 if mode == "timeout" else 300
            )
        normal = controls["normal"]
        if normal["state"] != "PASSED":
            raise Hold("Synthetic numerical control did not pass.")
        raw_log = read_regular(store.root / "records/logs/normal.log", LOG_BYTES)
        normal_record = json.loads(raw_log[: normal["log_bytes_used"]])
        if (
            normal_record["qualification_outcome"] != "NOT_EXECUTED"
            or normal_record["comparison"]["comparison_outcome"] != "MATCH"
        ):
            raise Hold("Synthetic control result differs from the preflight contract.")
        expected = {
            "timeout": "TIMEOUT",
            "overflow": "LOG_LIMIT",
            "drift": "SOURCE_DRIFT",
        }
        if any(
            controls[name]["state"] != "HOLD" or controls[name]["reason"] != reason
            for name, reason in expected.items()
        ):
            raise Hold("An expected failure-retention control did not refuse safely.")
        if any(
            digest(
                Path(__file__).resolve().parents[2] / name, BUCKETS["records/source"]
            )
            != value
            for name, value in sources.items()
        ):
            raise Hold("Original helpers drifted during preflight.")
        result = {
            "preflight_outcome": "PREFLIGHT_PASSED",
            "qualification_outcome": "NOT_EXECUTED",
            "scope": "Synthetic controls only; no CERN snapshot was opened or analyzed",
            "candidate_identity": identity,
            "source_sha256": sources,
            "protocol_identity": protocol_identity,
            "synthetic_comparison": normal_record,
            "controls": controls,
            "pilot_execution_ready": False,
            "remaining_gates": [
                "Separate owner execution authorization",
                "Reviewed helper identities",
                "Frozen Windows/Linux CPython 3.12 dependency manifests",
            ]
            + (
                []
                if candidate_wheel is not None
                else ["Qualified wheel and pinned-source identity check"]
            ),
            "total_ceiling_bytes": TOTAL_BYTES,
            **SCIENTIFIC,
        }
        store.write("records/comparison", "preflight.json", json_bytes(result))
        store.finish("supervisor", {"state": "PREFLIGHT_PASSED"})
        result["inventory"] = store.inventory()
        return result
    except BaseException as exc:
        reason = (
            str(exc)
            if isinstance(exc, Hold)
            else "Preflight interrupted or failed; no arbitrary exception text retained."
        )
        store.finish("supervisor", {"state": "HOLD", "reason": reason})
        # Never clean failed roots or pretend partially retained output is complete.
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise Hold(reason) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    parser.add_argument("--candidate-wheel")
    parser.add_argument(
        "--worker",
        choices=("normal", "timeout", "overflow", "drift"),
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    if args.worker:
        if args.output or args.candidate_wheel:
            parser.error("Synthetic workers do not accept file arguments.")
        snapshot = Path(__file__).resolve().parents[2]
        if (
            snapshot != Path.cwd().resolve()
            or snapshot.name != "source"
            or snapshot.parent.name != "records"
        ):
            parser.error("Workers require an active reserved source snapshot.")
        try:
            final = json.loads(
                read_regular(snapshot.parent / "logs/supervisor-final.json", 8192)
            )
        except (Hold, OSError, ValueError):
            parser.error("Worker supervisor reservation is unavailable.")
        if final.get("state") != "NOT_EXECUTED":
            parser.error("Closed preflight roots cannot restart workers.")
        return worker(args.worker)
    if not args.output:
        parser.error("--output NEW_DIRECTORY is required for synthetic preflight")
    try:
        result = run_preflight(args.output, args.candidate_wheel)
        print(
            json_bytes(
                {
                    "preflight_outcome": result["preflight_outcome"],
                    "qualification_outcome": "NOT_EXECUTED",
                    "pilot_execution_ready": False,
                    "inventory": result["inventory"],
                    **SCIENTIFIC,
                }
            ).decode(),
            end="",
        )
        return 0
    except (Hold, OSError):
        print(
            json_bytes(
                {
                    "preflight_outcome": "HOLD",
                    "qualification_outcome": "NOT_EXECUTED",
                    "pilot_execution_ready": False,
                    "reason": "Preflight refused; preserve any new output root and inspect its bounded receipts.",
                    **SCIENTIFIC,
                }
            ).decode(),
            end="",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
