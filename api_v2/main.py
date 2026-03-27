from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Dict, List

from ai_v2.correlation_engine import CorrelationEngine
from ai_v2.risk_scoring import RiskScorer
from api_v2.realtime import router as realtime_router
from automation_v2.expansion_engine import ExpansionEngine
from core_v2.pipeline_engine_v2 import PipelineEngineV2
from core_v2.tool_executor import ToolExecutor
from core_v2.tool_loader import ToolLoader
from core_v2.tool_registry import ToolRegistry
from distributed_v2.tasks import run_pipeline_task
from graph_v2.neo4j_client import GraphClient
from modules_v2.module_loader import ModuleLoader
from modules_v2.module_registry import ModuleRegistry
from workflows_v2.engine import WorkflowEngine


app = FastAPI(title="Intelligence OS API", version="3.0.0")
app.include_router(realtime_router)

registry = ToolRegistry()
loader = ToolLoader(registry)
loader.autodiscover(["tools_v2"])
loader.load_external_catalog(limit=900)
executor = ToolExecutor(registry)
pipeline_engine = PipelineEngineV2(executor)
workflow_engine = WorkflowEngine(pipeline_engine)
correlator = CorrelationEngine()
risk_scorer = RiskScorer()
expansion_engine = ExpansionEngine()

module_registry = ModuleRegistry()
ModuleLoader(module_registry).autodiscover(["modules_v2"])


class PipelineRunRequest(BaseModel):
    pipeline: str
    payload: Dict[str, Any]


class WorkflowRunRequest(BaseModel):
    workflow: str
    payload: Dict[str, Any]


class GraphQueryRequest(BaseModel):
    query: str
    params: Dict[str, Any] = Field(default_factory=dict)


class ModuleRunRequest(BaseModel):
    module: str
    payload: Dict[str, Any]


@app.get("/tools")
def list_tools() -> Dict[str, Any]:
    return {"counts": registry.counts(), "categories": registry.list_tools()}


@app.get("/modules")
def list_modules() -> Dict[str, Any]:
    return module_registry.list_modules()


@app.post("/module/run")
def run_module(req: ModuleRunRequest) -> Dict[str, Any]:
    module_cls = module_registry.get_module(req.module)
    if not module_cls:
        return {"status": "error", "message": f"module {req.module} not found"}
    return module_cls().run(req.payload).__dict__


@app.post("/pipeline/run")
def run_pipeline(req: PipelineRunRequest) -> Dict[str, Any]:
    result = pipeline_engine.execute_pipeline(req.pipeline, req.payload)
    entities = result.get("output", {}).get("entities", [])
    state = {
        "entities": entities,
        "pipeline": req.pipeline,
    }
    return {
        "result": result,
        "correlations": correlator.correlate(entities),
        "risk": risk_scorer.score([{"category": e.get("type", "generic"), "confidence": e.get("confidence", 0.5)} for e in entities]),
        "expansion": expansion_engine.next_actions(state),
    }


@app.post("/pipeline/async")
def run_pipeline_async(req: PipelineRunRequest) -> Dict[str, Any]:
    task = run_pipeline_task.delay(req.pipeline, req.payload)
    return {"task_id": task.id, "status": "queued"}


@app.post("/workflow/run")
def run_workflow(req: WorkflowRunRequest) -> Dict[str, Any]:
    return workflow_engine.run(req.workflow, req.payload)


@app.post("/automation/recursive-plan")
def recursive_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    return expansion_engine.recursive_plan(payload)


@app.post("/graph/query")
def query_graph(req: GraphQueryRequest) -> List[Dict[str, Any]]:
    client = GraphClient("bolt://neo4j:7687", "neo4j", "intelligence")
    try:
        return client.query(req.query, req.params)
    finally:
        client.close()


@app.post("/agents/heartbeat")
def agent_heartbeat(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "received", "agent": payload.get("agent_id"), "agent_status": payload.get("status", "unknown")}
