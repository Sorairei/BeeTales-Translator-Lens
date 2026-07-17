from __future__ import annotations

import sys

from beetales_translator_lens.translation import argos_support


def test_configure_argos_environment_uses_minisbd(tmp_path, monkeypatch) -> None:
    for variable in (
        "ARGOS_PACKAGES_DIR",
        "ARGOS_PACKAGE_DIR",
        "ARGOS_DEVICE_TYPE",
        "ARGOS_CHUNK_TYPE",
        "XDG_DATA_HOME",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
    ):
        monkeypatch.delenv(variable, raising=False)

    root = argos_support.configure_argos_environment(tmp_path)

    assert root == tmp_path
    assert (tmp_path / "packages").is_dir()
    assert argos_support.os.environ["ARGOS_CHUNK_TYPE"] == "MINISBD"
    installed_models = tmp_path / "data" / "argos-translate" / "minisbd"
    assert {path.name for path in installed_models.glob("*.onnx")} == {
        "en.onnx",
        "es.onnx",
        "ja.onnx",
        "pl.onnx",
        "pt.onnx",
    }


def test_missing_stanza_gets_a_clear_compatibility_stub(monkeypatch) -> None:
    monkeypatch.delitem(sys.modules, "stanza", raising=False)
    monkeypatch.setattr(argos_support.importlib.util, "find_spec", lambda name: None)

    argos_support._install_stanza_compatibility_stub()

    assert "stanza" in sys.modules
    try:
        sys.modules["stanza"].Pipeline()
    except RuntimeError as error:
        assert "MiniSBD" in str(error)
    else:
        raise AssertionError("The compatibility pipeline must not run.")
