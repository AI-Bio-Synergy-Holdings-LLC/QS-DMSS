import errno
import json
import os
from pathlib import Path
from time import sleep

import pytest

from qs_dmss import publication
from qs_dmss.execution import LocalJobRegistry


def _denial(winerror=None):
    exc = PermissionError(errno.EACCES, "synthetic publication denial")
    if winerror is not None:
        exc.winerror = winerror
    return exc


@pytest.fixture
def clock(monkeypatch):
    state = {"now": 0.0, "delays": []}

    def advance(delay):
        state["delays"].append(delay)
        state["now"] += delay

    monkeypatch.setattr(publication, "_WINDOWS", True)
    monkeypatch.setattr(publication, "monotonic", lambda: state["now"])
    monkeypatch.setattr(publication, "sleep", advance)
    return state


@pytest.mark.parametrize("winerror", [5, 32, 33])
def test_publication_retries_only_native_contention_and_returns_result(clock, winerror):
    calls = []
    result = object()

    def operation():
        calls.append(True)
        if len(calls) < 5:
            raise _denial(winerror)
        return result

    assert publication.retry_publication(operation) is result
    assert len(calls) == 5
    assert clock["delays"] == [0.025, 0.05, 0.1, 0.2]


@pytest.mark.parametrize("winerror", [5, 32, 33])
def test_publication_exhaustion_raises_last_native_error(clock, winerror):
    failures = []

    def operation():
        exc = _denial(winerror)
        failures.append(exc)
        raise exc

    with pytest.raises(PermissionError) as caught:
        publication.retry_publication(operation)
    assert caught.value is failures[-1]
    assert len(failures) == 5
    assert len(clock["delays"]) == 4


@pytest.mark.parametrize("winerror", [None, 2, 17, 183])
def test_other_os_errors_are_not_retried(clock, winerror):
    exc = _denial(winerror)

    def operation():
        raise exc

    with pytest.raises(PermissionError) as caught:
        publication.retry_publication(operation)
    assert caught.value is exc
    assert clock["delays"] == []


@pytest.mark.parametrize("exception", [ValueError("identity"), RuntimeError("bug")])
def test_non_os_failures_are_not_retried(clock, exception):
    def operation():
        raise exception

    with pytest.raises(type(exception)) as caught:
        publication.retry_publication(operation)
    assert caught.value is exception
    assert clock["delays"] == []


def test_non_windows_preserves_single_attempt(clock, monkeypatch):
    monkeypatch.setattr(publication, "_WINDOWS", False)
    exc = _denial(5)

    def operation():
        raise exc

    with pytest.raises(PermissionError) as caught:
        publication.retry_publication(operation)
    assert caught.value is exc
    assert clock["delays"] == []
    assert publication.retry_publication(lambda: "ok") == "ok"


@pytest.mark.parametrize("oversleep", [False, True])
def test_deadline_refuses_attempts_after_slow_syscall_or_sleep(
    clock, monkeypatch, oversleep
):
    calls = []
    exc = _denial(5)

    def operation():
        calls.append(True)
        if not oversleep:
            clock["now"] += 1
        raise exc

    if oversleep:
        monkeypatch.setattr(publication, "sleep", lambda _: clock.update(now=1))
    with pytest.raises(PermissionError) as caught:
        publication.retry_publication(operation)
    assert caught.value is exc
    assert len(calls) == 1


@pytest.mark.parametrize("failure_count", [1, 4, 5])
def test_registry_retries_only_publication_and_preserves_bytes(
    tmp_path, monkeypatch, clock, failure_count
):
    path = tmp_path / "job.json"
    path.write_bytes(b'{"state":"submitted"}\n')
    original = path.read_bytes()
    temporary = path.with_suffix(".json.tmp")
    payload = {"state": "running"}
    expected = (
        (json.dumps(payload, indent=2, sort_keys=True) + "\n")
        .replace("\n", os.linesep)
        .encode()
    )
    replace = Path.replace
    writes = []
    write = Path.write_text
    attempts = []

    def tracked_write(candidate, *args, **kwargs):
        if candidate == temporary:
            writes.append(True)
        return write(candidate, *args, **kwargs)

    def contended(candidate, target):
        assert candidate == temporary and target == path
        assert temporary.read_bytes() == expected
        assert path.read_bytes() == original
        attempts.append(True)
        if len(attempts) <= failure_count:
            raise _denial(5)
        return replace(candidate, target)

    monkeypatch.setattr(Path, "write_text", tracked_write)
    monkeypatch.setattr(Path, "replace", contended)
    registry = LocalJobRegistry(tmp_path / "unused-jobs")
    if failure_count == 5:
        with pytest.raises(PermissionError):
            registry._write_record(path, payload)
        assert path.read_bytes() == original
        assert temporary.read_bytes() == expected
    else:
        registry._write_record(path, payload)
        assert path.read_bytes() == expected
        assert not temporary.exists()
    assert len(writes) == 1
    assert len(attempts) == min(failure_count + 1, 5)


@pytest.mark.parametrize("release_during_backoff", [False, True])
def test_registry_real_windows_destination_handle(
    tmp_path, monkeypatch, windows_read_handle, release_during_backoff
):
    path = tmp_path / "job.json"
    original = b'{"state":"submitted"}\n'
    path.write_bytes(original)
    registry = LocalJobRegistry(tmp_path / "unused-jobs")
    delays = []
    with windows_read_handle(path) as release:

        def wait(delay):
            delays.append(delay)
            if release_during_backoff:
                release()
            sleep(delay)

        monkeypatch.setattr(publication, "sleep", wait)
        if release_during_backoff:
            registry._write_record(path, {"state": "running"})
            assert json.loads(path.read_bytes()) == {"state": "running"}
            assert delays[0] == 0.025 and 1 <= len(delays) <= 4
        else:
            with pytest.raises(PermissionError) as caught:
                registry._write_record(path, {"state": "running"})
            assert caught.value.winerror == 5
            assert path.read_bytes() == original
            assert path.with_suffix(".json.tmp").is_file()
            assert 1 <= len(delays) <= 4
