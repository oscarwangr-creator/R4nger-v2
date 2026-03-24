"""
RTF v2.0 — Core Entity Graph
Manages discovered entities and their relationships across all pipeline stages.

Entity types: domain, email, username, ip, phone, repository, url, credential, hash
Relationship types: owned_by, linked_to, discovered_from, resolves_to, hosted_on
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class EntityType(str, Enum):
    DOMAIN     = "domain"
    EMAIL      = "email"
    USERNAME   = "username"
    IP         = "ip"
    PHONE      = "phone"
    REPOSITORY = "repository"
    URL        = "url"
    CREDENTIAL = "credential"
    HASH       = "hash"
    PERSON     = "person"
    ORG        = "organization"
    CERT       = "certificate"
    CVE        = "cve"
    SERVICE    = "service"


class RelationshipType(str, Enum):
    OWNED_BY       = "owned_by"
    LINKED_TO      = "linked_to"
    DISCOVERED_FROM = "discovered_from"
    RESOLVES_TO    = "resolves_to"
    HOSTED_ON      = "hosted_on"
    USES           = "uses"
    MEMBER_OF      = "member_of"
    ASSOCIATED_WITH = "associated_with"
    EXPOSES        = "exposes"
    VULNERABLE_TO  = "vulnerable_to"


@dataclass
class Entity:
    id:         str
    type:       EntityType
    value:      str
    confidence: float = 1.0          # 0.0–1.0
    source:     str   = "manual"     # which tool/stage discovered this
    stage:      str   = "A"
    metadata:   Dict[str, Any] = field(default_factory=dict)
    tags:       List[str]      = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "type": self.type.value, "value": self.value,
            "confidence": self.confidence, "source": self.source, "stage": self.stage,
            "metadata": self.metadata, "tags": self.tags,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


@dataclass
class Relationship:
    id:       str
    from_id:  str
    to_id:    str
    rel_type: RelationshipType
    weight:   float = 1.0
    source:   str   = "manual"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "from": self.from_id, "to": self.to_id,
            "type": self.rel_type.value, "weight": self.weight,
            "source": self.source, "metadata": self.metadata, "created_at": self.created_at,
        }


class EntityGraph:
    """
    In-memory entity relationship graph for the full investigation.
    Supports deduplication, relationship traversal, confidence scoring,
    and export to JSON / Gephi / DOT formats.
    """

    def __init__(self) -> None:
        self._entities: Dict[str, Entity] = {}          # id → Entity
        self._by_value: Dict[str, str]    = {}          # "type:value" → id
        self._relationships: Dict[str, Relationship] = {}
        self._adj: Dict[str, Set[str]]    = {}          # id → set of related ids
        self.session_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.utcnow().isoformat()

    # ─── Entity management ──────────────────────────────────────────

    def add_entity(
        self,
        type: EntityType,
        value: str,
        source: str = "manual",
        stage: str = "A",
        confidence: float = 1.0,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> Entity:
        """Add or update an entity. Returns the entity (existing or new)."""
        value = value.strip().lower() if type not in (EntityType.CREDENTIAL, EntityType.HASH) else value.strip()
        key = f"{type.value}:{value}"
        if key in self._by_value:
            # Update existing
            ent = self._entities[self._by_value[key]]
            ent.confidence = max(ent.confidence, confidence)
            ent.updated_at = datetime.utcnow().isoformat()
            if metadata:
                ent.metadata.update(metadata)
            if tags:
                ent.tags = list(dict.fromkeys(ent.tags + tags))
            return ent
        ent = Entity(
            id=str(uuid.uuid4())[:12],
            type=type, value=value, source=source, stage=stage,
            confidence=confidence, metadata=metadata or {}, tags=tags or [],
        )
        self._entities[ent.id] = ent
        self._by_value[key] = ent.id
        self._adj[ent.id] = set()
        return ent

    def get_entity(self, type: EntityType, value: str) -> Optional[Entity]:
        key = f"{type.value}:{value.strip().lower()}"
        eid = self._by_value.get(key)
        return self._entities.get(eid) if eid else None

    def get_by_id(self, eid: str) -> Optional[Entity]:
        return self._entities.get(eid)

    def list_entities(self, type: Optional[EntityType] = None) -> List[Entity]:
        ents = list(self._entities.values())
        if type:
            ents = [e for e in ents if e.type == type]
        return sorted(ents, key=lambda e: e.created_at)

    def entity_count(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entities.values():
            counts[e.type.value] = counts.get(e.type.value, 0) + 1
        return counts

    # ─── Relationship management ────────────────────────────────────

    def add_relationship(
        self,
        from_entity: Entity,
        to_entity: Entity,
        rel_type: RelationshipType,
        source: str = "manual",
        weight: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> Relationship:
        """Add a relationship between two entities."""
        key = f"{from_entity.id}:{rel_type.value}:{to_entity.id}"
        if key in self._relationships:
            return self._relationships[key]
        rel = Relationship(
            id=str(uuid.uuid4())[:12],
            from_id=from_entity.id, to_id=to_entity.id,
            rel_type=rel_type, source=source, weight=weight, metadata=metadata or {},
        )
        self._relationships[rel.id] = rel
        self._relationships[key] = rel
        self._adj[from_entity.id].add(to_entity.id)
        self._adj[to_entity.id].add(from_entity.id)
        return rel

    def get_neighbors(self, entity: Entity) -> List[Entity]:
        """Get all entities directly connected to this one."""
        return [self._entities[eid] for eid in self._adj.get(entity.id, set())
                if eid in self._entities]

    def find_paths(self, from_entity: Entity, to_entity: Entity, max_depth: int = 4) -> List[List[Entity]]:
        """BFS to find paths between two entities."""
        if from_entity.id == to_entity.id:
            return [[from_entity]]
        visited: Set[str] = set()
        queue: List[Tuple[Entity, List[Entity]]] = [(from_entity, [from_entity])]
        paths: List[List[Entity]] = []
        while queue and len(paths) < 10:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue
            visited.add(current.id)
            for neighbor in self.get_neighbors(current):
                if neighbor.id == to_entity.id:
                    paths.append(path + [neighbor])
                elif neighbor.id not in visited:
                    queue.append((neighbor, path + [neighbor]))
        return paths

    # ─── Bulk import from investigation stages ──────────────────────

    def ingest_from_stage(
        self,
        stage: str,
        source: str,
        usernames: Optional[List[str]] = None,
        emails: Optional[List[str]]    = None,
        domains: Optional[List[str]]   = None,
        ips: Optional[List[str]]       = None,
        urls: Optional[List[str]]      = None,
        phones: Optional[List[str]]    = None,
        hashes: Optional[List[str]]    = None,
        repos: Optional[List[str]]     = None,
    ) -> Dict[str, int]:
        """Bulk-ingest entity data from a pipeline stage."""
        added: Dict[str, int] = {}
        mappings = [
            (EntityType.USERNAME,   usernames or []),
            (EntityType.EMAIL,      emails    or []),
            (EntityType.DOMAIN,     domains   or []),
            (EntityType.IP,         ips       or []),
            (EntityType.URL,        urls      or []),
            (EntityType.PHONE,      phones    or []),
            (EntityType.HASH,       hashes    or []),
            (EntityType.REPOSITORY, repos     or []),
        ]
        for etype, values in mappings:
            for v in values:
                if v and isinstance(v, str) and v.strip():
                    self.add_entity(etype, v, source=source, stage=stage)
                    added[etype.value] = added.get(etype.value, 0) + 1
        return added

    # ─── Statistics & analysis ──────────────────────────────────────

    def centrality(self) -> List[Tuple[Entity, int]]:
        """Return entities sorted by connection count (degree centrality)."""
        return sorted(
            [(self._entities[eid], len(neighbors))
             for eid, neighbors in self._adj.items() if eid in self._entities],
            key=lambda x: x[1], reverse=True,
        )

    def high_confidence_entities(self, min_confidence: float = 0.8) -> List[Entity]:
        return [e for e in self._entities.values() if e.confidence >= min_confidence]

    def pivot_candidates(self) -> List[Entity]:
        """Return entities that connect multiple clusters (good pivot points)."""
        candidates = []
        for eid, neighbors in self._adj.items():
            if eid not in self._entities:
                continue
            if len(neighbors) >= 3:
                candidates.append(self._entities[eid])
        return sorted(candidates, key=lambda e: len(self._adj.get(e.id, set())), reverse=True)

    # ─── Export ─────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id":    self.session_id,
            "created_at":    self.created_at,
            "entity_count":  self.entity_count(),
            "total_entities": len(self._entities),
            "total_relationships": len([r for r in self._relationships.values()
                                        if isinstance(r, Relationship)]),
            "entities":      [e.to_dict() for e in self._entities.values()],
            "relationships": [r.to_dict() for r in self._relationships.values()
                              if isinstance(r, Relationship)],
        }

    def save(self, path: str) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return str(p)

    @classmethod
    def load(cls, path: str) -> "EntityGraph":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        g = cls()
        g.session_id = data.get("session_id", g.session_id)
        g.created_at = data.get("created_at", g.created_at)
        for ed in data.get("entities", []):
            g.add_entity(
                type=EntityType(ed["type"]), value=ed["value"],
                source=ed.get("source","load"), stage=ed.get("stage","A"),
                confidence=ed.get("confidence",1.0), metadata=ed.get("metadata",{}),
                tags=ed.get("tags",[]),
            )
        return g

    def to_dot(self) -> str:
        """Export as Graphviz DOT format."""
        lines = ["digraph EntityGraph {", '  rankdir=LR;', '  node [shape=box];']
        colors = {
            "domain":"lightblue","email":"lightyellow","username":"lightgreen",
            "ip":"lightcoral","url":"lavender","credential":"tomato","hash":"wheat",
        }
        for e in self._entities.values():
            color = colors.get(e.type.value, "white")
            label = f"{e.type.value}\\n{e.value[:30]}"
            lines.append(f'  "{e.id}" [label="{label}" fillcolor="{color}" style=filled];')
        for r in self._relationships.values():
            if isinstance(r, Relationship):
                lines.append(f'  "{r.from_id}" -> "{r.to_id}" [label="{r.rel_type.value}"];')
        lines.append("}")
        return "\n".join(lines)

    def summary(self) -> str:
        counts = self.entity_count()
        lines = [f"Entity Graph — Session {self.session_id}",
                 f"Total entities: {len(self._entities)}"]
        for t, c in sorted(counts.items()):
            lines.append(f"  {t:15}: {c}")
        lines.append(f"Relationships: {len([r for r in self._relationships.values() if isinstance(r,Relationship)])}")
        return "\n".join(lines)


# Module-level singleton
entity_graph = EntityGraph()
