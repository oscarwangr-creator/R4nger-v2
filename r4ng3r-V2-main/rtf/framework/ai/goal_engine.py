from __future__ import annotations

from typing import Any, Dict, List


class GoalEngine:
    def build_goals(self, mission: Dict[str, Any]) -> List[Dict[str, Any]]:
        goals = []
        primary = mission.get("primary_goal", "Expand target intelligence coverage")
        goals.append({"name": primary, "priority": 100})
        for item in mission.get("target_types", ["username", "email", "domain", "ip"]):
            goals.append({"name": f"Enrich {item} intelligence", "priority": 70})
        if mission.get("include_validation", True):
            goals.append({"name": "Validate and correlate results", "priority": 60})
        return goals
