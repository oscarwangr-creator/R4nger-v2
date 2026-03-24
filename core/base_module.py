"""Base module primitives for R4nger V3."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass(slots=True)
class ModuleMetadata:
    name: str
    category: str
    description: str
    version: str = "3.0.0"
    author: str = "R4nger"
    tags: List[str] = field(default_factory=list)


class ModuleExecutionError(RuntimeError):
    """Raised when module execution fails and no fallback is available."""


class BaseModule(ABC):
    metadata: ModuleMetadata

    def __init__(self) -> None:
        self.fallback_handlers: List[Callable[[Dict[str, Any], Exception], Dict[str, Any]]] = []

    def add_fallback(self, handler: Callable[[Dict[str, Any], Exception], Dict[str, Any]]) -> None:
        self.fallback_handlers.append(handler)

    def validate_input(self, payload: Dict[str, Any]) -> None:
        if "target" not in payload or not str(payload["target"]).strip():
            raise ValueError(f"{self.metadata.name}: missing required input 'target'")

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.now(timezone.utc)
        self.validate_input(payload)
        try:
            result = self.execute(payload)
            return {
                "status": "success",
                "module": self.metadata.name,
                "category": self.metadata.category,
                "started_at": start.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "result": result,
            }
        except Exception as exc:  # noqa: BLE001
            for fallback in self.fallback_handlers:
                try:
                    fallback_result = fallback(payload, exc)
                    return {
                        "status": "fallback",
                        "module": self.metadata.name,
                        "error": str(exc),
                        "result": fallback_result,
                    }
                except Exception:
                    continue
            raise ModuleExecutionError(f"{self.metadata.name} failed: {exc}") from exc
