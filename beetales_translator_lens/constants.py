"""Constants shared throughout the application."""

from __future__ import annotations

from enum import StrEnum

APP_NAME = "BeeTales Translator Lens"
APP_AUTHOR = "BeeTales"
VERSION = "0.6.0"


class LensState(StrEnum):
    """Visual states shown by the capture lens."""

    IDLE = "Waiting for text…"
    ACTIVE = "Active"
    CAPTURING = "Reading…"
    OCR_PROCESSING = "Recognizing…"
    TRANSLATING = "Translating…"
    DOWNLOADING_MODEL = "Downloading model…"
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
