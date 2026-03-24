from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


ENTITY_TYPES = [
    "Person", "Username", "Email", "Phone", "Domain", "Organization", "Account",
    "Repository", "IP", "Location", "Device", "Website", "Document", "Media",
]
RELATIONSHIP_TYPES = [
    "REGISTERED_WITH", "CONNECTED_TO", "OWNS", "POSTED_FROM", "MENTIONED_IN",
    "FOLLOWS", "USES_EMAIL", "USES_PHONE", "USES_USERNAME", "ASSOCIATED_WITH",
    "HOSTED_ON", "INTERACTED_WITH",
]


@dataclass
class GraphNode:
    entity_type: str
    value: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    relationship: str
    target: str
    properties: Dict[str, Any] = field(default_factory=dict)


class TitanKnowledgeGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    def add_entity(self, entity_type: str, value: str, **properties: Any) -> GraphNode:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Unsupported entity type: {entity_type}")
        key = f"{entity_type}:{value}"
        node = self.nodes.get(key) or GraphNode(entity_type=entity_type, value=value)
        node.properties.update(properties)
        self.nodes[key] = node
        return node

    def relate(self, source: GraphNode, relationship: str, target: GraphNode, **properties: Any) -> GraphEdge:
        if relationship not in RELATIONSHIP_TYPES:
            raise ValueError(f"Unsupported relationship type: {relationship}")
        edge = GraphEdge(f"{source.entity_type}:{source.value}", relationship, f"{target.entity_type}:{target.value}", properties)
        self.edges.append(edge)
        return edge

    def ingest_identity(self, seed: Dict[str, Any]) -> Dict[str, Any]:
        primary = seed.get("subject") or seed.get("username") or seed.get("email") or seed.get("organization") or "unknown"
        person = self.add_entity("Person", primary, confidence=seed.get("confidence", 0.5), source="socmint")
        username_node = email_node = phone_node = domain_node = org_node = None

        if seed.get("username"):
            username_node = self.add_entity("Username", seed["username"], platform_hint=seed.get("platform_hint", "multi-platform"))
            self.relate(person, "USES_USERNAME", username_node, stage="B")
            account_node = self.add_entity("Account", seed.get("account", seed["username"]), source="username_discovery")
            self.relate(person, "OWNS", account_node, stage="B2")
            self.relate(account_node, "CONNECTED_TO", username_node, stage="B")
        if seed.get("email"):
            email_node = self.add_entity("Email", seed["email"], validation="synthetic")
            self.relate(person, "USES_EMAIL", email_node, stage="A")
        if seed.get("phone"):
            phone_node = self.add_entity("Phone", seed["phone"], normalized=True)
            self.relate(person, "USES_PHONE", phone_node, stage="A")
        if seed.get("domain"):
            domain_node = self.add_entity("Domain", seed["domain"], canonical=True)
            self.relate(person, "ASSOCIATED_WITH", domain_node, stage="E")
            website_node = self.add_entity("Website", f"https://{seed['domain']}", discovered_from="domain_intel")
            self.relate(website_node, "HOSTED_ON", domain_node, stage="E")
        if seed.get("organization"):
            org_node = self.add_entity("Organization", seed["organization"], normalized=True)
            self.relate(person, "REGISTERED_WITH", org_node, stage="A")
        if seed.get("repository"):
            repository = self.add_entity("Repository", seed["repository"], provider="github")
            self.relate(person, "MENTIONED_IN", repository, stage="F")
        if seed.get("location"):
            location = self.add_entity("Location", seed["location"], confidence=0.65)
            self.relate(person, "POSTED_FROM", location, stage="I")
        if seed.get("image"):
            media = self.add_entity("Media", seed["image"], artifact_type="image")
            self.relate(person, "MENTIONED_IN", media, stage="I")
        if username_node and email_node:
            self.relate(username_node, "REGISTERED_WITH", email_node, stage="C")
        if username_node and phone_node:
            self.relate(username_node, "CONNECTED_TO", phone_node, stage="G")
        if email_node and domain_node:
            self.relate(email_node, "CONNECTED_TO", domain_node, stage="C")
        if org_node and domain_node:
            self.relate(org_node, "OWNS", domain_node, stage="E")
        return self.export()

    def schema(self) -> Dict[str, Any]:
        return {
            "backend": "Neo4j",
            "entity_types": list(ENTITY_TYPES),
            "relationship_types": list(RELATIONSHIP_TYPES),
            "constraints": [f"(:{entity} {{value}}) UNIQUE" for entity in ENTITY_TYPES],
            "indexes": [
                "Person(value)", "Username(value)", "Email(value)", "Domain(value)",
                "Organization(value)", "Repository(value)",
            ],
        }

    def export(self) -> Dict[str, Any]:
        return {
            "nodes": [vars(node) for node in self.nodes.values()],
            "edges": [vars(edge) for edge in self.edges],
            **self.schema(),
            "cypher_preview": self.cypher_preview(),
        }

    def cypher_preview(self) -> List[str]:
        preview: List[str] = []
        for node in list(self.nodes.values())[:6]:
            preview.append(
                f"MERGE (n:{node.entity_type} {{value: '{node.value}'}}) SET n += {node.properties!r}"
            )
        for edge in self.edges[:8]:
            src_type, src_value = edge.source.split(":", 1)
            dst_type, dst_value = edge.target.split(":", 1)
            preview.append(
                "MATCH (a:{src_type} {{value: '{src_value}'}}), (b:{dst_type} {{value: '{dst_value}'}}) "
                "MERGE (a)-[r:{rel}]->(b) SET r += {props}".format(
                    src_type=src_type,
                    src_value=src_value,
                    dst_type=dst_type,
                    dst_value=dst_value,
                    rel=edge.relationship,
                    props=edge.properties,
                )
            )
        return preview
