"""RTF — OSINT: Profil3r username profiler"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class Profil3rWrapper(ToolWrapper):
    BINARY = "profil3r"; TOOL_NAME = "Profil3r"; TIMEOUT = 180
    INSTALL_CMD = "git clone https://github.com/Rog3rSm1th/Profil3r && cd Profil3r && pip install -r requirements.txt"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        return ["python3", "~/tools/Profil3r/profil3r/main.py", target]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        accounts = []
        for line in raw.splitlines():
            if "http" in line.lower() and ("found" in line.lower() or "[+]" in line):
                urls = self._extract_urls(line)
                if urls: accounts.append({"url": urls[0], "line": line.strip()})
        return {"accounts": accounts, "count": len(accounts), "username": target}

