from __future__ import annotations

import inspect
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml

from core_v2.base_tool import BaseTool
from core_v2.tool_loader import ToolLoader
from core_v2.tool_registry import ToolRegistry

STAGE_DEFINITIONS: Dict[str, str] = {
    "A": "Seed Normalization",
    "B": "Username Sweep",
    "C": "Deep Account Scraping",
    "D": "Multi-Engine Web Search",
    "E": "AI Correlation",
    "F": "Relationship Graphing",
    "G": "Automated Pivoting",
    "H": "Threat Assessment",
    "I": "Infrastructure Enrichment",
    "J": "Breach Intelligence",
    "K": "Multi-Format Reporting",
    "L": "Auxiliary/Unmapped",
}

INSTALL_METHODS = ("apt", "pip", "git", "go")

CATEGORY_TO_STAGE = {
    "identity": ["A", "E"],
    "username": ["B", "C"],
    "social media": ["B", "C"],
    "socmint": ["B", "C"],
    "email": ["D", "J"],
    "phone": ["D", "I"],
    "domain": ["D", "I"],
    "metadata": ["C", "I"],
    "code repository": ["B", "G"],
    "breach": ["J"],
    "threat actor": ["H"],
    "threatintel": ["H"],
    "credential": ["J"],
    "geoint": ["G"],
    "infrastructure": ["I"],
    "attack_surface": ["I"],
    "document": ["C"],
    "image": ["C"],
}


@dataclass
class ToolMetadata:
    name: str
    class_name: str
    module: str
    source_file: str
    category: str
    purpose: str
    stages: List[str] = field(default_factory=list)
    stage_names: List[str] = field(default_factory=list)
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    consumes_variables: List[str] = field(default_factory=list)
    produces_variables: List[str] = field(default_factory=list)
    output_mapping: Dict[str, Any] = field(default_factory=dict)
    dataclass_mappings: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    optional_integrations: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    install_method: str = "pip"
    reliability: str = "unknown"
    health_score: float | None = None
    distributed_notes: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    inferred_fields: List[str] = field(default_factory=list)


class RegistryManager:
    def __init__(
        self,
        package_names: Iterable[str] = ("tools_v2",),
        pipelines_path: str = "pipelines_v2",
        store_path: str = "discovery_v2/tool_metadata_store.json",
    ):
        self.package_names = tuple(package_names)
        self.pipelines_path = Path(pipelines_path)
        self.store_path = Path(store_path)

    def load_or_introspect(self) -> tuple[Dict[str, Any], List[str]]:
        warnings: List[str] = []
        try:
            payload = self.introspect_live(previous=self.load_store(silent=True))
            self.persist_store(payload)
            return payload, warnings
        except Exception as exc:
            warnings.append(f"Live registry introspection failed; fallback to persisted store: {exc}")
            payload = self.load_store(silent=False)
            return payload, warnings

    def load_store(self, silent: bool = False) -> Dict[str, Any]:
        if not self.store_path.exists():
            if silent:
                return {"generated_at": None, "tool_count": 0, "tools": []}
            raise FileNotFoundError(f"Metadata store not found: {self.store_path}")
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def persist_store(self, payload: Dict[str, Any]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def introspect_live(self, previous: Dict[str, Any] | None = None) -> Dict[str, Any]:
        previous = previous or {"tools": []}
        tools, failures = self._discover_runtime_tools()
        pipeline_index = self._pipeline_index()

        metadata: List[ToolMetadata] = []
        for tool_cls in tools.values():
            try:
                metadata.append(self._build_metadata(tool_cls, pipeline_index))
            except Exception as exc:
                failures.append(f"{getattr(tool_cls, '__name__', 'unknown')}: {exc}")

        self._infer_links(metadata)
        metadata_dicts = [asdict(item) for item in sorted(metadata, key=lambda m: m.name)]
        diff = self._diff_tools(previous.get("tools", []), metadata_dicts)
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "tool_count": len(metadata_dicts),
            "tools": metadata_dicts,
            "diff": diff,
            "failures": failures,
        }

    def _discover_runtime_tools(self) -> tuple[Dict[str, type[BaseTool]], List[str]]:
        failures: List[str] = []
        registry = ToolRegistry()
        loader = ToolLoader(registry)
        for package in self.package_names:
            try:
                loader.autodiscover((package,))
            except Exception as exc:
                failures.append(f"package {package}: {exc}")
        return registry.all_tools(), failures

    def _pipeline_index(self) -> Dict[str, List[str]]:
        index: Dict[str, List[str]] = {}
        if not self.pipelines_path.exists():
            return index
        for path in self.pipelines_path.glob("*.yaml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for stage in data.get("stages", []):
                stage_name = str(stage.get("name", "unknown"))
                for tool_name in stage.get("tools", []):
                    index.setdefault(tool_name, [])
                    if stage_name not in index[tool_name]:
                        index[tool_name].append(stage_name)
        return index

    def _build_metadata(self, tool_cls: type[BaseTool], pipeline_index: Dict[str, List[str]]) -> ToolMetadata:
        source = inspect.getsource(tool_cls)
        name = str(getattr(tool_cls, "name", tool_cls.__name__.lower()))
        category = str(getattr(tool_cls, "category", "generic"))
        purpose = self._purpose_for(tool_cls)
        input_types = self._as_list(getattr(tool_cls, "input_types", []))
        output_types = self._as_list(getattr(tool_cls, "output_types", []))

        stages = self._as_list(getattr(tool_cls, "pipeline_stages", []))
        inferred_fields: List[str] = []
        if not stages:
            stages = CATEGORY_TO_STAGE.get(category.lower(), ["L"])
            inferred_fields.append("stages")

        consumes_variables = sorted(set(self._extract_payload_vars(source) + self._extract_jinja_vars(source)))
        if not consumes_variables:
            inferred_fields.append("consumes_variables")

        produces_variables = self._as_list(getattr(tool_cls, "produces_variables", []))
        if not produces_variables:
            produces_variables = sorted(set(output_types + [f"{name}_result"]))
            inferred_fields.append("produces_variables")

        dataclass_mappings = self._detect_dataclass_mappings(source)
        install_method = str(getattr(tool_cls, "install_method", "pip")).lower()
        if install_method not in INSTALL_METHODS:
            install_method = "pip"
            inferred_fields.append("install_method")

        stage_names = pipeline_index.get(name, [])
        capabilities = self._extract_capabilities(tool_cls)
        output_mapping = self._extract_output_mapping(tool_cls)
        warnings: List[str] = []
        if not ("ScrapedProfile" in dataclass_mappings or "SearchResult" in dataclass_mappings):
            warnings.append("No explicit ScrapedProfile/SearchResult mapping found in tool source.")

        distributed_notes = {
            "distributed": bool(getattr(tool_cls, "distributed", False)),
            "celery_queue": getattr(tool_cls, "celery_queue", "default"),
            "redis_namespace": getattr(tool_cls, "redis_namespace", f"tool:{name}"),
        }

        return ToolMetadata(
            name=name,
            class_name=tool_cls.__name__,
            module=tool_cls.__module__,
            source_file=inspect.getsourcefile(tool_cls) or "",
            category=category,
            purpose=purpose,
            stages=sorted({s.upper() for s in stages}),
            stage_names=stage_names,
            input_types=input_types,
            output_types=output_types,
            capabilities=capabilities,
            consumes_variables=consumes_variables,
            produces_variables=produces_variables,
            output_mapping=output_mapping,
            dataclass_mappings=dataclass_mappings,
            optional_integrations=self._as_list(getattr(tool_cls, "optional_integrations", [])),
            install_method=install_method,
            reliability=str(getattr(tool_cls, "reliability", "unknown")),
            health_score=self._to_float(getattr(tool_cls, "health_score", None)),
            distributed_notes=distributed_notes,
            warnings=warnings,
            inferred_fields=inferred_fields,
        )

    def _infer_links(self, metadata: Sequence[ToolMetadata]) -> None:
        for tool in metadata:
            deps: set[str] = set(self._as_list(getattr(tool, "dependencies", [])))
            conflicts: set[str] = set(self._as_list(getattr(tool, "conflicts", [])))
            for other in metadata:
                if tool.name == other.name:
                    continue
                if set(tool.input_types) & set(other.output_types):
                    deps.add(other.name)
                if set(tool.stages) & set(other.stages) and set(tool.output_types) == set(other.output_types) and tool.output_types:
                    conflicts.add(other.name)
            tool.dependencies = sorted(deps)
            tool.conflicts = sorted(conflicts)

    def _diff_tools(self, previous_tools: Sequence[Dict[str, Any]], current_tools: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        prev_map = {item["name"]: item for item in previous_tools}
        curr_map = {item["name"]: item for item in current_tools}
        added = sorted(set(curr_map) - set(prev_map))
        removed = sorted(set(prev_map) - set(curr_map))
        changed: List[str] = []
        for name in sorted(set(prev_map) & set(curr_map)):
            a = prev_map[name]
            b = curr_map[name]
            if any(a.get(key) != b.get(key) for key in ("purpose", "stages", "category", "input_types", "output_types", "dependencies")):
                changed.append(name)
        return {"added": added, "removed": removed, "changed": changed}

    @staticmethod
    def _as_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value if item is not None]
        return [str(value)]

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_payload_vars(source: str) -> List[str]:
        return re.findall(r"payload\.get\([\"']([a-zA-Z0-9_]+)[\"']", source)

    @staticmethod
    def _extract_jinja_vars(source: str) -> List[str]:
        return re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", source)

    @staticmethod
    def _detect_dataclass_mappings(source: str) -> List[str]:
        mappings = []
        for token in ("ScrapedProfile", "SearchResult"):
            if token in source:
                mappings.append(token)
        return mappings

    @staticmethod
    def _extract_capabilities(tool_cls: type[BaseTool]) -> List[str]:
        explicit = getattr(tool_cls, "capabilities", None)
        if explicit:
            if isinstance(explicit, str):
                return [explicit]
            return [str(item) for item in explicit]
        doc = (tool_cls.__doc__ or "").strip().lower()
        words = [w for w in re.split(r"[^a-z0-9_]+", doc) if len(w) > 4]
        return sorted(set(words[:10]))

    @staticmethod
    def _extract_output_mapping(tool_cls: type[BaseTool]) -> Dict[str, str]:
        try:
            source = inspect.getsource(tool_cls.normalize)
        except Exception:
            return {}
        keys = re.findall(r"[\"']([a-zA-Z0-9_]+)[\"']\s*:", source)
        return {key: "normalized_field" for key in sorted(set(keys))}

    @staticmethod
    def _purpose_for(tool_cls: type[BaseTool]) -> str:
        doc = (tool_cls.__doc__ or "").strip()
        if doc:
            return doc.splitlines()[0].strip()
        spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", tool_cls.__name__).replace("Tool", "").strip()
        return f"{spaced} capability"
