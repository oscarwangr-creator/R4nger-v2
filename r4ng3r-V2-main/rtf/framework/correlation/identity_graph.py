from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Set


@dataclass
class IdentityCluster:
    cluster_id: str
    usernames: Set[str] = field(default_factory=set)
    emails: Set[str] = field(default_factory=set)
    domains: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    confidence: float = 0.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "usernames": sorted(self.usernames),
            "emails": sorted(self.emails),
            "domains": sorted(self.domains),
            "phones": sorted(self.phones),
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
        }


class IdentityGraph:
    def cluster(self, identities: List[Dict[str, Any]]) -> Dict[str, Any]:
        clusters: List[IdentityCluster] = []
        for identity in identities:
            matched = self._find_best_cluster(identity, clusters)
            if matched is None:
                matched = IdentityCluster(cluster_id=f"cluster-{len(clusters)+1}")
                clusters.append(matched)
            self._merge_identity(matched, identity)

        for cluster in clusters:
            cluster.confidence = self._score_cluster(cluster)

        return {
            "clusters": [cluster.to_dict() for cluster in clusters],
            "total_clusters": len(clusters),
            "deduplicated_entities": sum(len(c.usernames) + len(c.emails) + len(c.domains) + len(c.phones) for c in clusters),
        }

    def _find_best_cluster(self, identity: Dict[str, Any], clusters: List[IdentityCluster]) -> IdentityCluster | None:
        best: IdentityCluster | None = None
        best_score = 0.0
        for cluster in clusters:
            score = self._identity_similarity(identity, cluster)
            if score > best_score:
                best_score = score
                best = cluster
        return best if best_score >= 0.65 else None

    def _identity_similarity(self, identity: Dict[str, Any], cluster: IdentityCluster) -> float:
        scores: List[float] = []
        username = (identity.get("username") or "").lower()
        email = (identity.get("email") or "").lower()
        phone = self._normalize_phone(identity.get("phone") or "")
        domain = (identity.get("domain") or (email.split("@", 1)[1] if "@" in email else "")).lower()

        if username and cluster.usernames:
            scores.append(max(self._ratio(username, existing) for existing in cluster.usernames))
        if email and cluster.emails:
            scores.append(1.0 if email in cluster.emails else max(self._ratio(email, existing) for existing in cluster.emails))
        if domain and cluster.domains:
            scores.append(1.0 if domain in cluster.domains else max(self._ratio(domain, existing) for existing in cluster.domains))
        if phone and cluster.phones:
            scores.append(1.0 if phone in cluster.phones else max(self._ratio(phone, existing) for existing in cluster.phones))
        return max(scores, default=0.0)

    def _merge_identity(self, cluster: IdentityCluster, identity: Dict[str, Any]) -> None:
        username = (identity.get("username") or "").lower().strip()
        email = (identity.get("email") or "").lower().strip()
        phone = self._normalize_phone(identity.get("phone") or "")
        domain = (identity.get("domain") or (email.split("@", 1)[1] if "@" in email else "")).lower().strip()
        if username:
            cluster.usernames.add(username)
        if email:
            cluster.emails.add(email)
        if phone:
            cluster.phones.add(phone)
        if domain:
            cluster.domains.add(domain)
        cluster.evidence.append(identity)

    def _score_cluster(self, cluster: IdentityCluster) -> float:
        signals = 0.25 * bool(cluster.usernames) + 0.3 * bool(cluster.emails) + 0.2 * bool(cluster.domains) + 0.25 * bool(cluster.phones)
        density = min(1.0, len(cluster.evidence) / 5)
        return min(0.99, signals * 0.7 + density * 0.3)

    @staticmethod
    def _ratio(left: str, right: str) -> float:
        return SequenceMatcher(None, left, right).ratio()

    @staticmethod
    def _normalize_phone(value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())
