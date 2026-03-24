"""RTF — OSINT: Osintgram Instagram OSINT"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class OsintgramWrapper(ToolWrapper):
    BINARY = "osintgram"; TOOL_NAME = "Osintgram"; TIMEOUT = 180
    INSTALL_CMD = "git clone https://github.com/Datalux/Osintgram && cd Osintgram && pip install -r requirements.txt"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd_type = options.get("command", "info")
        return ["python3", "~/tools/Osintgram/main.py", target, "--command", cmd_type]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return {"data": [l.strip() for l in raw.splitlines() if l.strip()],
                "emails": self._extract_emails(raw),
                "urls":   self._extract_urls(raw),
                "username": target}

