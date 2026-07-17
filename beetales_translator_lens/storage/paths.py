"""Data paths independent from the executable location."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_path

from beetales_translator_lens.constants import APP_AUTHOR, APP_NAME


def data_directory() -> Path:
    """Return the local per-user data directory."""

    return Path(user_data_path(APP_NAME, APP_AUTHOR, roaming=False))


def ensure_data_directories(root: Path | None = None) -> dict[str, Path]:
    """Create the private data directories reserved by the architecture."""

    base = root or data_directory()
    paths = {name: base / name for name in ("config", "models", "cache", "logs", "history", "debug")}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths
