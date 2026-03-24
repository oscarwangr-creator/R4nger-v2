from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from core_v2.tool_registry import ToolRegistry


class ToolExecutor:
    def __init__(self, registry: ToolRegistry, max_workers: int = 8):
        self.registry = registry
        self.max_workers = max_workers

    def run_tool(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        tool_cls = self.registry.get_tool(tool_name)
        if not tool_cls:
            return {"tool": tool_name, "status": "error", "error": "tool not found"}
        result = tool_cls().run(payload)
        return result.__dict__

    def run_many(self, tool_names: List[str], payload: Dict[str, Any], parallel: bool = True) -> List[Dict[str, Any]]:
        if not parallel:
            return [self.run_tool(name, payload) for name in tool_names]

        results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self.run_tool, name, payload): name for name in tool_names}
            for future in as_completed(futures):
                results.append(future.result())
        return results
