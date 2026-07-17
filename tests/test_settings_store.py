"""Settings persistence, validation, and recovery tests."""

from __future__ import annotations

import json
from pathlib import Path

from beetales_translator_lens.constants import DEFAULT_OVERLAY_GEOMETRY
from beetales_translator_lens.storage.settings_store import AppSettings, SettingsStore


def test_defaults_are_safe() -> None:
    settings = AppSettings()
    assert settings.source_language == "pl"
    assert settings.target_language == "es"
    assert settings.capture_interval_ms == 750
    assert settings.overlay_locked is False


def test_settings_round_trip_preserves_languages_and_geometry(tmp_path: Path) -> None:
    path = tmp_path / "folder with spaces" / "settings.json"
    store = SettingsStore(path)
    expected = AppSettings(
        source_language="ja",
        target_language="pt",
        overlay_locked=True,
        overlay_geometry={"x": -1200, "y": 80, "width": 740, "height": 300},
        panel_geometry={"x": 30, "y": 420, "width": 640, "height": 390},
    )

    store.save(expected)
    actual = store.load()

    assert actual.source_language == "ja"
    assert actual.target_language == "pt"
    assert actual.overlay_locked is True
    assert actual.overlay_geometry == expected.overlay_geometry
    assert actual.panel_geometry == expected.panel_geometry


def test_auto_source_is_valid_and_updates_detection_flag(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"source_language": "auto", "target_language": "es"}),
        encoding="utf-8",
    )

    settings = SettingsStore(path).load()

    assert settings.source_language == "auto"
    assert settings.auto_detect_language is True


def test_invalid_values_fall_back_without_crashing(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "source_language": "xx",
                "target_language": 42,
                "capture_interval_ms": 17,
                "overlay_locked": "yes",
                "overlay_geometry": {"x": 1},
                "unknown_future_option": True,
            }
        ),
        encoding="utf-8",
    )

    settings = SettingsStore(path).load()

    assert settings.source_language == "pl"
    assert settings.target_language == "es"
    assert settings.capture_interval_ms == 750
    assert settings.overlay_locked is False
    assert settings.overlay_geometry == DEFAULT_OVERLAY_GEOMETRY


def test_manual_capture_interval_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"capture_interval_ms": 0}), encoding="utf-8")

    assert SettingsStore(path).load().capture_interval_ms == 0


def test_ocr_download_consent_is_persisted(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    settings = AppSettings(ocr_model_download_consent=True)

    store.save(settings)

    assert store.load().ocr_model_download_consent is True


def test_translation_preferences_are_persisted(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    settings = AppSettings(
        preserve_message_prefixes=False,
        translation_cache_size=750,
    )

    store.save(settings)
    actual = store.load()

    assert actual.preserve_message_prefixes is False
    assert actual.translation_cache_size == 750


def test_invalid_translation_cache_size_uses_default(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"translation_cache_size": 1}), encoding="utf-8")

    assert SettingsStore(path).load().translation_cache_size == 500


def test_corrupt_file_is_backed_up_and_defaults_are_restored(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{not valid json", encoding="utf-8")

    settings = SettingsStore(path).load()

    assert settings == AppSettings()
    assert not path.exists()
    backups = list(tmp_path.glob("settings.corrupt-*.json"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "{not valid json"
