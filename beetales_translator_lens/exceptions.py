"""Excepciones propias del proyecto."""


class BeeTalesError(Exception):
    """Error base recuperable de BeeTales Translator Lens."""


class SettingsError(BeeTalesError):
    """La configuración no se pudo leer o guardar."""
