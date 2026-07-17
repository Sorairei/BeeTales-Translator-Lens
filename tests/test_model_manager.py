"""Argos model route installation tests with fake packages."""

from pathlib import Path

from beetales_translator_lens.translation.model_manager import ArgosModelManager


class Package:
    def __init__(self, source: str, target: str) -> None:
        self.from_code = source
        self.to_code = target
        self.package_version = "1.0"

    def download(self) -> Path:
        return Path(f"{self.from_code}-{self.to_code}.argosmodel")


class PackageModule:
    def __init__(self, available: list[Package], installed: list[Package] | None = None) -> None:
        self.available = available
        self.installed = installed or []
        self.updated = False

    def update_package_index(self) -> None:
        self.updated = True

    def get_available_packages(self) -> list[Package]:
        return self.available

    def get_installed_packages(self) -> list[Package]:
        return self.installed

    def install_from_path(self, path: Path) -> None:
        source, target = path.stem.split("-")
        self.installed.append(Package(source, target))

    def uninstall(self, package: Package) -> None:
        self.installed.remove(package)


def test_direct_model_is_downloaded_and_installed() -> None:
    module = PackageModule([Package("en", "es")])
    manager = ArgosModelManager(package_module=module)

    result = manager.install_for_route("en", "es")

    assert result.error is None
    assert result.route == ["en", "es"]
    assert manager.installed_pairs() == {("en", "es")}


def test_two_models_are_installed_for_english_pivot() -> None:
    module = PackageModule([Package("pl", "en"), Package("en", "es")])
    manager = ArgosModelManager(package_module=module)

    result = manager.install_for_route("pl", "es")

    assert result.route == ["pl", "en", "es"]
    assert result.installed_pairs == [("pl", "en"), ("en", "es")]
