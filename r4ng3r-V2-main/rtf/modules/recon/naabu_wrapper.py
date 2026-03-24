"""RTF — Recon: Naabu port scanner wrapper"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class NaabuWrapper(ToolWrapper):
    BINARY = "naabu"; TOOL_NAME = "Naabu"; TIMEOUT = 300
    INSTALL_CMD = "go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "-host", target, "-silent"]
        ports = options.get("ports", "top-100")
        if ports == "top-100":    cmd += ["-top-ports", "100"]
        elif ports == "top-1000": cmd += ["-top-ports", "1000"]
        elif ports == "full":     cmd += ["-p", "-"]
        else:                     cmd += ["-p", ports]
        if options.get("rate"):  cmd += ["-rate", str(options["rate"])]
        if options.get("nmap"):  cmd += ["-nmap-cli", "nmap -sV -Pn"]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        ports = []
        for line in raw.splitlines():
            m = re.search(r"(\S+):(\d+)", line)
            if m: ports.append({"host": m.group(1), "port": int(m.group(2))})
        return {"open_ports": ports, "count": len(ports), "target": target}

