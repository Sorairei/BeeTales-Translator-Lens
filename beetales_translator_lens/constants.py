"""Constants shared throughout the application."""

from __future__ import annotations

from enum import StrEnum

APP_NAME = "BeeTales Translator Lens"
APP_AUTHOR = "BeeTales"
VERSION = "0.2.0"


class LensState(StrEnum):
    """Visual states shown by the capture lens."""

    IDLE = "Waiting for text…"
    ACTIVE = "Active"
    CAPTURING = "Reading…"
    PAUSED = "Paused"
    LOCKED = "Locked"
    ERROR = "Error"


LANGUAGES: dict[str, str] = {
    "es": "Spanish",
    "en": "English",
    "pl": "Polish",
    "ja": "Japanese",
    "pt": "Portuguese",
}

SOURCE_LANGUAGES: tuple[tuple[str, str], ...] = (
    ("auto", "Automatic"),
    *tuple(LANGUAGES.items()),
)
TARGET_LANGUAGES: tuple[tuple[str, str], ...] = tuple(LANGUAGES.items())

DEFAULT_OVERLAY_GEOMETRY = {"x": 120, "y": 120, "width": 620, "height": 250}
DEFAULT_PANEL_GEOMETRY = {"x": 120, "y": 386, "width": 620, "height": 370}

SIMULATED_ORIGINAL = "Czy ktoś chce zagrać dzisiaj?"
SIMULATED_TRANSLATION = "¿Alguien quiere jugar hoy?"
