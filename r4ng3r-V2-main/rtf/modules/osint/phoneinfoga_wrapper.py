"""RTF — OSINT: PhoneInfoga phone number scanner"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class PhoneinfogaWrapper(ToolWrapper):
    BINARY = "phoneinfoga"; TOOL_NAME = "PhoneInfoga"; TIMEOUT = 120
    INSTALL_CMD = "go install github.com/sundowndev/phoneinfoga/v2/cmd/phoneinfoga@latest"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        return [self.BINARY, "scan", "-n", target, "--output", "json"]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            data = json.loads(raw)
            return {"phone_data": data, "number": target}
        except Exception:
            lines = [l.strip() for l in raw.splitlines() if l.strip()]
            return {"raw_info": lines, "number": target}

