from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Type

from intelligence_os.tooling.base import BaseModule
from intelligence_os.tooling.catalog import (
    load_framework_analysis,
    load_module_mappings,
    load_pipeline_mappings,
    load_tool_catalog,
)
from intelligence_os.tooling.wrappers import MODULE_CLASSES


@dataclass
class ToolDefinition:
    name: str
    category: str
    input_types: List[str]
    output_types: List[str]
    mode: str
    command_template: str
    pipeline_compatible: bool
    rate_limit_per_minute: int
    parser: str
    api_required: bool = False
    display_name: str | None = None
    validation: str | None = None
    install_method: str | None = None
    module: str | None = None
    dependencies: List[str] = field(default_factory=list)
    pipelines: List[str] = field(default_factory=list)


class ToolRegistry:
    def __init__(self) -> None:
        raw_catalog = [ToolDefinition(**entry) for entry in load_tool_catalog()]
        self._manifest_modules = {entry['name']: entry for entry in load_module_mappings()}
        self._manifest_pipelines = {entry['name']: entry for entry in load_pipeline_mappings()}
        self._catalog = [self._enrich(entry) for entry in raw_catalog]
        self._modules: Dict[str, Type[BaseModule]] = MODULE_CLASSES.copy()
        self._analysis = load_framework_analysis()

    def _enrich(self, entry: ToolDefinition) -> ToolDefinition:
        generated_module = f"{entry.name.replace('-', '_')}_module"
        if generated_module in self._manifest_modules:
            manifest_module = self._manifest_modules[generated_module]
            entry.module = generated_module
            entry.install_method = entry.install_method or 'apt'
            entry.dependencies = manifest_module.get('tools', [])[1:3]
            entry.pipelines = manifest_module.get('pipelines', [])[:12]
        return entry

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._catalog)

    def list_module_mappings(self) -> List[Dict[str, Any]]:
        return list(self._manifest_modules.values())

    def list_pipeline_mappings(self) -> List[Dict[str, Any]]:
        return list(self._manifest_pipelines.values())

    def framework_analysis(self) -> Dict[str, Any]:
        return self._analysis

    def summary(self) -> Dict[str, Any]:
        categories: Dict[str, int] = {}
        install_methods: Dict[str, int] = {}
        for entry in self._catalog:
            categories[entry.category] = categories.get(entry.category, 0) + 1
            install_key = entry.install_method or 'unspecified'
            install_methods[install_key] = install_methods.get(install_key, 0) + 1
        return {
            'total_tools': len(self._catalog),
            'categories': categories,
            'install_methods': install_methods,
            'wrapped_modules': sorted(self._modules),
            'mapped_modules': len(self._manifest_modules),
            'mapped_pipelines': len(self._manifest_pipelines),
        }

    def get(self, name: str) -> ToolDefinition | None:
        return next((entry for entry in self._catalog if entry.name == name), None)

    def resolve_module(self, name: str) -> Type[BaseModule]:
        if name in self._modules:
            return self._modules[name]
        definition = self.get(name)
        if not definition:
            return type(
                f"{name.title().replace('-', '').replace('_', '')}Module",
                (BaseModule,),
                {
                    'name': name,
                    'category': 'Generated Intelligence Module',
                    'input_types': ['seed'],
                    'output_types': ['artifact'],
                    'command_template': f'{name} {{seed}}',
                },
            )
        return type(
            f"{name.title().replace('-', '').replace('_', '')}Module",
            (BaseModule,),
            {
                'name': definition.name,
                'category': definition.category,
                'input_types': definition.input_types,
                'output_types': definition.output_types,
                'command_template': definition.command_template,
            },
        )


registry = ToolRegistry()
