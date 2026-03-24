from __future__ import annotations

from typing import Any, Dict, List

from framework.graph.graph_builder import GraphBuilder


class RelationshipEngine:
    def __init__(self, builder: GraphBuilder | None = None) -> None:
        self.builder = builder or GraphBuilder()

    def correlate(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        cluster = {
            "people": entities.get("people", []),
            "usernames": entities.get("usernames", []),
            "emails": entities.get("emails", []),
            "domains": entities.get("domains", []),
            "phones": entities.get("phones", []),
        }
        self.builder.ingest_cluster(cluster)
        emails = entities.get("emails", [])
        domains = entities.get("domains", [])
        for email in emails:
            domain = email.split("@", 1)[1] if "@" in email else ""
            if domain:
                self.builder.add_edge(self.builder.add_node("Email", email), self.builder.add_node("Domain", domain), "BELONGS_TO")
        for domain in domains:
            self.builder.add_node("Domain", domain)
        return self.builder.export()
