from __future__ import annotations

from typing import Any, Dict, List

from ai_v2.decision_engine import DecisionEngine


class ExpansionEngine:
    def __init__(self):
        self.decision_engine = DecisionEngine()

    def discover_entities(self, pipeline_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        entities = []
        for stage in pipeline_output.get("stages", []):
            for tool_result in stage.get("results", []):
                entities.extend(tool_result.get("normalized", {}).get("entities", []))
        return entities

    def next_actions(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pipelines = self.decision_engine.select_next_pipelines(state)
        return {"next_pipelines": pipelines, "count": len(pipelines)}
