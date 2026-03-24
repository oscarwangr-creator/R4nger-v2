"""RTF — OSINT: Social Analyzer username check"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class SocialAnalyzerWrapper(ToolWrapper):
    BINARY = "social-analyzer"; TOOL_NAME = "Social-Analyzer"; TIMEOUT = 300
    INSTALL_CMD = "pipx install social-analyzer"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        return [self.BINARY, "--username", target, "--mode", "fast",
                "--output", "json", "--logs-to-json"]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        profiles = []
        try:
            data = json.loads(raw) if raw.startswith("{") else {}
            profiles = data.get("detected", [])
        except Exception:
            for line in raw.splitlines():
                if "http" in line.lower():
                    profiles.append({"url": self._extract_urls(line)})
        return {"profiles": profiles, "count": len(profiles), "username": target}

