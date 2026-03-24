from __future__ import annotations

from typing import Any, Dict, List


class DecisionEngine:
    def select_next_pipelines(self, current_state: Dict[str, Any]) -> List[str]:
        risk = current_state.get("risk", {}).get("risk_score", 0)
        discovered_types = {e.get("type") for e in current_state.get("entities", [])}
        plan: List[str] = []

        if "domain" in discovered_types:
            plan.extend(["attack_surface_pipeline", "infrastructure_pipeline"])
        if "email" in discovered_types:
            plan.extend(["credential_pipeline", "breach_pipeline"])
        if risk > 60:
            plan.append("threat_actor_profiling_pipeline")
        if not plan:
            plan.append("identity_pipeline")
        return list(dict.fromkeys(plan))
