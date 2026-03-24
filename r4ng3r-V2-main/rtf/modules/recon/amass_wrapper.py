"""RTF — Recon: Amass wrapper (subdomain enumeration)"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class AmassWrapper(ToolWrapper):
    BINARY = "amass"; TOOL_NAME = "Amass"; TIMEOUT = 600
    INSTALL_CMD = "go install github.com/owasp-amass/amass/v4/...@latest"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "enum", "-passive", "-d", target]
        if options.get("active"):     cmd[2] = "-active"
        if options.get("output"):     cmd += ["-o", options["output"]]
        if options.get("timeout"):    cmd += ["-timeout", str(options["timeout"]//60)]
        if options.get("config"):     cmd += ["-config", options["config"]]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        subs = list(dict.fromkeys(
            l.strip() for l in raw.splitlines()
            if l.strip() and not l.startswith("[") and target and target in l
        )) or self._extract_domains(raw)
        return {"subdomains": subs, "count": len(subs), "target": target}

