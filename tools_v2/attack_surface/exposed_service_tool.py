from __future__ import annotations

from hashlib import md5
from typing import Any, Dict

from core_v2.base_tool import BaseTool


class ExposedServiceDiscoveryTool(BaseTool):
    name = "exposed_service_discovery"
    category = "attack_surface"
    input_types = ['domain', 'ip']
    output_types = ['service_exposure']

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        value = payload.get("value", "")
        fingerprint = md5(f"exposed_service_discovery:{value}".encode()).hexdigest()[:12]
        return {
            "query": value,
            "fingerprint": fingerprint,
            "source": "exposed_service_discovery",
            "confidence": 0.74,
            "attributes": {
                "category": "attack_surface",
                "observed": True,
                "details": f"exposed_service_discovery generated intelligence for {value}"
            }
        }

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = f"attack_surface:{raw['fingerprint']}"
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
