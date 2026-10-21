"""Owned process trees and single-reader, nonblocking pipe capture."""

import ctypes as C
import math
import os
import signal
import subprocess
import sys
import time

from .contract import LOG_BYTES, Hold


def windows_job():
    import ctypes.wintypes as W

    class Basic(C.Structure):
        _fields_ = [
            ("times", C.c_longlong * 2),
            ("flags", W.DWORD),
            ("working_set", C.c_size_t * 2),
            ("active", W.DWORD),
            ("affinity", C.c_size_t),
            ("classes", W.DWORD * 2),
        ]

    class Limits(C.Structure):
        _fields_ = [
            ("basic", Basic),
            ("io", C.c_ulonglong * 6),
            ("memory", C.c_size_t * 4),
        ]

    api = C.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateJobObjectW": ([C.c_void_p, W.LPCWSTR], W.HANDLE),
        "SetInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
        "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
        "CloseHandle": ([W.HANDLE], W.BOOL),
        "PeekNamedPipe": (
            [W.HANDLE, C.c_void_p, W.DWORD, C.c_void_p, C.POINTER(W.DWORD), C.c_void_p],
            W.BOOL,
        ),
    }
    for name, (args, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes, function.restype = args, result
    handle = api.CreateJobObjectW(None, None)
    if not handle:
        raise C.WinError(C.get_last_error())
    limits = Limits()
    limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
    if not api.SetInformationJobObject(handle, 9, C.byref(limits), C.sizeof(limits)):
        error = C.get_last_error()
        api.CloseHandle(handle)
        raise C.WinError(error)
    return api, handle


class ProcessTree:
    def __init__(self):
        self.process = self.api = self.job = None

    def spawn(self, command, *, cache, **kwargs):
        if os.name == "nt":
            self.api, self.job = windows_job()
            cache.mkdir(exist_ok=False)
            # Trusted stdlib wrapper waits before spawning, so assignment has
            # no descendant race. Its child exit status remains authoritative.
            gate = "import sys,subprocess;raise SystemExit(subprocess.call(sys.argv[1:],stdin=subprocess.DEVNULL) if sys.stdin.buffer.read(1)==b'1' else 125)"
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    "-X",
                    "pycache_prefix=" + str(cache),
                    "-c",
                    gate,
                    *command,
                ],
                stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                **kwargs,
            )
            if not self.api.AssignProcessToJobObject(
                self.job, int(self.process._handle)
            ):
                raise C.WinError(C.get_last_error())
            self.process.stdin.write(b"1")
            self.process.stdin.close()
        else:
            self.process = subprocess.Popen(
                command, stdin=subprocess.DEVNULL, start_new_session=True, **kwargs
            )
            os.set_blocking(self.process.stdout.fileno(), False)
        return self.process

    def read(self, ceiling):
        stream = self.process.stdout
        if os.name == "nt":
            import msvcrt

            available = C.c_ulong()
            if not self.api.PeekNamedPipe(
                msvcrt.get_osfhandle(stream.fileno()),
                None,
                0,
                None,
                C.byref(available),
                None,
            ):
                if C.get_last_error() == 109:  # Broken pipe means EOF.
                    return b""
                raise C.WinError(C.get_last_error())
            if not available.value:
                return None
            ceiling = min(ceiling, available.value)
        try:
            return os.read(stream.fileno(), ceiling)
        except BlockingIOError:
            return None

    def close(self):
        try:
            if self.job:
                handle, self.job = self.job, None
                if not self.api.CloseHandle(handle):
                    raise C.WinError(C.get_last_error())
            elif self.process and os.name != "nt":
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Group already exited.
        finally:
            if self.process:
                try:
                    if self.process.poll() is None:
                        self.process.kill()
                    self.process.wait(timeout=2)
                finally:
                    # Raw FileIO, no reader thread and no contended buffer lock.
                    self.process.stdout.close()
                    if self.process.stdin and not self.process.stdin.closed:
                        self.process.stdin.close()


def bounded_timeout(timeout):
    if (
        type(timeout) not in (int, float)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 300
    ):
        raise Hold("Invalid worker timeout.")


def capture(store, role, command, timeout, environment=None):
    bounded_timeout(timeout)
    tree = ProcessTree()
    used, overflow, reason, cleanup = 0, None, None, None
    started = time.monotonic()
    try:
        process = tree.spawn(
            command,
            cache=store.root / "records/source" / ("cache-driver-" + role),
            cwd=store.root / "records/source",
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        with (store.root / "records/logs" / (role + ".log")).open(
            "r+b", buffering=0
        ) as log:
            while True:
                if time.monotonic() - started >= timeout:
                    reason = "TIMEOUT"
                    break
                data = tree.read(min(4096, LOG_BYTES - used + 1))
                if data:
                    retained = data[: LOG_BYTES - used]
                    written = log.write(retained)
                    used += written or 0
                    if written != len(retained):
                        reason = "LOG_STORAGE_FAILURE"
                        break
                    if len(data) > len(retained):
                        overflow, reason = (
                            data[len(retained) : len(retained) + 1].hex(),
                            "LOG_LIMIT",
                        )
                        break
                if data == b"" and process.poll() is not None:
                    reason = "WORKER_REFUSAL" if process.returncode else None
                    break
                store.audit()
                time.sleep(0.02)
            os.fsync(log.fileno())
        store.audit()
    except (OSError, subprocess.SubprocessError, Hold):
        reason = reason or "SUPERVISION_FAILURE"
    finally:
        try:
            tree.close()
        except (OSError, subprocess.SubprocessError):
            cleanup = "PROCESS_TREE_CLEANUP_UNVERIFIED"
            reason = reason or cleanup
    return dict(
        state="HOLD" if reason else "PASSED",
        reason=reason,
        tree_cleanup_failure=cleanup,
        log_bytes_used=used,
        overflow_byte_hex=overflow,
        output_complete=reason is None,
        timeout_seconds=timeout,
        elapsed_seconds=round(time.monotonic() - started, 6),
    )
