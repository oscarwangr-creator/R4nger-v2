"""Workflow engine that orchestrates multiple pipelines with optional conditions."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


class WorkflowEngine:
    def __init__(self, pipeline_engine: Any, workflows_dir: str = "workflows") -> None:
        self.pipeline_engine = pipeline_engine
        self.workflows_dir = Path(workflows_dir)

    def _workflow_files(self) -> list[Path]:
        return sorted(self.workflows_dir.glob("*.yaml"))

    def list_workflows(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for workflow_file in self._workflow_files():
            data = yaml.safe_load(workflow_file.read_text()) or {}
            if not data.get("name"):
                continue
            items.append(
                {
                    "name": data.get("name"),
                    "description": data.get("description", ""),
                    "steps": len(data.get("steps", [])),
                    "file": workflow_file.name,
                }
            )
        return items

    def load_workflow(self, name: str) -> Dict[str, Any]:
        for workflow_file in self._workflow_files():
            data = yaml.safe_load(workflow_file.read_text()) or {}
            if data.get("name") == name:
                return data
        raise FileNotFoundError(f"Workflow not found: {name}")

    def _should_run(self, condition: str, payload: Dict[str, Any]) -> bool:
        """Very small/safe condition evaluator for usability.

        Supported:
        - absent/"always" => True
        - "payload.<key> == <value>"
        - "payload.<key> != <value>"
        """
        condition = (condition or "always").strip()
        if condition == "always":
            return True

        if condition.startswith("payload.") and "==" in condition:
            left, right = condition.split("==", 1)
            key = left.strip().replace("payload.", "", 1)
            expected = right.strip().strip("\"'")
            return str(payload.get(key)) == expected

        if condition.startswith("payload.") and "!=" in condition:
            left, right = condition.split("!=", 1)
            key = left.strip().replace("payload.", "", 1)
            expected = right.strip().strip("\"'")
            return str(payload.get(key)) != expected

        return False

    def execute(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        workflow = self.load_workflow(name)
        results: List[Dict[str, Any]] = []

        for step in workflow.get("steps", []):
            if not self._should_run(step.get("condition", "always"), payload):
                results.append(
                    {
                        "step": step.get("name"),
                        "pipeline": step.get("pipeline"),
                        "status": "skipped",
                        "reason": "condition_not_met",
                    }
                )
                continue

            pipeline_result = self.pipeline_engine.execute(
                name=step["pipeline"],
                payload=payload,
                parallel=bool(step.get("parallel", False)),
                max_workers=int(step.get("max_workers", 4)),
            )
            results.append(
                {
                    "step": step.get("name"),
                    "pipeline": step.get("pipeline"),
                    "status": pipeline_result.get("status", "unknown"),
                    "result": pipeline_result,
                }
            )

            if step.get("required", True) and pipeline_result.get("status") != "completed":
                return {
                    "workflow": name,
                    "status": "failed",
                    "step_results": results,
                }

        return {
            "workflow": name,
            "status": "completed",
            "step_results": results,
        }
