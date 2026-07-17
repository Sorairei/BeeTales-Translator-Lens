"""Compatibilidad de escalado DPI para Windows 10 y 11."""

from __future__ import annotations

import ctypes
import logging
import sys

LOGGER = logging.getLogger(__name__)


def enable_dpi_awareness() -> bool:
    """Activa DPI por monitor usando la mejor API disponible."""

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
        LOGGER.warning("No se pudo activar la compatibilidad DPI: %s", exc)
        return False
