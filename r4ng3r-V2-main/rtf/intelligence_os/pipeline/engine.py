from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import yaml

from intelligence_os.ai.correlation import CorrelationEngine
from intelligence_os.graph.store import InMemoryGraphStore
from intelligence_os.models import PipelineExecutionResult
from intelligence_os.tooling.base import ModuleContext
from intelligence_os.tooling.registry import registry


class PipelineEngine:
    def __init__(self, graph_store: InMemoryGraphStore | None = None) -> None:
        self.graph_store = graph_store or InMemoryGraphStore()
        self.correlation = CorrelationEngine()

    def load_pipeline(self, path: str | Path) -> Dict[str, Any]:
        return yaml.safe_load(Path(path).read_text())

    def _seed_value_for(self, field_name: str, seed: Dict[str, Any], context: Dict[str, Any]) -> Any:
        return context.get(field_name, seed.get(field_name, next(iter(seed.values()), field_name)))

    def _build_stage_input(self, stage: Dict[str, Any], seed: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        mapping = stage.get('input', {})
        if not mapping:
            return seed.copy()
        resolved: Dict[str, Any] = {}
        for target_key, source_key in mapping.items():
            if isinstance(source_key, str):
                resolved[target_key] = self._seed_value_for(source_key, seed, context)
            else:
                resolved[target_key] = source_key
        return resolved

    def execute_pipeline(self, definition: Dict[str, Any], seed: Dict[str, Any], workspace: str = 'default') -> PipelineExecutionResult:
        context: Dict[str, Any] = {
            'seed': deepcopy(seed),
            'transformations': [],
            'stage_results': [],
            'executed_tools': [],
            'pipeline_purpose': definition.get('purpose'),
            'recursive_pivoting': definition.get('recursive_pivoting', False),
            'ai_assisted': definition.get('ai_assisted', False),
        }
        result = PipelineExecutionResult(pipeline=definition['name'], success=True, context=context)
        entities = []
        relationships = []

        for order, stage in enumerate(definition.get('stages', []), start=1):
            module_name = stage['module']
            module_cls = registry.resolve_module(module_name)
            module = module_cls()
            module_input = self._build_stage_input(stage, seed, context)
            stage_meta = {
                'order': order,
                'name': stage.get('name', module_name),
                'module': module_name,
                'tool': stage.get('tool', module_name),
                'input': deepcopy(module_input),
                'required': stage.get('required', True),
            }
            try:
                execution = module.execute(module_input, ModuleContext(seed=seed, workspace=workspace, telemetry=context))
            except Exception as exc:  # pragma: no cover - defensive fallback for generated wrappers
                execution = type('ExecutionFailure', (), {'success': False, 'error': str(exc), 'entities': [], 'relationships': [], 'telemetry': {}})()
            result.executed_modules.append(module_name)
            context['executed_tools'].append(stage_meta['tool'])
            stage_meta['success'] = execution.success
            stage_meta['entity_count'] = len(execution.entities)
            stage_meta['relationship_count'] = len(execution.relationships)
            stage_meta['error'] = execution.error
            context['stage_results'].append(stage_meta)
            if not execution.success:
                result.success = False
                result.errors.append(execution.error or f'{module_name} failed')
                if stage.get('required', True):
                    break
                continue
            entities.extend(execution.entities)
            relationships.extend(execution.relationships)
            if execution.entities:
                context.setdefault('latest_entities', {})[module_name] = [entity.value for entity in execution.entities]
            for transform in stage.get('transformations', []):
                context['transformations'].append({'module': module_name, 'transform': transform})
                if transform == 'extract_domains':
                    context['domains'] = [e.value for e in execution.entities if e.entity_type == 'Domain']
                elif transform == 'extract_accounts':
                    context['accounts'] = [e.value for e in execution.entities if e.entity_type == 'Account']
                elif transform == 'extract_emails':
                    context['emails'] = [e.value for e in execution.entities if e.entity_type == 'Email']

        result.entities = entities
        result.relationships = relationships
        result.graph_writes = self.graph_store.ingest(entities, relationships)
        context['identity_fusions'] = self.correlation.fuse_identities(entities)
        context['risk_score'] = self.correlation.risk_score(entities)
        context['patterns'] = self.correlation.detect_patterns(entities)
        context['entity_summary'] = self.correlation.entity_summary(entities)
        context['recommended_next_steps'] = definition.get('output', {}).get('next_steps', [])
        return result
