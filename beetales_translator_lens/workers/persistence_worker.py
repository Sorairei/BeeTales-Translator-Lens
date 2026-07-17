"""Background writes for optional history and persistent translation cache."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from beetales_translator_lens.storage.history_store import HistoryStore
from beetales_translator_lens.storage.translation_cache_store import TranslationCacheStore
from beetales_translator_lens.translation.models import TranslationResult


class PersistenceSignals(QObject):
    completed = Signal(str)


class SaveTranslationTask(QRunnable):
    def __init__(
        self,
        result: TranslationResult,
        history_store: HistoryStore,
        cache_store: TranslationCacheStore,
        cache_snapshot: list[TranslationResult],
        *,
        save_history: bool,
        save_cache: bool,
    ) -> None:
        super().__init__()
        self.result = result
        self.history_store = history_store
        self.cache_store = cache_store
        self.cache_snapshot = cache_snapshot
        self.save_history = save_history
        self.save_cache = save_cache
        self.signals = PersistenceSignals()

    @Slot()
    def run(self) -> None:
        try:
            if self.save_history:
                self.history_store.append(self.result)
            if self.save_cache:
                self.cache_store.save(self.cache_snapshot)
            self.signals.completed.emit("")
        except Exception as exc:
            self.signals.completed.emit(f"Saved-data write failed: {exc}")


class ClearSavedDataTask(QRunnable):
    def __init__(self, history_store: HistoryStore, cache_store: TranslationCacheStore) -> None:
        super().__init__()
        self.history_store = history_store
        self.cache_store = cache_store
        self.signals = PersistenceSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.history_store.clear()
            self.cache_store.clear()
            self.signals.completed.emit("")
        except Exception as exc:
            self.signals.completed.emit(f"Saved data could not be cleared: {exc}")
