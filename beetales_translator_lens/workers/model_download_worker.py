"""Background Argos model download and installation task."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from beetales_translator_lens.translation.model_manager import ArgosModelManager


class ModelDownloadSignals(QObject):
    progress = Signal(str)
    completed = Signal(object)


class ModelDownloadTask(QRunnable):
    def __init__(self, manager: ArgosModelManager, source: str, target: str) -> None:
        super().__init__()
        self.manager = manager
        self.source = source
        self.target = target
        self.signals = ModelDownloadSignals()

    @Slot()
    def run(self) -> None:
        result = self.manager.install_for_route(
            self.source,
            self.target,
            progress=self.signals.progress.emit,
        )
        self.signals.completed.emit(result)
