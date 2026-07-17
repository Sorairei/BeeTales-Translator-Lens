"""Non-blocking rotating application logging without captured text."""

from __future__ import annotations

import logging
import logging.handlers
import queue
from dataclasses import dataclass
from pathlib import Path

from beetales_translator_lens.storage.paths import ensure_data_directories


class PrivacyLogFilter(logging.Filter):
    """Exclude verbose third-party records that may repeat translated text."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith("beetales") or record.levelno >= logging.WARNING


@dataclass(slots=True, weakref_slot=True)
class LogManager:
    listener: logging.handlers.QueueListener
    queue_handler: logging.Handler

    def close(self) -> None:
        root = logging.getLogger()
        root.removeHandler(self.queue_handler)
        self.listener.stop()
        for handler in self.listener.handlers:
            handler.close()


def configure_logging(log_directory: Path | None = None) -> LogManager:
    """Send log writes to a listener thread and rotate files at 1 MiB."""

    directory = log_directory or ensure_data_directories()["logs"]
    directory.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = logging.handlers.RotatingFileHandler(
        directory / "beetales.log",
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log_queue: queue.Queue[logging.LogRecord] = queue.Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.addFilter(PrivacyLogFilter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(queue_handler)
    listener = logging.handlers.QueueListener(
        log_queue,
        file_handler,
        stream_handler,
        respect_handler_level=True,
    )
    listener.start()
    return LogManager(listener, queue_handler)
