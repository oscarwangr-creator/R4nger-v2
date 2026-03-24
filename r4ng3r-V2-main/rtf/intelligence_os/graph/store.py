from __future__ import annotations
from typing import Dict, List

from intelligence_os.models import Entity, Relationship

class InMemoryGraphStore:
    def __init__(self) -> None:
        self.nodes: Dict[str, Entity] = {}
        self.edges: List[Relationship] = []

    def upsert_entity(self, entity: Entity) -> str:
        key = f'{entity.entity_type}:{entity.value}'
        self.nodes[key] = entity
        return key

    def upsert_relationship(self, relationship: Relationship) -> None:
        self.edges.append(relationship)

    def ingest(self, entities: List[Entity], relationships: List[Relationship]) -> int:
        writes = 0
        for entity in entities:
            self.upsert_entity(entity)
            writes += 1
        for relationship in relationships:
            self.upsert_relationship(relationship)
            writes += 1
        return writes

    def neighbors(self, value: str) -> List[Relationship]:
        return [edge for edge in self.edges if edge.source == value or edge.target == value]
