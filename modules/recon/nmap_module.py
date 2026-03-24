from __future__ import annotations

from typing import Any, Dict

from core.base_module import BaseModule, ModuleMetadata


class NmapModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="nmap_recon",
            category="Recon",
            description="Network mapping and service detection",
            tags=['recon', 'network'],
        )
        self.add_fallback(self._fallback)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload["target"]
        return {
            "target": target,
            "module": self.metadata.name,
            "summary": "Mapped open ports and service banners",
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
