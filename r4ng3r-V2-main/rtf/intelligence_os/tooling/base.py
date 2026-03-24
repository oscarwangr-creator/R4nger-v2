from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List

from intelligence_os.models import Entity, ModuleExecutionResult, Relationship

@dataclass
class RateLimitPolicy:
    requests_per_minute: int = 30
    burst: int = 5

@dataclass
class ModuleContext:
    seed: Dict[str, Any]
    workspace: str = 'default'
    telemetry: Dict[str, Any] = field(default_factory=dict)

class BaseModule:
    name = ''
    category = ''
    input_types: List[str] = []
    output_types: List[str] = []
    command_template = ''
    rate_limit = RateLimitPolicy()
    pipeline_compatible = True

    def __init__(self) -> None:
        self._window_started = datetime.utcnow()
        self._request_count = 0

    def check_rate_limit(self) -> None:
        now = datetime.utcnow()
        if now - self._window_started > timedelta(minutes=1):
            self._window_started = now
            self._request_count = 0
        self._request_count += 1
        if self._request_count > self.rate_limit.requests_per_minute + self.rate_limit.burst:
            raise RuntimeError(f'rate limit exceeded for {self.name}')

    def build_command(self, input_data: Dict[str, Any]) -> str:
        class SafeDict(dict):
            def __missing__(self, key: str) -> str:
                if self:
                    return str(next(iter(self.values())))
                return f'{{{key}}}'

        return self.command_template.format_map(SafeDict({k: v for k, v in input_data.items()}))

    def run(self, input_data: Dict[str, Any], context: ModuleContext | None = None) -> Dict[str, Any]:
        self.check_rate_limit()
        return {'command': self.build_command(input_data), 'artifacts': [], 'input': input_data}

    def parse_output(self, raw_data: Dict[str, Any]) -> ModuleExecutionResult:
        entities = [Entity(entity_type=o, value=f'{self.name}:{o}:{idx}', confidence=0.5, properties={'raw': raw_data}) for idx, o in enumerate(self.output_types or ['artifact'], start=1)]
        return ModuleExecutionResult(module=self.name, success=True, entities=entities, raw=raw_data)

    def execute(self, input_data: Dict[str, Any], context: ModuleContext | None = None) -> ModuleExecutionResult:
        raw = self.run(input_data, context)
        return self.parse_output(raw)

class JsonEntityModule(BaseModule):
    entity_map: Dict[str, str] = {}
    relationship_type = 'connected_to'

    def parse_output(self, raw_data: Dict[str, Any]) -> ModuleExecutionResult:
        artifacts = raw_data.get('artifacts', [])
        entities: List[Entity] = []
        relationships: List[Relationship] = []
        seed_value = next(iter(raw_data.get('input', {}).values()), 'seed')
        for artifact in artifacts:
            for key, entity_type in self.entity_map.items():
                value = artifact.get(key)
                if not value:
                    continue
                entity_id = f'{entity_type}:{value}'
                entities.append(Entity(entity_type=entity_type, value=value, confidence=artifact.get('confidence', 0.7), properties=artifact))
                relationships.append(Relationship(source=str(seed_value), relationship=self.relationship_type, target=entity_id, confidence=artifact.get('confidence', 0.7)))
        return ModuleExecutionResult(module=self.name, success=True, entities=entities, relationships=relationships, raw=raw_data)
