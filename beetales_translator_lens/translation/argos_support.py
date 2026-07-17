"""Shared lazy Argos Translate environment configuration."""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import types
from pathlib import Path

from beetales_translator_lens.resources import minisbd_model_directory
from beetales_translator_lens.storage.paths import ensure_data_directories


def configure_argos_environment(model_root: Path | None = None) -> Path:
    root = model_root or ensure_data_directories()["models"] / "argos"
    package_dir = root / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("ARGOS_PACKAGES_DIR", str(package_dir))
    # Retain the legacy singular form for older Argos releases.
    os.environ.setdefault("ARGOS_PACKAGE_DIR", str(package_dir))
    os.environ.setdefault("ARGOS_DEVICE_TYPE", "cpu")
    # MiniSBD is the lightweight local sentence splitter bundled with Argos.
    # Selecting it avoids loading the optional Stanza/Torch and SpaCy stacks.
    os.environ.setdefault("ARGOS_CHUNK_TYPE", "MINISBD")
    os.environ.setdefault("XDG_DATA_HOME", str(root / "data"))
    os.environ.setdefault("XDG_CONFIG_HOME", str(root / "config"))
    os.environ.setdefault("XDG_CACHE_HOME", str(root / "cache"))
    _install_bundled_minisbd_models(root)
    _install_stanza_compatibility_stub()
    return root


def _install_bundled_minisbd_models(root: Path) -> None:
    """Seed the private Argos cache so sentence splitting works offline."""

    source_directory = minisbd_model_directory()
    target_directory = root / "data" / "argos-translate" / "minisbd"
    target_directory.mkdir(parents=True, exist_ok=True)
    for source in source_directory.glob("*.onnx"):
        target = target_directory / source.name
        if not target.exists() or target.stat().st_size != source.stat().st_size:
            shutil.copy2(source, target)


def _install_stanza_compatibility_stub() -> None:
    """Satisfy Argos' unconditional optional import in compact builds."""

    if "stanza" in sys.modules or importlib.util.find_spec("stanza") is not None:
        return

    stanza_stub = types.ModuleType("stanza")

    class UnsupportedStanzaPipeline:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("Stanza is unavailable; BeeTales uses MiniSBD.")

    stanza_stub.Pipeline = UnsupportedStanzaPipeline
    sys.modules["stanza"] = stanza_stub
