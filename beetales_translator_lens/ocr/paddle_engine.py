"""Lazy local PaddleOCR adapter supporting version 3 and legacy results."""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
import types
from collections.abc import Iterable, Mapping
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray

from beetales_translator_lens.ocr.base import OCREngine
from beetales_translator_lens.ocr.models import OCRLine, OCRResult
from beetales_translator_lens.storage.paths import ensure_data_directories

PADDLE_LANGUAGE_CODES = {
    "auto": "en",
    "en": "en",
    "es": "es",
    "pl": "pl",
    "pt": "pt",
    "ja": "japan",
}

LOGGER = logging.getLogger(__name__)


def _default_backend_factory(**kwargs: Any) -> Any:
    install_modelscope_compatibility_stub()
    from paddleocr import PaddleOCR

    return PaddleOCR(**kwargs)


def install_modelscope_compatibility_stub() -> None:
    """Satisfy PaddleX's unused ModelScope import in compact builds."""

    if "modelscope" in sys.modules or importlib.util.find_spec("modelscope") is not None:
        return

    modelscope_stub = types.ModuleType("modelscope")

    def unavailable_snapshot_download(*args: object, **kwargs: object) -> None:
        raise RuntimeError("ModelScope is unavailable; BeeTales uses Hugging Face models.")

    modelscope_stub.snapshot_download = unavailable_snapshot_download
    sys.modules["modelscope"] = modelscope_stub


class PaddleOCREngine(OCREngine):
    """Load one local PaddleOCR pipeline per requested recognition language."""

    def __init__(
        self,
        *,
        minimum_confidence: float = 0.45,
        backend_factory: Callable[..., Any] | None = None,
        model_root: Path | None = None,
    ) -> None:
        self.minimum_confidence = max(0.0, min(float(minimum_confidence), 1.0))
        self._backend_factory = backend_factory or _default_backend_factory
        self._uses_default_backend = backend_factory is None
        self._model_root = model_root or ensure_data_directories()["models"]
        self._engines: dict[str, Any] = {}
        self._lock = RLock()

    @staticmethod
    def is_available() -> bool:
        """Return whether both local inference packages are installed."""

        return (
            importlib.util.find_spec("paddleocr") is not None
            and importlib.util.find_spec("paddle") is not None
        )

    @staticmethod
    def backend_language(source_language: str | None) -> str:
        return PADDLE_LANGUAGE_CODES.get(source_language or "en", "en")

    def recognize(
        self,
        image: NDArray,
        source_language: str | None = None,
    ) -> OCRResult:
        started = perf_counter()
        language = source_language or "en"
        if image.size == 0:
            return self._error_result("The OCR image is empty.", language, started)
        if self._uses_default_backend and not self.is_available():
            return self._error_result(
                "PaddleOCR is not installed. Install the OCR dependencies first.",
                language,
                started,
            )

        try:
            with self._lock:
                engine = self._get_engine(language)
                if hasattr(engine, "predict"):
                    raw = engine.predict(np.ascontiguousarray(image))
                    lines = self._parse_v3_results(raw)
                elif hasattr(engine, "ocr"):
                    raw = engine.ocr(np.ascontiguousarray(image), cls=False)
                    lines = self._parse_legacy_results(raw)
                else:
                    raise RuntimeError("The PaddleOCR backend has no supported prediction method.")
        except Exception as exc:
            LOGGER.exception("Local OCR inference failed for language %s", language)
            return self._error_result(self._friendly_error(exc), language, started)

        lines = [line for line in lines if line.text.strip() and line.confidence >= self.minimum_confidence]
        lines.sort(key=self._reading_order)
        full_text = "\n".join(line.text.strip() for line in lines)
        return OCRResult(
            full_text=full_text,
            lines=lines,
            elapsed_ms=(perf_counter() - started) * 1000,
            language=language,
        )

    def clear(self) -> None:
        """Release references to loaded language pipelines."""

        with self._lock:
            self._engines.clear()

    def _get_engine(self, source_language: str) -> Any:
        backend_language = self.backend_language(source_language)
        if backend_language not in self._engines:
            self._configure_model_cache()
            LOGGER.info("Loading local PaddleOCR pipeline for language %s", backend_language)
            self._engines[backend_language] = self._backend_factory(
                lang=backend_language,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                device="cpu",
                enable_mkldnn=False,
            )
        return self._engines[backend_language]

    def _configure_model_cache(self) -> None:
        """Keep model downloads under the application's per-user data tree."""

        self._model_root.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("PADDLEOCR_HOME", str(self._model_root / "paddleocr"))
        os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(self._model_root / "paddlex"))

    def _parse_v3_results(self, raw_results: Any) -> list[OCRLine]:
        lines: list[OCRLine] = []
        if raw_results is None:
            return lines
        results = raw_results if isinstance(raw_results, Iterable) and not isinstance(raw_results, (str, bytes, Mapping)) else [raw_results]
        for raw_result in results:
            payload = self._result_payload(raw_result)
            texts = self._as_list(payload.get("rec_texts"))
            scores = self._as_list(payload.get("rec_scores"))
            polygons = self._as_list(payload.get("rec_polys"))
            for index, text in enumerate(texts):
                score = float(scores[index]) if index < len(scores) else 0.0
                polygon = polygons[index] if index < len(polygons) else []
                lines.append(OCRLine(str(text), score, self._polygon(polygon)))
        return lines

    @staticmethod
    def _result_payload(raw_result: Any) -> Mapping[str, Any]:
        payload: Any = raw_result
        if not isinstance(payload, Mapping):
            json_value = getattr(payload, "json", None)
            if callable(json_value):
                json_value = json_value()
            if json_value is not None:
                payload = json_value
            elif hasattr(payload, "res"):
                payload = getattr(payload, "res")
        if isinstance(payload, Mapping) and isinstance(payload.get("res"), Mapping):
            payload = payload["res"]
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, np.ndarray):
            return list(value)
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            return list(value)
        return []

    def _parse_legacy_results(self, raw_results: Any) -> list[OCRLine]:
        lines: list[OCRLine] = []
        if not raw_results:
            return lines
        pages = raw_results
        if self._looks_like_legacy_line(raw_results[0]):
            pages = [raw_results]
        for page in pages:
            if not page:
                continue
            for item in page:
                if not self._looks_like_legacy_line(item):
                    continue
                polygon, recognition = item
                text, confidence = recognition
                lines.append(OCRLine(str(text), float(confidence), self._polygon(polygon)))
        return lines

    @staticmethod
    def _looks_like_legacy_line(value: Any) -> bool:
        return (
            isinstance(value, (list, tuple))
            and len(value) == 2
            and isinstance(value[1], (list, tuple))
            and len(value[1]) >= 2
            and isinstance(value[1][0], str)
        )

    @staticmethod
    def _polygon(value: Any) -> list[tuple[int, int]]:
        try:
            array = np.asarray(value).reshape(-1, 2)
            return [(int(round(float(x))), int(round(float(y)))) for x, y in array]
        except (TypeError, ValueError):
            return []

    @staticmethod
    def _reading_order(line: OCRLine) -> tuple[int, int]:
        if not line.bounding_box:
            return (0, 0)
        center_y = round(sum(point[1] for point in line.bounding_box) / len(line.bounding_box))
        left_x = min(point[0] for point in line.bounding_box)
        return (center_y, left_x)

    @staticmethod
    def _friendly_error(error: Exception) -> str:
        message = str(error)
        if "requires additional dependencies" in message.lower():
            return (
                "OCR components are incomplete. Reinstall the latest BeeTales "
                "Translator Lens package."
            )
        return f"OCR failed: {message}"

    @staticmethod
    def _error_result(message: str, language: str, started: float) -> OCRResult:
        return OCRResult(
            full_text="",
            lines=[],
            elapsed_ms=(perf_counter() - started) * 1000,
            language=language,
            error=message,
        )
