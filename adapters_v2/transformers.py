from __future__ import annotations

from typing import Any, Dict


def flatten_result(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tool": result.get("tool"),
        "status": result.get("status"),
        "entities": result.get("normalized", {}).get("entities", []),
        "relationships": result.get("normalized", {}).get("relationships", []),
    }


def deduplicate_entities(state: Dict[str, Any]) -> Dict[str, Any]:
    seen = set()
    entities = []
    for entity in state.get("entities", []):
        key = (entity.get("type"), entity.get("value"))
        if key not in seen:
            seen.add(key)
            entities.append(entity)
    state["entities"] = entities
    return state
