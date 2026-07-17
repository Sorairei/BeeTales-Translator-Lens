"""Global-hotkey parsing tests independent from the Windows API."""

from beetales_translator_lens.platform.windows_hotkeys import (
    MOD_ALT, MOD_CONTROL, MOD_SHIFT, parse_hotkey,
)


def test_parse_letter_hotkey() -> None:
    assert parse_hotkey("Ctrl+Shift+T") == (MOD_CONTROL | MOD_SHIFT, ord("T"))


def test_parse_function_key() -> None:
    assert parse_hotkey("Alt+F12") == (MOD_ALT, 0x7B)


def test_invalid_hotkey_is_rejected() -> None:
    assert parse_hotkey("Ctrl+Banana") is None
    assert parse_hotkey("") is None
