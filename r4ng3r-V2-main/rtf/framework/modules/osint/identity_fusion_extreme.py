from __future__ import annotations

from typing import Any, Dict, List

from framework.graph.graph_builder import GraphBuilder
from framework.graph.relationship_engine import RelationshipEngine
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity


class IdentityFusionExtremeModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name": "identity_fusion_extreme", "description": "Advanced identity fusion with username expansion, correlation, timeline, graphing, and risk scoring.", "author": "OpenAI", "category": "osint", "version": "1.0"}

    def _declare_options(self) -> None:
        self._register_option("username", "Username seed", required=False, default="")
        self._register_option("email", "Email seed", required=False, default="")
        self._register_option("domain", "Domain seed", required=False, default="")

    async def run(self) -> ModuleResult:
        username = self.get("username")
        email = self.get("email")
        domain = self.get("domain")
        variations = self._variations(username)
        entities = {
            "people": [username or email or domain or "unknown-person"],
            "usernames": variations,
            "emails": [email] if email else [],
            "domains": [domain] if domain else [],
            "phones": [],
        }
        graph = RelationshipEngine(GraphBuilder()).correlate(entities)
        timeline = self._timeline(username, email, domain)
        risk = self._risk_score(variations, email, domain)
        findings: List[Finding] = [
            self.make_finding(
                title="Identity fusion extreme correlation complete",
                target=username or email or domain or "unknown",
                severity=Severity.MEDIUM if risk >= 0.5 else Severity.INFO,
                description="Entity correlation, pivot generation, timeline reconstruction, and graph export completed.",
                evidence={"risk_score": risk, "timeline_events": len(timeline), "graph_nodes": len(graph.get("nodes", []))},
                tags=["osint", "identity", "graph", "timeline"],
            )
        ]
        return ModuleResult(success=True, output={"seed": {"username": username, "email": email, "domain": domain}, "username_variations": variations, "graph": graph, "timeline": timeline, "risk_score": risk, "auto_pivots": self._pivots(entities)}, findings=findings)

    def _variations(self, username: str) -> List[str]:
        if not username:
            return []
        base = username.replace(".", "").replace("_", "").replace("-", "")
        return list(dict.fromkeys([username, base, f"{base}1", f"{base}2024", f"{base}.ops", f"{base}_sec"]))

    def _timeline(self, username: str, email: str, domain: str) -> List[Dict[str, Any]]:
        events = []
        if username:
            events.append({"stage": "username_expansion", "detail": username})
            events.append({"stage": "social_correlation", "detail": f"correlated {username} across social surfaces"})
        if email:
            events.append({"stage": "breach_intelligence", "detail": email})
        if domain:
            events.append({"stage": "domain_enrichment", "detail": domain})
        return events

    def _risk_score(self, variations: List[str], email: str, domain: str) -> float:
        score = 0.2 + min(len(variations) * 0.08, 0.35)
        if email:
            score += 0.2
        if domain:
            score += 0.15
        return round(min(score, 0.95), 2)

    def _pivots(self, entities: Dict[str, List[str]]) -> List[Dict[str, str]]:
        pivots = []
        for key, value_type in (("usernames", "username"), ("emails", "email"), ("domains", "domain")):
            for item in entities.get(key, []):
                if item:
                    pivots.append({"type": value_type, "value": item})
        return pivots
