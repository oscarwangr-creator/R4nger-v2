"""RTF — Recon: Subfinder wrapper"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class SubfinderWrapper(ToolWrapper):
    BINARY = "subfinder"; TOOL_NAME = "Subfinder"; TIMEOUT = 300
    INSTALL_CMD = "go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "-d", target, "-silent"]
        if options.get("all"):        cmd.append("-all")
        if options.get("recursive"):  cmd.append("-recursive")
        if options.get("output"):     cmd += ["-o", options["output"]]
        if options.get("rate"):       cmd += ["-rate-limit", str(options["rate"])]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        subs = list(dict.fromkeys(l.strip() for l in raw.splitlines() if l.strip()))
        return {"subdomains": subs, "count": len(subs), "target": target}

