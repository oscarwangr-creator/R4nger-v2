from __future__ import annotations

from hashlib import md5
from typing import Any, Dict

from core_v2.base_tool import BaseTool


class PasswordReuseDetectorTool(BaseTool):
    name = "password_reuse_detector"
    category = "credential"
    input_types = ['credential']
    output_types = ['reuse_signal']

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        value = payload.get("value", "")
        fingerprint = md5(f"password_reuse_detector:{value}".encode()).hexdigest()[:12]
        return {
            "query": value,
            "fingerprint": fingerprint,
            "source": "password_reuse_detector",
            "confidence": 0.74,
            "attributes": {
                "category": "credential",
                "observed": True,
                "details": f"password_reuse_detector generated intelligence for {value}"
            }
        }

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = f"credential:{raw['fingerprint']}"
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
