from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable

from modules_v2.base_module import BaseModule
from modules_v2.module_registry import ModuleRegistry


class ModuleLoader:
    def __init__(self, registry: ModuleRegistry):
        self.registry = registry

    def autodiscover(self, packages: Iterable[str] = ("modules_v2",)) -> int:
        registered = 0
        for package_name in packages:
            package = importlib.import_module(package_name)
            if not hasattr(package, "__path__"):
                continue
            for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
                try:
                    module = importlib.import_module(module_info.name)
                except Exception:
                    continue
                for item in module.__dict__.values():
                    if isinstance(item, type) and issubclass(item, BaseModule) and item is not BaseModule:
                        self.registry.register(item)
                        registered += 1
        return registered
