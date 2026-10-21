"""Fixed synthetic controls over the shared bounded process backend."""

import sys

from .contract import LOG_BYTES, WORKERS, Hold
from .processes import bounded_timeout, capture
from .retention import digest


def fingerprints(store):
    root = store.root / "records/source"
    return {
        path.relative_to(root).as_posix(): digest(path, 256 * 1024)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def run_worker(store, mode, timeout_seconds=300):
    if mode not in WORKERS:
        raise Hold("Only fixed synthetic workers are admitted.")
    bounded_timeout(timeout_seconds)
    before = fingerprints(store)
    command = [
        sys.executable,
        "-B",
        "-m",
        "research.cern_dimuon_qualification.preflight",
        "--worker",
        mode,
    ]
    result = capture(store, mode, command, timeout_seconds)
    try:
        after = fingerprints(store)
    except (OSError, Hold):
        after = {"identity_read": "REFUSED"}
    reason = result["reason"]
    if before != after:
        reason = "SOURCE_DRIFT"
    elif reason == "WORKER_REFUSAL":
        reason = "WORKER_FAILURE"
    result.update(
        state="HOLD" if reason else "PASSED",
        reason=reason,
        output_complete=reason is None,
        observed_seconds=result.pop("elapsed_seconds"),
        log_capacity_bytes=LOG_BYTES,
        source_before=before,
        source_after=after,
        scope="Fixed reviewed no-child synthetic worker; not a hostile-code/RSS sandbox",
    )
    store.finish(mode, result)
    store.audit()
    return result
