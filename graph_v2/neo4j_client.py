from __future__ import annotations

from typing import Any, Dict, List

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover
    GraphDatabase = None


class GraphClient:
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(user, password)) if GraphDatabase else None

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def ingest_entities(self, entities: List[Dict[str, Any]]) -> int:
        if not self.driver:
            return 0
        query = """
        UNWIND $entities AS e
        MERGE (n:Entity {id: e.id})
        SET n += e
        """
        with self.driver.session() as session:
            session.run(query, entities=entities)
        return len(entities)

    def ingest_relationships(self, relationships: List[Dict[str, Any]]) -> int:
        if not self.driver:
            return 0
        query = """
        UNWIND $rels AS r
        MATCH (a:Entity {id: r.source})
        MATCH (b:Entity {id: r.target})
        MERGE (a)-[rel:RELATED_TO {relation: r.relation}]->(b)
        SET rel.confidence = r.confidence
        """
        with self.driver.session() as session:
            session.run(query, rels=relationships)
        return len(relationships)

    def query(self, cypher: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        if not self.driver:
            return []
        with self.driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]
