"""Local Argos translation-model management dialog."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QVBoxLayout
)

from beetales_translator_lens.constants import TARGET_LANGUAGES
from beetales_translator_lens.translation.model_manager import ArgosModelManager


class ModelManagerDialog(QDialog):
    install_requested = Signal(str, str)

    def __init__(self, manager: ArgosModelManager, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Translation Models")
        self.resize(520, 380)
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Installed local Argos translation models"))
        self.status_label = QLabel("Models are downloaded only when you request a route.")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)
        self.models = QListWidget()
        root.addWidget(self.models)
        route = QHBoxLayout()
        self.source = QComboBox()
        self.target = QComboBox()
        for code, name in TARGET_LANGUAGES:
            self.source.addItem(name, code)
            self.target.addItem(name, code)
        route.addWidget(self.source)
        route.addWidget(QLabel("→"))
        route.addWidget(self.target)
        install = QPushButton("Install route")
        install.clicked.connect(self._request_install)
        route.addWidget(install)
        root.addLayout(route)
        controls = QHBoxLayout()
        refresh = QPushButton("Refresh")
        remove = QPushButton("Remove selected")
        refresh.clicked.connect(self.refresh)
        remove.clicked.connect(self.remove_selected)
        controls.addWidget(refresh)
        controls.addWidget(remove)
        root.addLayout(controls)
        self.refresh()

    def refresh(self) -> None:
        self.models.clear()
        try:
            for model in self.manager.installed_models():
                item = f"{model.source_language} → {model.target_language}"
                if model.version:
                    item += f"  (version {model.version})"
                self.models.addItem(item)
            if self.models.count() == 0:
                self.models.addItem("No translation models are installed.")
        except Exception as exc:
            self.models.addItem(f"Could not read installed models: {exc}")

    def _request_install(self) -> None:
        source = str(self.source.currentData())
        target = str(self.target.currentData())
        if source == target:
            QMessageBox.information(self, "Translation Models", "Choose two different languages.")
            return
        self.install_requested.emit(source, target)

    def set_status(self, message: str, error: bool = False) -> None:
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #c45b64;" if error else "")

    def remove_selected(self) -> None:
        item = self.models.currentItem()
        if not item or " → " not in item.text():
            return
        source, remainder = item.text().split(" → ", 1)
        target = remainder.split()[0]
        if QMessageBox.question(self, "Translation Models", f"Remove {source} → {target}?") == QMessageBox.Yes:
            self.manager.uninstall_pair(source, target)
            self.refresh()
