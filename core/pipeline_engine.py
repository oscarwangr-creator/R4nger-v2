"""Pipeline engine with parallel stage execution and fallback handling."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml


class PipelineEngine:
    def __init__(self, module_registry: Dict[str, Any], pipelines_dir: str = "pipelines") -> None:
        self.module_registry = module_registry
        self.pipelines_dir = Path(pipelines_dir)

    def load_pipeline(self, name: str) -> Dict[str, Any]:
        for p in self.pipelines_dir.glob("*.yaml"):
            data = yaml.safe_load(p.read_text())
            if data.get("name") == name:
                return data
        raise FileNotFoundError(f"Pipeline not found: {name}")

    def list_pipelines(self) -> List[dict]:
        items = []
        for p in self.pipelines_dir.glob("*.yaml"):
            data = yaml.safe_load(p.read_text())
            if not isinstance(data, dict) or not data.get("name"):
                continue
            items.append({
                "name": data.get("name"),
                "description": data.get("description", ""),
                "stages": len(data.get("stages", [])),
                "file": p.name,
            })
        return sorted(items, key=lambda x: x["name"])

    def execute(self, name: str, payload: Dict[str, Any], parallel: bool = False, max_workers: int = 4) -> Dict[str, Any]:
        pipeline = self.load_pipeline(name)
        stage_results: List[dict] = []
        started = datetime.now(timezone.utc)

        def run_stage(stage: Dict[str, Any]) -> dict:
            module_name = stage["module"]
            module = self.module_registry[module_name]
            args = dict(stage.get("args", {}))
            args.update(payload)
            result = module.run(args)
            return {"stage": stage["name"], "module": module_name, "result": result}

        stages = pipeline.get("stages", [])
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(run_stage, s) for s in stages]
                for fut in as_completed(futures):
                    try:
                        stage_results.append(fut.result())
                    except Exception as exc:  # noqa: BLE001
                        stage_results.append({"status": "error", "error": str(exc)})
        else:
            for stage in stages:
                try:
                    stage_results.append(run_stage(stage))
                except Exception as exc:  # noqa: BLE001
                    stage_results.append({"stage": stage.get("name"), "status": "error", "error": str(exc)})
                    if stage.get("required", True):
                        break

        return {
            "pipeline": name,
            "status": "completed",
            "parallel": parallel,
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "stage_results": stage_results,
        }
