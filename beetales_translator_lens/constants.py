"""Constantes compartidas por la aplicación."""

from __future__ import annotations

from enum import StrEnum

APP_NAME = "BeeTales Translator Lens"
APP_AUTHOR = "BeeTales"
VERSION = "0.1.0"


class LensState(StrEnum):
    """Estados visibles disponibles durante la Fase 1."""

    IDLE = "Esperando texto…"
    ACTIVE = "Activa"
    PAUSED = "Pausada"
    LOCKED = "Bloqueada"
    ERROR = "Error"


LANGUAGES: dict[str, str] = {
    "es": "Español",
    "en": "Inglés",
    "pl": "Polaco",
    "ja": "Japonés",
    "pt": "Portugués",
}

SOURCE_LANGUAGES: tuple[tuple[str, str], ...] = (
    ("auto", "Automático"),
    *tuple(LANGUAGES.items()),
)
TARGET_LANGUAGES: tuple[tuple[str, str], ...] = tuple(LANGUAGES.items())

DEFAULT_OVERLAY_GEOMETRY = {"x": 120, "y": 120, "width": 620, "height": 250}
DEFAULT_PANEL_GEOMETRY = {"x": 120, "y": 386, "width": 620, "height": 370}

SIMULATED_ORIGINAL = "Czy ktoś chce zagrać dzisiaj?"
SIMULATED_TRANSLATION = "¿Alguien quiere jugar hoy?"
