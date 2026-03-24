from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


class AIAssistant:
    def __init__(self, provider: Any = None) -> None:
        self.provider = provider

    async def analyze_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        severity_counts = Counter((finding.get("severity") or "info").lower() for finding in findings)
        categories = Counter((finding.get("category") or "general").lower() for finding in findings)
        highest = next((level for level in ("critical", "high", "medium", "low", "info") if severity_counts.get(level)), "info")
        suggestions = self.suggest_next_modules(findings)
        ranked = self.rank_vulnerabilities(findings)
        summary = self.generate_summary(findings)
        provider_output = None
        if self.provider is not None:
            try:
                provider_output = await self.provider.analyze(findings)
            except Exception:
                provider_output = {"available": False, "reason": "provider_unavailable"}
        return {
            "severity_counts": dict(severity_counts),
            "categories": dict(categories),
            "highest_severity": highest,
            "suggested_modules": suggestions,
            "ranked_findings": ranked,
            "summary": summary,
            "provider_output": provider_output,
        }

    def suggest_next_modules(self, findings: List[Dict[str, Any]]) -> List[str]:
        tags = {tag.lower() for finding in findings for tag in finding.get("tags", [])}
        suggestions: List[str] = []
        if "osint" in tags or any("email" in tag for tag in tags):
            suggestions.append("osint/breach_correlation")
        if "web" in tags or "header" in tags:
            suggestions.append("web/misconfig_scanner")
        if "credential" in tags or "password" in tags:
            suggestions.append("post_exploitation/credential_reuse_analyzer")
        if not suggestions:
            suggestions.append("recon/tech_stack_fingerprinter")
        return suggestions

    def rank_vulnerabilities(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        return sorted(findings, key=lambda finding: order.get((finding.get("severity") or "info").lower(), 0), reverse=True)

    def generate_summary(self, findings: List[Dict[str, Any]]) -> str:
        if not findings:
            return "No findings available for AI augmentation."
        top_titles = ", ".join(finding.get("title", "unknown") for finding in findings[:3])
        return f"Observed {len(findings)} findings. Top leads: {top_titles}."
