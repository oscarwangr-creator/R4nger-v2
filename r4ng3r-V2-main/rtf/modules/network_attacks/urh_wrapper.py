from __future__ import annotations

from typing import Any, Dict, List

from modules.base_wrapper import ToolWrapper


class URHWrapper(ToolWrapper):
    BINARY = "urh"
    TOOL_NAME = "universal_radio_hacker"
    INSTALL_CMD = "apt install -y urh"

    def _build_cmd(self, target: str, options: Dict[str, Any]) -> List[str]:
        return [self.BINARY, "--help"]

    def parse_output(self, raw: str, target: str = "", options: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {
            "target": target,
            "capabilities": [
                "sub-ghz_capture",
                "iot_signal_decoding",
                "replay_attack_testing",
                "physical_access_control_testing",
            ],
            "raw_preview": raw[:400],
        }
