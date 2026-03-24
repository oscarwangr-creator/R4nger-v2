from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from framework.correlation.identity_graph import IdentityGraph


class Neo4jIdentityService:
    EDGE_TYPES = [
        "REGISTERED_WITH",
        "LOGGED_IN_FROM",
        "OWNS",
        "MENTIONED_IN",
        "FOLLOWS",
        "CONTRIBUTED_TO",
        "CONNECTED_TO",
    ]

    def __init__(self) -> None:
        self._fallback = IdentityGraph()

    def correlate(self, seeds: List[Dict[str, Any]]) -> Dict[str, Any]:
        clustered = self._fallback.cluster(seeds)
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        node_index = set()
        for cluster in clustered.get("clusters", []):
            for item in cluster.get("evidence", []):
                for label in ("username", "email", "phone", "ip", "domain", "organization", "repository", "account"):
                    value = item.get(label)
                    if value:
                        key = (label, str(value).lower())
                        if key not in node_index:
                            nodes.append({"label": label, "value": value, "cluster_id": cluster["cluster_id"]})
                            node_index.add(key)
                username = item.get("username")
                email = item.get("email")
                domain = item.get("domain") or (email.split("@", 1)[1] if isinstance(email, str) and "@" in email else "")
                if username and email:
                    edges.append({"source": username, "target": email, "type": "REGISTERED_WITH"})
                if username and domain:
                    edges.append({"source": username, "target": domain, "type": "CONNECTED_TO"})
        confidence = self._confidence_scores(clustered.get("clusters", []))
        return {
            "backend": "neo4j-compatible",
            "mode": "offline-emulation",
            "nodes": nodes,
            "edges": edges,
            "clusters": clustered.get("clusters", []),
            "confidence_scores": confidence,
            "edge_types": self.EDGE_TYPES,
        }

    def _confidence_scores(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        counts = Counter()
        for cluster in clusters:
            evidence = cluster.get("evidence", [])
            for item in evidence:
                subject = item.get("username") or item.get("email") or item.get("domain") or "unknown"
                counts[subject] += 1
        return [
            {
                "subject": subject,
                "score": round(min(0.99, 0.35 + (count * 0.12)), 2),
                "accounts_seen": count,
            }
            for subject, count in counts.items()
        ]
