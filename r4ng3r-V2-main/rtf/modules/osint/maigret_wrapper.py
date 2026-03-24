"""RTF — OSINT: Maigret multi-network username search"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class MaigretWrapper(ToolWrapper):
    BINARY = "maigret"; TOOL_NAME = "Maigret"; TIMEOUT = 300
    INSTALL_CMD = "pipx install maigret"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        out = options.get("output", f"/tmp/maigret_{target}")
        cmd = [self.BINARY, target, "-J", "all", "-fo", f"{out}.json", "--no-progressbar"]
        if options.get("timeout"): cmd += ["--timeout", str(options["timeout"])]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import os
        out = f"/tmp/maigret_{target}.json"
        accounts = []
        if os.path.exists(out):
            try:
                data = json.loads(open(out).read())
                for site, info in data.get("sites", {}).items():
                    if info.get("status", {}).get("id") == "FOUND":
                        accounts.append({"site": site, "url": info.get("url_main",""),
                                         "status": "found"})
            except Exception: pass
        if not accounts:
            for line in raw.splitlines():
                m = re.search(r"\[\+\]\s+(\S+)\s+(https?://\S+)", line)
                if m: accounts.append({"site": m.group(1), "url": m.group(2)})
        return {"accounts": accounts, "count": len(accounts), "username": target}

