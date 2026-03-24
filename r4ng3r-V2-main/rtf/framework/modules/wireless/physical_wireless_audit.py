from __future__ import annotations

from typing import Any, Dict

from framework.intelligence.json_schema import intelligence_envelope
from framework.modules.base import BaseModule, ModuleResult, Severity
from modules.network_attacks.urh_wrapper import URHWrapper


class PhysicalWirelessAuditModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name": "physical_wireless_audit", "description": "Physical and wireless audit pipeline with SDR/URH capability mapping for sub-GHz and IoT environments.", "author": "OpenAI", "category": "wireless", "version": "1.0"}

    def _declare_options(self) -> None:
        self._register_option("target", "Facility, badge system, or IoT target label", required=True)

    async def run(self) -> ModuleResult:
        target = self.get("target")
        urh = URHWrapper().run(target).to_dict()
        payload = intelligence_envelope(
            module="wireless/physical_wireless_audit",
            stage="sdr-audit",
            summary={"target": target, "tool_available": urh.get("success", False)},
            entities={"targets": [target]},
            evidence=[{"tool": "urh", "result": urh.get("data", {})}],
            analytics={"capabilities": urh.get("data", {}).get("capabilities", [])},
        )
        finding = self.make_finding(
            title="Physical wireless audit workflow prepared",
            target=target,
            severity=Severity.INFO,
            description="SDR capture, IoT decoding, replay, and badge-system validation capabilities were staged.",
            evidence={"tool": urh},
            tags=["wireless", "sdr", "urh"],
        )
        return ModuleResult(success=True, output=payload, findings=[finding])
