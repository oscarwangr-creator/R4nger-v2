from __future__ import annotations

from hashlib import md5
from typing import Any, Dict

from core_v2.base_tool import BaseTool


class PortScanTool(BaseTool):
    name = "port_scan"
    category = "infrastructure"
    input_types = ['ip', 'domain']
    output_types = ['open_port']

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        value = payload.get("value", "")
        fingerprint = md5(f"port_scan:{value}".encode()).hexdigest()[:12]
        return {
            "query": value,
            "fingerprint": fingerprint,
            "source": "port_scan",
            "confidence": 0.74,
            "attributes": {
                "category": "infrastructure",
                "observed": True,
                "details": f"port_scan generated intelligence for {value}"
            }
        }

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = f"infrastructure:{raw['fingerprint']}"
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
