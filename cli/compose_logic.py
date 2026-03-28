from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

STAGE_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

USE_CASE_HINTS = {
    "username-to-breach": ["B", "C", "D", "J"],
    "domain-infrastructure-mapping": ["D", "I", "G"],
    "identity-correlation": ["A", "E", "F", "H"],
    "email-risk-triage": ["D", "J", "H"],
}


@dataclass
class CompositionArtifact:
    use_case: str
    stages: List[str]
    tools: List[Dict[str, Any]]
    ordering_warnings: List[str]
    contention_warnings: List[str]
    variable_flow: List[Dict[str, str]]
    yaml_file: str
    python_stub_file: str


class ComposeEngine:
    def compose(self, use_case: str, tools: List[Dict[str, Any]], output_dir: str = "generated") -> CompositionArtifact:
        wanted_stages = self._stages_for_use_case(use_case)
        selected = [t for t in tools if set(t.get("stages", [])) & set(wanted_stages)]
        selected.sort(key=lambda t: min([STAGE_ORDER.index(s) for s in t.get("stages", ["L"]) if s in STAGE_ORDER] or [99]))

        ordering_warnings = self._ordering_warnings(selected)
        contention_warnings = self._contention_warnings(selected)
        variable_flow = self._variable_flow(selected)

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_name = use_case.replace(" ", "-").lower()
        yaml_file = out_dir / f"{safe_name}_pipeline.yaml"
        py_file = out_dir / f"{safe_name}_pipeline.py"
        yaml_file.write_text(self._yaml_for(use_case, selected), encoding="utf-8")
        py_file.write_text(self._python_stub_for(use_case, selected), encoding="utf-8")

        return CompositionArtifact(
            use_case=use_case,
            stages=wanted_stages,
            tools=selected,
            ordering_warnings=ordering_warnings,
            contention_warnings=contention_warnings,
            variable_flow=variable_flow,
            yaml_file=str(yaml_file),
            python_stub_file=str(py_file),
        )

    def suggest_use_cases(self, tools: List[Dict[str, Any]]) -> List[str]:
        suggestions = set(USE_CASE_HINTS)
        stages_present = {stage for tool in tools for stage in tool.get("stages", [])}
        if {"B", "J"}.issubset(stages_present):
            suggestions.add("username-to-breach")
        if {"D", "I"}.issubset(stages_present):
            suggestions.add("domain-infrastructure-mapping")
        if {"A", "E", "F"}.issubset(stages_present):
            suggestions.add("identity-correlation")
        return sorted(suggestions)

    def _stages_for_use_case(self, use_case: str) -> List[str]:
        case = use_case.lower()
        if case in USE_CASE_HINTS:
            return USE_CASE_HINTS[case]
        if "username" in case and "breach" in case:
            return ["B", "C", "D", "J"]
        if "domain" in case and ("infra" in case or "mapping" in case):
            return ["D", "I", "G"]
        return ["A", "L"]

    def _ordering_warnings(self, tools: List[Dict[str, Any]]) -> List[str]:
        warnings: List[str] = []
        last_index = -1
        for tool in tools:
            idx = min([STAGE_ORDER.index(s) for s in tool.get("stages", ["L"]) if s in STAGE_ORDER] or [99])
            if idx < last_index:
                warnings.append(f"{tool['name']} violates A→K+L ordering")
            last_index = idx
        return warnings

    def _contention_warnings(self, tools: List[Dict[str, Any]]) -> List[str]:
        warnings: List[str] = []
        namespaces: Dict[str, str] = {}
        for tool in tools:
            redis_ns = tool.get("distributed_notes", {}).get("redis_namespace")
            if redis_ns:
                if redis_ns in namespaces:
                    warnings.append(f"Redis namespace collision: {namespaces[redis_ns]} and {tool['name']} share {redis_ns}")
                namespaces[redis_ns] = tool["name"]
            if "neo4j" in " ".join(tool.get("capabilities", [])).lower():
                warnings.append(f"Potential Neo4j write contention for {tool['name']}")
        return sorted(set(warnings))

    def _variable_flow(self, tools: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        flow: List[Dict[str, str]] = []
        for producer in tools:
            for output in producer.get("produces_variables", []):
                for consumer in tools:
                    if producer["name"] == consumer["name"]:
                        continue
                    if output in consumer.get("consumes_variables", []) or output in consumer.get("input_types", []):
                        flow.append({"from": producer["name"], "to": consumer["name"], "variable": f"{{{{{output}}}}}"})
        return flow

    def _yaml_for(self, use_case: str, tools: List[Dict[str, Any]]) -> str:
        lines = [
            f"name: {use_case.replace(' ', '_')}_pipeline",
            f"description: Auto-generated composition for {use_case}",
            "entrypoint: value",
            "stages:",
        ]
        for tool in tools:
            stage = sorted(tool.get("stages", ["L"]))[0]
            lines.extend([
                f"  - name: stage_{stage.lower()}",
                "    tools:",
                f"      - {tool['name']}",
                "    input:",
            ])
            vars_list = tool.get("consumes_variables", []) or ["value"]
            for var in vars_list:
                lines.append(f"      {var}: {{{{{var}}}}}")
        lines.extend(["outputs:", "  - entities", "  - relationships", "  - evidence"])
        return "\n".join(lines) + "\n"

    def _python_stub_for(self, use_case: str, tools: List[Dict[str, Any]]) -> str:
        selected = [t["name"] for t in tools]
        return (
            "from core_v2.tool_registry import ToolRegistry\n"
            "from core_v2.tool_loader import ToolLoader\n"
            "from core_v2.tool_executor import ToolExecutor\n"
            "from core_v2.pipeline_engine_v2 import PipelineEngineV2\n\n"
            f"USE_CASE = {use_case!r}\n"
            f"SELECTED_TOOLS = {selected!r}\n\n"
            "def run(payload: dict) -> dict:\n"
            "    registry = ToolRegistry()\n"
            "    ToolLoader(registry).autodiscover(['tools_v2'])\n"
            "    executor = ToolExecutor(registry)\n"
            "    engine = PipelineEngineV2(executor)\n"
            "    return engine.execute_pipeline('identity_pipeline', payload)\n\n"
            "if __name__ == '__main__':\n"
            "    print(run({'input_type': 'identity', 'value': 'example'}))\n"
        )
