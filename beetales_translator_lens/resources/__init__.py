"""Packaged visual resources."""

from pathlib import Path


def application_icon_path() -> Path:
    return Path(__file__).resolve().parent / "icons" / "beetales_translator_lens.png"


def brand_logo_path() -> Path:
    return Path(__file__).resolve().parent / "icons" / "beetales-logo-v2.png"


def mascot_image_path() -> Path:
    return Path(__file__).resolve().parent / "icons" / "sora-avatar.png"


def minisbd_model_directory() -> Path:
    """Return the bundled sentence-boundary models for supported languages."""

    return Path(__file__).resolve().parent / "minisbd_models"
