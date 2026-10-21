"""Fixed serial, synthetic-only Windows/Linux rehearsal; no CERN input option."""

import argparse
import io
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

from .candidate import IDENTITY_MODULES
from .contract import (
    BUCKETS,
    COMMIT,
    INPUT_SHA256,
    LOG_BYTES,
    PROFILE,
    SCIENTIFIC,
    WHEEL_SHA256,
    Hold,
    checked_protocol,
    json_bytes,
)
from .retention import Store, digest, literal, read_regular
from .runtime import WINDOWS_LAUNCHER_SHA256, admit_environment, load_locks, sha

STAGES = ("windows", "linux", "comparison", "control")
ENV_BYTES = 16 * 1024
ROWS = 20000
ROOT = Path(__file__).resolve().parents[2]
WHEEL_NAME = "qs_dmss-0.14.0-py3-none-any.whl"


def synthetic_fixture(rows=ROWS):
    if type(rows) is not int or not 4 <= rows <= 25000:
        raise Hold("Synthetic fixture row bound refused.")
    header = "Run,Event,type1,E1,px1,py1,pz1,pt1,eta1,phi1,Q1,type2,E2,px2,py2,pz2,pt2,eta2,phi2,Q2"
    lines = [header]
    for index in range(rows):
        token = str(1505 + 50 * (index % 20))
        energy = token[:-3] + "." + token[-3:]
        if index in (0, 1):
            energy = "1" if index == 0 else "2.5"
        kind = "T" if index == 3 else "G"
        eta = "2.4" if index == 2 else "0"
        lines.append(
            f"900000001,{index + 1},{kind},{energy},0.5,0,0,0.5,{eta},0,1,T,{energy},-0.5,0,0,0.5,0,3,-1"
        )
    raw = ("\n".join(lines) + "\n").encode("ascii")
    if sha(raw) == INPUT_SHA256 or len(raw) > BUCKETS["input"]:
        raise Hold("Synthetic fixture identity or size refused.")
    return raw


def source_names(repository):
    helpers = repository / "research/cern_dimuon_qualification"
    return sorted(
        [
            path.relative_to(repository).as_posix()
            for path in helpers.iterdir()
            if path.suffix in {".py", ".json"}
        ]
        + [
            "research/cern_dimuon_qualification/environments/v1/" + name
            for name in (
                "manifest.json",
                "windows-cp312.lock.txt",
                "linux-cp312.lock.txt",
            )
        ]
        + [
            "tests/test_cern_dimuon_qualification.py",
            "tests/test_cern_dimuon_environment_locks.py",
            "tests/test_cern_dimuon_readiness.py",
            "docs/cern-dimuon-execution-readiness.md",
        ]
    )


def source_plan(files, modules):
    index = {
        "candidate_identity": {
            "wheel_sha256": WHEEL_SHA256,
            "candidate_commit": COMMIT,
            "module_sha256": modules,
        },
        "files": {
            name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in files.items()
        },
        "fixture_rows": ROWS,
        "fixture_sha256": sha(synthetic_fixture()),
        "scope": "Complete active helper/lock/test/guide snapshot; historical review records remain external and unchanged",
        "qualification_outcome": "NOT_EXECUTED",
        **SCIENTIFIC,
    }
    raw_index = json_bytes(index)
    source_bytes = sum(map(len, files.values())) + len(raw_index) + 4 * ENV_BYTES
    if source_bytes > BUCKETS["records/source"]:
        raise Hold(
            "Complete sources, locks and reserved environment receipts do not fit."
        )
    return raw_index, source_bytes


def prepare(store, repository, wheel):
    checked_protocol()
    load_locks()
    files = {
        name: read_regular(repository / name, BUCKETS["records/source"])
        for name in source_names(repository)
    }
    wheel_raw = read_regular(wheel, BUCKETS["wheel"])
    if sha(wheel_raw) != WHEEL_SHA256:
        raise Hold("Rehearsal wheel differs from the approved candidate.")
    modules = {}
    with zipfile.ZipFile(io.BytesIO(wheel_raw)) as archive:
        for member in IDENTITY_MODULES.values():
            saved = archive.read(member)
            pinned = subprocess.run(
                ["git", "show", f"{COMMIT}:src/{member}"],
                cwd=repository,
                check=True,
                capture_output=True,
                timeout=10,
            ).stdout
            if saved != pinned:
                raise Hold("Candidate differs from the pinned Git objects.")
            modules[member] = sha(pinned)
    raw_index, source_bytes = source_plan(files, modules)
    for name, raw in files.items():
        store.write("records/source", name, raw)
    store.write("records/source", "source-index.json", raw_index)
    for target in ("windows", "linux"):
        for phase in ("before", "after"):
            placeholder = json_bytes(
                {"state": "NOT_EXECUTED", "target": target, "phase": phase}
            )
            store.write(
                "records/source",
                f"{target}-environment-{phase}.json",
                placeholder.ljust(ENV_BYTES, b" "),
            )
    store.write("wheel", WHEEL_NAME, wheel_raw)
    store.write("input", "synthetic.csv", synthetic_fixture())
    if any(
        digest(repository / name, len(raw)) != sha(raw) for name, raw in files.items()
    ):
        raise Hold("Original readiness sources changed while snapshotting.")
    return sha(raw_index), source_bytes


def check_sources(root, index_sha):
    source = root / "records/source"
    raw = read_regular(source / "source-index.json", BUCKETS["records/source"])
    if sha(raw) != index_sha:
        raise Hold("Readiness source-index identity changed.")
    index = json.loads(raw)
    if index["fixture_rows"] != ROWS or index["fixture_sha256"] != sha(
        synthetic_fixture()
    ):
        raise Hold("Only the built-in synthetic fixture is admitted.")
    if set(index["files"]) != set(source_names(source)):
        raise Hold("Readiness source snapshot is incomplete or changed.")
    for name, entry in index["files"].items():
        if digest(source / name, entry["bytes"]) != entry["sha256"]:
            raise Hold("Readiness helper or lock bytes drifted.")
    return index


def environment_receipt(root, target, phase, value):
    if target not in ("windows", "linux") or phase not in ("before", "after"):
        raise Hold("Unknown environment receipt slot.")
    path = literal(root / "records/source" / f"{target}-environment-{phase}.json")
    previous = read_regular(path, ENV_BYTES)
    if len(previous) != ENV_BYTES or json.loads(previous)["state"] != "NOT_EXECUTED":
        raise Hold("Environment receipt slot is not an unused reservation.")
    raw = json_bytes(
        {
            **value,
            "target": target,
            "phase": phase,
            "qualification_outcome": "NOT_EXECUTED",
            **SCIENTIFIC,
        }
    )
    if len(raw) > ENV_BYTES:
        raise Hold("Environment receipt exceeds its unchanged reserved source space.")
    with path.open("r+b") as stream:
        stream.write(raw.ljust(ENV_BYTES, b" "))
        stream.flush()
        os.fsync(stream.fileno())
    return sha(raw)


def retained_store(root):
    view = object.__new__(Store)
    view.root = literal(root)
    return view


def claim_worker(root, name):
    if name not in ("windows", "linux-setup", "linux"):
        raise Hold("Unknown serial worker claim.")
    if name != "windows":
        final = json.loads(read_regular(root / "records/logs/windows-final.json", 8192))
        if final.get("state") != "PASSED":
            raise Hold("Linux cannot start before successful Windows completion.")
    if name == "linux" and not (root / "records/source/claims/linux-setup").is_dir():
        raise Hold("Linux native worker requires its one-time offline bootstrap.")
    claim = literal(root / "records/source/claims" / name)
    claim.parent.mkdir(exist_ok=True)
    try:
        claim.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise Hold("Worker already claimed; no duplicate start or retry.") from exc


def native_worker(root, target, wheelhouse, repository, index_sha):
    store = retained_store(root)
    index = check_sources(root, index_sha)
    claim_worker(root, target)
    phase = "before"
    try:
        before = admit_environment(
            target,
            root / "wheel" / WHEEL_NAME,
            wheelhouse,
            repository,
            candidate_identity=index["candidate_identity"],
        )
        environment_receipt(root, target, phase, before)
        phase = "after"
        # No input read, candidate analysis or reference evaluation precedes admission.
        raw = read_regular(root / "input/synthetic.csv", BUCKETS["input"])
        if sha(raw) != sha(synthetic_fixture()) or sha(raw) == INPUT_SHA256:
            raise Hold("Native rehearsal fixture identity changed.")
        from qs_dmss.external_data.contracts import AnalysisProfile
        from qs_dmss.external_data.evidence import run_analysis, verify_bundle

        from .candidate import probe
        from .comparison import compare
        from .reference import parse

        output = root / target / "synthetic"
        run_analysis(
            root / "input/synthetic.csv",
            output,
            kind="synthetic",
            profile=AnalysisProfile(**PROFILE),
            expected_sha256=sha(raw),
            source_commit=COMMIT,
            candidate_wheel_sha256=load_locks()["candidate_wheel_sha256"],
        )
        verified = verify_bundle(output / "dimuon-evidence.zip", recompute=True)
        if not verified["success"]:
            raise Hold("Native synthetic evidence verification refused.")
        result, views = probe(raw, "synthetic")
        comparison = compare(parse(raw), result, views)
        store.write(
            "records/comparison", target + "-comparison.json", json_bytes(comparison)
        )
        if (
            not comparison.get("complete")
            or comparison["comparison_outcome"] != "MATCH"
        ):
            raise Hold(
                "Synthetic numerical comparison did not match the fixed criteria."
            )
        after = admit_environment(
            target,
            root / "wheel" / WHEEL_NAME,
            wheelhouse,
            repository,
            candidate_identity=index["candidate_identity"],
        )
        environment_receipt(root, target, phase, after)
        if before != after:
            raise Hold("Native runtime identity changed during rehearsal.")
        check_sources(root, index_sha)
        store.audit()
        print(
            json_bytes(
                {
                    "state": "PASSED",
                    "target": target,
                    "label": "SYNTHETIC_NOT_COLLISION_DATA",
                    "rows": len(views),
                    "qualification_outcome": "NOT_EXECUTED",
                    **SCIENTIFIC,
                }
            ).decode(),
            end="",
        )
    except BaseException as exc:
        reason = (
            str(exc)
            if isinstance(exc, Hold)
            else "Native synthetic worker failed; preserve partial evidence."
        )
        try:
            environment_receipt(
                root, target, phase, {"state": "HOLD", "reason": reason}
            )
        except (OSError, Hold, ValueError):
            pass  # The immutable stage STARTED receipt remains if a slot is torn/unwritable.
        raise Hold(reason) from exc


def supervise(store, stage, command, index_sha, *, timeout=300):
    if (
        stage not in ("windows", "linux")
        or type(timeout) not in (int, float)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 300
    ):
        raise Hold("Only fixed native stages and bounded timeouts are admitted.")
    check_sources(store.root, index_sha)
    used = 0
    overflow = None
    capture_failed = False
    stopped = threading.Event()
    process = None
    reader = None
    reason = None
    started = time.monotonic()
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC", "PATHEXT"}
    }
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        process = subprocess.Popen(
            command,
            cwd=store.root / "records/source",
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            if os.name == "nt"
            else 0,
        )

        def capture():
            nonlocal used, overflow, capture_failed
            try:
                with (store.root / "records/logs" / (stage + ".log")).open(
                    "r+b"
                ) as log:
                    while True:
                        data = process.stdout.read(min(4096, LOG_BYTES - used + 1))
                        if not data:
                            break
                        remaining = LOG_BYTES - used
                        retained = data[:remaining]
                        log.write(retained)
                        log.flush()
                        used += len(retained)
                        if len(data) > remaining:
                            overflow = data[remaining : remaining + 1].hex()
                            stopped.set()
                            break
                    os.fsync(log.fileno())
            except (OSError, ValueError):
                capture_failed = True
                stopped.set()

        reader = threading.Thread(target=capture, daemon=True)
        reader.start()
        while process.poll() is None:
            if stopped.wait(0.05):
                reason = "LOG_STORAGE_FAILURE" if capture_failed else "LOG_LIMIT"
                break
            if time.monotonic() - started >= timeout:
                reason = "TIMEOUT"
                break
            store.audit()
        if reason and process.poll() is None:
            process.kill()
        process.wait(timeout=2)
        reader.join(timeout=2)
        if reader.is_alive():
            raise Hold("Native worker output stream did not terminate.")
        if stopped.is_set():
            reason = "LOG_STORAGE_FAILURE" if capture_failed else "LOG_LIMIT"
        if process.returncode and reason is None:
            reason = "WORKER_REFUSAL"
        check_sources(store.root, index_sha)
        store.audit()
    except (OSError, subprocess.SubprocessError, Hold):
        reason = reason or "SUPERVISION_FAILURE"
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=2)
            if reader is not None:
                reader.join(timeout=2)
            if process.stdout is not None:
                process.stdout.close()
    result = {
        "state": "HOLD" if reason else "PASSED",
        "reason": reason,
        "log_bytes_used": used,
        "overflow_byte_hex": overflow,
        "output_complete": reason is None,
        "timeout_seconds": timeout,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    store.finish(stage, result)
    if reason:
        raise Hold("Native rehearsal stage refused; inspect its reserved receipt.")
    return result


def linux_bootstrap(root, wheelhouse, repository, index_sha):
    import venv

    plan = load_locks()
    if (
        platform.system() != "Linux"
        or sys.version != plan["targets"]["linux"]["runtime_sys_version"]
    ):
        raise Hold("Linux bootstrap is outside its pinned runtime.")
    check_sources(root, index_sha)
    claim_worker(root, "linux-setup")
    destination = Path(tempfile.mkdtemp(prefix="qs-dmss-readiness-native-"))
    for row in plan["targets"]["linux"]["packages"]:
        artifact = (
            root / "wheel" / WHEEL_NAME
            if row["name"] == "qs-dmss"
            else wheelhouse / row["filename"]
        )
        if sha(read_regular(artifact, row["bytes"])) != row["sha256"]:
            raise Hold("Offline bootstrap artifact identity changed.")
    venv.EnvBuilder(with_pip=False).create(destination)
    pip = next(
        row for row in plan["targets"]["linux"]["packages"] if row["name"] == "pip"
    )
    python = destination / "bin/python"
    code = "import sys;sys.path.insert(0,sys.argv.pop(1));from pip._internal.cli.main import main;raise SystemExit(main())"
    subprocess.run(
        [
            str(python),
            "-I",
            "-B",
            "-c",
            code,
            str(wheelhouse / pip["filename"]),
            "--isolated",
            "--disable-pip-version-check",
            "install",
            "--quiet",
            "--no-index",
            "--find-links",
            str(wheelhouse),
            "--find-links",
            str(root / "wheel"),
            "--only-binary=:all:",
            "--require-hashes",
            "--no-compile",
            "-r",
            str(Path(__file__).parent / "environments/v1/linux-cp312.lock.txt"),
        ],
        check=True,
        timeout=300,
    )
    args = [
        str(python),
        "-E",
        "-s",
        "-B",
        "-m",
        __spec__.name,
        "--worker",
        "linux",
        "--root",
        str(root),
        "--wheelhouse",
        str(wheelhouse),
        "--repository",
        str(repository),
        "--index-sha256",
        index_sha,
    ]
    os.execve(str(python), args, os.environ.copy())


def linux_stage(store, wheelhouse, repository, index_sha):
    image = load_locks()["targets"]["linux"]["runtime_distribution"]["image"]
    subprocess.run(
        ["docker", "image", "inspect", image],
        check=True,
        stdout=subprocess.DEVNULL,
        timeout=10,
    )
    name = "qs-dmss-readiness-" + uuid.uuid4().hex
    command = [
        "docker",
        "create",
        "--name",
        name,
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/runtime:rw,exec,size=512m",
        "--env",
        "TMPDIR=/runtime",
        "--workdir",
        "/evidence/records/source",
        "--mount",
        f"type=bind,source={store.root},target=/evidence",
        "--mount",
        f"type=bind,source={wheelhouse},target=/wheels,readonly",
        image,
        "python",
        "-E",
        "-s",
        "-B",
        "-m",
        "research.cern_dimuon_qualification.readiness",
        "--worker",
        "linux-setup",
        "--root",
        "/evidence",
        "--wheelhouse",
        "/wheels",
        "--repository",
        "/repository",
        "--index-sha256",
        index_sha,
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=30)
        return supervise(
            store, "linux", ["docker", "start", "--attach", name], index_sha
        )
    finally:
        try:
            cleaned = subprocess.run(
                ["docker", "rm", "--force", name], capture_output=True, timeout=15
            )
            # A create timeout has an unknown outcome: always attempt cleanup,
            # then independently confirm this unique name is absent.
            present = subprocess.run(
                [
                    "docker",
                    "container",
                    "ls",
                    "--all",
                    "--filter",
                    "name=^/" + name + "$",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                timeout=10,
            )
            if cleaned.returncode or present.returncode or present.stdout.strip():
                store.finish(
                    "linux", {"state": "HOLD", "reason": "CONTAINER_CLEANUP_UNVERIFIED"}
                )
                raise Hold("Disposable Linux container teardown could not be verified.")
        except (OSError, subprocess.SubprocessError) as exc:
            store.finish(
                "linux", {"state": "HOLD", "reason": "CONTAINER_CLEANUP_UNVERIFIED"}
            )
            raise Hold(
                "Disposable Linux container teardown could not be verified."
            ) from exc


def compare_platforms(store):
    records = {
        target: json.loads(
            read_regular(
                store.root / "records/comparison" / (target + "-comparison.json"),
                BUCKETS["records/comparison"],
            )
        )
        for target in ("windows", "linux")
    }
    if any(
        value.get("comparison_outcome") != "MATCH" or not value.get("complete")
        for value in records.values()
    ):
        raise Hold("Both native comparisons must satisfy the unchanged criteria.")
    keys = ("input_rows", "selected", "histogram_counts")
    if any(records["windows"][key] != records["linux"][key] for key in keys):
        raise Hold("Native exact row/count reconciliation differs.")
    selection_keys = (
        "data_row",
        "physical_line",
        "Run",
        "Event",
        "first_failure",
        "tokens",
    )
    decisions = {
        target: [
            {key: item[key] for key in selection_keys} for item in record["exclusions"]
        ]
        for target, record in records.items()
    }
    if decisions["windows"] != decisions["linux"]:
        raise Hold("Native row identities or first-failure decisions differ.")
    result = {
        "state": "PASSED",
        "label": "SYNTHETIC_NOT_COLLISION_DATA",
        "exact_fields": list(keys),
        "native_criteria": "Unchanged protocol; each candidate checked against its reference",
        "reference_digests_identical": records["windows"]["reference_stream_sha256"]
        == records["linux"]["reference_stream_sha256"],
        "qualification_outcome": "NOT_EXECUTED",
        **SCIENTIFIC,
    }
    store.write(
        "records/comparison", "platform-reconciliation.json", json_bytes(result)
    )
    store.finish("comparison", {"state": "PASSED"})


def failure_controls(store):
    refused = []
    for name, operation, error in (
        (
            "immutable_write",
            lambda: store.write("input", "synthetic.csv", b"no overwrite"),
            FileExistsError,
        ),
        (
            "allocation",
            lambda: store.write("input", "oversize.bin", bytes(BUCKETS["input"] + 1)),
            Hold,
        ),
    ):
        try:
            operation()
        except error:
            refused.append(name)
        else:
            raise Hold("A synthetic refusal control did not stop.")
    with patch(
        "os.scandir", side_effect=PermissionError("synthetic enumeration refusal")
    ):
        try:
            store.audit()
        except Hold:
            refused.append("unreadable_directory")
        else:
            raise Hold("Synthetic enumeration refusal did not stop.")
    store.write(
        "records/comparison",
        "controls.json",
        json_bytes(
            {
                "refused": refused,
                "scope": "In-process refusal checks; timeout/log/drift transport controls are separately regression-tested",
                "qualification_outcome": "NOT_EXECUTED",
                **SCIENTIFIC,
            }
        ),
    )
    store.finish("control", {"state": "PASSED", "refused": refused})


def run_rehearsal(
    output, *, wheel, windows_python, windows_wheels, linux_wheels, repository=ROOT
):
    store = Store(output, workers=STAGES)
    stage = None
    try:
        if platform.system() != "Windows":
            raise Hold(
                "This coordinator requires the reviewed native Windows host and local Linux Docker transport."
            )
        wheel, windows_python, windows_wheels, linux_wheels, repository = map(
            literal, (wheel, windows_python, windows_wheels, linux_wheels, repository)
        )
        if (
            sha(read_regular(windows_python, 32 * 1024 * 1024))
            != WINDOWS_LAUNCHER_SHA256
        ):
            raise Hold("Only the reviewed Windows Python launcher may be started.")
        if not (repository / ".git").is_dir():
            raise Hold("Pinned Git objects must be available in a literal repository.")
        index_sha, source_bytes = prepare(store, repository, wheel)
        windows = [
            str(windows_python),
            "-E",
            "-s",
            "-B",
            "-m",
            "research.cern_dimuon_qualification.readiness",
            "--worker",
            "windows",
            "--root",
            str(store.root),
            "--wheelhouse",
            str(windows_wheels),
            "--repository",
            str(repository),
            "--index-sha256",
            index_sha,
        ]
        stage = "windows"
        supervise(store, stage, windows, index_sha)
        stage = "linux"
        linux_stage(store, linux_wheels, repository, index_sha)
        stage = "comparison"
        compare_platforms(store)
        stage = "control"
        failure_controls(store)
        check_sources(store.root, index_sha)
        result = {
            "readiness_outcome": "SYNTHETIC_REHEARSAL_PASSED",
            "qualification_outcome": "NOT_EXECUTED",
            "pilot_execution_ready": False,
            "fixture_rows": ROWS,
            "source_reserved_bytes": source_bytes,
            "source_index_sha256": index_sha,
            "stage_order": list(STAGES),
            "scope": "Synthetic-only rehearsal; no CERN snapshot, production changes, deployment or release",
            **SCIENTIFIC,
        }
        store.write("records/comparison", "readiness.json", json_bytes(result))
        store.finish("supervisor", {"state": "SYNTHETIC_REHEARSAL_PASSED"})
        result["inventory"] = store.inventory()
        return result
    except BaseException as exc:
        reason = (
            str(exc)
            if isinstance(exc, Hold)
            else "Readiness rehearsal failed; preserve this root and partial records."
        )
        if stage is not None:
            saved = json.loads(
                read_regular(
                    store.root / "records/logs" / (stage + "-final.json"), 8192
                )
            )
            if saved.get("state") != "HOLD":
                store.finish(stage, {"state": "HOLD", "reason": reason})
        store.finish("supervisor", {"state": "HOLD", "reason": reason})
        try:
            if not (store.root / "records/integrity/inventory.json").exists():
                store.inventory()
        except (OSError, Hold):
            pass  # HOLD/STARTED survive when complete accounting is unavailable.
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise Hold(reason) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "wheel", "windows-python", "windows-wheels", "linux-wheels"):
        parser.add_argument("--" + name)
    parser.add_argument(
        "--worker", choices=("windows", "linux", "linux-setup"), help=argparse.SUPPRESS
    )
    for name in ("root", "wheelhouse", "repository", "index-sha256"):
        parser.add_argument("--" + name, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.worker:
            if any(
                (
                    args.output,
                    args.wheel,
                    args.windows_python,
                    args.windows_wheels,
                    args.linux_wheels,
                )
            ) or not all(
                (args.root, args.wheelhouse, args.repository, args.index_sha256)
            ):
                parser.error(
                    "Fixed workers require only their controller-supplied paths and index identity."
                )
            root = literal(args.root)
            if Path(__file__).resolve().parents[2] != root / "records/source":
                parser.error(
                    "Workers must execute from their retained source snapshot."
                )
            receipt = json.loads(
                read_regular(root / "records/logs/supervisor-final.json", 8192)
            )
            if receipt.get("state") != "NOT_EXECUTED":
                parser.error("Closed rehearsal roots cannot restart workers.")
            if args.worker == "linux-setup":
                linux_bootstrap(
                    root,
                    literal(args.wheelhouse),
                    literal(args.repository),
                    args.index_sha256,
                )
            else:
                native_worker(
                    root,
                    args.worker,
                    literal(args.wheelhouse),
                    literal(args.repository),
                    args.index_sha256,
                )
            return 0
        if any(
            (args.root, args.wheelhouse, args.repository, args.index_sha256)
        ) or not all(
            (
                args.output,
                args.wheel,
                args.windows_python,
                args.windows_wheels,
                args.linux_wheels,
            )
        ):
            parser.error(
                "Supply a new output root, approved wheel, Windows Python and both locked wheelhouses."
            )
        result = run_rehearsal(
            args.output,
            wheel=args.wheel,
            windows_python=args.windows_python,
            windows_wheels=args.windows_wheels,
            linux_wheels=args.linux_wheels,
        )
        print(json_bytes(result).decode(), end="")
        return 0
    except (OSError, Hold, subprocess.SubprocessError):
        print(
            json_bytes(
                {
                    "readiness_outcome": "HOLD",
                    "qualification_outcome": "NOT_EXECUTED",
                    "pilot_execution_ready": False,
                    "reason": "Rehearsal refused; preserve its reserved receipts and partial files.",
                    **SCIENTIFIC,
                }
            ).decode(),
            end="",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
