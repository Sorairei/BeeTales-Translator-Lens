"""DPI scaling support for Windows 10 and 11."""

from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

LOGGER = logging.getLogger(__name__)


def enable_dpi_awareness() -> bool:
    """Enable per-monitor DPI awareness through the best available API."""

    if sys.platform != "win32":
        return False
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return True
    except (AttributeError, OSError):
        pass
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return True
    except (AttributeError, OSError):
        pass
    try:
        return bool(ctypes.windll.user32.SetProcessDPIAware())
    except (AttributeError, OSError) as exc:
        LOGGER.warning("Could not enable DPI awareness: %s", exc)
        return False


def physical_window_rect(window_handle: int) -> tuple[int, int, int, int] | None:
    """Return the physical rectangle of a DPI-aware Windows window."""

    if sys.platform != "win32" or not window_handle:
        return None
    rect = wintypes.RECT()
    try:
        if not ctypes.windll.user32.GetWindowRect(wintypes.HWND(window_handle), ctypes.byref(rect)):
            return None
    except (AttributeError, OSError, ValueError):
        return None
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
