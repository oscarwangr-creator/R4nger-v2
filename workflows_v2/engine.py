from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict

from core_v2.pipeline_engine_v2 import PipelineEngineV2


class WorkflowEngine:
    def __init__(self, pipeline_engine: PipelineEngineV2, workflows_path: str = "workflows_v2"):
        self.pipeline_engine = pipeline_engine
        self.workflows_path = Path(workflows_path)

    def run(self, workflow_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        wf = self._load_workflow(workflow_name)
        if not wf:
            return {"status": "error", "message": f"workflow {workflow_name} not found"}

        step_map = {s["name"]: s for s in wf.get("steps", [])}
        current = wf["steps"][0]["name"]
        outcomes: Dict[str, Any] = {}

        while current:
            step = step_map[current]
            condition = step.get("condition")
            if condition and not eval(condition, {}, {"payload": payload, "outcomes": outcomes}):
                current = step.get("on_failure")
                continue

            result = self.pipeline_engine.execute_pipeline(step["pipeline"], payload)
            outcomes[current] = result
            current = step.get("on_success") if result.get("status") == "completed" else step.get("on_failure")

        return {"status": "completed", "workflow": workflow_name, "outcomes": outcomes}

    def _load_workflow(self, name: str) -> Dict[str, Any]:
        file_path = self.workflows_path / f"{name}.yaml"
        if not file_path.exists():
            return {}
        with file_path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
