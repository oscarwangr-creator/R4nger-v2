from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Type

from core_v2.base_tool import BaseTool
from core_v2.tool_catalog import ExternalToolSpec


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._by_category: Dict[str, list[str]] = defaultdict(list)
        self._external_tools: Dict[str, ExternalToolSpec] = {}

    def register(self, tool_class: Type[BaseTool]) -> None:
        self._tools[tool_class.name] = tool_class
        if tool_class.name not in self._by_category[tool_class.category]:
            self._by_category[tool_class.category].append(tool_class.name)

    def register_external(self, tool_spec: ExternalToolSpec) -> None:
        self._external_tools[tool_spec.name] = tool_spec
        if tool_spec.name not in self._by_category[tool_spec.category]:
            self._by_category[tool_spec.category].append(tool_spec.name)

    def get_tool(self, name: str) -> Type[BaseTool] | None:
        return self._tools.get(name)

    def get_external_tool(self, name: str) -> ExternalToolSpec | None:
        return self._external_tools.get(name)

    def list_tools(self, category: str | None = None) -> Dict[str, Any]:
        if category:
            return {category: sorted(self._by_category.get(category, []))}
        return {k: sorted(v) for k, v in self._by_category.items()}

    def all_tools(self) -> Dict[str, Type[BaseTool]]:
        return dict(self._tools)

    def counts(self) -> Dict[str, int]:
        return {
            "internal": len(self._tools),
            "external": len(self._external_tools),
            "total": len(self._tools) + len(self._external_tools),
        }
