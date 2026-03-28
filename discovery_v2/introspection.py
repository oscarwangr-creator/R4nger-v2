from __future__ import annotations

import ast
import inspect
import json
import logging
import re
import textwrap
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from core_v2.base_tool import BaseTool
from core_v2.tool_loader import ToolLoader
from core_v2.tool_registry import ToolRegistry

LOGGER = logging.getLogger("discovery_v2")

STAGE_BY_CATEGORY = {
    "identity": ["A", "K"],
    "username": ["B"],
    "socmint": ["C"],
    "document": ["C"],
    "metadata": ["C"],
    "image": ["C"],
    "threatintel": ["D"],
    "darkweb": ["D"],
    "email": ["E"],
    "domain": ["F"],
    "infrastructure": ["G"],
    "attack_surface": ["G"],
    "credential": ["H"],
    "breach": ["I"],
    "geoint": ["J"],
}


@dataclass
class ToolMetadata:
    name: str
    class_name: str
    module: str
    category: str
    purpose: str
    pipeline_stage_labels: List[str] = field(default_factory=list)
    pipeline_stage_names: List[str] = field(default_factory=list)
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    consumes_variables: List[str] = field(default_factory=list)
    produces_variables: List[str] = field(default_factory=list)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    references_dataclasses: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    source_file: str = ""
    warnings: List[str] = field(default_factory=list)


class DiscoveryService:
    """Runtime tool registry introspection and metadata generation service."""

    def __init__(
        self,
        package_names: Iterable[str] = ("tools_v2",),
        pipelines_path: str = "pipelines_v2",
        store_path: str = "discovery_v2/tool_metadata_store.json",
        graph_path: str = "discovery_v2/dependency_graph.json",
        docs_path: str = "docs_v2/tools",
        audit_log_path: str = "logs/audit.log",
    ):
        self.package_names = tuple(package_names)
        self.pipelines_path = Path(pipelines_path)
        self.store_path = Path(store_path)
        self.graph_path = Path(graph_path)
        self.docs_path = Path(docs_path)
        self.audit_log_path = Path(audit_log_path)

    def regenerate(self) -> Dict[str, Any]:
        self._audit("regen_started", {"packages": list(self.package_names)})
        tool_map = self._discover_runtime_tools()
        pipeline_index = self._pipeline_index()
        metadata = [self._build_metadata(t, pipeline_index) for t in tool_map.values()]
        self._attach_dependencies_and_conflicts(metadata)

        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "tool_count": len(metadata),
            "tools": [asdict(item) for item in metadata],
        }
        self.store_path.write_text(json.dumps(metadata_payload, indent=2), encoding="utf-8")

        graph_payload = self._build_graph(metadata)
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        self.graph_path.write_text(json.dumps(graph_payload, indent=2), encoding="utf-8")

        self._generate_docs(metadata)
        self._audit("regen_completed", {"tool_count": len(metadata)})
        return metadata_payload

    def load_store(self) -> Dict[str, Any]:
        if not self.store_path.exists():
            return self.regenerate()
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def recommend(self, use_case: str) -> Dict[str, Any]:
        payload = self.load_store()
        tools = payload.get("tools", [])
        case = use_case.lower()

        if "username" in case and "breach" in case:
            stages = ["B", "E", "I"]
        elif "domain" in case and "infra" in case:
            stages = ["F", "G", "J"]
        else:
            stages = ["A", "L"]

        selected = [tool for tool in tools if set(tool.get("pipeline_stage_labels", [])) & set(stages)]
        handoffs = []
        for tool in selected:
            for output_type in tool.get("output_types", []):
                consumers = [
                    candidate["name"]
                    for candidate in selected
                    if output_type in candidate.get("input_types", []) and candidate["name"] != tool["name"]
                ]
                for consumer in consumers:
                    handoffs.append({
                        "from": tool["name"],
                        "to": consumer,
                        "variable": f"{{{{{output_type}}}}}",
                    })

        return {
            "use_case": use_case,
            "stages": stages,
            "tools": selected,
            "handoffs": handoffs,
        }

    def _discover_runtime_tools(self) -> Dict[str, type[BaseTool]]:
        registry = ToolRegistry()
        ToolLoader(registry).autodiscover(self.package_names)
        return registry.all_tools()

    def _pipeline_index(self) -> Dict[str, List[str]]:
        index: Dict[str, List[str]] = {}
        for path in self.pipelines_path.glob("*.yaml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for stage in data.get("stages", []):
                stage_name = stage.get("name", "unknown")
                for tool_name in stage.get("tools", []):
                    index.setdefault(tool_name, [])
                    if stage_name not in index[tool_name]:
                        index[tool_name].append(stage_name)
        return index

    def _build_metadata(self, tool_cls: type[BaseTool], pipeline_index: Dict[str, List[str]]) -> ToolMetadata:
        warnings: List[str] = []
        name = getattr(tool_cls, "name", tool_cls.__name__.lower())
        category = getattr(tool_cls, "category", "generic")
        input_types = list(getattr(tool_cls, "input_types", []))
        output_types = list(getattr(tool_cls, "output_types", []))

        doc = (tool_cls.__doc__ or "").strip()
        purpose = doc.splitlines()[0].strip() if doc else self._infer_purpose(tool_cls.__name__, category)
        if not doc:
            warnings.append("Missing class docstring; purpose inferred from class name/category.")

        source = inspect.getsource(tool_cls)
        consumes = sorted(set(re.findall(r"payload\.get\([\"']([a-zA-Z0-9_]+)[\"']", source)))
        consumes = [item for item in consumes if item not in {"input_type", "value", "timestamp"}]

        yaml_vars = self._extract_jinja_variables(source)
        for var in yaml_vars:
            if var not in consumes:
                consumes.append(var)

        if not input_types:
            warnings.append("No input_types declared.")
        if not output_types:
            warnings.append("No output_types declared.")

        output_schema = self._extract_normalize_schema(tool_cls)
        references_dataclasses = self._find_dataclass_references(source)
        if "ScrapedProfile" not in references_dataclasses:
            warnings.append("ScrapedProfile dataclass reference not found for this tool.")
        if "SearchResult" not in references_dataclasses:
            warnings.append("SearchResult dataclass reference not found for this tool.")

        stages = sorted(set(STAGE_BY_CATEGORY.get(category, ["L"])))
        pipeline_stages = pipeline_index.get(name, [])
        if not pipeline_stages:
            warnings.append("Tool is not present in any YAML pipeline definition.")

        produces = sorted(set(output_types + [f"{name}_result", "entities", "relationships"]))

        return ToolMetadata(
            name=name,
            class_name=tool_cls.__name__,
            module=tool_cls.__module__,
            category=category,
            purpose=purpose,
            pipeline_stage_labels=stages,
            pipeline_stage_names=pipeline_stages,
            input_types=input_types,
            output_types=output_types,
            consumes_variables=sorted(consumes),
            produces_variables=produces,
            output_schema=output_schema,
            references_dataclasses=references_dataclasses,
            source_file=inspect.getsourcefile(tool_cls) or "",
            warnings=warnings,
        )

    def _extract_normalize_schema(self, tool_cls: type[BaseTool]) -> Dict[str, Any]:
        try:
            method_src = textwrap.dedent(inspect.getsource(tool_cls.normalize))
            tree = ast.parse(method_src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                    schema: Dict[str, Any] = {}
                    for key_node, value_node in zip(node.value.keys, node.value.values):
                        if isinstance(key_node, ast.Constant):
                            if isinstance(value_node, ast.List):
                                schema[str(key_node.value)] = "list"
                            elif isinstance(value_node, ast.Dict):
                                schema[str(key_node.value)] = "object"
                            else:
                                schema[str(key_node.value)] = type(value_node).__name__
                    return schema
        except Exception as exc:
            LOGGER.warning("Failed to parse normalize schema for %s: %s", tool_cls.__name__, exc)
        return {}

    def _find_dataclass_references(self, source: str) -> List[str]:
        refs: List[str] = []
        for name in ("ScrapedProfile", "SearchResult", "ScrapedToolProfile"):
            if name in source:
                refs.append(name)
        return refs

    def _extract_jinja_variables(self, text: str) -> List[str]:
        return re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", text)

    def _infer_purpose(self, class_name: str, category: str) -> str:
        words = re.sub(r"([a-z])([A-Z])", r"\1 \2", class_name).replace("Tool", "").strip()
        return f"{words} capability for {category} intelligence workflows."

    def _attach_dependencies_and_conflicts(self, metadata: List[ToolMetadata]) -> None:
        for tool in metadata:
            deps: List[str] = []
            conflicts: List[str] = []
            for candidate in metadata:
                if tool.name == candidate.name:
                    continue
                if set(tool.output_types) & set(candidate.input_types):
                    deps.append(candidate.name)
                same_stage = bool(set(tool.pipeline_stage_labels) & set(candidate.pipeline_stage_labels))
                if same_stage and set(tool.output_types) == set(candidate.output_types) and tool.output_types:
                    conflicts.append(f"Overlap with {candidate.name}: identical output types in shared stage")
            tool.dependencies = sorted(set(deps))
            tool.conflicts = sorted(set(conflicts))

    def _build_graph(self, metadata: List[ToolMetadata]) -> Dict[str, Any]:
        nodes = [{"id": tool.name, "stage_labels": tool.pipeline_stage_labels} for tool in metadata]
        edges = []
        for tool in metadata:
            for dep in tool.dependencies:
                edges.append({"from": tool.name, "to": dep, "type": "data_handoff"})
            for conflict in tool.conflicts:
                target = conflict.split(" ")[2].rstrip(":") if " with " in conflict else "unknown"
                edges.append({"from": tool.name, "to": target, "type": "conflict"})
        return {"generated_at": datetime.utcnow().isoformat(), "nodes": nodes, "edges": edges}

    def _generate_docs(self, metadata: List[ToolMetadata]) -> None:
        self.docs_path.mkdir(parents=True, exist_ok=True)
        for tool in metadata:
            doc_path = self.docs_path / f"{tool.name}.md"
            yaml_inputs = "\n".join([f"      {item}: {{{{{item}}}}}" for item in (tool.consumes_variables or ["value"])])
            markdown = (
                f"# {tool.name}\n\n"
                f"## Purpose\n{tool.purpose}\n\n"
                f"## Pipeline Coverage\n"
                f"- Stage labels: {', '.join(tool.pipeline_stage_labels) or 'L'}\n"
                f"- YAML stage names: {', '.join(tool.pipeline_stage_names) or 'Not mapped'}\n\n"
                f"## Input Schema\n"
                f"- input_types: {tool.input_types}\n"
                f"- consumes variables: {tool.consumes_variables}\n\n"
                f"## Output Schema\n"
                f"- output_types: {tool.output_types}\n"
                f"- normalized keys: {tool.output_schema}\n"
                f"- formats: JSON\n\n"
                f"## YAML Usage\n"
                f"```yaml\n"
                f"stages:\n"
                f"  - name: discovery\n"
                f"    tools:\n"
                f"      - {tool.name}\n"
                f"    input:\n{yaml_inputs}\n"
                f"```\n\n"
                f"## Dependencies\n{tool.dependencies}\n\n"
                f"## Conflicts\n{tool.conflicts}\n\n"
                f"## Metadata Warnings\n{tool.warnings}\n"
            )
            doc_path.write_text(markdown, encoding="utf-8")

    def _audit(self, event: str, details: Dict[str, Any]) -> None:
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": datetime.utcnow().isoformat(),
            "event": event,
            "details": details,
        }
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
