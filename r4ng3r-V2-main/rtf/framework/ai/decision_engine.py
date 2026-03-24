from __future__ import annotations

from typing import Any, Dict, List


class DecisionEngine:
    def score_action(self, data_value: float, success_probability: float, novelty: float, cost: float) -> float:
        return (data_value * 0.4) + (success_probability * 0.3) + (novelty * 0.2) - (cost * 0.1)

    def analyze_gaps(self, context: Dict[str, Any]) -> List[str]:
        gaps = []
        targets = context.get("active_targets", [])
        if not any(item.get("type") == "email" for item in targets):
            gaps.append("email")
        if not any(item.get("type") == "domain" for item in targets):
            gaps.append("domain")
        if not any(item.get("type") == "ip" for item in targets):
            gaps.append("ip")
        if not any(item.get("type") == "username" for item in targets):
            gaps.append("username")
        return gaps

    def rank_actions(self, actions: List[Dict[str, Any]], gaps: List[str]) -> List[Dict[str, Any]]:
        ranked = []
        for action in actions:
            coverage = len(set(action.get("target_types", [])) & set(gaps))
            data_value = min(1.0, 0.4 + (coverage * 0.2))
            success_probability = action.get("success_probability", 0.75)
            novelty = action.get("novelty", 0.65 if coverage else 0.3)
            cost = action.get("cost", 0.25 if action.get("type") == "workflow" else 0.15)
            score = self.score_action(data_value, success_probability, novelty, cost)
            ranked.append({**action, "score": round(score, 4)})
        return sorted(ranked, key=lambda item: item["score"], reverse=True)
