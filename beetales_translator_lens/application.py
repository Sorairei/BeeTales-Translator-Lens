"""Qt application creation and execution."""

from __future__ import annotations

import importlib
import logging
import os
import sys
import tempfile
import traceback
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from beetales_translator_lens.constants import APP_NAME, VERSION
from beetales_translator_lens.platform.windows_dpi import enable_dpi_awareness
from beetales_translator_lens.resources import application_icon_path
from beetales_translator_lens.storage.logging_setup import configure_logging
from beetales_translator_lens.storage.settings_store import SettingsStore
from beetales_translator_lens.ui.main_controller import MainController
from beetales_translator_lens.ui.theme import APP_STYLESHEET


def run_packaging_self_test() -> int:
    """Import the packaged runtime stack without opening the interface."""

    from beetales_translator_lens.ocr.paddle_engine import install_modelscope_compatibility_stub
    from beetales_translator_lens.translation.argos_support import configure_argos_environment

    configure_argos_environment()
    install_modelscope_compatibility_stub()
    for module_name in (
        "argostranslate.translate",
        "ctranslate2",
        "cv2",
        "lingua",
        "minisbd",
        "mss",
        "numpy",
        "paddle",
        "paddleocr._pipelines.ocr",
        "paddlex.inference.pipelines.ocr",
    ):
        importlib.import_module(module_name)
    if not application_icon_path().is_file():
        raise FileNotFoundError("The packaged application icon is missing.")
    return 0


def run_application() -> int:
    """Start BeeTales Translator Lens and return its exit code."""

    if "--self-test" in sys.argv:
        report_path = Path(tempfile.gettempdir()) / "beetales-translator-lens-self-test.log"
        try:
            result = run_packaging_self_test()
            report_path.write_text("BeeTales packaging self-test passed.\n", encoding="utf-8")
        except Exception:
            report_path.write_text(traceback.format_exc(), encoding="utf-8")
            result = 1
        # Some native inference libraries keep background threads alive after
        # import. The diagnostic mode must still provide a deterministic exit.
        os._exit(result)

    enable_dpi_awareness()
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setWindowIcon(QIcon(str(application_icon_path())))
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
