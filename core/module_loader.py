"""Dynamic module discovery and loading helpers."""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import Dict

from core.base_module import BaseModule


class ModuleLoader:
    """Discover and instantiate module classes from a python package tree."""

    def __init__(self, package_name: str = "modules") -> None:
        self.package_name = package_name

    def _walk_packages(self) -> list[ModuleType]:
        root = importlib.import_module(self.package_name)
        packages = [root]

        if not hasattr(root, "__path__"):
            return packages

        for info in pkgutil.walk_packages(root.__path__, prefix=f"{self.package_name}."):
            packages.append(importlib.import_module(info.name))
        return packages

    def discover(self) -> Dict[str, BaseModule]:
        discovered: Dict[str, BaseModule] = {}

        for module in self._walk_packages():
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if not issubclass(cls, BaseModule) or cls is BaseModule:
                    continue
                if cls.__module__ != module.__name__:
                    continue
                instance = cls()
                discovered[instance.metadata.name] = instance

        return discovered
