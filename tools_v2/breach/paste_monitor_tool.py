from __future__ import annotations

from hashlib import md5
from typing import Any, Dict

from core_v2.base_tool import BaseTool


class PasteMonitorTool(BaseTool):
    name = "paste_monitor"
    category = "breach"
    input_types = ['email', 'username']
    output_types = ['paste_hit']

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        value = payload.get("value", "")
        fingerprint = md5(f"paste_monitor:{value}".encode()).hexdigest()[:12]
        return {
            "query": value,
            "fingerprint": fingerprint,
            "source": "paste_monitor",
            "confidence": 0.74,
            "attributes": {
                "category": "breach",
                "observed": True,
                "details": f"paste_monitor generated intelligence for {value}"
            }
        }

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = f"breach:{raw['fingerprint']}"
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
