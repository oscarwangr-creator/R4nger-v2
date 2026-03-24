from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class AgentContext:
    seed: Dict[str, Any] = field(default_factory=dict)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    active_targets: List[Dict[str, Any]] = field(default_factory=list)
    completed_actions: List[Dict[str, Any]] = field(default_factory=list)
    memory_summary: Dict[str, Any] = field(default_factory=dict)
    loaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ContextManager:
    def load(self, seed: Dict[str, Any] | None = None, memory: Dict[str, Any] | None = None) -> AgentContext:
        seed = dict(seed or {})
        memory = dict(memory or {})
        active = list(memory.get("pivot_targets", []))
        if seed and seed not in active:
            active.insert(0, seed)
        return AgentContext(seed=seed, active_targets=active, memory_summary=memory)

    def record_observation(self, context: AgentContext, observation: Dict[str, Any]) -> None:
        context.observations.append(observation)

    def mark_action(self, context: AgentContext, action: Dict[str, Any]) -> None:
        context.completed_actions.append(action)

    def snapshot(self, context: AgentContext) -> Dict[str, Any]:
        return {
            "seed": context.seed,
            "active_targets": context.active_targets,
            "observations": context.observations[-50:],
            "completed_actions": context.completed_actions[-50:],
            "memory_summary": context.memory_summary,
            "loaded_at": context.loaded_at,
        }
