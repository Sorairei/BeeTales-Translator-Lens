"""Product and privacy information."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QVBoxLayout

from beetales_translator_lens.constants import APP_NAME, VERSION
from beetales_translator_lens.resources import brand_logo_path, mascot_image_path


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)

        logo = QLabel()
        logo.setObjectName("aboutBrandLogo")
        logo.setAccessibleName("The BeeTales logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(
            QPixmap(str(brand_logo_path())).scaledToWidth(
                360, Qt.TransformationMode.SmoothTransformation
            )
        )
        layout.addWidget(logo)

        version = QLabel(f"{APP_NAME} · Version {VERSION}")
        version.setObjectName("aboutVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        content = QHBoxLayout()
        mascot = QLabel()
        mascot.setObjectName("aboutMascot")
        mascot.setAccessibleName("Sora, the BeeTales mascot")
        mascot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mascot.setPixmap(
            QPixmap(str(mascot_image_path())).scaled(
                130,
                130,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        content.addWidget(mascot)
        details = QLabel(
            "A local screen-text recognition and translation lens for Windows.<br><br>"
            "BeeTales does not include telemetry. Captures are processed in memory, and translation "
            "history is stored only when explicitly enabled.<br><br>License: MIT"
        )
        details.setWordWrap(True)
        content.addWidget(details, 1)
        layout.addLayout(content)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
