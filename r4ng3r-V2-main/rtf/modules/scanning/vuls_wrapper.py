"""RTF — Scanning: Vuls vulnerability scanner"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class VulsWrapper(ToolWrapper):
    BINARY = "vuls"; TOOL_NAME = "Vuls"; TIMEOUT = 600
    INSTALL_CMD = "docker pull vuls/vuls"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        config = options.get("config", "/vuls/config.toml")
        return [self.BINARY, "scan", "-config", config]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            data = json.loads(raw)
            return {"scan_results": data, "target": target}
        except Exception:
            return {"summary": [l for l in raw.splitlines() if l.strip()][:30], "target": target}

