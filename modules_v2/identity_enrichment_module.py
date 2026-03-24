from __future__ import annotations

from typing import Any, Dict

from modules_v2.base_module import BaseModule


class IdentityEnrichmentModule(BaseModule):
    name = "identity_enrichment_module"
    module_type = "identity"
    description = "Module-level identity enrichment wrapper for tool output aggregation."

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        value = payload.get("value", "")
        entity = {
            "id": f"identity:{value}",
            "type": "identity",
            "value": value,
            "confidence": 0.65,
            "attributes": {
                "source": "module.identity_enrichment",
                "input_type": payload.get("input_type", "identity"),
            },
        }
        return {
            "artifacts": [{"type": "module_output", "module": self.name, "value": value}],
            "entities": [entity],
            "relationships": [],
        }
