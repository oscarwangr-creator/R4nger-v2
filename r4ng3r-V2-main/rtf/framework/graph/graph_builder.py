from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GraphNode:
    id: str
    type: str
    value: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = field(default_factory=dict)


class GraphBuilder:
    def __init__(self, neo4j_enabled: bool = False, neo4j_driver: Any = None) -> None:
        self.neo4j_enabled = neo4j_enabled and neo4j_driver is not None
        self.neo4j_driver = neo4j_driver
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    def add_node(self, node_type: str, value: str, **properties: Any) -> str:
        node_id = f"{node_type}:{value}"
        self.nodes.setdefault(node_id, GraphNode(id=node_id, type=node_type, value=value, properties=properties))
        return node_id

    def add_edge(self, source: str, target: str, relation: str, **properties: Any) -> None:
        self.edges.append(GraphEdge(source=source, target=target, relation=relation, properties=properties))

    def ingest_cluster(self, cluster: Dict[str, Any]) -> Dict[str, int]:
        usernames = cluster.get("usernames", [])
        emails = cluster.get("emails", [])
        domains = cluster.get("domains", [])
        phones = cluster.get("phones", [])
        people = cluster.get("people", []) or [cluster.get("cluster_id", "person-unknown")]
        for person in people:
            person_id = self.add_node("Person", person)
            for username in usernames:
                self.add_edge(person_id, self.add_node("Username", username), "USES")
            for email in emails:
                email_id = self.add_node("Email", email)
                self.add_edge(person_id, email_id, "USES")
            for domain in domains:
                self.add_edge(person_id, self.add_node("Domain", domain), "OWNS")
            for phone in phones:
                self.add_edge(person_id, self.add_node("IP", phone), "LINKED_TO", semantic_type="phone")
        return {"nodes": len(self.nodes), "edges": len(self.edges)}

    def export(self) -> Dict[str, Any]:
        payload = {
            "nodes": [node.__dict__ for node in self.nodes.values()],
            "edges": [edge.__dict__ for edge in self.edges],
            "backend": "neo4j" if self.neo4j_enabled else "memory",
        }
        if self.neo4j_enabled:
            self._sync_neo4j(payload)
        return payload

    def _sync_neo4j(self, payload: Dict[str, Any]) -> None:
        if not self.neo4j_enabled:
            return
        with self.neo4j_driver.session() as session:
            for node in payload["nodes"]:
                session.run(
                    "MERGE (n:Entity {id: $id}) SET n.type = $type, n.value = $value, n += $properties",
                    id=node["id"],
                    type=node["type"],
                    value=node["value"],
                    properties=node.get("properties", {}),
                )
            for edge in payload["edges"]:
                session.run(
                    "MATCH (a:Entity {id: $source}), (b:Entity {id: $target}) "
                    "MERGE (a)-[r:RELATED {relation: $relation}]->(b) SET r += $properties",
                    source=edge["source"],
                    target=edge["target"],
                    relation=edge["relation"],
                    properties=edge.get("properties", {}),
                )
