from __future__ import annotations

from framework.engines import engine_runtime, engine_registry
from framework.modules.base import BaseModule, ModuleResult


class ArchitectureEngineModule(BaseModule):
    ENGINE_NAME = ""

    def info(self):
        spec = engine_registry.get(self.ENGINE_NAME)
        return {
            "name": self.ENGINE_NAME.replace("rtf-", "").replace("-", "_"),
            "description": spec.description,
            "author": "OpenAI",
            "category": "architecture",
            "version": "1.0",
        }

    def _declare_options(self) -> None:
        self._register_option("target", "Primary engine target or seed identifier", required=False, default="")
        self._register_option("operation_id", "Operation identifier", required=False, default="")

    async def run(self) -> ModuleResult:
        payload = engine_runtime.run(
            self.ENGINE_NAME,
            {"target": self.get("target"), "operation_id": self.get("operation_id")},
        )
        finding = self.make_finding(
            title=f"Architecture engine ready: {self.ENGINE_NAME}",
            target=self.get("target") or self.ENGINE_NAME,
            description="Engine registered with module system, async pipeline, distributed worker roles, graph storage hooks, and CLI integration.",
            evidence={
                "queue": payload["async_pipeline"]["queue"],
                "worker_roles": payload["worker_roles"],
                "tool_wrappers": payload["tool_wrappers"],
            },
            tags=["architecture", "engine", "distributed", "async"],
        )
        return ModuleResult(success=True, output=payload, findings=[finding])
