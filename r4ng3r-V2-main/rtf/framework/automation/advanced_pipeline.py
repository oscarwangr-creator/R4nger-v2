from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from framework.workflows.engine import Step, WorkflowBuilder

StepCallable = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
ConditionCallable = Callable[[Dict[str, Any]], bool]
TransformCallable = Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass
class AdvancedStep:
    name: str
    runner: StepCallable
    condition: Optional[ConditionCallable] = None
    retries: int = 0
    parallel_group: Optional[str] = None
    transform: Optional[TransformCallable] = None
    isolate_failures: bool = True


@dataclass
class AdvancedPipelineResult:
    success: bool
    context: Dict[str, Any]
    steps: List[Dict[str, Any]] = field(default_factory=list)


class AdvancedPipeline:
    def __init__(self, name: str) -> None:
        self.name = name
        self.steps: List[AdvancedStep] = []

    def add_step(self, step: AdvancedStep) -> "AdvancedPipeline":
        self.steps.append(step)
        return self

    async def run(self, initial_context: Optional[Dict[str, Any]] = None) -> AdvancedPipelineResult:
        context = dict(initial_context or {})
        records: List[Dict[str, Any]] = []
        idx = 0
        while idx < len(self.steps):
            step = self.steps[idx]
            if step.parallel_group:
                group = [step]
                idx += 1
                while idx < len(self.steps) and self.steps[idx].parallel_group == group[0].parallel_group:
                    group.append(self.steps[idx])
                    idx += 1
                results = await asyncio.gather(*(self._execute_step(item, context) for item in group))
                for result in results:
                    records.append(result)
                    if result["success"] and isinstance(result.get("output"), dict):
                        context.update(result["output"])
                continue
            result = await self._execute_step(step, context)
            records.append(result)
            if result["success"] and isinstance(result.get("output"), dict):
                context.update(result["output"])
            idx += 1
        return AdvancedPipelineResult(success=all(item["success"] or item["isolated"] for item in records), context=context, steps=records)

    async def _execute_step(self, step: AdvancedStep, context: Dict[str, Any]) -> Dict[str, Any]:
        if step.condition and not step.condition(context):
            return {"name": step.name, "success": True, "skipped": True, "isolated": True, "output": {}}
        effective_context = dict(context)
        if step.transform:
            effective_context.update(step.transform(context))
        error = ""
        for attempt in range(step.retries + 1):
            try:
                output = await step.runner(effective_context)
                return {"name": step.name, "success": True, "attempts": attempt + 1, "isolated": step.isolate_failures, "output": output}
            except Exception as exc:
                error = str(exc)
                if attempt < step.retries:
                    await asyncio.sleep(min(2 * (attempt + 1), 5))
        return {"name": step.name, "success": False, "attempts": step.retries + 1, "isolated": step.isolate_failures, "error": error, "output": {}}

    def to_workflow_builder(self) -> WorkflowBuilder:
        builder = WorkflowBuilder(self.name)
        for step in self.steps:
            if hasattr(step.runner, "module_class"):
                builder.add_step(
                    name=step.name,
                    module_class=step.runner.module_class,
                    transformer=step.transform,
                    required=not step.isolate_failures,
                    retry_count=step.retries,
                )
        return builder
