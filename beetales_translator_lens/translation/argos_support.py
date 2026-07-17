"""Shared lazy Argos Translate environment configuration."""

from __future__ import annotations

import os
from pathlib import Path

from beetales_translator_lens.storage.paths import ensure_data_directories


def configure_argos_environment(model_root: Path | None = None) -> Path:
    root = model_root or ensure_data_directories()["models"] / "argos"
    package_dir = root / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("ARGOS_PACKAGES_DIR", str(package_dir))
    # Retain the legacy singular form for older Argos releases.
    os.environ.setdefault("ARGOS_PACKAGE_DIR", str(package_dir))
    os.environ.setdefault("ARGOS_DEVICE_TYPE", "cpu")
    os.environ.setdefault("XDG_DATA_HOME", str(root / "data"))
    os.environ.setdefault("XDG_CONFIG_HOME", str(root / "config"))
    os.environ.setdefault("XDG_CACHE_HOME", str(root / "cache"))
    return root
