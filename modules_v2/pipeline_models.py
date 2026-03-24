from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class PipelineStage(BaseModel):
    name: str
    tools: List[str] = Field(default_factory=list)
    parallel: bool = True
    transforms: List[str] = Field(default_factory=list)


class PipelineDefinition(BaseModel):
    name: str
    description: str
    entrypoint: str
    stages: List[PipelineStage]
    outputs: List[str] = Field(default_factory=list)
    graph_relationships: List[Dict[str, Any]] = Field(default_factory=list)
