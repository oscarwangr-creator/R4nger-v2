from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Set

from ai_v2.decision_engine import DecisionEngine


class ExpansionEngine:
    """Recursive intelligence expansion planner.

    The engine never hard-fails on sparse or partially broken data; it continues
    generating next pipeline recommendations from whichever entities are available.
    """

    def __init__(self):
        self.decision_engine = DecisionEngine()

    def discover_entities(self, pipeline_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        entities: List[Dict[str, Any]] = []
        for stage in pipeline_output.get("stages", []):
            for tool_result in stage.get("results", []):
                entities.extend(tool_result.get("normalized", {}).get("entities", []))
        return entities

    def next_actions(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pipelines = self.decision_engine.select_next_pipelines(state)
        return {"next_pipelines": pipelines, "count": len(pipelines)}

    def recursive_plan(self, seed_state: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        queue = deque([(seed_state, 0)])
        visited_pipelines: Set[str] = set()
        actions: List[Dict[str, Any]] = []

        while queue:
            state, depth = queue.popleft()
            if depth >= max_depth:
                continue

            suggestion = self.next_actions(state)
            next_pipelines = suggestion.get("next_pipelines", [])
            actions.append({"depth": depth, "state": state, "suggestion": suggestion})

            for pipeline in next_pipelines:
                if pipeline in visited_pipelines:
                    continue
                visited_pipelines.add(pipeline)
                queue.append(({"pipeline": pipeline, "source": "recursive_expansion"}, depth + 1))

        return {
            "status": "planned",
            "max_depth": max_depth,
            "visited_pipelines": sorted(visited_pipelines),
            "actions": actions,
        }
