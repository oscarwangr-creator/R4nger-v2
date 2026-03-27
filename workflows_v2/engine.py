from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict

import yaml

from core_v2.pipeline_engine_v2 import PipelineEngineV2


class SafeConditionEvaluator:
    ALLOWED_NODES = {
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.UnaryOp,
        ast.Not,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.In,
        ast.NotIn,
        ast.Gt,
        ast.GtE,
        ast.Lt,
        ast.LtE,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.Subscript,
        ast.Dict,
        ast.List,
        ast.Tuple,
        ast.Attribute,
    }

    def evaluate(self, expression: str, context: Dict[str, Any]) -> bool:
        tree = ast.parse(expression, mode="eval")
        for node in ast.walk(tree):
            if type(node) not in self.ALLOWED_NODES:
                raise ValueError(f"unsupported condition expression node: {type(node).__name__}")
        return bool(eval(compile(tree, "<workflow_condition>", "eval"), {"__builtins__": {}}, context))


class WorkflowEngine:
    def __init__(self, pipeline_engine: PipelineEngineV2, workflows_path: str = "workflows_v2"):
        self.pipeline_engine = pipeline_engine
        self.workflows_path = Path(workflows_path)
        self._condition_evaluator = SafeConditionEvaluator()

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
            if condition:
                try:
                    should_run = self._condition_evaluator.evaluate(condition, {"payload": payload, "outcomes": outcomes})
                except Exception as exc:
                    outcomes[current] = {
                        "status": "error",
                        "message": f"invalid condition '{condition}': {exc}",
                    }
                    current = step.get("on_failure")
                    continue

                if not should_run:
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
