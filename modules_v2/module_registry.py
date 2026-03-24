from __future__ import annotations

from collections import defaultdict
from typing import Dict, Type, Any

from modules_v2.base_module import BaseModule


class ModuleRegistry:
    def __init__(self):
        self._modules: Dict[str, Type[BaseModule]] = {}
        self._by_type: Dict[str, list[str]] = defaultdict(list)

    def register(self, module_class: Type[BaseModule]) -> None:
        self._modules[module_class.name] = module_class
        if module_class.name not in self._by_type[module_class.module_type]:
            self._by_type[module_class.module_type].append(module_class.name)

    def get_module(self, name: str) -> Type[BaseModule] | None:
        return self._modules.get(name)

    def all_modules(self) -> Dict[str, Type[BaseModule]]:
        return dict(self._modules)

    def list_modules(self, module_type: str | None = None) -> Dict[str, Any]:
        if module_type:
            return {module_type: sorted(self._by_type.get(module_type, []))}
        return {k: sorted(v) for k, v in self._by_type.items()}
