"""Synthetic execution readiness cannot admit CERN data or change criteria."""

import copy
import json
import os
import py_compile
import subprocess
import sys
import time
import zipfile
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.cern_dimuon_qualification import processes, retention
from research.cern_dimuon_qualification import readiness as r
from research.cern_dimuon_qualification import runtime as rt
from research.cern_dimuon_qualification.contract import (
    BUCKETS,
    INPUT_SHA256,
    LOG_BYTES,
    SCIENTIFIC,
    TOTAL_BYTES,
    Hold,
    json_bytes,
)
from research.cern_dimuon_qualification.retention import Store

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_bytes())


def record(store, name):
    return read_json(store.root / "records" / name)


def wheel_row(data):
    return dict(bytes=len(data), sha256=rt.sha(data), version="1")


@pytest.fixture
def serial(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    launcher = tmp_path / "python.exe"
    launcher.write_bytes(b"launcher")
    monkeypatch.setattr(r.platform, "system", lambda: "Windows")
    monkeypatch.setattr(r, "WINDOWS_LAUNCHER_SHA256", rt.sha(b"launcher"))
    monkeypatch.setattr(r, "prepare", lambda *a: ("index", 1))
    return dict(
        output=tmp_path / "evidence",
        wheel=tmp_path,
        windows_python=launcher,
        windows_wheels=tmp_path,
        linux_wheels=tmp_path,
        repository=tmp_path,
    )


def observed(target):
    plan = rt.load_locks()
    value = plan["targets"][target]
    return {
        "system": target.title(),
        "implementation": "CPython",
        "python": plan["python"],
        "sys_version": value["runtime_sys_version"],
        "machine": value["machine"],
        "pointer_bits": 64,
        "isolated_environment": True,
        "packages": {row["name"]: row["version"] for row in value["packages"]},
    }


@pytest.mark.parametrize("target", ["windows", "linux"])
def test_runtime_observations_are_exact(target):
    value = observed(target)
    rt.check_observations(target, rt.load_locks(), value)
    for key, bad in (
        ("system", "other"),
        ("implementation", "PyPy"),
        ("python", "3.12.14"),
        ("sys_version", "different build"),
        ("machine", "arm64"),
        ("pointer_bits", 32),
        ("isolated_environment", False),
        ("packages", {}),
    ):
        changed = {**value, key: bad}
        with pytest.raises(Hold):
            rt.check_observations(target, rt.load_locks(), changed)
    for mutation in ("extra", "missing", "version"):
        changed = copy.deepcopy(value)
        if mutation == "extra":
            changed["packages"]["unexpected"] = "1"
        elif mutation == "missing":
            changed["packages"].pop("pip")
        else:
            changed["packages"]["numpy"] = "2.5.3"
        with pytest.raises(Hold):
            rt.check_observations(target, rt.load_locks(), changed)


def test_manifest_and_lock_drift_refuse(tmp_path):
    for name in ("manifest.json", "windows-cp312.lock.txt", "linux-cp312.lock.txt"):
        (tmp_path / name).write_bytes((rt.LOCKS / name).read_bytes())
    rt.load_locks(tmp_path)
    path = tmp_path / "linux-cp312.lock.txt"
    path.write_bytes(path.read_bytes() + b"# drift\n")
    with pytest.raises(Hold, match="lock identity"):
        rt.load_locks(tmp_path)
    (tmp_path / "manifest.json").write_bytes(b"{}")
    with pytest.raises(Hold, match="manifest"):
        rt.load_locks(tmp_path)


@pytest.mark.parametrize("name", [None, "../pkg", "", "a/b", "a:b"])
def test_distribution_names_are_closed(name):
    with pytest.raises(Hold):
        rt.canonical(name)


def wheel_case(tmp_path, members=None):
    members = members or {
        "pkg/a.py": b"value=1\n",
        "pkg-1.dist-info/RECORD": b"ignored",
    }
    wheel = tmp_path / "test.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    prefix = tmp_path / "env"
    prefix.mkdir()
    for name, data in members.items():
        path = prefix / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    distribution = SimpleNamespace(locate_file=lambda name: prefix / name)
    return wheel, wheel_row(wheel.read_bytes()), distribution, prefix


def test_installed_wheel_members_match_and_only_record_is_exempt(tmp_path):
    args = wheel_case(tmp_path)
    result = rt.check_installed_wheel(*args)
    assert result["installed_members"] == 1
    (args[3] / "pkg-1.dist-info/RECORD").write_bytes(b"installer regenerated")
    assert rt.check_installed_wheel(*args) == result
    (args[3] / "pkg/a.py").write_bytes(b"value=2\n")
    with pytest.raises(Hold, match="Installed runtime member"):
        rt.check_installed_wheel(*args)


def test_runtime_artifact_and_install_escape_refuse(tmp_path):
    wheel, row, distribution, prefix = wheel_case(tmp_path)
    with pytest.raises(Hold):
        rt.check_installed_wheel(
            wheel, {**row, "sha256": "0" * 64}, distribution, prefix
        )
    outside = tmp_path / "outside"
    outside.write_bytes(b"value=1\n")
    with pytest.raises(Hold, match="escaped"):
        rt.check_installed_wheel(
            wheel, row, SimpleNamespace(locate_file=lambda _: outside), prefix
        )


@pytest.mark.parametrize(
    "name", ["/absolute", "pkg/../x", "pkg\\x", "x:y", "pkg.data/a.py"]
)
def test_runtime_member_paths_refuse(tmp_path, name):
    with pytest.raises(Hold, match="layout"):
        rt.check_member_path(name, 1)
    if "\\" in name:
        return  # Windows ZipInfo normalizes its own separator on archive reads.
    wheel = tmp_path / "test.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(name, b"x")
    with pytest.raises(Hold, match="layout"):
        rt.check_installed_wheel(wheel, wheel_row(wheel.read_bytes()), None, tmp_path)


def test_retained_candidate_map_is_complete_and_imports_are_checked(
    monkeypatch, tmp_path
):
    from research.cern_dimuon_qualification.contract import COMMIT, WHEEL_SHA256

    path = tmp_path / "module.py"
    path.write_bytes(b"value=1\n")
    identity = {
        "candidate_commit": COMMIT,
        "wheel_sha256": WHEEL_SHA256,
        "module_sha256": {
            name: rt.sha(path.read_bytes()) for name in rt.IDENTITY_MODULES.values()
        },
    }
    monkeypatch.setattr(
        rt.importlib, "import_module", lambda _: SimpleNamespace(__file__=str(path))
    )
    assert (
        "controller Git check"
        in rt.retained_candidate_identity(identity)["commit_assertion"]
    )
    for field, value in (
        ("candidate_commit", "wrong"),
        ("wheel_sha256", "wrong"),
        ("module_sha256", {}),
    ):
        with pytest.raises(Hold):
            rt.retained_candidate_identity({**identity, field: value})
    path.write_bytes(b"changed")
    with pytest.raises(Hold):
        rt.retained_candidate_identity(identity)


def test_fixed_layout_keeps_the_original_budget(tmp_path):
    store = Store(tmp_path / "new", workers=r.STAGES)
    ledger = store.audit()
    assert ledger["total_bytes"] == ledger["bucket_bytes"]["records/logs"] == 192 * 1024
    assert sum(BUCKETS.values()) == TOTAL_BYTES == 26 * 1024 * 1024
    for stage in r.STAGES:
        assert (
            store.root / "records/logs" / (stage + ".log")
        ).stat().st_size == LOG_BYTES
    with pytest.raises(Hold):
        Store(tmp_path / "bad", workers=("arbitrary",))
    with pytest.raises(Hold):
        Store(store.root, workers=r.STAGES)


def test_fixture_is_original_deterministic_and_bounded():
    raw = r.synthetic_fixture()
    assert raw == r.synthetic_fixture() and rt.sha(raw) != INPUT_SHA256
    assert len(raw.splitlines()) == r.ROWS + 1
    assert len(raw) < BUCKETS["input"]
    for invalid in (True, 0, 3, 25001, 4.0):
        with pytest.raises(Hold):
            r.synthetic_fixture(invalid)
    from research.cern_dimuon_qualification.reference import evaluate, parse

    rows = parse(r.synthetic_fixture(8))
    assert sum(evaluate(row, "binary64")["selected"] for row in rows) == 4


def snapshot(tmp_path, monkeypatch):
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    source = store.root / "records/source"
    name = "helper.py"
    store.write("records/source", name, b"# stable\n")
    index = {
        "files": {name: {"bytes": 9, "sha256": rt.sha(b"# stable\n")}},
        "fixture_rows": r.ROWS,
        "fixture_sha256": rt.sha(r.synthetic_fixture()),
        "candidate_identity": {},
    }
    raw = json_bytes(index)
    store.write("records/source", "source-index.json", raw)
    monkeypatch.setattr(r, "source_names", lambda _: [name])
    for target in ("windows", "linux"):
        for phase in ("before", "after"):
            store.write(
                "records/source",
                f"{target}-environment-{phase}.json",
                json_bytes({"state": "NOT_EXECUTED"}).ljust(r.ENV_BYTES, b" "),
            )
    return store, rt.sha(raw), source


def test_source_drift_and_index_drift_refuse(tmp_path, monkeypatch):
    store, sha, source = snapshot(tmp_path, monkeypatch)
    assert r.check_sources(store.root, sha)["fixture_rows"] == r.ROWS
    (source / "helper.py").write_bytes(b"# drift!\n")
    with pytest.raises(Hold, match="drifted"):
        r.check_sources(store.root, sha)
    with pytest.raises(Hold, match="index identity"):
        r.check_sources(store.root, "0" * 64)


def test_environment_receipts_are_reserved_bounded_and_once_only(tmp_path, monkeypatch):
    store, _, _ = snapshot(tmp_path, monkeypatch)
    before = store.audit()["total_bytes"]
    r.environment_receipt(store.root, "windows", "before", {"state": "ADMITTED"})
    assert store.audit()["total_bytes"] == before
    result = record(store, "source/windows-environment-before.json")
    assert all(result[key] == value for key, value in SCIENTIFIC.items())
    with pytest.raises(Hold, match="unused"):
        r.environment_receipt(store.root, "windows", "before", {"state": "ADMITTED"})
    with pytest.raises(Hold, match="reserved source"):
        r.environment_receipt(
            store.root,
            "linux",
            "before",
            {"state": "HOLD", "reason": "x" * r.ENV_BYTES},
        )
    assert record(store, "source/linux-environment-before.json")["state"] == "NOT_EXECUTED"
    with pytest.raises(Hold):
        r.environment_receipt(store.root, "other", "before", {})


def test_claims_enforce_order_and_no_duplicate_start(tmp_path, monkeypatch):
    store, _, _ = snapshot(tmp_path, monkeypatch)
    with pytest.raises(Hold, match="Windows completion"):
        r.claim_worker(store.root, "linux-setup")
    r.claim_worker(store.root, "windows")
    with pytest.raises(Hold, match="duplicate"):
        r.claim_worker(store.root, "windows")
    store.finish("windows", {"state": "PASSED"})
    with pytest.raises(Hold, match="bootstrap"):
        r.claim_worker(store.root, "linux")
    r.claim_worker(store.root, "linux-setup")
    r.claim_worker(store.root, "linux")
    with pytest.raises(Hold):
        r.claim_worker(store.root, "linux")


def test_failed_admission_does_not_open_fixture(tmp_path, monkeypatch):
    store, sha, _ = snapshot(tmp_path, monkeypatch)
    monkeypatch.setattr(
        r,
        "admit_environment",
        lambda *a, **k: (_ for _ in ()).throw(Hold("runtime refused")),
    )
    original = r.read_regular

    def guarded(path, ceiling):
        assert Path(path).name != "synthetic.csv", "fixture opened before admission"
        return original(path, ceiling)

    monkeypatch.setattr(r, "read_regular", guarded)
    with pytest.raises(Hold, match="runtime refused"):
        r.native_worker(store.root, "windows", tmp_path, ROOT, sha)
    receipt = record(store, "source/windows-environment-before.json")
    assert receipt["state"] == "HOLD"


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("normal", None),
        ("timeout", "TIMEOUT"),
        ("overflow", "LOG_LIMIT"),
        ("refusal", "WORKER_REFUSAL"),
        ("drift", "SUPERVISION_FAILURE"),
    ],
)
def test_supervision_retains_every_failure(tmp_path, monkeypatch, mode, expected):
    store, sha, source = snapshot(tmp_path, monkeypatch)
    code = {
        "normal": "print('synthetic complete')",
        "timeout": "import time;print('before timeout',flush=True);time.sleep(10)",
        "overflow": f"import sys;sys.stdout.write('x'*{LOG_BYTES + 1});sys.stdout.flush()",
        "refusal": "print('synthetic refusal');raise SystemExit(7)",
        "drift": "from pathlib import Path;Path('helper.py').write_bytes(b'# changed\\n')",
    }[mode]
    command = [sys.executable, "-I", "-B", "-c", code]
    with pytest.raises(Hold) if expected else nullcontext():
        r.supervise(
            store, "windows", command, sha, timeout=0.5 if mode == "timeout" else 20
        )
    receipt = record(store, "logs/windows-final.json")
    assert receipt["reason"] == expected
    assert receipt["output_complete"] is (expected is None)
    assert (store.root / "records/logs/windows-started.json").exists()
    assert (source / "helper.py").exists()
    assert store.audit()["total_bytes"] <= TOTAL_BYTES
    if mode == "overflow":
        assert (
            receipt["log_bytes_used"] == LOG_BYTES
            and receipt["overflow_byte_hex"] == "78"
        )


@pytest.mark.parametrize(
    "timeout", [True, 0, -1, 301, float("nan"), float("inf"), "300"]
)
def test_invalid_worker_timeout_refuses_before_start(tmp_path, timeout):
    with pytest.raises(Hold):
        r.supervise(
            SimpleNamespace(root=tmp_path), "windows", [], "unused", timeout=timeout
        )


def records(store, *, numeric="3.1", count=1, decision="mass_window"):
    for target in ("windows", "linux"):
        record = {
            "comparison_outcome": "MATCH",
            "complete": True,
            "input_rows": 4,
            "selected": 3,
            "histogram_counts": [1, 2],
            "reference_stream_sha256": target,
            "exclusions": [
                {
                    "data_row": 1,
                    "physical_line": 2,
                    "Run": "1",
                    "Event": "1",
                    "first_failure": decision if target == "linux" else "mass_window",
                    "tokens": {},
                    "mass_binary64": numeric if target == "linux" else "3.0",
                }
            ],
        }
        if target == "linux":
            record["histogram_counts"][0] = count
        store.write(
            "records/comparison", target + "-comparison.json", json_bytes(record)
        )


def test_cross_platform_criteria_do_not_require_numeric_string_identity(tmp_path):
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    records(store)
    r.compare_platforms(store)
    result = record(store, "comparison/platform-reconciliation.json")
    assert result["state"] == "PASSED" and not result["reference_digests_identical"]
    assert result["qualification_outcome"] == "NOT_EXECUTED"


@pytest.mark.parametrize("kwargs", [{"count": 2}, {"decision": "eta"}])
def test_cross_platform_exact_decisions_and_counts_refuse(tmp_path, kwargs):
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    records(store, **kwargs)
    with pytest.raises(Hold):
        r.compare_platforms(store)


def test_failure_controls_preserve_fixture_and_limits(tmp_path):
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    store.write("input", "synthetic.csv", b"original synthetic")
    r.failure_controls(store)
    assert (store.root / "input/synthetic.csv").read_bytes() == b"original synthetic"
    assert not (store.root / "input/oversize.bin").exists()
    result = record(store, "comparison/controls.json")
    assert result["refused"] == [
        "immutable_write",
        "allocation",
        "unreadable_directory",
    ]


def test_linux_transport_is_offline_minimal_and_always_cleaned(tmp_path, monkeypatch):
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    calls = []
    environments = []
    for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG"):
        monkeypatch.setenv(key, "synthetic-selection")

    def run(command, **kwargs):
        calls.append(command)
        environments.append(kwargs["env"])
        return SimpleNamespace(returncode=0, stdout=b"")

    def spawn(command, **kwargs):
        environments.append(kwargs["env"])
        return SimpleNamespace(poll=lambda: 0, returncode=0)

    monkeypatch.setattr(r.subprocess, "run", run)
    monkeypatch.setattr(r, "check_sources", lambda *a: None)
    monkeypatch.setattr(
        processes,
        "ProcessTree",
        lambda: SimpleNamespace(spawn=spawn, read=lambda n: b"", close=lambda: None),
    )
    r.linux_stage(store, tmp_path / "wheels", ROOT, "index")
    command = next(value for value in calls if value[1] == "create")
    assert (
        command[command.index("--network") + 1] == "none" and "--read-only" in command
    )
    assert (
        r.load_locks()["targets"]["linux"]["runtime_distribution"]["image"] in command
    )
    mounts = [
        command[index + 1] for index, value in enumerate(command) if value == "--mount"
    ]
    assert len(mounts) == 2 and all(".git" not in value for value in mounts)
    assert any(value[1:3] == ["rm", "--force"] for value in calls)
    assert calls[-1][1:3] == ["container", "ls"]
    assert all(env == environments[0] for env in environments)
    assert all(
        environments[0][key] == "synthetic-selection"
        for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG")
    )
    assert command[command.index("-X") + 1].startswith("pycache_prefix=/evidence/")


def test_unknown_create_outcome_still_attempts_teardown(tmp_path, monkeypatch):
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if command[1] == "create":
            raise subprocess.TimeoutExpired(command, 30)
        return SimpleNamespace(returncode=0, stdout=b"")

    monkeypatch.setattr(r.subprocess, "run", run)
    with pytest.raises(subprocess.TimeoutExpired):
        r.linux_stage(store, tmp_path, ROOT, "index")
    assert any(command[1:3] == ["rm", "--force"] for command in calls)


def test_serial_failure_stops_before_linux_and_retains_hold(serial, monkeypatch):
    monkeypatch.setattr(
        r, "supervise", lambda *a, **k: (_ for _ in ()).throw(Hold("Windows refused"))
    )
    monkeypatch.setattr(
        r, "linux_stage", lambda *a: pytest.fail("Linux started after Windows failure")
    )
    with pytest.raises(Hold):
        r.run_rehearsal(**serial)
    final = read_json(serial["output"] / "records/logs/supervisor-final.json")
    assert final["state"] == "HOLD" and final["qualification_outcome"] == "NOT_EXECUTED"


@pytest.mark.parametrize("option", ["--input", "--pilot", "--execute", "--command"])
def test_cli_has_no_real_input_or_execution_surface(option):
    with pytest.raises(SystemExit) as result:
        r.main([option, "unused"])
    assert result.value.code == 2


def test_complete_source_overallocation_refuses_before_copy(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "large.py").write_bytes(bytes(BUCKETS["records/source"]))
    wheel = tmp_path / "candidate.whl"
    with zipfile.ZipFile(wheel, "w"):
        pass
    monkeypatch.setattr(r, "source_names", lambda _: ["large.py"])
    monkeypatch.setattr(r, "IDENTITY_MODULES", {})
    monkeypatch.setattr(r, "WHEEL_SHA256", rt.sha(wheel.read_bytes()))
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    with pytest.raises(Hold, match="reserved environment"):
        r.prepare(store, repository, wheel)
    assert store.audit()["total_bytes"] == 192 * 1024
    assert not list((store.root / "wheel").iterdir())
    assert not list((store.root / "input").iterdir())


def test_serial_success_has_fixed_order_and_never_promotes_pilot(serial, monkeypatch):
    monkeypatch.setattr(r, "check_sources", lambda *a: None)
    order = []
    monkeypatch.setattr(r, "supervise", lambda *a, **k: order.append("windows"))
    monkeypatch.setattr(r, "linux_stage", lambda *a: order.append("linux"))
    monkeypatch.setattr(r, "compare_platforms", lambda *a: order.append("comparison"))
    monkeypatch.setattr(r, "failure_controls", lambda *a: order.append("control"))
    result = r.run_rehearsal(**serial)
    assert order == list(r.STAGES)
    assert result["qualification_outcome"] == "NOT_EXECUTED"
    assert result["pilot_execution_ready"] is False
    assert all(result[key] == value for key, value in SCIENTIFIC.items())


def test_complete_source_plan_includes_locks_tests_guide_and_reserved_receipts():
    names = r.source_names(ROOT)
    assert "tests/test_cern_dimuon_readiness.py" in names
    assert "docs/cern-dimuon-execution-readiness.md" in names
    assert sum(name.endswith(".lock.txt") for name in names) == 2
    files = {name: (ROOT / name).read_bytes() for name in names}
    raw, size = r.source_plan(
        files, {name: "0" * 64 for name in rt.IDENTITY_MODULES.values()}
    )
    assert size == sum(map(len, files.values())) + len(raw) + 4 * r.ENV_BYTES
    assert size <= BUCKETS["records/source"]
    attributes = (ROOT / ".gitattributes").read_text()
    assert "tests/test_cern_dimuon_readiness.py text eol=lf" in attributes


@pytest.mark.parametrize("parent_wait", [0, 20])
def test_descendant_pipe_is_bounded(tmp_path, monkeypatch, parent_wait):
    store, sha, source = snapshot(tmp_path, monkeypatch)
    child = "import time;open('ready','w').close();time.sleep(30)"
    parent = f"import subprocess,sys,time;subprocess.Popen([sys.executable,'-I','-B','-c',{child!r}],stdout=sys.stdout,stderr=sys.stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));time.sleep({parent_wait})"
    command = [sys.executable, "-I", "-B", "-c", parent]
    tree = processes.ProcessTree()
    try:
        process = tree.spawn(
            command, cache=source / "fixture-cache", cwd=source,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0,
        )
        deadline = time.monotonic() + 10
        while not (source / "ready").is_file() or (not parent_wait and process.poll() is None):
            assert time.monotonic() < deadline, "descendant fixture did not start"
            time.sleep(0.02)
        monkeypatch.setattr(tree, "spawn", lambda *a, **kw: process)
        monkeypatch.setattr(processes, "ProcessTree", lambda: tree)
        start = time.monotonic()
        with pytest.raises(Hold):
            r.supervise(store, "windows", command, sha, timeout=0.5)
        assert time.monotonic() - start < 3
        final = record(store, "logs/windows-final.json")
        assert final["reason"] == "TIMEOUT" and not final["output_complete"]
    finally:
        if tree.process is None or not tree.process.stdout.closed:
            tree.close()


def test_fresh_startup_cache_defeats_stale_bytecode(tmp_path):
    module = tmp_path / "probe.py"
    module.write_text("value=1\n")
    stamp = module.stat().st_mtime_ns
    py_compile.compile(str(module), doraise=True)
    module.write_text("value=2\n")
    os.utime(module, ns=(stamp, stamp))
    cache = tmp_path / "new-cache"
    cache.mkdir()
    code = "import probe; print(probe.value)"

    def run(flags):
        return subprocess.run(
            [*flags, "-c", code],
            cwd=tmp_path,
            capture_output=True,
            check=True,
            timeout=10,
        ).stdout.strip()

    assert run([sys.executable, "-E", "-s", "-B"]) == b"1"
    assert run(r.python_flags(sys.executable, cache)) == b"2"
    assert not list(cache.iterdir())


@pytest.mark.parametrize("drift", ["flag", "prefix", "populated"])
def test_cache_admission_refuses_drift(tmp_path, monkeypatch, drift):
    monkeypatch.setattr(rt.sys, "pycache_prefix", str(tmp_path))
    monkeypatch.setattr(rt.sys, "_xoptions", {"pycache_prefix": str(tmp_path)})
    monkeypatch.setattr(rt.sys, "flags", SimpleNamespace(dont_write_bytecode=True))
    assert rt.check_cache(tmp_path) == str(tmp_path)
    if drift == "flag":
        monkeypatch.setattr(rt.sys, "flags", SimpleNamespace(dont_write_bytecode=False))
    elif drift == "prefix":
        monkeypatch.setattr(rt.sys, "pycache_prefix", str(tmp_path / "other"))
    else:
        (tmp_path / "stale.pyc").write_bytes(b"old")
    with pytest.raises(Hold):
        rt.check_cache(tmp_path)


@pytest.mark.parametrize("persistent", [False, True])
def test_vanished_entries_get_only_one_complete_rescan(
    tmp_path, monkeypatch, persistent
):
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    store.write("input", "receipt.json", b"retained")
    original = retention.os.walk
    scans = []

    def walk(*args, **kwargs):
        scans.append(1)
        if persistent or len(scans) == 1:
            return iter([(str(store.root / "input"), [], ["receipt.pending.json"])])
        return original(*args, **kwargs)

    monkeypatch.setattr(retention.os, "walk", walk)
    if persistent:
        with pytest.raises(Hold, match="disappearing"):
            store.audit()
    else:
        assert store.audit()["bucket_bytes"]["input"] == len(b"retained")
    assert len(scans) == 2


@pytest.mark.parametrize("reason", ["TIMEOUT", "LOG_LIMIT"])
@pytest.mark.parametrize("cleanup", ["returncode", "timeout"])
def test_cleanup_preserves_primary_diagnostics(tmp_path, monkeypatch, reason, cleanup):
    store = Store(tmp_path / "evidence", workers=r.STAGES)
    primary = dict(
        state="HOLD",
        reason=reason,
        tree_cleanup_failure="PROCESS_TREE_CLEANUP_UNVERIFIED",
        overflow_byte_hex="78",
        log_bytes_used=LOG_BYTES,
        elapsed_seconds=300,
    )

    def worker(*a, **kw):
        store.finish("linux", primary)
        raise Hold("worker failed")

    def run(command, **kw):
        if command[1] == "rm":
            if cleanup == "timeout":
                raise subprocess.TimeoutExpired(command, 15)
            return SimpleNamespace(returncode=1, stdout=b"")
        return SimpleNamespace(returncode=0, stdout=b"")

    monkeypatch.setattr(r, "supervise", worker)
    monkeypatch.setattr(r.subprocess, "run", run)
    with pytest.raises(Hold):
        r.linux_stage(store, tmp_path, ROOT, "index")
    final = record(store, "logs/linux-final.json")
    assert all(final[k] == v for k, v in primary.items())
    assert final["cleanup_failure"] == "CONTAINER_CLEANUP_UNVERIFIED"


@pytest.mark.parametrize("damage", ["json", "missing", "write"])
def test_supervisor_hold_survives_stage_damage(serial, monkeypatch, damage):
    original = Store.finish

    def finish(self, worker, value):
        if worker == "windows" and damage == "write":
            raise PermissionError("synthetic")
        return original(self, worker, value)

    def fail(store, *a, **kw):
        path = store.root / "records/logs/windows-final.json"
        if damage == "json":
            path.write_bytes(b"{".ljust(8192, b" "))
        elif damage == "missing":
            path.unlink()
        raise Hold("worker failed")

    monkeypatch.setattr(Store, "finish", finish)
    monkeypatch.setattr(r, "supervise", fail)
    with pytest.raises(Hold):
        r.run_rehearsal(**serial)
    root = serial["output"]
    assert read_json(root / "records/logs/supervisor-final.json")["state"] == "HOLD"
    assert (root / "records/integrity/inventory.json").is_file()
