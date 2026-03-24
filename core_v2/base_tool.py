from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import traceback
from typing import Any, Dict, List


@dataclass
class ToolResult:
    tool: str
    category: str
    status: str
    started_at: str
    finished_at: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    normalized: Dict[str, Any]
    error: str | None = None


class BaseTool(ABC):
    name: str = "base_tool"
    category: str = "generic"
    input_types: List[str] = []
    output_types: List[str] = []

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool logic and return raw output."""

    @abstractmethod
    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw output to canonical Intelligence OS schema."""

    def run(self, payload: Dict[str, Any]) -> ToolResult:
        started = datetime.utcnow().isoformat()
        try:
            self._validate_payload(payload)
            raw_output = self.execute(payload)
            normalized = self.normalize(raw_output)
            return ToolResult(
                tool=self.name,
                category=self.category,
                status="success",
                started_at=started,
                finished_at=datetime.utcnow().isoformat(),
                input=payload,
                output=raw_output,
                normalized=normalized,
            )
        except Exception as exc:
            return ToolResult(
                tool=self.name,
                category=self.category,
                status="error",
                started_at=started,
                finished_at=datetime.utcnow().isoformat(),
                input=payload,
                output={},
                normalized={},
                error=f"{exc}\n{traceback.format_exc()}"
            )

    def _validate_payload(self, payload: Dict[str, Any]) -> None:
        if self.input_types and "input_type" in payload and payload["input_type"] not in self.input_types:
            raise ValueError(f"{self.name} does not accept input_type={payload['input_type']}")
