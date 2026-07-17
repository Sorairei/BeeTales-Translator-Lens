"""Argos package discovery, installation, and removal."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from beetales_translator_lens.translation.argos_support import configure_argos_environment
from beetales_translator_lens.translation.route_resolver import TranslationRouteResolver


@dataclass(frozen=True, slots=True)
class ModelPackageInfo:
    source_language: str
    target_language: str
    version: str = ""
    installed: bool = False


@dataclass(frozen=True, slots=True)
class ModelInstallResult:
    route: list[str]
    installed_pairs: list[tuple[str, str]]
    error: str | None = None


class ArgosModelManager:
    def __init__(
        self,
        *,
        model_root: Path | None = None,
        package_module: Any | None = None,
        route_resolver: TranslationRouteResolver | None = None,
    ) -> None:
        self._model_root = model_root
        self._package_module = package_module
        self.route_resolver = route_resolver or TranslationRouteResolver()
        self._available_packages: list[Any] | None = None

    @staticmethod
    def is_available() -> bool:
        return importlib.util.find_spec("argostranslate") is not None

    def installed_pairs(self) -> set[tuple[str, str]]:
        package_module = self._packages()
        return {
            (str(package.from_code), str(package.to_code))
            for package in package_module.get_installed_packages()
        }

    def installed_models(self) -> list[ModelPackageInfo]:
        package_module = self._packages()
        return [
            ModelPackageInfo(
                str(package.from_code),
                str(package.to_code),
                str(getattr(package, "package_version", "")),
                True,
            )
            for package in package_module.get_installed_packages()
        ]

    def refresh_available(self) -> list[ModelPackageInfo]:
        package_module = self._packages()
        package_module.update_package_index()
        self._available_packages = list(package_module.get_available_packages())
        installed = self.installed_pairs()
        return [
            ModelPackageInfo(
                str(package.from_code),
                str(package.to_code),
                str(getattr(package, "package_version", "")),
                (str(package.from_code), str(package.to_code)) in installed,
            )
            for package in self._available_packages
        ]

    def install_for_route(
        self,
        source_language: str,
        target_language: str,
        progress: Callable[[str], None] | None = None,
    ) -> ModelInstallResult:
        try:
            available_info = self.refresh_available()
            available_pairs = {
                (package.source_language, package.target_language)
                for package in available_info
            }
            route = self.route_resolver.resolve_available(
                source_language,
                target_language,
                available_pairs,
            )
            if route is None:
                return ModelInstallResult(
                    [],
                    [],
                    f"No direct or English-pivot model route is available for {source_language} -> {target_language}.",
                )

            installed = self.installed_pairs()
            newly_installed: list[tuple[str, str]] = []
            for route_source, route_target in zip(route, route[1:]):
                pair = (route_source, route_target)
                if pair in installed:
                    continue
                package = self._find_available(route_source, route_target)
                if package is None:
                    return ModelInstallResult(route, newly_installed, f"Model {route_source} -> {route_target} was not found.")
                if progress:
                    progress(f"Downloading model {route_source} -> {route_target}...")
                package_path = package.download()
                if progress:
                    progress(f"Installing model {route_source} -> {route_target}...")
                self._packages().install_from_path(package_path)
                newly_installed.append(pair)
            return ModelInstallResult(route, newly_installed)
        except Exception as exc:
            return ModelInstallResult([], [], f"Model installation failed: {exc}")

    def uninstall_pair(self, source_language: str, target_language: str) -> bool:
        package_module = self._packages()
        for package in package_module.get_installed_packages():
            if str(package.from_code) == source_language and str(package.to_code) == target_language:
                package_module.uninstall(package)
                return True
        return False

    def _find_available(self, source_language: str, target_language: str) -> Any | None:
        for package in self._available_packages or []:
            if str(package.from_code) == source_language and str(package.to_code) == target_language:
                return package
        return None

    def _packages(self) -> Any:
        if self._package_module is None:
            if not self.is_available():
                raise RuntimeError("Argos Translate is not installed.")
            configure_argos_environment(self._model_root)
            import argostranslate.package as package_module

            self._package_module = package_module
        return self._package_module
