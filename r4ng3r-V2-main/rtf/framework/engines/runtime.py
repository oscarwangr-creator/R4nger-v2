from __future__ import annotations

from typing import Any, Dict

from framework.engines.registry import EngineSpec, engine_registry


class EngineRuntime:
    def describe(self, name: str) -> Dict[str, Any]:
        spec = engine_registry.get(name)
        return self._payload(spec)

    def run(self, name: str, seed: Dict[str, Any] | None = None) -> Dict[str, Any]:
        spec = engine_registry.get(name)
        payload = self._payload(spec)
        payload["seed"] = seed or {}
        payload["status"] = "planned"
        payload["async_pipeline"] = {
            "queue": spec.queue,
            "stages": [
                {"name": stage, "mode": "async", "distributed": True, "worker_roles": list(spec.worker_roles)}
                for stage in spec.task_pipeline
            ],
        }
        payload["integration"] = {
            "module_path": spec.module_path,
            "cli": f"rtf engine run {spec.name}",
            "scheduler_hooks": list(spec.scheduler_hooks),
        }
        return payload

    def _payload(self, spec: EngineSpec) -> Dict[str, Any]:
        return {
            "name": spec.name,
            "category": spec.category,
            "description": spec.description,
            "dependencies": list(spec.dependencies),
            "task_pipeline": list(spec.task_pipeline),
            "worker_roles": list(spec.worker_roles),
            "graph_capabilities": list(spec.graph_capabilities),
            "tool_wrappers": list(spec.tool_wrappers),
            "scheduler_hooks": list(spec.scheduler_hooks),
        }


engine_runtime = EngineRuntime()
