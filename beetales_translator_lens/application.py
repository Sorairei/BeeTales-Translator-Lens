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
from beetales_translator_lens.platform.windows_dpi import enable_dpi_awareness, set_windows_app_user_model_id
from beetales_translator_lens.resources import application_icon_path, brand_logo_path, mascot_image_path
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
        "pyclipper",
        "pypdfium2",
    ):
        importlib.import_module(module_name)
    from paddlex.utils.deps import is_extra_available

    if not is_extra_available("ocr-core"):
        raise RuntimeError("The packaged PaddleX OCR core dependencies are incomplete.")
    for resource_path in (application_icon_path(), brand_logo_path(), mascot_image_path()):
        if not resource_path.is_file():
            raise FileNotFoundError(f"The packaged visual resource is missing: {resource_path.name}")
    return 0


def run_ocr_self_test() -> int:
    """Recognize generated text with the real local OCR pipeline."""

    import cv2
    import numpy as np

    from beetales_translator_lens.ocr.paddle_engine import PaddleOCREngine

    image = np.full((180, 900, 3), 255, dtype=np.uint8)
    cv2.putText(
        image,
        "BEETALES OCR TEST",
        (25, 115),
        cv2.FONT_HERSHEY_SIMPLEX,
        2.1,
        (0, 0, 0),
        5,
        cv2.LINE_AA,
    )
    result = PaddleOCREngine(minimum_confidence=0.20).recognize(image, "en")
    if result.error:
        raise RuntimeError(result.error)
    if not result.full_text.strip():
        raise RuntimeError("The real OCR self-test did not recognize any text.")
    return 0


def run_application() -> int:
    """Start BeeTales Translator Lens and return its exit code."""

    if "--self-test" in sys.argv or "--ocr-self-test" in sys.argv:
        report_path = Path(tempfile.gettempdir()) / "beetales-translator-lens-self-test.log"
        try:
            result = run_packaging_self_test()
            if "--ocr-self-test" in sys.argv:
                result = run_ocr_self_test()
                message = "BeeTales packaging and real OCR self-tests passed.\n"
            else:
                message = "BeeTales packaging self-test passed.\n"
            report_path.write_text(message, encoding="utf-8")
        except Exception:
            report_path.write_text(traceback.format_exc(), encoding="utf-8")
            result = 1
        # Some native inference libraries keep background threads alive after
        # import. The diagnostic mode must still provide a deterministic exit.
        os._exit(result)

    enable_dpi_awareness()
    set_windows_app_user_model_id("BeeTales.TranslatorLens")
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
