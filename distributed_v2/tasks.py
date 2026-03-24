from __future__ import annotations

from typing import Any, Dict

from ai_v2.correlation_engine import CorrelationEngine
from ai_v2.risk_scoring import RiskScorer
from automation_v2.expansion_engine import ExpansionEngine
from core_v2.pipeline_engine_v2 import PipelineEngineV2
from core_v2.tool_executor import ToolExecutor
from core_v2.tool_loader import ToolLoader
from core_v2.tool_registry import ToolRegistry
from distributed_v2.celery_app import celery_app


registry = ToolRegistry()
ToolLoader(registry).autodiscover(["tools_v2"]) 
executor = ToolExecutor(registry)
pipeline_engine = PipelineEngineV2(executor)
correlator = CorrelationEngine()
risk_scorer = RiskScorer()
expander = ExpansionEngine()


@celery_app.task(name="distributed_v2.tasks.run_pipeline")
def run_pipeline_task(pipeline_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    result = pipeline_engine.execute_pipeline(pipeline_name, payload)
    entities = result.get("output", {}).get("entities", [])
    correlations = correlator.correlate(entities)
    risk = risk_scorer.score([{"category": e.get("type", "generic"), "confidence": e.get("confidence", 0.5)} for e in entities])
    next_actions = expander.next_actions({"entities": entities, "risk": risk})
    return {"pipeline": result, "correlations": correlations, "risk": risk, "next": next_actions}


@celery_app.task(name="distributed_v2.tasks.autonomous_recon_loop")
def autonomous_recon_loop() -> Dict[str, Any]:
    seed = {"input_type": "domain", "value": "example.com"}
    output = run_pipeline_task("attack_surface_pipeline", seed)
    return {"status": "loop_executed", "output": output}
