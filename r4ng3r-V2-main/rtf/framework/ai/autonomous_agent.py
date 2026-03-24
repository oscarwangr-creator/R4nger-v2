from __future__ import annotations

from typing import Any, Dict, List, Optional

from framework.ai.context_manager import ContextManager
from framework.ai.decision_engine import DecisionEngine
from framework.ai.goal_engine import GoalEngine
from framework.ai.memory_store import MemoryStore, MemoryRecord
from framework.ai.strategy_library import StrategyLibrary
from framework.modules.loader import module_loader
from framework.workflows.engine import get_workflow


class AutonomousAgent:
    def __init__(self) -> None:
        self.context_manager = ContextManager()
        self.decision_engine = DecisionEngine()
        self.goal_engine = GoalEngine()
        self.memory_store = MemoryStore()
        self.strategy_library = StrategyLibrary()
        self.memories: List[MemoryRecord] = []
        module_loader.load_all()

    async def run(self, mission: Dict[str, Any], max_iterations: int = 3) -> Dict[str, Any]:
        goals = self.goal_engine.build_goals(mission)
        context = self.context_manager.load(seed=mission.get("seed", {}), memory=self.memory_store.summarize(self.memories))
        execution_log: List[Dict[str, Any]] = []
        for _ in range(max_iterations):
            gaps = self.decision_engine.analyze_gaps(self.context_manager.snapshot(context))
            ranked = self.decision_engine.rank_actions(self.strategy_library.list_actions(), gaps)
            if not ranked:
                break
            action = ranked[0]
            result = await self._execute_action(action, mission.get("seed", {}))
            pivots = self._extract_pivots(result)
            memory = self.memory_store.store(goals[0]["name"], action["name"], action["score"], result, pivots)
            self.memories.append(memory)
            self.context_manager.record_observation(context, {"gaps": gaps, "result": result})
            self.context_manager.mark_action(context, {"action": action["name"], "score": action["score"]})
            context.active_targets.extend(p for p in pivots if p not in context.active_targets)
            execution_log.append({"action": action, "result": result, "pivots": pivots})
            if not pivots:
                break
        return {
            "goals": goals,
            "context": self.context_manager.snapshot(context),
            "execution_log": execution_log,
            "memory": self.memory_store.summarize(self.memories),
        }

    async def _execute_action(self, action: Dict[str, Any], seed: Dict[str, Any]) -> Dict[str, Any]:
        if action.get("type") == "workflow":
            workflow = get_workflow(action["workflow"])
            result = await workflow.run(seed)
            return result.to_dict()
        cls = module_loader.get(action["module"])
        module = cls()
        opts = self._module_options(action["module"], seed)
        result = await module.execute(opts)
        return result.to_dict()

    def _module_options(self, module_path: str, seed: Dict[str, Any]) -> Dict[str, Any]:
        if module_path == "osint/breach_correlation":
            return {"query": seed.get("email") or seed.get("username") or seed.get("target", "")}
        if module_path == "recon/tech_stack_fingerprinter":
            return {"target": seed.get("domain") or seed.get("ip") or seed.get("target", "")}
        return seed

    def _extract_pivots(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        pivots: List[Dict[str, Any]] = []
        serialized = str(result)
        for marker, target_type in (("@", "email"), ("http", "domain")):
            if marker in serialized:
                pivots.append({"type": target_type, "value": marker})
        return pivots[:10]
