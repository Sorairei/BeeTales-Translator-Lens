"""First-run language and privacy setup."""

from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWizard, QWizardPage

from beetales_translator_lens.constants import APP_NAME, SOURCE_LANGUAGES, TARGET_LANGUAGES
from beetales_translator_lens.ui.widget_helpers import configure_combo_box


class FirstRunWizard(QWizard):
    def __init__(self, source: str, target: str) -> None:
        super().__init__()
        self.setWindowTitle(f"Welcome to {APP_NAME}")
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(560, 380)
        welcome = QWizardPage()
        welcome.setTitle(f"Welcome to {APP_NAME}")
        layout = QVBoxLayout(welcome)
        label = QLabel(
            "BeeTales recognizes and translates text visible on your screen.\n\n"
            "Capture, recognition, language detection, and translation run locally. "
            "Models may require an initial download. Translation history is disabled by default."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        self.addPage(welcome)

        languages = QWizardPage()
        languages.setTitle("Choose your default languages")
        language_layout = QVBoxLayout(languages)
        language_layout.addWidget(QLabel("Source language"))
        self.source_combo = QComboBox()
        for code, name in SOURCE_LANGUAGES:
            self.source_combo.addItem(name, code)
        configure_combo_box(self.source_combo, minimum_width=240)
        self.source_combo.setCurrentIndex(max(0, self.source_combo.findData(source)))
        language_layout.addWidget(self.source_combo)
        language_layout.addWidget(QLabel("Target language"))
        self.target_combo = QComboBox()
        for code, name in TARGET_LANGUAGES:
            self.target_combo.addItem(name, code)
        configure_combo_box(self.target_combo, minimum_width=240)
        self.target_combo.setCurrentIndex(max(0, self.target_combo.findData(target)))
        language_layout.addWidget(self.target_combo)
        self.addPage(languages)

    def selected_languages(self) -> tuple[str, str]:
        return str(self.source_combo.currentData()), str(self.target_combo.currentData())
