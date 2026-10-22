"""Bounded retries for Windows file-handle contention at publication only."""

from __future__ import annotations

import os
from collections.abc import Callable
from time import monotonic, sleep
from typing import TypeVar

_WINDOWS = os.name == "nt"
_RETRY_ERRORS = frozenset({5, 32, 33})
_RETRY_DELAYS = (0.025, 0.05, 0.1, 0.2)
_RETRY_WINDOW = 0.5
_T = TypeVar("_T")


def retry_publication(operation: Callable[[], _T]) -> _T:
    """Retry the same atomic operation, not its writes or scientific work.

    Access denial can be permanent: exhaustion still raises the native error.
    The deadline bounds eligibility for another attempt, not OS syscall time.
    Callers retain responsibility for containment and collision checks on every
    attempt, and for retaining completed artifacts if publication still fails.
    """
    if not _WINDOWS:
        return operation()
    deadline = monotonic() + _RETRY_WINDOW
    attempt = 0
    while True:
        try:
            return operation()
        except OSError as exc:
            if getattr(exc, "winerror", None) not in _RETRY_ERRORS or attempt == len(
                _RETRY_DELAYS
            ):
                raise
            delay = _RETRY_DELAYS[attempt]
            if monotonic() + delay >= deadline:
                raise
            sleep(delay)
            if monotonic() >= deadline:
                raise
            attempt += 1
