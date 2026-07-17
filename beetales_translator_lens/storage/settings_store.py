"""Validated JSON settings with corrupt-file recovery."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from beetales_translator_lens.constants import (
    DEFAULT_OVERLAY_GEOMETRY,
    DEFAULT_PANEL_GEOMETRY,
    LANGUAGES,
)
from beetales_translator_lens.storage.paths import ensure_data_directories

LOGGER = logging.getLogger(__name__)
VALID_SOURCES = {"auto", *LANGUAGES}


def _geometry(default: dict[str, int]) -> dict[str, int]:
    return dict(default)


@dataclass(slots=True)
class AppSettings:
    """Persistent application preferences."""

    source_language: str = "pl"
    target_language: str = "es"
    capture_interval_ms: int = 750
    change_sensitivity: str = "normal"
    preprocessing_profile: str = "dark_background"
    show_original_text: bool = True
    translation_panel_position: str = "bottom"
    click_through: bool = False
    history_enabled: bool = False
    persistent_cache_enabled: bool = False
    history_max_entries: int = 1000
    first_run_completed: bool = False
    start_minimized: bool = False
    theme: str = "dark"
    translation_font_size: int = 10
    global_hotkeys_enabled: bool = True
    shortcuts: dict[str, str] = field(
        default_factory=lambda: {
            "toggle_visibility": "Ctrl+Shift+T",
            "pause_resume": "Ctrl+Shift+P",
            "copy_translation": "Ctrl+Shift+C",
            "toggle_lock": "Ctrl+Shift+L",
            "force_read": "Ctrl+Shift+R",
            "toggle_click_through": "Ctrl+Shift+X",
        }
    )
    overlay_locked: bool = False
    auto_detect_language: bool = False
    ocr_model_download_consent: bool = False
    preserve_message_prefixes: bool = True
    translation_cache_size: int = 500
    overlay_geometry: dict[str, int] = field(
        default_factory=lambda: _geometry(DEFAULT_OVERLAY_GEOMETRY)
    )
    panel_geometry: dict[str, int] = field(
        default_factory=lambda: _geometry(DEFAULT_PANEL_GEOMETRY)
    )

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "AppSettings":
        """Create safe settings while ignoring unknown or future keys."""

        defaults = cls()
        source = data.get("source_language")
        target = data.get("target_language")
        if source in VALID_SOURCES:
            defaults.source_language = source
        if target in LANGUAGES:
            defaults.target_language = target
        if defaults.source_language != "auto" and defaults.source_language == defaults.target_language:
            defaults.source_language = "pl" if defaults.target_language != "pl" else "en"

        for key in (
            "show_original_text",
            "click_through",
            "history_enabled",
            "persistent_cache_enabled",
            "first_run_completed",
            "start_minimized",
            "global_hotkeys_enabled",
            "overlay_locked",
            "auto_detect_language",
            "ocr_model_download_consent",
            "preserve_message_prefixes",
        ):
            value = data.get(key)
            if isinstance(value, bool):
                setattr(defaults, key, value)

        interval = data.get("capture_interval_ms")
        if isinstance(interval, int) and interval in {0, 250, 500, 750, 1000, 1500, 2000}:
            defaults.capture_interval_ms = interval

        cache_size = data.get("translation_cache_size")
        if isinstance(cache_size, int) and 10 <= cache_size <= 10_000:
            defaults.translation_cache_size = cache_size

        history_max_entries = data.get("history_max_entries")
        if isinstance(history_max_entries, int) and 10 <= history_max_entries <= 10_000:
            defaults.history_max_entries = history_max_entries

        if not defaults.history_enabled:
            defaults.persistent_cache_enabled = False

        theme = data.get("theme")
        if theme in {"dark", "light"}:
            defaults.theme = theme

        font_size = data.get("translation_font_size")
        if isinstance(font_size, int) and 8 <= font_size <= 28:
            defaults.translation_font_size = font_size

        shortcuts = data.get("shortcuts")
        if isinstance(shortcuts, dict):
            for action, default_value in defaults.shortcuts.items():
                value = shortcuts.get(action)
                if isinstance(value, str) and value.strip():
                    defaults.shortcuts[action] = value.strip()

        for key, allowed in {
            "change_sensitivity": {"low", "normal", "high"},
            "preprocessing_profile": {
                "automatic", "dark_background", "light_background", "small_text", "japanese", "none"
            },
            "translation_panel_position": {"top", "bottom", "left", "right", "detached"},
        }.items():
            value = data.get(key)
            if value in allowed:
                setattr(defaults, key, value)

        defaults.overlay_geometry = _validated_geometry(
            data.get("overlay_geometry"), DEFAULT_OVERLAY_GEOMETRY
        )
        defaults.panel_geometry = _validated_geometry(
            data.get("panel_geometry"), DEFAULT_PANEL_GEOMETRY
        )
        defaults.auto_detect_language = defaults.source_language == "auto"
        return defaults


def _validated_geometry(value: Any, fallback: dict[str, int]) -> dict[str, int]:
    if not isinstance(value, dict):
        return dict(fallback)
    required = ("x", "y", "width", "height")
    if not all(isinstance(value.get(key), int) for key in required):
        return dict(fallback)
    width = max(240, min(value["width"], 8192))
    height = max(120, min(value["height"], 8192))
    return {"x": value["x"], "y": value["y"], "width": width, "height": height}


class SettingsStore:
    """Load and save settings through atomic writes."""

    def __init__(self, settings_file: Path | None = None) -> None:
        if settings_file is None:
            settings_file = ensure_data_directories()["config"] / "settings.json"
        self.path = Path(settings_file)

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("The settings root must be a JSON object")
            return AppSettings.from_mapping(raw)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            LOGGER.warning("Settings are corrupt; restoring defaults: %s", exc)
            self._backup_corrupt_file()
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        payload = json.dumps(asdict(settings), ensure_ascii=False, indent=2)
        temporary.write_text(payload + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def _backup_corrupt_file(self) -> None:
        if not self.path.exists():
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}")
        try:
            self.path.replace(backup)
        except OSError as exc:
            LOGGER.error("Could not back up the corrupt settings file: %s", exc)
