"""Product and privacy information."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from beetales_translator_lens.constants import APP_NAME, VERSION


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        layout = QVBoxLayout(self)
        title = QLabel(f"<h2>{APP_NAME}</h2><p>Version {VERSION}</p>")
        title.setTextFormat(Qt.RichText)
        layout.addWidget(title)
        details = QLabel(
            "A local screen-text recognition and translation lens for Windows.<br><br>"
            "BeeTales does not include telemetry. Captures are processed in memory, and translation "
            "history is stored only when explicitly enabled.<br><br>License: MIT"
        )
        details.setWordWrap(True)
        layout.addWidget(details)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
