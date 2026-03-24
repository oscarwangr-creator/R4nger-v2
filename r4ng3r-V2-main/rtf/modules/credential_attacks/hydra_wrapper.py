"""RTF — Credential: Hydra network brute-forcer"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class HydraWrapper(ToolWrapper):
    BINARY = "hydra"; TOOL_NAME = "Hydra"; TIMEOUT = 600
    INSTALL_CMD = "apt install hydra"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        service  = options.get("service", "ssh")
        userlist = options.get("userlist", "")
        passlist = options.get("passlist", "/usr/share/wordlists/rockyou.txt")
        username = options.get("username", "")
        password = options.get("password", "")
        cmd = [self.BINARY, "-t", str(options.get("threads",4)),
               "-f", "-o", "/tmp/hydra_out.txt"]
        if username: cmd += ["-l", username]
        elif userlist: cmd += ["-L", userlist]
        if password: cmd += ["-p", password]
        elif passlist: cmd += ["-P", passlist]
        port = options.get("port","")
        if port: cmd += ["-s", str(port)]
        cmd += [target, service]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import os
        cracked = []
        out = "/tmp/hydra_out.txt"
        src = open(out).read() if os.path.exists(out) else raw
        for line in src.splitlines():
            m = re.search(r"\[\d+\]\[(\w+)\] host: (\S+)\s+login: (\S+)\s+password: (\S+)", line)
            if m: cracked.append({"service":m.group(1),"host":m.group(2),"user":m.group(3),"pass":m.group(4)})
        return {"cracked": cracked, "count": len(cracked), "target": target}

