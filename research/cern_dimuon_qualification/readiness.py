"""Fixed serial, synthetic-only Windows/Linux rehearsal; no CERN input option."""

import argparse
import io
import json
import os
import platform
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from .candidate import IDENTITY_MODULES
from .contract import (
    BUCKETS,
    COMMIT,
    INPUT_SHA256,
    PROFILE,
    SCIENTIFIC,
    WHEEL_SHA256,
    Hold,
    checked_protocol,
    json_bytes,
)
from .processes import bounded_timeout, capture
from .retention import Store, digest, literal, read_regular
from .runtime import (
    WINDOWS_LAUNCHER_SHA256,
    admit_environment,
    check_cache,
    load_locks,
    sha,
)

STAGES = ("windows", "linux", "comparison", "control")
ENV_BYTES = 16 * 1024
ROWS = 20000
ROOT = Path(__file__).resolve().parents[2]
WHEEL_NAME = "qs_dmss-0.14.0-py3-none-any.whl"
STATUS = {"qualification_outcome": "NOT_EXECUTED", **SCIENTIFIC}


def emit(value):
    print(json_bytes(value).decode(), end="")


def cache_path(root, role):
    return root / "records/source" / ("cache-" + role)


def python_flags(python, cache):
    return [str(python), "-E", "-s", "-B", "-X", "pycache_prefix=" + str(cache)]


def worker_args(role, root, wheelhouse, repository, index_sha):
    options = {
        "worker": role,
        "root": root,
        "wheelhouse": wheelhouse,
        "repository": repository,
        "index-sha256": index_sha,
    }
    return [
        "-m",
        __spec__.name,
        *[
            str(token)
            for name, value in options.items()
            for token in ("--" + name, value)
        ],
    ]


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
        "scope": "Complete active sources; historical reviews remain external, unchanged",
        **STATUS,
    }
    raw_index = (
        json.dumps(index, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()
    source_bytes = sum(map(len, files.values())) + len(raw_index) + 4 * ENV_BYTES
    if source_bytes > BUCKETS["records/source"]:
        raise Hold(
            f"Sources, locks and reserved environment receipts need {source_bytes} bytes; cap {BUCKETS['records/source']}."
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
        raise Hold("Approved wheel identity mismatch.")
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
                raise Hold("Pinned Git module mismatch.")
            modules[member] = sha(pinned)
    raw_index, source_bytes = source_plan(files, modules)
    for name, raw in files.items():
        store.write("records/source", name, raw)
    store.write("records/source", "source-index.json", raw_index)
    for role in ("windows", "linux", "linux-setup", "linux-install"):
        cache_path(store.root, role).mkdir(exist_ok=False)
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
        raise Hold("Original source changed during snapshot.")
    return sha(raw_index), source_bytes


def check_sources(root, index_sha):
    source = root / "records/source"
    raw = read_regular(source / "source-index.json", BUCKETS["records/source"])
    if sha(raw) != index_sha:
        raise Hold("Source-index identity changed.")
    index = json.loads(raw)
    if index["fixture_rows"] != ROWS or index["fixture_sha256"] != sha(
        synthetic_fixture()
    ):
        raise Hold("Built-in synthetic fixture required.")
    if set(index["files"]) != set(source_names(source)):
        raise Hold("Source snapshot membership changed.")
    for name, entry in index["files"].items():
        if digest(source / name, entry["bytes"]) != entry["sha256"]:
            raise Hold("Helper or lock bytes drifted.")
    return index


def environment_receipt(root, target, phase, value):
    if target not in ("windows", "linux") or phase not in ("before", "after"):
        raise Hold("Unknown environment slot.")
    path = literal(root / "records/source" / f"{target}-environment-{phase}.json")
    previous = read_regular(path, ENV_BYTES)
    if len(previous) != ENV_BYTES or json.loads(previous)["state"] != "NOT_EXECUTED":
        raise Hold("Environment slot is not unused.")
    raw = json_bytes(
        {
            **value,
            "target": target,
            "phase": phase,
            **STATUS,
        }
    )
    if len(raw) > ENV_BYTES:
        raise Hold("Environment receipt exceeds reserved source space.")
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
            raise Hold("Linux requires successful Windows completion.")
    if name == "linux" and not (root / "records/source/claims/linux-setup").is_dir():
        raise Hold("Linux requires its one-time bootstrap.")
    claim = literal(root / "records/source/claims" / name)
    claim.parent.mkdir(exist_ok=True)
    try:
        claim.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise Hold("Worker duplicate claim; no retry.") from exc


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
            cache_dir=cache_path(root, target),
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
            raise Hold("Synthetic comparison failed fixed criteria.")
        after = admit_environment(
            target,
            root / "wheel" / WHEEL_NAME,
            wheelhouse,
            repository,
            candidate_identity=index["candidate_identity"],
            cache_dir=cache_path(root, target),
        )
        environment_receipt(root, target, phase, after)
        if before != after:
            raise Hold("Native runtime identity changed during rehearsal.")
        check_sources(root, index_sha)
        store.audit()
        emit(
            {
                "state": "PASSED",
                "target": target,
                "label": "SYNTHETIC_NOT_COLLISION_DATA",
                "rows": len(views),
                **STATUS,
            }
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


def supervise(store, stage, command, index_sha, *, timeout=300, environment=None):
    if stage not in ("windows", "linux"):
        raise Hold("Invalid native stage.")
    bounded_timeout(timeout)
    check_sources(store.root, index_sha)
    if stage == "linux":
        env = environment.copy() if environment is not None else os.environ.copy()
    else:
        allowed = {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC", "PATHEXT"}
        env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = capture(store, stage, command, timeout, env)
    try:
        check_sources(store.root, index_sha)
    except (OSError, Hold):
        result.update(
            state="HOLD",
            reason=result["reason"] or "SUPERVISION_FAILURE",
            output_complete=False,
        )
    store.finish(stage, result)
    if result["reason"]:
        raise Hold("Native stage HOLD; see reserved receipt.")
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
            "-X",
            "pycache_prefix=" + str(cache_path(root, "linux-install")),
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
    args = python_flags(python, cache_path(root, "linux")) + worker_args(
        "linux", root, wheelhouse, repository, index_sha
    )
    os.execve(str(python), args, os.environ.copy())


def linux_stage(store, wheelhouse, repository, index_sha):
    environment = os.environ.copy()
    image = load_locks()["targets"]["linux"]["runtime_distribution"]["image"]
    subprocess.run(
        ["docker", "image", "inspect", image],
        check=True,
        stdout=subprocess.DEVNULL,
        timeout=10,
        env=environment,
    )
    name = "qs-dmss-readiness-" + uuid.uuid4().hex
    command = (
        [
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
        ]
        + python_flags("python", cache_path(PurePosixPath("/evidence"), "linux-setup"))
        + worker_args("linux-setup", "/evidence", "/wheels", "/repository", index_sha)
    )
    try:
        subprocess.run(
            command, check=True, capture_output=True, timeout=30, env=environment
        )
        return supervise(
            store,
            "linux",
            ["docker", "start", "--attach", name],
            index_sha,
            environment=environment,
        )
    finally:
        try:
            cleaned = subprocess.run(
                ["docker", "rm", "--force", name],
                capture_output=True,
                timeout=15,
                env=environment,
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
                env=environment,
            )
            if cleaned.returncode or present.returncode or present.stdout.strip():
                hold_stage(
                    store,
                    "linux",
                    "CONTAINER_CLEANUP_UNVERIFIED",
                    cleanup_failure="CONTAINER_CLEANUP_UNVERIFIED",
                )
                raise Hold("Linux teardown unverified.")
        except (OSError, subprocess.SubprocessError) as exc:
            hold_stage(
                store,
                "linux",
                "CONTAINER_CLEANUP_UNVERIFIED",
                cleanup_failure="CONTAINER_CLEANUP_UNVERIFIED",
            )
            raise Hold("Linux teardown unverified.") from exc


def hold_stage(store, stage, reason, **details):
    try:
        saved = json.loads(
            read_regular(store.root / "records/logs" / (stage + "-final.json"), 8192)
        )
    except (OSError, ValueError):
        saved = {}
    if not isinstance(saved, dict):
        saved = {}
    if saved.get("state") != "HOLD" or not saved.get("reason"):
        saved["reason"] = reason
    store.finish(stage, {**saved, "state": "HOLD", **details})


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
        raise Hold("Both native comparisons must pass fixed criteria.")
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
        raise Hold("Native identities or first-failure decisions differ.")
    result = {
        "state": "PASSED",
        "label": "SYNTHETIC_NOT_COLLISION_DATA",
        "exact_fields": list(keys),
        "native_criteria": "Unchanged protocol; each candidate checked against its reference",
        "reference_digests_identical": records["windows"]["reference_stream_sha256"]
        == records["linux"]["reference_stream_sha256"],
        **STATUS,
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
                "scope": "Refusal checks; transport faults regression-tested",
                **STATUS,
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
            raise Hold("Reviewed Windows host and local Linux Docker required.")
        wheel, windows_python, windows_wheels, linux_wheels, repository = map(
            literal, (wheel, windows_python, windows_wheels, linux_wheels, repository)
        )
        if (
            sha(read_regular(windows_python, 32 * 1024 * 1024))
            != WINDOWS_LAUNCHER_SHA256
        ):
            raise Hold("Reviewed Windows launcher required.")
        if not (repository / ".git").is_dir():
            raise Hold("Literal repository with pinned Git objects required.")
        index_sha, source_bytes = prepare(store, repository, wheel)
        windows = python_flags(
            windows_python, cache_path(store.root, "windows")
        ) + worker_args("windows", store.root, windows_wheels, repository, index_sha)
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
            "pilot_execution_ready": False,
            "fixture_rows": ROWS,
            "source_reserved_bytes": source_bytes,
            "source_index_sha256": index_sha,
            "stage_order": list(STAGES),
            "scope": "Synthetic-only rehearsal; no CERN snapshot, production changes, deployment or release",
            **STATUS,
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
        try:
            store.finish("supervisor", {"state": "HOLD", "reason": reason})
        except (OSError, Hold):
            pass  # Reserved slot unavailable.
        if stage is not None:
            try:
                hold_stage(store, stage, reason)
            except (OSError, Hold):
                pass  # Best effort; supervisor attempted first.
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
    public = {
        name: getattr(args, name)
        for name in (
            "output",
            "wheel",
            "windows_python",
            "windows_wheels",
            "linux_wheels",
        )
    }
    private = (args.root, args.wheelhouse, args.repository, args.index_sha256)
    try:
        if args.worker:
            if any(public.values()) or not all(private):
                parser.error("Fixed worker paths and index identity required.")
            root = literal(args.root)
            check_cache(cache_path(root, args.worker))
            if Path(__file__).resolve().parents[2] != root / "records/source":
                parser.error("Execute workers from the retained snapshot.")
            receipt = json.loads(
                read_regular(root / "records/logs/supervisor-final.json", 8192)
            )
            if receipt.get("state") != "NOT_EXECUTED":
                parser.error("Closed rehearsal roots cannot restart workers.")
            paths = (
                literal(args.wheelhouse),
                literal(args.repository),
                args.index_sha256,
            )
            if args.worker == "linux-setup":
                linux_bootstrap(root, *paths)
            else:
                native_worker(root, args.worker, *paths)
            return 0
        if any(private) or not all(public.values()):
            parser.error(
                "Supply a new output root, approved wheel, Windows Python and both locked wheelhouses."
            )
        result = run_rehearsal(**public)
        emit(result)
        return 0
    except (OSError, Hold, subprocess.SubprocessError):
        emit(
            {
                "readiness_outcome": "HOLD",
                "pilot_execution_ready": False,
                "reason": "Rehearsal refused; preserve its reserved receipts and partial files.",
                **STATUS,
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
