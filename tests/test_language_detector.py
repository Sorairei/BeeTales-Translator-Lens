"""Language detector confidence and ambiguity tests."""

from dataclasses import dataclass

from beetales_translator_lens.translation.language_detector import LanguageDetector


@dataclass
class Iso:
    name: str


@dataclass
class Language:
    code: str

    @property
    def iso_code_639_1(self) -> Iso:
        return Iso(self.code)


@dataclass
class Confidence:
    code: str
    value: float

    @property
    def language(self) -> Language:
        return Language(self.code)


class Backend:
    def __init__(self, values: list[Confidence]) -> None:
        self.values = values

    def compute_language_confidence_values(self, text: str) -> list[Confidence]:
        return self.values


def test_confident_language_is_returned() -> None:
    detector = LanguageDetector(backend=Backend([Confidence("PL", 0.84), Confidence("ES", 0.08)]))

    result = detector.detect("Czy ktoś chce zagrać?")

    assert result.language == "pl"
    assert result.confident is True


def test_ambiguous_and_too_short_text_are_rejected() -> None:
    detector = LanguageDetector(backend=Backend([Confidence("EN", 0.51), Confidence("ES", 0.45)]))

    assert detector.detect("hello world").language is None
    assert detector.detect("ok").error == "Text is too short for reliable language detection."
