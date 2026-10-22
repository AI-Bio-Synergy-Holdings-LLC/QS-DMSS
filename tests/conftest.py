"""Explicit native-handle fixtures; no global changes to filesystem behavior."""

import ctypes
import ctypes.wintypes as wintypes
import os
from contextlib import contextmanager

import pytest


@pytest.fixture
def windows_read_handle():
    if os.name != "nt":
        pytest.skip("Native Windows handle-sharing regression")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL

    @contextmanager
    def opened(path):
        handle = kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 0, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        closed = False

        def release():
            nonlocal closed
            if not closed:
                assert kernel.CloseHandle(handle)
                closed = True

        try:
            yield release
        finally:
            release()

    return opened
