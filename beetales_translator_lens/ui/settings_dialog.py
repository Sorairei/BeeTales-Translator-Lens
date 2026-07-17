"""User-experience preferences and configurable shortcuts."""

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QSpinBox, QVBoxLayout
)

from beetales_translator_lens.storage.settings_store import AppSettings
from beetales_translator_lens.ui.widget_helpers import configure_combo_box


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("BeeTales Settings")
        self.resize(540, 500)
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        configure_combo_box(self.theme_combo, minimum_width=180)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(settings.theme)))
        self.start_minimized = QCheckBox("Start in the system tray")
        self.start_minimized.setChecked(settings.start_minimized)
        self.show_original = QCheckBox("Show detected text")
        self.show_original.setChecked(settings.show_original_text)
        self.hotkeys_enabled = QCheckBox("Enable Windows global shortcuts")
        self.hotkeys_enabled.setChecked(settings.global_hotkeys_enabled)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 28)
        self.font_size.setValue(settings.translation_font_size)
        form.addRow("Theme", self.theme_combo)
        form.addRow("Translation font size", self.font_size)
        form.addRow(self.start_minimized)
        form.addRow(self.show_original)
        form.addRow(self.hotkeys_enabled)
        self.shortcut_edits: dict[str, QLineEdit] = {}
        labels = {
            "toggle_visibility": "Show or hide",
            "pause_resume": "Pause or resume",
            "copy_translation": "Copy translation",
            "toggle_lock": "Lock or unlock",
            "force_read": "Force read",
            "toggle_click_through": "Toggle click-through",
        }
        for action, label in labels.items():
            edit = QLineEdit(settings.shortcuts[action])
            edit.setPlaceholderText("Ctrl+Shift+Key")
            self.shortcut_edits[action] = edit
            form.addRow(label, edit)
        root.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def apply_to(self, settings: AppSettings) -> None:
        settings.theme = str(self.theme_combo.currentData())
        settings.start_minimized = self.start_minimized.isChecked()
        settings.show_original_text = self.show_original.isChecked()
        settings.global_hotkeys_enabled = self.hotkeys_enabled.isChecked()
        settings.translation_font_size = self.font_size.value()
        settings.shortcuts = {action: edit.text().strip() for action, edit in self.shortcut_edits.items()}
