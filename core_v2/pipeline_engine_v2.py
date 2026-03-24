from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml

from adapters_v2.transformers import deduplicate_entities
from core_v2.tool_executor import ToolExecutor


class PipelineEngineV2:
    def __init__(self, executor: ToolExecutor, pipelines_path: str = "pipelines_v2"):
        self.executor = executor
        self.pipelines_path = Path(pipelines_path)

    def execute_pipeline(self, pipeline_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        definition = self._load_pipeline(pipeline_name)
        if not definition:
            return {"status": "error", "message": f"pipeline {pipeline_name} not found"}

        state: Dict[str, Any] = {"input": payload, "entities": [], "relationships": [], "evidence": []}
        stages_out = []
        for stage in definition.get("stages", []):
            results = self.executor.run_many(stage.get("tools", []), payload, parallel=stage.get("parallel", True))
            for result in results:
                normalized = result.get("normalized", {})
                state["entities"].extend(normalized.get("entities", []))
                state["relationships"].extend(normalized.get("relationships", []))
                state["evidence"].append(result)
            stages_out.append({"name": stage["name"], "results": results})

        state = deduplicate_entities(state)
        return {
            "status": "completed",
            "pipeline": pipeline_name,
            "description": definition.get("description", ""),
            "stages": stages_out,
            "output": state,
        }

    def _load_pipeline(self, pipeline_name: str) -> Dict[str, Any]:
        file_path = self.pipelines_path / f"{pipeline_name}.yaml"
        if not file_path.exists():
            return {}
        with file_path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
