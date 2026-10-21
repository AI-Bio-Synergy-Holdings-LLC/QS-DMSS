"""Supervise four fixed synthetic modes, not arbitrary commands or datasets."""

import os
import subprocess
import sys
import threading
import time

from .contract import LOG_BYTES, WORKERS, Hold
from .retention import digest


def fingerprints(store):
    root = store.root / "records/source"
    return {
        path.relative_to(root).as_posix(): digest(path, 256 * 1024)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def run_worker(store, mode, timeout_seconds=300):
    if (
        mode not in WORKERS
        or type(timeout_seconds) not in (int, float)
        or not 0 < timeout_seconds <= 300
    ):
        raise Hold("Only fixed synthetic workers and bounded timeouts are admitted.")
    before = fingerprints(store)
    captured = {"bytes": 0, "overflow_byte_hex": None, "read_failed": False}
    exceeded = threading.Event()
    started = time.monotonic()
    process = None
    reader = None
    reason = None
    after = {}
    log_path = store.root / "records/logs" / (mode + ".log")
    try:
        flags = (
            (
                getattr(subprocess, "CREATE_NO_WINDOW", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
            if os.name == "nt"
            else 0
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-B",
                "-m",
                "research.cern_dimuon_qualification.preflight",
                "--worker",
                mode,
            ],
            cwd=store.root / "records/source",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )

        def capture():
            try:
                with log_path.open("r+b") as log:
                    while True:
                        remaining = LOG_BYTES - captured["bytes"]
                        chunk = process.stdout.read(min(4096, remaining + 1))
                        if not chunk:
                            break
                        retained = chunk[:remaining]
                        log.write(retained)
                        log.flush()
                        captured["bytes"] += len(retained)
                        if len(chunk) > remaining:
                            captured["overflow_byte_hex"] = chunk[-1:].hex()
                            exceeded.set()
                            break
                    os.fsync(log.fileno())
            except (OSError, ValueError):
                captured["read_failed"] = True
                exceeded.set()

        reader = threading.Thread(target=capture, daemon=True)
        reader.start()
        while process.poll() is None:
            if exceeded.wait(0.02):
                reason = (
                    "LOG_LIMIT"
                    if not captured["read_failed"]
                    else "LOG_STORAGE_FAILURE"
                )
                break
            if time.monotonic() - started >= timeout_seconds:
                reason = "TIMEOUT"
                break
        if reason and process.poll() is None:
            process.kill()
        process.wait(timeout=2)
        reader.join(timeout=2)
        if reader.is_alive():
            raise Hold("Fixed worker log stream did not terminate.")
        if exceeded.is_set():
            reason = "LOG_STORAGE_FAILURE" if captured["read_failed"] else "LOG_LIMIT"
        try:
            after = fingerprints(store)
        except (OSError, Hold):
            after = {"identity_read": "REFUSED"}
        if after != before:
            reason = "SOURCE_DRIFT"
        if process.returncode != 0 and reason is None:
            reason = "WORKER_FAILURE"
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
        "observed_seconds": round(time.monotonic() - started, 6),
        "timeout_seconds": timeout_seconds,
        "log_capacity_bytes": LOG_BYTES,
        "log_bytes_used": captured["bytes"],
        "overflow_byte_hex": captured["overflow_byte_hex"],
        "output_complete": reason is None,
        "source_before": before,
        "source_after": after,
        "scope": "Fixed reviewed no-child synthetic worker; not a hostile-code/RSS sandbox",
    }
    store.finish(mode, result)
    store.audit()
    return result
