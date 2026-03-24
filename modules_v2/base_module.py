from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
import traceback


@dataclass
class ModuleResult:
    name: str
    module_type: str
    status: str
    started_at: str
    finished_at: str
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    error: str | None = None


class BaseModule(ABC):
    """Base class for non-tool intelligence modules.

    Modules can orchestrate one or more tools and optionally apply AI enhancements,
    but they must always remain functional without AI dependencies.
    """

    name: str = "base_module"
    module_type: str = "generic"
    description: str = ""

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute module logic and return a normalized module output."""

    def run(self, payload: Dict[str, Any]) -> ModuleResult:
        started = datetime.utcnow().isoformat()
        try:
            output = self.execute(payload)
            return ModuleResult(
                name=self.name,
                module_type=self.module_type,
                status="success",
                started_at=started,
                finished_at=datetime.utcnow().isoformat(),
                artifacts=output.get("artifacts", []),
                entities=output.get("entities", []),
                relationships=output.get("relationships", []),
            )
        except Exception as exc:
            return ModuleResult(
                name=self.name,
                module_type=self.module_type,
                status="error",
                started_at=started,
                finished_at=datetime.utcnow().isoformat(),
                error=f"{exc}\n{traceback.format_exc()}",
            )
