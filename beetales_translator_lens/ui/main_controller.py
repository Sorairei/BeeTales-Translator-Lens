"""Coordinación de ventanas y lógica simulada de la Fase 1."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from beetales_translator_lens.constants import LensState, SIMULATED_ORIGINAL, SIMULATED_TRANSLATION
from beetales_translator_lens.storage.settings_store import AppSettings, SettingsStore
from beetales_translator_lens.ui.capture_overlay import CaptureOverlay
from beetales_translator_lens.ui.translation_panel import TranslationPanel


class MainController(QObject):
    """Mantiene las dos ventanas sincronizadas y guarda preferencias."""

    def __init__(self, app: QApplication, store: SettingsStore) -> None:
        super().__init__()
        self.app = app
        self.store = store
        self.settings = store.load()
        self.overlay = CaptureOverlay()
        self.panel = TranslationPanel()
        self._paused = False
        self._closing = False
        self._connect_signals()
        self._restore_settings()

    def _connect_signals(self) -> None:
        self.panel.start_requested.connect(self.start_simulation)
        self.panel.pause_requested.connect(self.toggle_pause)
        self.panel.copy_requested.connect(self.copy_translation)
        self.panel.lock_requested.connect(self.toggle_lock)
        self.panel.close_requested.connect(self.close)
        self.panel.language_changed.connect(self._language_changed)
        self.app.aboutToQuit.connect(self.save_settings)

    def _restore_settings(self) -> None:
        self._apply_geometry(self.overlay, self.settings.overlay_geometry)
        self._apply_geometry(self.panel, self.settings.panel_geometry)
        self.panel.select_languages(self.settings.source_language, self.settings.target_language)
        self.overlay.set_locked(self.settings.overlay_locked)
        self.panel.lock_button.setChecked(self.settings.overlay_locked)
        self.panel.lock_button.setText("Desbloquear lupa" if self.settings.overlay_locked else "Bloquear lupa")

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

    def start_simulation(self) -> None:
        self._paused = False
        self.panel.set_simulated_result(SIMULATED_ORIGINAL, SIMULATED_TRANSLATION)
        self.panel.set_status("Activa")
        self.panel.start_button.setText("Actualizar")
        self.panel.pause_button.setEnabled(True)
        self.panel.pause_button.setText("Pausar")
        self.overlay.set_state(LensState.ACTIVE)

    def toggle_pause(self) -> None:
        self._paused = not self._paused
        if self._paused:
            self.panel.set_status("Pausado", paused=True)
            self.panel.pause_button.setText("Reanudar")
            self.overlay.set_state(LensState.PAUSED)
        else:
            self.panel.set_status("Activa")
            self.panel.pause_button.setText("Pausar")
            self.overlay.set_state(LensState.ACTIVE)

    def copy_translation(self) -> None:
        text = self.panel.translated_text.toPlainText()
        if text:
            self.app.clipboard().setText(text)
            self.panel.set_status("Traducción copiada")
        else:
            self.panel.set_status("No hay traducción para copiar", paused=True)

    def toggle_lock(self) -> None:
        locked = self.panel.lock_button.isChecked()
        self.overlay.set_locked(locked)
        self.panel.lock_button.setText("Desbloquear lupa" if locked else "Bloquear lupa")
        self.panel.set_status("Lupa bloqueada" if locked else "Lupa desbloqueada")

    def _language_changed(self) -> None:
        source, target = self.panel.selected_languages()
        if source != "auto" and source == target:
            self.panel.set_status("Elige idiomas diferentes", paused=True)

    @staticmethod
    def _rect_mapping(widget) -> dict[str, int]:  # type: ignore[no-untyped-def]
        rect = widget.geometry()
        return {"x": rect.x(), "y": rect.y(), "width": rect.width(), "height": rect.height()}

    def save_settings(self) -> None:
        source, target = self.panel.selected_languages()
        self.settings.source_language = source
        self.settings.target_language = target
        self.settings.auto_detect_language = source == "auto"
        self.settings.overlay_locked = self.overlay.is_locked()
        self.settings.overlay_geometry = self._rect_mapping(self.overlay)
        self.settings.panel_geometry = self._rect_mapping(self.panel)
        self.store.save(self.settings)

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.save_settings()
        self.overlay.close()
        self.panel.close()
        self.app.quit()
