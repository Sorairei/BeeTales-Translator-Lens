"""Exclude application windows through SetWindowDisplayAffinity."""

from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

LOGGER = logging.getLogger(__name__)

WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011


def exclude_window_from_capture(window_handle: int) -> bool:
    """Apply and verify WDA_EXCLUDEFROMCAPTURE on Windows 10 2004+."""

    if sys.platform != "win32" or not window_handle:
        return False
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        setter = user32.SetWindowDisplayAffinity
        setter.argtypes = [wintypes.HWND, wintypes.DWORD]
        setter.restype = wintypes.BOOL
        getter = user32.GetWindowDisplayAffinity
        getter.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        getter.restype = wintypes.BOOL

        handle = wintypes.HWND(window_handle)
        if not setter(handle, WDA_EXCLUDEFROMCAPTURE):
            LOGGER.warning("SetWindowDisplayAffinity failed: %s", ctypes.get_last_error())
            return False
        affinity = wintypes.DWORD()
        if not getter(handle, ctypes.byref(affinity)):
            LOGGER.warning("GetWindowDisplayAffinity failed: %s", ctypes.get_last_error())
            return False
        return affinity.value == WDA_EXCLUDEFROMCAPTURE
    except (AttributeError, OSError, ValueError) as exc:
        LOGGER.warning("Capture exclusion is unavailable: %s", exc)
        return False


def restore_window_capture(window_handle: int) -> bool:
    """Restore the default capture affinity for a window."""

    if sys.platform != "win32" or not window_handle:
        return False
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        return bool(user32.SetWindowDisplayAffinity(wintypes.HWND(window_handle), WDA_NONE))
    except (AttributeError, OSError, ValueError):
        return False
