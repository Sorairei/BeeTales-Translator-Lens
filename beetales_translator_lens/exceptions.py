"""Project-specific exceptions."""


class BeeTalesError(Exception):
    """Base class for recoverable BeeTales errors."""


class SettingsError(BeeTalesError):
    """Settings could not be loaded or saved."""
