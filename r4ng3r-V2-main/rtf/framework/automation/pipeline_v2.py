from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

StepRunner = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
Condition = Callable[[Dict[str, Any]], bool]


@dataclass
class PipelineStepV2:
    name: str
    runner: StepRunner
    condition: Optional[Condition] = None
    retries: int = 0
    parallel_group: Optional[str] = None
    isolate_failures: bool = True


@dataclass
class PipelineResultV2:
    success: bool
    context: Dict[str, Any]
    history: List[Dict[str, Any]] = field(default_factory=list)


class PipelineEngineV2:
    def __init__(self, concurrency: int = 4) -> None:
        self.concurrency = concurrency
        self.steps: List[PipelineStepV2] = []

    def add_step(self, step: PipelineStepV2) -> "PipelineEngineV2":
        self.steps.append(step)
        return self

    async def run(self, initial_context: Optional[Dict[str, Any]] = None) -> PipelineResultV2:
        context = dict(initial_context or {})
        history: List[Dict[str, Any]] = []
        idx = 0
        while idx < len(self.steps):
            step = self.steps[idx]
            if step.parallel_group:
                group = [step]
                idx += 1
                while idx < len(self.steps) and self.steps[idx].parallel_group == step.parallel_group:
                    group.append(self.steps[idx])
                    idx += 1
                results = await asyncio.gather(*(self._execute(item, context) for item in group))
                for result in results:
                    history.append(result)
                    if result.get("success"):
                        context.update(result.get("output", {}))
                continue
            result = await self._execute(step, context)
            history.append(result)
            if result.get("success"):
                context.update(result.get("output", {}))
            idx += 1
        return PipelineResultV2(success=all(item.get("success") or item.get("isolated") for item in history), context=context, history=history)

    async def _execute(self, step: PipelineStepV2, context: Dict[str, Any]) -> Dict[str, Any]:
        if step.condition and not step.condition(context):
            return {"name": step.name, "success": True, "skipped": True, "isolated": True, "output": {}}
        error = ""
        for attempt in range(step.retries + 1):
            try:
                output = await step.runner(dict(context))
                return {"name": step.name, "success": True, "attempts": attempt + 1, "isolated": step.isolate_failures, "output": output}
            except Exception as exc:
                error = str(exc)
                if attempt < step.retries:
                    await asyncio.sleep(min(2 ** attempt, 5))
        return {"name": step.name, "success": False, "attempts": step.retries + 1, "isolated": step.isolate_failures, "error": error, "output": {}}
