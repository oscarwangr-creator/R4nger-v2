from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List


class Entity(BaseModel):
    id: str
    type: str
    value: str
    confidence: float = 0.5
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    source: str
    target: str
    relation: str
    confidence: float = 0.5


class IntelligenceRecord(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
