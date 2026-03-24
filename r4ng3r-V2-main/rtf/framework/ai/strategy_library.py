from __future__ import annotations

from typing import Any, Dict, List


class StrategyLibrary:
    def list_actions(self) -> List[Dict[str, Any]]:
        return [
            {"name": "identity_fusion_extreme", "type": "workflow", "workflow": "identity_fusion_extreme", "target_types": ["username", "email", "domain"]},
            {"name": "attack_surface_mapping", "type": "workflow", "workflow": "attack_surface_mapping", "target_types": ["domain", "ip"]},
            {"name": "social_engineering_intel", "type": "workflow", "workflow": "social_engineering_intel", "target_types": ["username", "email"]},
            {"name": "threat_intelligence_pipeline", "type": "workflow", "workflow": "threat_intelligence_pipeline", "target_types": ["domain", "ip", "email"]},
            {"name": "breach_correlation", "type": "module", "module": "osint/breach_correlation", "target_types": ["email", "username"]},
            {"name": "tech_stack_fingerprinter", "type": "module", "module": "recon/tech_stack_fingerprinter", "target_types": ["domain", "ip"]},
        ]
