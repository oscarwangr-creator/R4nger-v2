from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class Evidence:
    source: str
    artifact: Dict[str, Any]
    confidence: float = 0.5

@dataclass
class Entity:
    entity_type: str
    value: str
    confidence: float = 0.5
    properties: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)

@dataclass
class Relationship:
    source: str
    relationship: str
    target: str
    confidence: float = 0.5
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModuleExecutionResult:
    module: str
    success: bool
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    raw: Any = None
    error: Optional[str] = None
    telemetry: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PipelineExecutionResult:
    pipeline: str
    success: bool
    context: Dict[str, Any] = field(default_factory=dict)
    executed_modules: List[str] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    graph_writes: int = 0
    errors: List[str] = field(default_factory=list)
