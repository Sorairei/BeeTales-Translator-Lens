"""Qt application creation and execution."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from beetales_translator_lens.constants import APP_NAME, VERSION
from beetales_translator_lens.platform.windows_dpi import enable_dpi_awareness
from beetales_translator_lens.storage.logging_setup import configure_logging
from beetales_translator_lens.storage.settings_store import SettingsStore
from beetales_translator_lens.ui.main_controller import MainController
from beetales_translator_lens.ui.theme import APP_STYLESHEET


def run_application() -> int:
    """Start BeeTales Translator Lens and return its exit code."""

    enable_dpi_awareness()
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)

    log_manager = configure_logging()
    logging.getLogger(__name__).info("Starting %s version %s", APP_NAME, VERSION)
    controller = MainController(app, SettingsStore())
    controller.show()
    # Keep the controller alive for the entire event loop.
    app.setProperty("mainController", controller)
    app.setProperty("logManager", log_manager)
    app.aboutToQuit.connect(
        lambda: logging.getLogger(__name__).info("Closing %s", APP_NAME)
    )
    app.aboutToQuit.connect(log_manager.close)
    return app.exec()
