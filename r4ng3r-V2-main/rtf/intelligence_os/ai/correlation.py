from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List

from intelligence_os.models import Entity


class CorrelationEngine:
    def match_entities(self, entities: List[Entity]) -> Dict[str, List[Entity]]:
        buckets = defaultdict(list)
        for entity in entities:
            buckets[(entity.entity_type, entity.value.lower())].append(entity)
        return {f'{k[0]}:{k[1]}': v for k, v in buckets.items()}

    def fuse_identities(self, entities: List[Entity]) -> List[Dict[str, object]]:
        buckets = self.match_entities(entities)
        return [
            {
                'identity_key': key,
                'entity_count': len(items),
                'confidence': round(sum(i.confidence for i in items) / len(items), 2),
            }
            for key, items in buckets.items()
        ]

    def risk_score(self, entities: List[Entity]) -> float:
        risky = sum(1 for e in entities if e.entity_type in {'Credential', 'Breach', 'IP', 'Account'})
        return min(1.0, 0.2 + risky * 0.1)

    def detect_patterns(self, entities: List[Entity]) -> List[str]:
        patterns = []
        if len([e for e in entities if e.entity_type == 'Email']) >= 2:
            patterns.append('multi_email_presence')
        if len([e for e in entities if e.entity_type == 'Domain']) >= 3:
            patterns.append('broad_attack_surface')
        if len([e for e in entities if e.entity_type == 'Account']) >= 3:
            patterns.append('cross_platform_presence')
        return patterns

    def entity_summary(self, entities: List[Entity]) -> Dict[str, int]:
        return dict(Counter(entity.entity_type for entity in entities))
