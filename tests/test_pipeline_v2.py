from core_v2.pipeline_engine_v2 import PipelineEngineV2
from core_v2.tool_executor import ToolExecutor
from core_v2.tool_loader import ToolLoader
from core_v2.tool_registry import ToolRegistry


def test_identity_pipeline_executes():
    registry = ToolRegistry()
    ToolLoader(registry).autodiscover(["tools_v2"])
    executor = ToolExecutor(registry)
    engine = PipelineEngineV2(executor)
    result = engine.execute_pipeline("identity_pipeline", {"input_type": "identity", "value": "alice"})
    assert result["status"] == "completed"
    assert result["output"]["entities"]
