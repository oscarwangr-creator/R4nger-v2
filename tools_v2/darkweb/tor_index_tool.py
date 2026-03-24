from __future__ import annotations

from hashlib import md5
from typing import Any, Dict

from core_v2.base_tool import BaseTool


class TorIndexLookupTool(BaseTool):
    name = "tor_index_lookup"
    category = "darkweb"
    input_types = ['email', 'domain']
    output_types = ['darkweb_hit']

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        value = payload.get("value", "")
        fingerprint = md5(f"tor_index_lookup:{value}".encode()).hexdigest()[:12]
        return {
            "query": value,
            "fingerprint": fingerprint,
            "source": "tor_index_lookup",
            "confidence": 0.74,
            "attributes": {
                "category": "darkweb",
                "observed": True,
                "details": f"tor_index_lookup generated intelligence for {value}"
            }
        }

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = f"darkweb:{raw['fingerprint']}"
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
