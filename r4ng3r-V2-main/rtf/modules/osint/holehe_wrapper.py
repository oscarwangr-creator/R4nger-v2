"""RTF — OSINT: Holehe email account checker"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class HoleheWrapper(ToolWrapper):
    BINARY = "holehe"; TOOL_NAME = "Holehe"; TIMEOUT = 180
    INSTALL_CMD = "pipx install holehe"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        return [self.BINARY, target, "--no-color"]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        registered = []
        for line in raw.splitlines():
            if "[+]" in line or "REGISTERED" in line.upper():
                m = re.search(r"(\w[\w\.\-]+\w\.\w+)", line)
                if m: registered.append(m.group(1))
        return {"registered_on": registered, "count": len(registered), "email": target}

