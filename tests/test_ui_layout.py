"""DPI-safe layout checks for menus and compact floating controls."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QScrollArea

from beetales_translator_lens.storage.settings_store import AppSettings
from beetales_translator_lens.ui.about_dialog import AboutDialog
from beetales_translator_lens.ui.first_run_wizard import FirstRunWizard
from beetales_translator_lens.ui.model_manager_dialog import ModelManagerDialog
from beetales_translator_lens.ui.settings_dialog import SettingsDialog
from beetales_translator_lens.ui.theme import APP_STYLESHEET
from beetales_translator_lens.ui.translation_panel import TranslationPanel


class StubModelManager:
    def installed_models(self) -> list[object]:
        return []


def application() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(APP_STYLESHEET)
    return app


def test_translation_panel_controls_do_not_collapse_or_overlap() -> None:
    app = application()
    panel = TranslationPanel()
    panel.resize(int(panel.property("preferredWidth")), int(panel.property("preferredHeight")))
    panel.show()
    app.processEvents()

    assert panel.windowType() == Qt.WindowType.Window
    scroll_area = panel.findChild(QScrollArea, "panelScrollArea")
    assert scroll_area is not None
    assert scroll_area.horizontalScrollBar().maximum() == 0
    assert scroll_area.verticalScrollBar().maximum() == 0
    assert panel.start_button.isVisibleTo(scroll_area.viewport())
    combos = panel.findChildren(QComboBox)
    assert len(combos) == 5
    assert all(combo.height() >= 27 for combo in combos)
    assert not any(
        first.geometry().intersects(second.geometry())
        for index, first in enumerate(combos)
        for second in combos[index + 1 :]
        if first.parent() is second.parent()
    )
    panel.close()


def test_all_dialog_drop_downs_reserve_readable_popup_widths() -> None:
    app = application()
    widgets = (
        FirstRunWizard("en", "es"),
        SettingsDialog(AppSettings()),
        ModelManagerDialog(StubModelManager()),  # type: ignore[arg-type]
    )

    for widget in widgets:
        widget.show()
        app.processEvents()
        combos = widget.findChildren(QComboBox)
        assert combos
        assert all(combo.height() >= 27 for combo in combos)
        assert all(combo.view().minimumWidth() >= combo.minimumWidth() for combo in combos)
        widget.close()


def test_brand_assets_are_visible_in_panel_and_about_dialog() -> None:
    app = application()
    panel = TranslationPanel()
    about = AboutDialog()
    panel.show()
    about.show()
    app.processEvents()

    panel_logo = panel.findChild(QLabel, "brandLogo")
    about_logo = about.findChild(QLabel, "aboutBrandLogo")
    mascot = about.findChild(QLabel, "aboutMascot")
    assert panel_logo is not None and not panel_logo.pixmap().isNull()
    assert about_logo is not None and not about_logo.pixmap().isNull()
    assert mascot is not None and not mascot.pixmap().isNull()

    about.close()
    panel.close()
