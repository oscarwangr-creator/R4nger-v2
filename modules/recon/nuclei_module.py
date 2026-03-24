from __future__ import annotations

from typing import Any, Dict

from core.base_module import BaseModule, ModuleMetadata


class NucleiReconModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="nuclei_recon",
            category="Recon",
            description="Template-based vulnerability reconnaissance",
            tags=['recon', 'nuclei'],
        )
        self.add_fallback(self._fallback)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload["target"]
        return {
            "target": target,
            "module": self.metadata.name,
            "summary": "Identified candidate vulnerabilities using templates",
            "evidence": [
                {"key": "simulated", "value": True},
                {"key": "timestamp", "value": payload.get("timestamp", "runtime")},
            ],
        }

    def _fallback(self, payload: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        return {
            "target": payload.get("target"),
            "module": self.metadata.name,
            "fallback": True,
            "reason": str(exc),
            "summary": "Fallback output generated because primary operation failed.",
        }
