from __future__ import annotations

from hashlib import md5
from typing import Any, Dict

from core_v2.base_tool import BaseTool


class TwitterMentionsTool(BaseTool):
    name = "twitter_mentions"
    category = "socmint"
    input_types = ['username']
    output_types = ['mention']

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        value = payload.get("value", "")
        fingerprint = md5(f"twitter_mentions:{value}".encode()).hexdigest()[:12]
        return {
            "query": value,
            "fingerprint": fingerprint,
            "source": "twitter_mentions",
            "confidence": 0.74,
            "attributes": {
                "category": "socmint",
                "observed": True,
                "details": f"twitter_mentions generated intelligence for {value}"
            }
        }

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = f"socmint:{raw['fingerprint']}"
        return {
            "entities": [{
                "id": entity_id,
                "type": self.category,
                "value": raw.get("query", ""),
                "confidence": raw.get("confidence", 0.5),
                "attributes": raw.get("attributes", {})
            }],
            "relationships": []
        }
