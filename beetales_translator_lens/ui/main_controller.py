"""Coordinate the capture, OCR, detection, and local translation pipeline."""

from __future__ import annotations

import logging
import sys
from time import perf_counter

from PySide6.QtCore import QObject, QPoint, QRect, QThreadPool, QTimer, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox

from beetales_translator_lens.capture.change_detector import ChangeDetector
from beetales_translator_lens.capture.image_preprocessor import ImagePreprocessor
from beetales_translator_lens.constants import APP_NAME, LensState
from beetales_translator_lens.ocr.models import OCRResult
from beetales_translator_lens.ocr.paddle_engine import PaddleOCREngine
from beetales_translator_lens.performance import PipelinePerformanceMonitor
from beetales_translator_lens.platform.windows_capture_exclusion import exclude_window_from_capture
from beetales_translator_lens.storage.history_store import HistoryStore
from beetales_translator_lens.storage.settings_store import SettingsStore
from beetales_translator_lens.storage.translation_cache_store import TranslationCacheStore
from beetales_translator_lens.translation.argos_engine import ArgosTranslationEngine
from beetales_translator_lens.translation.language_detector import LanguageDetector
from beetales_translator_lens.translation.model_manager import ArgosModelManager, ModelInstallResult
from beetales_translator_lens.translation.models import TranslationResult
from beetales_translator_lens.translation.route_resolver import TranslationRouteResolver
from beetales_translator_lens.translation.translation_cache import TranslationCache
from beetales_translator_lens.ui.capture_overlay import CaptureOverlay
from beetales_translator_lens.ui.translation_panel import TranslationPanel
from beetales_translator_lens.workers.capture_worker import CaptureTask, FrameAnalysis
from beetales_translator_lens.workers.ocr_worker import OCRTask
from beetales_translator_lens.workers.model_download_worker import ModelDownloadTask
from beetales_translator_lens.workers.persistence_worker import (
    ClearSavedDataTask,
    SaveTranslationTask,
)
from beetales_translator_lens.workers.translation_worker import (
    TranslationPreparation,
    TranslationPreparationTask,
    TranslationTask,
)

LOGGER = logging.getLogger(__name__)


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
        self.persistence_pool = QThreadPool(self)
        self.persistence_pool.setMaxThreadCount(1)
        self.detector = ChangeDetector(self.settings.change_sensitivity)
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = PaddleOCREngine()
        self.translation_engine = ArgosTranslationEngine(
            preserve_message_prefixes=self.settings.preserve_message_prefixes
        )
        self.language_detector = LanguageDetector()
        self.route_resolver = TranslationRouteResolver()
        self.model_manager = ArgosModelManager(route_resolver=self.route_resolver)
        self.translation_cache = TranslationCache(self.settings.translation_cache_size)
        self.history_store = HistoryStore(maximum_entries=self.settings.history_max_entries)
        self.translation_cache_store = TranslationCacheStore()
        if self.settings.history_enabled and self.settings.persistent_cache_enabled:
            self.translation_cache.load(self.translation_cache_store.load())
        self.performance = PipelinePerformanceMonitor()
        self.capture_timer = QTimer(self)
        self.capture_timer.setTimerType(Qt.PreciseTimer)
        self.capture_timer.timeout.connect(self.request_capture)
        self._paused = False
        self._running = False
        self._processing = False
        self._closing = False
        self._capture_exclusion_ok = sys.platform != "win32"
        self._fallback_hidden = False
        self._active_task: object | None = None
        self._latest_analysis: FrameAnalysis | None = None
        self._latest_ocr_result: OCRResult | None = None
        self._pending_translation: TranslationPreparation | None = None
        self._cycle_started: float | None = None
        self._latest_metrics_text = ""
        self._background_tasks: set[object] = set()
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
        self.panel.swap_requested.connect(self.swap_languages)
        self.panel.clear_requested.connect(self.clear_result)
        self.panel.privacy_settings_changed.connect(self._privacy_settings_changed)
        self.panel.clear_saved_data_requested.connect(self.clear_saved_data)
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
        self.panel.select_privacy_settings(
            self.settings.history_enabled,
            self.settings.persistent_cache_enabled,
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
        if not self.translation_engine.is_available():
            self.panel.set_status(
                "Argos Translate is not installed. Run pip install -r requirements.txt.",
                paused=True,
            )
            self.overlay.set_state(LensState.ERROR)
            return
        if not self.language_detector.is_available():
            self.panel.set_status(
                "Lingua is not installed. Run pip install -r requirements.txt.",
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

        if self._closing or self._paused or not self._running:
            return
        self.performance.record_request()
        if self._processing:
            self.performance.record_busy_skip()
            self._refresh_metrics()
            return
        region = self.overlay.capture_region()
        if not region.is_valid:
            self._capture_failed("The selected area is too small.")
            return
        self._processing = True
        self._cycle_started = perf_counter()
        self.overlay.set_state(LensState.CAPTURING)
        self.panel.set_status("Reading the selected area…")
        if sys.platform == "win32" and not self._capture_exclusion_ok:
            self._set_overlays_temporarily_hidden(True)
            QTimer.singleShot(35, lambda: self._submit_capture(region, force))
        else:
            self._submit_capture(region, force)

    def _submit_capture(self, region, force: bool) -> None:  # type: ignore[no-untyped-def]
        if self._closing:
            self._finish_cycle()
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
                    "Recognizing text before automatic language detection…"
                )
            else:
                self.panel.set_status("Recognizing text…")
            task = OCRTask(self.ocr_engine, analysis.processed_image, source_language)
            task.signals.completed.connect(self._ocr_completed)
            self._active_task = task
            self.thread_pool.start(task)
        else:
            self._finish_cycle(unchanged=True)
            self.panel.set_status(
                f"No changes ({analysis.change.changed_ratio * 100:.1f}%)"
            )
            self.overlay.set_state(LensState.ACTIVE)

    def _ocr_completed(self, result: OCRResult) -> None:
        self._active_task = None
        if self._closing:
            return
        analysis = self._latest_analysis
        if result.error:
            LOGGER.error("OCR cycle failed: %s", result.error)
            self.panel.set_status(result.error, paused=True)
            self.overlay.set_state(LensState.ERROR)
            self._update_metrics(result, analysis)
            self._finish_cycle()
            return
        if not result.full_text.strip():
            self.panel.clear_result()
            self.panel.set_status("No readable text was detected.", paused=True)
            self.overlay.set_state(LensState.ACTIVE)
            self._update_metrics(result, analysis)
            self._finish_cycle()
            return
        self._latest_ocr_result = result
        self._update_metrics(result, analysis)
        selected_source, target = self.panel.selected_languages()
        self.panel.set_status("Preparing local translation…")
        task = TranslationPreparationTask(
            result.full_text,
            selected_source,
            target,
            self.language_detector,
            self.model_manager,
            self.route_resolver,
        )
        task.signals.completed.connect(self._translation_prepared)
        self._active_task = task
        self.thread_pool.start(task)

    def _translation_prepared(self, preparation: TranslationPreparation) -> None:
        self._active_task = None
        if self._closing:
            self._processing = False
            return
        self._pending_translation = preparation
        if preparation.detection is not None:
            self._latest_metrics_text = (
                f"{self._latest_metrics_text} · Detection: "
                f"{preparation.detection.elapsed_ms:.0f} ms "
                f"({preparation.detection.confidence:.0%})"
            )
            self._refresh_metrics()
        if preparation.normalized_text:
            self.panel.set_detected_text(preparation.normalized_text)
        if preparation.error:
            self._finish_cycle()
            self.panel.set_status(preparation.error, paused=True)
            self.overlay.set_state(LensState.ERROR)
            return
        if preparation.source_language is None:
            self._finish_cycle()
            self.panel.set_status("The source language could not be resolved.", paused=True)
            self.overlay.set_state(LensState.ERROR)
            return

        cached = self.translation_cache.get(
            preparation.source_language,
            preparation.target_language,
            preparation.normalized_text,
        )
        if cached is not None:
            self.performance.record_cache_hit()
            self._display_translation(cached, cached=True)
            self._finish_cycle()
            return
        if preparation.route is not None:
            self._start_translation(preparation.normalized_text, preparation.route)
            return

        self._finish_cycle()
        self._processing = True
        self.overlay.set_state(LensState.ERROR)
        answer = QMessageBox.question(
            self.panel,
            APP_NAME,
            f"No local model route is installed for {preparation.source_language} → "
            f"{preparation.target_language}. Download and install the required Argos model(s) now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self._processing = False
            self.panel.set_status(
                f"Model not installed for {preparation.source_language} → {preparation.target_language}.",
                paused=True,
            )
            return
        self._cycle_started = perf_counter()
        self.overlay.set_state(LensState.DOWNLOADING_MODEL)
        self.panel.set_status("Checking available translation models…")
        task = ModelDownloadTask(
            self.model_manager,
            preparation.source_language,
            preparation.target_language,
        )
        task.signals.progress.connect(self.panel.set_status)
        task.signals.completed.connect(self._model_download_completed)
        self._active_task = task
        self.thread_pool.start(task)

    def _model_download_completed(self, result: ModelInstallResult) -> None:
        self._active_task = None
        if self._closing:
            self._processing = False
            return
        if result.error:
            LOGGER.error("Translation model installation failed: %s", result.error)
            self._finish_cycle()
            self.panel.set_status(result.error, paused=True)
            self.overlay.set_state(LensState.ERROR)
            return
        preparation = self._pending_translation
        if preparation is None or not result.route:
            self._finish_cycle()
            self.panel.set_status("The translation model was installed, but no route was returned.", paused=True)
            self.overlay.set_state(LensState.ERROR)
            return
        self._start_translation(preparation.normalized_text, result.route)

    def _start_translation(self, text: str, route: list[str]) -> None:
        self._processing = True
        if self._cycle_started is None:
            self._cycle_started = perf_counter()
        self.overlay.set_state(LensState.TRANSLATING)
        route_text = " → ".join(route)
        self.panel.set_status(f"Translating locally via {route_text}…")
        task = TranslationTask(self.translation_engine, text, route)
        task.signals.completed.connect(self._translation_completed)
        self._active_task = task
        self.thread_pool.start(task)

    def _translation_completed(self, result: TranslationResult) -> None:
        self._active_task = None
        if self._closing:
            return
        if result.error:
            LOGGER.error("Translation cycle failed: %s", result.error)
            self.panel.set_status(result.error, paused=True)
            self.overlay.set_state(LensState.ERROR)
            self._finish_cycle()
            return
        self.translation_cache.put(result)
        self._display_translation(result)
        self._schedule_persistence(result)
        self._finish_cycle()

    def _display_translation(self, result: TranslationResult, *, cached: bool = False) -> None:
        self.panel.original_text.setPlainText(result.original_text)
        self.panel.translated_text.setPlainText(result.translated_text)
        pivot = len(result.route) > 2
        if cached:
            status = "Translation loaded from cache"
        elif pivot:
            status = "Translation completed through English"
        else:
            status = "Translation completed locally"
        self.panel.set_status(f"{status} · {result.elapsed_ms:.0f} ms")
        self.overlay.set_state(LensState.ACTIVE)
        if self._latest_ocr_result is not None:
            self._latest_metrics_text = (
                f"{self._latest_metrics_text} · Translation: "
                f"{result.elapsed_ms:.0f} ms · Route: {' → '.join(result.route)}"
            )
            self._refresh_metrics()

    def _update_metrics(
        self,
        result: OCRResult,
        analysis: FrameAnalysis | None,
    ) -> None:
        if analysis is None:
            self._latest_metrics_text = f"OCR: {result.elapsed_ms:.0f} ms"
            self._refresh_metrics()
            return
        total = analysis.capture.elapsed_ms + analysis.preprocessing_ms + result.elapsed_ms
        self._latest_metrics_text = (
            f"Capture: {analysis.capture.elapsed_ms:.0f} ms · "
            f"Preprocess: {analysis.preprocessing_ms:.0f} ms · "
            f"OCR: {result.elapsed_ms:.0f} ms · Total: {total:.0f} ms · "
            f"Confidence: {result.average_confidence:.0%}"
        )
        self._refresh_metrics()

    def _capture_failed(self, message: str) -> None:
        LOGGER.error("Capture cycle failed: %s", message)
        self._active_task = None
        self._set_overlays_temporarily_hidden(False)
        self.panel.set_status(message, paused=True)
        self.overlay.set_state(LensState.ERROR)
        self._finish_cycle()

    def _finish_cycle(self, *, unchanged: bool = False) -> None:
        self._processing = False
        if self._cycle_started is not None:
            elapsed_ms = (perf_counter() - self._cycle_started) * 1000
            self.performance.record_completed_cycle(elapsed_ms, unchanged=unchanged)
            self._cycle_started = None
        self._refresh_metrics()

    def _refresh_metrics(self) -> None:
        snapshot = self.performance.snapshot()
        performance_text = (
            f"Average cycle: {snapshot.average_cycle_ms:.0f} ms · "
            f"Cache hits: {snapshot.cache_hits} · Busy ticks skipped: {snapshot.skipped_busy_ticks}"
        )
        if self._latest_metrics_text:
            performance_text = f"{self._latest_metrics_text} · {performance_text}"
        self.panel.metrics_label.setText(performance_text)

    def _schedule_persistence(self, result: TranslationResult) -> None:
        save_history = self.settings.history_enabled
        save_cache = save_history and self.settings.persistent_cache_enabled
        if not save_history and not save_cache:
            return
        task = SaveTranslationTask(
            result,
            self.history_store,
            self.translation_cache_store,
            self.translation_cache.snapshot(),
            save_history=save_history,
            save_cache=save_cache,
        )
        self._background_tasks.add(task)
        task.signals.completed.connect(
            lambda message, current=task: self._persistence_completed(current, message)
        )
        self.persistence_pool.start(task)

    def _persistence_completed(
        self,
        task: object,
        message: str,
        success_status: str | None = None,
    ) -> None:
        self._background_tasks.discard(task)
        if message:
            LOGGER.warning("%s", message)
            if not self._processing:
                self.panel.set_status(message, paused=True)
        elif success_status and not self._processing:
            self.panel.set_status(success_status)

    def clear_result(self) -> None:
        self.panel.clear_result()
        self._latest_ocr_result = None
        self._pending_translation = None
        self._latest_metrics_text = ""
        self._refresh_metrics()
        self.panel.set_status("Displayed text cleared")

    def _privacy_settings_changed(self) -> None:
        history_enabled, persistent_cache_enabled = self.panel.selected_privacy_settings()
        self.settings.history_enabled = history_enabled
        self.settings.persistent_cache_enabled = persistent_cache_enabled
        self.save_settings()
        if history_enabled:
            self.panel.set_status("Local translation history enabled")
        else:
            self.panel.set_status("Translation history disabled")

    def clear_saved_data(self) -> None:
        answer = QMessageBox.question(
            self.panel,
            APP_NAME,
            "Clear all saved translation history and the persistent translation cache?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.translation_cache.clear()
        task = ClearSavedDataTask(self.history_store, self.translation_cache_store)
        self._background_tasks.add(task)
        task.signals.completed.connect(
            lambda message, current=task: self._persistence_completed(
                current,
                message,
                "Saved translation data cleared",
            )
        )
        self.persistence_pool.start(task)

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
            return
        if self._running and not self._processing:
            self.request_capture(force=True)

    def swap_languages(self) -> None:
        if not self.panel.swap_languages():
            self.panel.set_status("Automatic source language cannot be swapped.", paused=True)
            return
        self.panel.set_status("Languages swapped")
        if self._running and not self._processing:
            self.request_capture(force=True)

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
        history_enabled, persistent_cache_enabled = self.panel.selected_privacy_settings()
        self.settings.history_enabled = history_enabled
        self.settings.persistent_cache_enabled = persistent_cache_enabled
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
        self.persistence_pool.waitForDone(2000)
        self.ocr_engine.clear()
        self.translation_cache.clear()
        self.app.quit()
