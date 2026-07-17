"""Background rotating-log configuration tests."""

from __future__ import annotations

import logging
import weakref
from pathlib import Path

from beetales_translator_lens.storage.logging_setup import configure_logging


def test_logging_writes_to_the_private_log_directory(tmp_path: Path) -> None:
    manager = configure_logging(tmp_path)
    logging.getLogger("beetales.test").info("operational test message")

    manager.close()

    content = (tmp_path / "beetales.log").read_text(encoding="utf-8")
    assert "operational test message" in content


def test_log_manager_supports_qt_weak_references(tmp_path: Path) -> None:
    manager = configure_logging(tmp_path)

    reference = weakref.ref(manager)

    assert reference() is manager
    manager.close()


def test_third_party_info_cannot_repeat_recognized_text(tmp_path: Path) -> None:
    manager = configure_logging(tmp_path)
    logging.getLogger("argostranslate.utils").info("private recognized text")
    logging.getLogger("beetales.pipeline").info("translation completed")

    manager.close()

    content = (tmp_path / "beetales.log").read_text(encoding="utf-8")
    assert "private recognized text" not in content
    assert "translation completed" in content
