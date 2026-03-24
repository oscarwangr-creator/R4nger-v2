from __future__ import annotations

from typing import Any, Dict, List


class QueryEngine:
    def __init__(self, graph_payload: Dict[str, Any]) -> None:
        self.graph = graph_payload

    def find_nodes(self, node_type: str) -> List[Dict[str, Any]]:
        return [node for node in self.graph.get("nodes", []) if node.get("type") == node_type]

    def neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        related_ids = [edge["target"] for edge in self.graph.get("edges", []) if edge.get("source") == node_id]
        return [node for node in self.graph.get("nodes", []) if node.get("id") in related_ids]
