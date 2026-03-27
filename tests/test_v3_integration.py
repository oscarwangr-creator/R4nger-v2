from core_v2.tool_loader import ToolLoader
from core_v2.tool_registry import ToolRegistry
from modules_v2.module_loader import ModuleLoader
from modules_v2.module_registry import ModuleRegistry
from workflows_v2.engine import SafeConditionEvaluator


def test_external_catalog_loads_large_set():
    registry = ToolRegistry()
    loader = ToolLoader(registry)
    loaded = loader.load_external_catalog(limit=600)
    assert loaded >= 500
    assert registry.counts()["external"] >= 500


def test_module_loader_discovers_base_modules():
    module_registry = ModuleRegistry()
    loaded = ModuleLoader(module_registry).autodiscover(["modules_v2"])
    assert loaded >= 1
    assert "identity" in module_registry.list_modules()


def test_safe_condition_evaluator_blocks_calls():
    evaluator = SafeConditionEvaluator()
    assert evaluator.evaluate("payload['run'] == True", {"payload": {"run": True}, "outcomes": {}}) is True
    try:
        evaluator.evaluate("__import__('os').system('id')", {"payload": {}, "outcomes": {}})
    except ValueError:
        assert True
    else:
        assert False
