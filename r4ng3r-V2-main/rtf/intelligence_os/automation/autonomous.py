from __future__ import annotations
from collections import deque
from pathlib import Path
from typing import Dict, List, Set, Tuple

from intelligence_os.pipeline.engine import PipelineEngine

ENTITY_PIPELINE_MAP = {
    'Username': 'username_intelligence_pipeline.yaml',
    'Email': 'email_intelligence_pipeline.yaml',
    'Domain': 'domain_intelligence_pipeline.yaml',
    'Phone': 'phone_intelligence_pipeline.yaml',
}

class AutonomousInvestigationEngine:
    def __init__(self, pipeline_engine: PipelineEngine | None = None, pipeline_dir: str | Path | None = None) -> None:
        self.pipeline_engine = pipeline_engine or PipelineEngine()
        self.pipeline_dir = Path(pipeline_dir or Path(__file__).resolve().parents[1] / 'pipelines')

    def investigate(self, seed: Dict[str, str], max_depth: int = 2) -> Dict[str, object]:
        queue = deque([(seed, 0)])
        visited: Set[Tuple[str, str]] = set()
        runs: List[Dict[str, object]] = []
        while queue:
            current_seed, depth = queue.popleft()
            if depth > max_depth:
                continue
            for key, value in current_seed.items():
                entity_type = key.capitalize() if key != 'domain' else 'Domain'
                marker = (entity_type, value)
                if marker in visited or entity_type not in ENTITY_PIPELINE_MAP:
                    continue
                visited.add(marker)
                definition = self.pipeline_engine.load_pipeline(self.pipeline_dir / ENTITY_PIPELINE_MAP[entity_type])
                result = self.pipeline_engine.execute_pipeline(definition, {key: value})
                runs.append({'entity': marker, 'pipeline': definition['name'], 'result': result})
                for entity in result.entities:
                    if entity.entity_type in ENTITY_PIPELINE_MAP and (entity.entity_type, entity.value) not in visited:
                        queue.append(({entity.entity_type.lower(): entity.value}, depth + 1))
        return {'visited': sorted(visited), 'runs': runs}
