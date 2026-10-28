"""Repository-only regression controls; never an EDRS/v3 execution entry point.

Startup accounting uses an isolated clock. Native pipe tests pre-arm a real
owned process tree so slow interpreter startup cannot masquerade as bad cleanup.
These additional tests do not alter the retained v1 source membership or policy.
"""

import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from research.cern_dimuon_qualification import processes
from research.cern_dimuon_qualification.readiness import STAGES
from research.cern_dimuon_qualification.retention import Store


@pytest.mark.parametrize("startup_ms", [0, 200, 500, 750])
def test_capture_deadline_includes_spawn_time(tmp_path, monkeypatch, startup_ms):
    class Clock:
        milliseconds = 0

        def monotonic(self):
            return self.milliseconds / 1000

        def sleep(self, seconds):
            self.milliseconds += round(seconds * 1000)

    clock = Clock()
    calls = []

    def spawn(*args, **kwargs):
        calls.append("spawn")
        clock.milliseconds += startup_ms
        return SimpleNamespace(poll=lambda: None)

    def read(ceiling):
        calls.append("read")
        assert calls.count("read") <= 25, "deadline was not enforced"

    tree = SimpleNamespace(
        spawn=spawn, read=read, close=lambda: calls.append("close")
    )
    monkeypatch.setattr(processes, "ProcessTree", lambda: tree)
    # Replace this module's reference, never the global time.monotonic function.
    monkeypatch.setattr(processes, "time", clock)
    store = Store(tmp_path / "evidence", workers=STAGES)
    result = processes.capture(store, "windows", ["not-executed"], 0.5)

    assert calls[0] == "spawn" and calls[-1] == "close"
    assert calls.count("spawn") == calls.count("close") == 1
    assert calls.count("read") == max(0, (500 - startup_ms) // 20)
    assert result["elapsed_seconds"] == max(500, startup_ms) / 1000
    assert result["state"] == "HOLD" and result["reason"] == "TIMEOUT"
    assert result["timeout_seconds"] == 0.5
    assert not result["output_complete"] and result["log_bytes_used"] == 0
    assert result["tree_cleanup_failure"] is None


@contextmanager
def ready_tree(directory, parent_wait):
    """One start, at most ten seconds of setup, and unconditional OS cleanup."""
    child = "import time;open('ready','w').close();time.sleep(30)"
    parent = (
        "import subprocess,sys,time;"
        f"subprocess.Popen([sys.executable,'-I','-B','-c',{child!r}],"
        "stdout=sys.stdout,stderr=sys.stderr,"
        "creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));"
        f"time.sleep({parent_wait})"
    )
    tree = processes.ProcessTree()
    original_close = tree.close  # Saved before any broken-cleanup control.
    cleaned = False

    def close():
        nonlocal cleaned
        if not cleaned:
            original_close()
            cleaned = True

    witness = None
    try:
        process = tree.spawn(
            [sys.executable, "-I", "-B", "-c", parent],
            cache=directory / "cache",
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        deadline = time.monotonic() + 10
        while not (directory / "ready").is_file() or (
            not parent_wait and process.poll() is None
        ):
            assert time.monotonic() < deadline, "native fixture startup timed out"
            time.sleep(0.02)
        if parent_wait:
            assert process.poll() is None, "parent exited before supervision"
        else:
            assert process.poll() == 0

        # Closing the supervisor's reader must not look like EOF. Keep an
        # independent descriptor; EOF proves every inherited writer has closed.
        witness = os.fdopen(os.dup(process.stdout.fileno()), "rb", buffering=0)
        probe = SimpleNamespace(
            process=SimpleNamespace(stdout=witness), api=tree.api
        )
        def read():
            return type(tree).read(probe, 1)

        assert read() is None, "descendant did not retain the pipe"
        yield tree, process, read, close
    finally:
        # Also runs for fixture refusal and deliberately broken capture cleanup.
        # The child watchdog is a last resort, never a passing-test condition.
        try:
            close()
        finally:
            if witness is not None:
                witness.close()


def assert_pipe_eof(read, deadline):
    while read() != b"":
        assert time.monotonic() < deadline, "descendant pipe remains open"
        time.sleep(0.02)


@pytest.mark.parametrize("parent_wait", [0, 20], ids=["parent-exited", "parent-live"])
@pytest.mark.parametrize("cleanup", ["owned-tree", "none", "parent-only"])
def test_native_pipe_witness_detects_incomplete_cleanup(
    tmp_path, monkeypatch, parent_wait, cleanup
):
    store = Store(tmp_path / "evidence", workers=STAGES)
    with ready_tree(tmp_path, parent_wait) as (tree, process, read, real_close):
        monkeypatch.setattr(tree, "spawn", lambda *a, **kw: process)
        monkeypatch.setattr(processes, "ProcessTree", lambda: tree)
        closed = []

        def close():
            closed.append(True)
            if cleanup == "owned-tree":
                real_close()
            elif cleanup == "parent-only":
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=2)
                process.stdout.close()
            # "none" intentionally leaves the tree and pipe open.

        monkeypatch.setattr(tree, "close", close)
        started = time.monotonic()
        result = processes.capture(store, "windows", ["pre-armed-fixture"], 0.5)
        assert time.monotonic() - started < 3
        assert closed == [True]
        assert result["state"] == "HOLD" and result["reason"] == "TIMEOUT"
        assert result["timeout_seconds"] == 0.5
        assert result["elapsed_seconds"] >= 0.5
        assert result["log_bytes_used"] == 0 and not result["output_complete"]
        assert result["tree_cleanup_failure"] is None

        if cleanup == "owned-tree":
            assert_pipe_eof(read, started + 3)
        else:
            # A false-success cleanup must be rejected, not retried or skipped.
            with pytest.raises(AssertionError, match="descendant pipe remains open"):
                assert_pipe_eof(read, time.monotonic() + 0.1)

        store.finish("windows", result)
        receipt = json.loads(
            (store.root / "records/logs/windows-final.json").read_bytes()
        )
        assert all(receipt[key] == value for key, value in result.items())
        assert store.audit()["total_bytes"] > 0
