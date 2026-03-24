from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable

from core_v2.base_tool import BaseTool
from core_v2.tool_registry import ToolRegistry


class ToolLoader:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def autodiscover(self, packages: Iterable[str] = ("tools_v2",)) -> int:
        registered = 0
        for package_name in packages:
            package = importlib.import_module(package_name)
            for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
                try:
                    module = importlib.import_module(module_info.name)
                except Exception:
                    continue
                for item in module.__dict__.values():
                    if isinstance(item, type) and issubclass(item, BaseTool) and item is not BaseTool:
                        self.registry.register(item)
                        registered += 1
        return registered
