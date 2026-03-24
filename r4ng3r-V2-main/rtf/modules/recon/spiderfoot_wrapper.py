"""RTF — Recon: SpiderFoot OSINT automation"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class SpiderfootWrapper(ToolWrapper):
    BINARY = "sf"; TOOL_NAME = "SpiderFoot"; TIMEOUT = 600
    INSTALL_CMD = "git clone https://github.com/smicallef/spiderfoot && cd spiderfoot && pip install -r requirements.txt"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        out = options.get("output", "/tmp/sf_out.json")
        return ["python3", "~/tools/spiderfoot/sf.py", "-s", target,
                "-o", "json", "-q", "-l", "127.0.0.1:15555"]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        entities: Dict[str, list] = {"domains":[], "emails":[], "ips":[], "usernames":[], "urls":[]}
        entities["domains"] = self._extract_domains(raw)
        entities["emails"]  = self._extract_emails(raw)
        entities["ips"]     = self._extract_ips(raw)
        entities["urls"]    = self._extract_urls(raw)
        entities["target"]  = target
        return entities

