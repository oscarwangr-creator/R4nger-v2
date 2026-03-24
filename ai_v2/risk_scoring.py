from __future__ import annotations

from typing import Any, Dict, List


class RiskScorer:
    WEIGHTS = {
        "credential": 0.35,
        "breach": 0.3,
        "infrastructure": 0.15,
        "darkweb": 0.2,
        "threatintel": 0.25,
    }

    def score(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        score = 0.0
        drivers = []
        for finding in findings:
            category = finding.get("category", "generic")
            base = self.WEIGHTS.get(category, 0.05)
            confidence = finding.get("confidence", 0.5)
            contrib = base * confidence
            score += contrib
            drivers.append({"category": category, "contribution": round(contrib, 4)})
        normalized = min(100, round(score * 100, 2))
        tier = "low" if normalized < 30 else "medium" if normalized < 70 else "high"
        return {"risk_score": normalized, "tier": tier, "drivers": drivers}
