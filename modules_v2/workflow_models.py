from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Dict, List, Any


class WorkflowStep(BaseModel):
    name: str
    pipeline: str
    on_success: str | None = None
    on_failure: str | None = None
    condition: str | None = None


class WorkflowDefinition(BaseModel):
    name: str
    trigger: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = Field(default_factory=dict)
