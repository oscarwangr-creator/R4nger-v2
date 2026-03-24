from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from framework.titan.identity_resolution import IdentityResolutionEngine
from framework.titan.knowledge_graph import TitanKnowledgeGraph
from framework.titan.wrappers import StaticToolCatalog


SOCMINT_STAGES = [
    ("A", "Seed normalization"),
    ("B", "Username discovery"),
    ("B2", "Deep account scraping"),
    ("B3", "Search engine scraping"),
    ("B4", "Social network analysis"),
    ("C", "Email breach intelligence"),
    ("D", "Social media deep analysis"),
    ("E", "Domain intelligence"),
    ("F", "Code intelligence"),
    ("G", "Phone intelligence"),
    ("H", "Dark web monitoring"),
    ("I", "Metadata intelligence"),
    ("J", "AI correlation engine"),
    ("K", "Graph integration"),
    ("L", "Recursive pivot engine"),
    ("M", "Threat scoring"),
]


@dataclass
class StageResult:
    code: str
    name: str
    status: str
    summary: Dict[str, Any]


class TitanSOCMINTPipeline:
    def __init__(self) -> None:
        self.identity_engine = IdentityResolutionEngine()
        self.graph = TitanKnowledgeGraph()

    def run(self, seed: Dict[str, Any]) -> Dict[str, Any]:
        normalized_seed = self._normalize_seed(seed)
        profile_a = {
            "username": normalized_seed.get("username", ""),
            "email": normalized_seed.get("email", ""),
            "bio": normalized_seed.get("bio", ""),
            "posting_hour": normalized_seed.get("posting_hour", 12),
            "writing_sample": normalized_seed.get("writing_sample", ""),
            "avatar_hash": normalized_seed.get("avatar_hash", ""),
        }
        profile_b = {
            "username": normalized_seed.get("candidate_username", normalized_seed.get("username", "")),
            "email": normalized_seed.get("candidate_email", normalized_seed.get("email", "")),
            "bio": normalized_seed.get("candidate_bio", normalized_seed.get("bio", "")),
            "posting_hour": normalized_seed.get("candidate_posting_hour", normalized_seed.get("posting_hour", 12)),
            "writing_sample": normalized_seed.get("candidate_writing_sample", normalized_seed.get("writing_sample", "")),
            "avatar_hash": normalized_seed.get("candidate_avatar_hash", normalized_seed.get("avatar_hash", "")),
        }
        correlation = self.identity_engine.resolve([profile_a, profile_b])
        graph = self.graph.ingest_identity(normalized_seed)
        stages: List[StageResult] = []
        tool_summary = StaticToolCatalog.summary()
        for code, name in SOCMINT_STAGES:
            summary: Dict[str, Any] = {"seed_keys": sorted(normalized_seed.keys())[:8]}
            if code == "A":
                summary = {
                    "normalized": {
                        "username": normalized_seed.get("username", ""),
                        "email": normalized_seed.get("email", ""),
                        "phone": normalized_seed.get("phone", ""),
                        "domain": normalized_seed.get("domain", ""),
                    },
                    "canonicalization": ["E164 phone", "lowercased email", "domain normalization", "URL canonicalization"],
                }
            elif code == "B":
                summary = {"tools": tool_summary["username_discovery"], "coverage": ">=500 platforms"}
            elif code == "B2":
                summary = {"tools": tool_summary["social_scrapers"], "collects": ["bio", "posts", "followers", "links", "profile metadata"]}
            elif code == "B3":
                summary = {"engines": tool_summary["search_engines"], "extracts": ["profiles", "mentions", "documents", "images", "videos"]}
            elif code == "B4":
                summary = {"analytics": ["follower graph mapping", "mutual connections", "timeline correlation", "bot detection", "account similarity scoring"]}
            elif code == "C":
                summary = {"sources": tool_summary["email_breach"], "detections": ["breach presence", "credential reuse", "historic aliases"]}
            elif code == "D":
                summary = {"coverage": ["Twitter sentiment", "Instagram engagement", "LinkedIn networks", "Reddit behavior", "TikTok metadata"]}
            elif code == "E":
                summary = {"tools": tool_summary["domain_intel"], "capabilities": ["subdomain discovery", "service detection", "web fingerprinting"]}
            elif code == "F":
                summary = {"tools": tool_summary["code_intel"], "detections": ["exposed secrets", "tokens", "credentials"]}
            elif code == "G":
                summary = {"capabilities": ["carrier detection", "VOIP detection", "reverse lookup"]}
            elif code == "H":
                summary = {"sources": ["Tor", "I2P", "dark forums", "leak markets"]}
            elif code == "I":
                summary = {"tool": "ExifTool", "extracts": ["image metadata", "GPS coordinates", "timestamps", "device identifiers"]}
            elif code == "J":
                summary = correlation
            elif code == "K":
                summary = {"graph_nodes": len(graph["nodes"]), "graph_edges": len(graph["edges"]), "backend": graph["backend"]}
            elif code == "L":
                summary = {"pivots": self._pivot_candidates(normalized_seed), "mode": "recursive"}
            elif code == "M":
                summary = {"risk_score": correlation["risk_score"], "confidence": correlation["confidence"], "cluster": correlation["cluster"]}
            stages.append(StageResult(code, name, "ready", summary))
        return {
            "pipeline": "titan_socmint_omega",
            "stage_count": len(stages),
            "stages": [stage.__dict__ for stage in stages],
            "normalized_seed": normalized_seed,
            "graph": graph,
            "identity_resolution": correlation,
            "reporting": {"formats": ["HTML", "PDF", "JSON", "XLSX"]},
        }

    def _normalize_seed(self, seed: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(seed)
        if seed.get("email"):
            normalized["email"] = str(seed["email"]).strip().lower()
            if not normalized.get("domain") and "@" in normalized["email"]:
                normalized["domain"] = normalized["email"].split("@", 1)[1]
        if seed.get("domain"):
            normalized["domain"] = str(seed["domain"]).strip().lower().removeprefix("https://").removeprefix("http://").strip("/")
        if seed.get("username"):
            normalized["username"] = str(seed["username"]).strip()
        if seed.get("phone"):
            digits = "".join(ch for ch in str(seed["phone"]) if ch.isdigit())
            if len(digits) == 10:
                normalized["phone"] = f"+1{digits}"
            elif digits:
                normalized["phone"] = f"+{digits}"
        return normalized

    def _pivot_candidates(self, seed: Dict[str, Any]) -> List[str]:
        pivots = []
        for key in ("username", "email", "phone", "domain", "organization"):
            value = seed.get(key)
            if value:
                pivots.append(f"pivot:{key}:{value}")
        return pivots[:8]
