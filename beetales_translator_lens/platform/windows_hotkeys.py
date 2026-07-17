"""Native Windows global hotkeys with a Qt event-filter bridge."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008


def parse_hotkey(sequence: str) -> tuple[int, int] | None:
    parts = [part.strip().upper() for part in sequence.split("+") if part.strip()]
    if not parts:
        return None
    modifiers = 0
    key: int | None = None
    for part in parts:
        if part in {"CTRL", "CONTROL"}:
            modifiers |= MOD_CONTROL
        elif part == "SHIFT":
            modifiers |= MOD_SHIFT
        elif part == "ALT":
            modifiers |= MOD_ALT
        elif part in {"WIN", "WINDOWS"}:
            modifiers |= MOD_WIN
        elif len(part) == 1 and part.isalnum():
            key = ord(part)
        elif part.startswith("F") and part[1:].isdigit() and 1 <= int(part[1:]) <= 24:
            key = 0x70 + int(part[1:]) - 1
        else:
            return None
    return (modifiers, key) if key is not None else None


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class GlobalHotkeyManager(QObject, QAbstractNativeEventFilter):
    activated = Signal(str)

    def __init__(self) -> None:
        QObject.__init__(self)
        QAbstractNativeEventFilter.__init__(self)
        self._registered: dict[int, str] = {}

    @property
    def supported(self) -> bool:
        return sys.platform == "win32"

    def register(self, shortcuts: dict[str, str]) -> dict[str, bool]:
        self.unregister_all()
        results: dict[str, bool] = {}
        if not self.supported:
            return {action: False for action in shortcuts}
        user32 = ctypes.windll.user32
        for identifier, (action, sequence) in enumerate(shortcuts.items(), start=0xBEE0):
            parsed = parse_hotkey(sequence)
            success = bool(parsed and user32.RegisterHotKey(None, identifier, parsed[0], parsed[1]))
            results[action] = success
            if success:
                self._registered[identifier] = action
        return results

    def unregister_all(self) -> None:
        if self.supported:
            for identifier in self._registered:
                ctypes.windll.user32.UnregisterHotKey(None, identifier)
        self._registered.clear()

    def nativeEventFilter(self, event_type, message):  # type: ignore[no-untyped-def]
        del event_type
        if self.supported:
            native_message = ctypes.cast(int(message), ctypes.POINTER(_MSG)).contents
            if native_message.message == WM_HOTKEY:
                action = self._registered.get(int(native_message.wParam))
                if action:
                    self.activated.emit(action)
                    return True, 0
        return False, 0
