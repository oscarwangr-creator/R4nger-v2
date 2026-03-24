"""RTF — Recon: reNgine wrapper (automated reconnaissance platform)"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class RengineWrapper(ToolWrapper):
    BINARY      = "reNgine"
    TOOL_NAME   = "reNgine"
    TIMEOUT     = 3600
    INSTALL_CMD = (
        "git clone https://github.com/yogeshojha/rengine && "
        "cd rengine && docker-compose up -d"
    )

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        # reNgine is typically Docker/API based; expose CLI wrapper
        cmd = ["python3", "manage.py", "scan", target]
        if options.get("yaml_config"):
            cmd += ["--config", options["yaml_config"]]
        if options.get("profile"):
            cmd += ["--engine", options["profile"]]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        subdomains = re.findall(r"(?:Found|Subdomain):\s*([a-zA-Z0-9._-]+\." + re.escape(target) + r")", raw)
        endpoints  = re.findall(r"https?://[^\s\"'<>]+", raw)
        vulns      = re.findall(r"(?:VULNERABILITY|CVE-\d{4}-\d+|nuclei.*\[)", raw, re.I)
        return {
            "target":     target,
            "subdomains": list(dict.fromkeys(subdomains)),
            "endpoints":  list(dict.fromkeys(endpoints))[:50],
            "vulns_found": len(vulns),
            "raw_snippet": raw[:500],
        }
