from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


class CorrelationEngine:
    def correlate(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_value = defaultdict(list)
        for e in entities:
            by_value[e.get("value", "")].append(e)
        correlated = []
        for value, group in by_value.items():
            if len(group) > 1:
                correlated.append(
                    {
                        "value": value,
                        "entities": [g.get("id") for g in group],
                        "confidence": min(0.99, 0.6 + len(group) * 0.05),
                    }
                )
        return {"correlations": correlated, "count": len(correlated)}
