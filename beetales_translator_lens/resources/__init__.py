"""Packaged visual resources."""

from pathlib import Path


def application_icon_path() -> Path:
    return Path(__file__).resolve().parent / "icons" / "beetales_translator_lens.png"


def minisbd_model_directory() -> Path:
    """Return the bundled sentence-boundary models for supported languages."""

    return Path(__file__).resolve().parent / "minisbd_models"
