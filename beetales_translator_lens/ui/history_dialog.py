"""Search, copy, delete, and export optional translation history."""

import json
from dataclasses import asdict
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QHBoxLayout, QLineEdit, QListWidget, QMessageBox,
    QPushButton, QTextEdit, QVBoxLayout,
)

from beetales_translator_lens.storage.history_store import HistoryEntry, HistoryStore


class HistoryDialog(QDialog):
    def __init__(self, store: HistoryStore, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.store = store
        self.entries: list[HistoryEntry] = []
        self.setWindowTitle("Translation History")
        self.resize(720, 480)
        root = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search original or translated text")
        self.search.textChanged.connect(self.refresh)
        root.addWidget(self.search)
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._show_current)
        root.addWidget(self.list_widget)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        root.addWidget(self.details)
        buttons = QHBoxLayout()
        for text, callback in (
            ("Copy", self.copy_current), ("Delete", self.delete_current),
            ("Clear all", self.clear_all), ("Export TXT", self.export_txt),
            ("Export JSON", self.export_json),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        root.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        query = self.search.text().casefold()
        self.entries = [
            entry for entry in reversed(self.store.load())
            if not query or query in entry.original_text.casefold() or query in entry.translated_text.casefold()
        ]
        self.list_widget.clear()
        for entry in self.entries:
            self.list_widget.addItem(
                f"{entry.timestamp[:19]}  {entry.source_language} → {entry.target_language}  {entry.original_text[:70]}"
            )
        if self.entries:
            self.list_widget.setCurrentRow(0)
        else:
            self.details.setPlainText("No saved translations.")

    def _current(self) -> HistoryEntry | None:
        row = self.list_widget.currentRow()
        return self.entries[row] if 0 <= row < len(self.entries) else None

    def _show_current(self) -> None:
        entry = self._current()
        if entry:
            self.details.setPlainText(f"Original:\n{entry.original_text}\n\nTranslation:\n{entry.translated_text}")

    def copy_current(self) -> None:
        entry = self._current()
        if entry:
            QApplication.clipboard().setText(entry.translated_text)

    def delete_current(self) -> None:
        entry = self._current()
        if entry and self.store.delete(entry.timestamp):
            self.refresh()

    def clear_all(self) -> None:
        if QMessageBox.question(self, "Translation History", "Clear all saved history?") == QMessageBox.Yes:
            self.store.clear()
            self.refresh()

    def export_txt(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export history", "translations.txt", "Text (*.txt)")
        if path:
            content = "\n\n".join(
                f"{entry.timestamp} | {entry.source_language} -> {entry.target_language}\n"
                f"Original: {entry.original_text}\nTranslation: {entry.translated_text}"
                for entry in reversed(self.entries)
            )
            Path(path).write_text(content + "\n", encoding="utf-8")

    def export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export history", "translations.json", "JSON (*.json)")
        if path:
            Path(path).write_text(json.dumps([asdict(entry) for entry in reversed(self.entries)], ensure_ascii=False, indent=2), encoding="utf-8")
