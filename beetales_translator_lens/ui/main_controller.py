"""Window coordination and Phase 2 regional capture."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QPoint, QRect, QThreadPool, QTimer, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox

from beetales_translator_lens.capture.change_detector import ChangeDetector
from beetales_translator_lens.capture.image_preprocessor import ImagePreprocessor
from beetales_translator_lens.constants import APP_NAME, LensState
from beetales_translator_lens.ocr.models import OCRResult
from beetales_translator_lens.ocr.paddle_engine import PaddleOCREngine
from beetales_translator_lens.platform.windows_capture_exclusion import exclude_window_from_capture
from beetales_translator_lens.storage.settings_store import SettingsStore
from beetales_translator_lens.ui.capture_overlay import CaptureOverlay
from beetales_translator_lens.ui.translation_panel import TranslationPanel
from beetales_translator_lens.workers.capture_worker import CaptureTask, FrameAnalysis
from beetales_translator_lens.workers.ocr_worker import OCRTask


class MainController(QObject):
    """Keep both windows synchronized and persist preferences."""

    def __init__(self, app: QApplication, store: SettingsStore) -> None:
        super().__init__()
        self.app = app
        self.store = store
        self.settings = store.load()
        self.overlay = CaptureOverlay()
        self.panel = TranslationPanel()
        self.thread_pool = QThreadPool.globalInstance()
        self.detector = ChangeDetector(self.settings.change_sensitivity)
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = PaddleOCREngine()
        self.capture_timer = QTimer(self)
        self.capture_timer.setTimerType(Qt.PreciseTimer)
        self.capture_timer.timeout.connect(self.request_capture)
        self._paused = False
        self._running = False
        self._processing = False
        self._closing = False
        self._capture_exclusion_ok = sys.platform != "win32"
        self._fallback_hidden = False
        self._active_task: CaptureTask | None = None
        self._latest_analysis: FrameAnalysis | None = None
        self._connect_signals()
        self._restore_settings()

    def _connect_signals(self) -> None:
        self.panel.start_requested.connect(self.start_capture)
        self.panel.pause_requested.connect(self.toggle_pause)
        self.panel.copy_requested.connect(self.copy_translation)
        self.panel.lock_requested.connect(self.toggle_lock)
        self.panel.close_requested.connect(self.close)
        self.panel.language_changed.connect(self._language_changed)
        self.panel.capture_settings_changed.connect(self._capture_settings_changed)
        self.overlay.geometry_changed.connect(self._capture_geometry_changed)
        self.app.aboutToQuit.connect(self.save_settings)

    def _restore_settings(self) -> None:
        self._apply_geometry(self.overlay, self.settings.overlay_geometry)
        self._apply_geometry(self.panel, self.settings.panel_geometry)
        self.panel.select_languages(self.settings.source_language, self.settings.target_language)
        self.panel.select_capture_settings(
            self.settings.capture_interval_ms,
            self.settings.change_sensitivity,
            self.settings.preprocessing_profile,
        )
        self.overlay.set_locked(self.settings.overlay_locked)
        self.panel.lock_button.setChecked(self.settings.overlay_locked)
        self.panel.lock_button.setText("Unlock lens" if self.settings.overlay_locked else "Lock lens")

    @staticmethod
    def _apply_geometry(widget, geometry: dict[str, int]) -> None:  # type: ignore[no-untyped-def]
        requested = QRect(geometry["x"], geometry["y"], geometry["width"], geometry["height"])
        screens = QGuiApplication.screens()
        visible = any(screen.availableGeometry().intersects(requested) for screen in screens)
        if not visible and screens:
            area = screens[0].availableGeometry()
            requested.moveTopLeft(area.topLeft() + QPoint(40, 40))
        widget.setGeometry(requested)

    def show(self) -> None:
        self.overlay.show()
        self.panel.show()
        self.overlay.raise_()
        self.panel.raise_()
        QTimer.singleShot(0, self._apply_capture_exclusion)

    def _apply_capture_exclusion(self) -> None:
        """Use the native API, falling back to brief per-cycle hiding."""

        if sys.platform != "win32":
            self._capture_exclusion_ok = True
            return
        self._capture_exclusion_ok = all(
            (
                exclude_window_from_capture(int(self.overlay.winId())),
                exclude_window_from_capture(int(self.panel.winId())),
            )
        )

    def start_capture(self) -> None:
        """Start the cycle or force a read when it is already active."""

        if not self.ocr_engine.is_available():
            self.panel.set_status(
                "OCR dependencies are not installed. Run pip install -r requirements.txt.",
                paused=True,
            )
            self.overlay.set_state(LensState.ERROR)
            return
        if not self.settings.ocr_model_download_consent:
            answer = QMessageBox.question(
                self.panel,
                APP_NAME,
                "The first OCR run for each language may download local PaddleOCR models. "
                "The models can use several hundred megabytes and remain on this computer. "
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                self.panel.set_status("OCR model download was cancelled.", paused=True)
                return
            self.settings.ocr_model_download_consent = True
            self.save_settings()

        already_running = self._running and not self._paused
        self._running = True
        self._paused = False
        self.panel.set_status("Preparing capture…")
        self.panel.start_button.setText("Force read")
        self.panel.pause_button.setEnabled(True)
        self.panel.pause_button.setText("Pause")
        self._configure_timer()
        self.request_capture(force=True if already_running else False)

    def _configure_timer(self) -> None:
        interval, _, _ = self.panel.selected_capture_settings()
        self.capture_timer.stop()
        if self._running and not self._paused and interval > 0:
            self.capture_timer.start(interval)

    def request_capture(self, force: bool = False) -> None:
        """Schedule at most one task and discard overlapping ticks."""

        if self._closing or self._paused or not self._running or self._processing:
            return
        region = self.overlay.capture_region()
        if not region.is_valid:
            self._capture_failed("The selected area is too small.")
            return
        self._processing = True
        self.overlay.set_state(LensState.CAPTURING)
        self.panel.set_status("Reading the selected area…")
        if sys.platform == "win32" and not self._capture_exclusion_ok:
            self._set_overlays_temporarily_hidden(True)
            QTimer.singleShot(35, lambda: self._submit_capture(region, force))
        else:
            self._submit_capture(region, force)

    def _submit_capture(self, region, force: bool) -> None:  # type: ignore[no-untyped-def]
        if self._closing:
            self._processing = False
            self._set_overlays_temporarily_hidden(False)
            return
        task = CaptureTask(
            region,
            self.detector,
            self.preprocessor,
            self.settings.preprocessing_profile,
            force=force,
        )
        task.signals.completed.connect(self._capture_completed)
        task.signals.failed.connect(self._capture_failed)
        self._active_task = task
        self.thread_pool.start(task)

    def _capture_completed(self, analysis: FrameAnalysis) -> None:
        self._active_task = None
        self._set_overlays_temporarily_hidden(False)
        if self.panel.preview_button.isChecked():
            preview = analysis.processed_image if analysis.processed_image is not None else analysis.capture.image
            self._show_preview(preview)

        if analysis.change.changed:
            if analysis.processed_image is None:
                self._capture_failed("The changed frame could not be preprocessed.")
                return
            self._latest_analysis = analysis
            source_language, _ = self.panel.selected_languages()
            self.overlay.set_state(LensState.OCR_PROCESSING)
            if source_language == "auto":
                self.panel.set_status(
                    "Recognizing with the English fallback model; automatic detection arrives in Phase 4…"
                )
            else:
                self.panel.set_status("Recognizing text…")
            task = OCRTask(self.ocr_engine, analysis.processed_image, source_language)
            task.signals.completed.connect(self._ocr_completed)
            self._active_task = task  # type: ignore[assignment]
            self.thread_pool.start(task)
        else:
            self._processing = False
            self.panel.set_status(
                f"No changes ({analysis.change.changed_ratio * 100:.1f}%)"
            )
            self.overlay.set_state(LensState.ACTIVE)

    def _ocr_completed(self, result: OCRResult) -> None:
        self._processing = False
        self._active_task = None
        if self._closing:
            return
        analysis = self._latest_analysis
        if result.error:
            self.panel.set_status(result.error, paused=True)
            self.overlay.set_state(LensState.ERROR)
            self._update_metrics(result, analysis)
            return
        if not result.full_text.strip():
            self.panel.clear_result()
            self.panel.set_status("No readable text was detected.", paused=True)
            self.overlay.set_state(LensState.ACTIVE)
            self._update_metrics(result, analysis)
            return
        self.panel.set_detected_text(result.full_text)
        self.panel.set_status(
            f"Recognized {len(result.lines)} line(s) · {result.average_confidence:.0%} confidence"
        )
        self.overlay.set_state(LensState.ACTIVE)
        self._update_metrics(result, analysis)

    def _update_metrics(
        self,
        result: OCRResult,
        analysis: FrameAnalysis | None,
    ) -> None:
        if analysis is None:
            self.panel.metrics_label.setText(f"OCR: {result.elapsed_ms:.0f} ms")
            return
        total = analysis.capture.elapsed_ms + analysis.preprocessing_ms + result.elapsed_ms
        self.panel.metrics_label.setText(
            f"Capture: {analysis.capture.elapsed_ms:.0f} ms · "
            f"Preprocess: {analysis.preprocessing_ms:.0f} ms · "
            f"OCR: {result.elapsed_ms:.0f} ms · Total: {total:.0f} ms · "
            f"Confidence: {result.average_confidence:.0%}"
        )

    def _capture_failed(self, message: str) -> None:
        self._processing = False
        self._active_task = None
        self._set_overlays_temporarily_hidden(False)
        self.panel.set_status(message, paused=True)
        self.overlay.set_state(LensState.ERROR)

    def _set_overlays_temporarily_hidden(self, hidden: bool) -> None:
        if hidden and not self._fallback_hidden:
            self._fallback_hidden = True
            self.overlay.setWindowOpacity(0.0)
            self.panel.setWindowOpacity(0.0)
        elif not hidden and self._fallback_hidden:
            self._fallback_hidden = False
            self.overlay.setWindowOpacity(1.0)
            self.panel.setWindowOpacity(1.0)

    def _show_preview(self, image) -> None:  # type: ignore[no-untyped-def]
        height, width = image.shape[:2]
        image_format = QImage.Format_Grayscale8 if image.ndim == 2 else QImage.Format_BGR888
        qimage = QImage(image.data, width, height, int(image.strides[0]), image_format).copy()
        pixmap = QPixmap.fromImage(qimage).scaled(
            self.panel.preview_label.size(),
            aspectMode=Qt.KeepAspectRatio,
            mode=Qt.SmoothTransformation,
        )
        self.panel.preview_label.setPixmap(pixmap)

    def toggle_pause(self) -> None:
        if not self._running:
            return
        self._paused = not self._paused
        if self._paused:
            self.capture_timer.stop()
            self.panel.set_status("Paused", paused=True)
            self.panel.pause_button.setText("Resume")
            self.overlay.set_state(LensState.PAUSED)
        else:
            self.panel.set_status("Active")
            self.panel.pause_button.setText("Pause")
            self.overlay.set_state(LensState.ACTIVE)
            self._configure_timer()
            self.request_capture(force=True)

    def copy_translation(self) -> None:
        text = self.panel.translated_text.toPlainText()
        if text:
            self.app.clipboard().setText(text)
            self.panel.set_status("Translation copied")
        else:
            self.panel.set_status("There is no translation to copy", paused=True)

    def toggle_lock(self) -> None:
        locked = self.panel.lock_button.isChecked()
        self.overlay.set_locked(locked)
        self.panel.lock_button.setText("Unlock lens" if locked else "Lock lens")
        self.panel.set_status("Lens locked" if locked else "Lens unlocked")

    def _language_changed(self) -> None:
        source, target = self.panel.selected_languages()
        if source != "auto" and source == target:
            self.panel.set_status("Choose two different languages", paused=True)

    def _capture_settings_changed(self) -> None:
        interval, sensitivity, profile = self.panel.selected_capture_settings()
        self.settings.capture_interval_ms = interval
        self.settings.change_sensitivity = sensitivity
        self.settings.preprocessing_profile = profile
        self.detector.sensitivity = sensitivity
        self._configure_timer()

    def _capture_geometry_changed(self) -> None:
        if not self._processing:
            self.detector.reset()

    @staticmethod
    def _rect_mapping(widget) -> dict[str, int]:  # type: ignore[no-untyped-def]
        rect = widget.geometry()
        return {"x": rect.x(), "y": rect.y(), "width": rect.width(), "height": rect.height()}

    def save_settings(self) -> None:
        source, target = self.panel.selected_languages()
        self.settings.source_language = source
        self.settings.target_language = target
        self.settings.auto_detect_language = source == "auto"
        interval, sensitivity, profile = self.panel.selected_capture_settings()
        self.settings.capture_interval_ms = interval
        self.settings.change_sensitivity = sensitivity
        self.settings.preprocessing_profile = profile
        self.settings.overlay_locked = self.overlay.is_locked()
        self.settings.overlay_geometry = self._rect_mapping(self.overlay)
        self.settings.panel_geometry = self._rect_mapping(self.panel)
        self.store.save(self.settings)

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.capture_timer.stop()
        self.save_settings()
        self.overlay.close()
        self.panel.close()
        self.thread_pool.clear()
        self.thread_pool.waitForDone(2000)
        self.ocr_engine.clear()
        self.app.quit()
