"""RTF — Credential: NCrack network authentication cracker"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class NcrackWrapper(ToolWrapper):
    BINARY = "ncrack"; TOOL_NAME = "NCrack"; TIMEOUT = 600
    INSTALL_CMD = "apt install ncrack"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "-v", "--user", options.get("username",""), 
               "-P", options.get("passlist","/usr/share/wordlists/rockyou.txt")]
        service = options.get("service","ssh")
        port    = options.get("port", {"ssh":22,"rdp":3389,"ftp":21,"telnet":23}.get(service,22))
        cmd.append(f"{service}://{target}:{port}")
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        cracked = []
        for line in raw.splitlines():
            if "Discovered credentials" in line or "password:" in line.lower():
                m = re.search(r"login: (\S+)\s+password: (\S+)", line, re.I)
                if m: cracked.append({"user": m.group(1), "pass": m.group(2)})
        return {"cracked": cracked, "count": len(cracked), "target": target}

