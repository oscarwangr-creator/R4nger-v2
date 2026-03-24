"""RTF — Recon: Virtual Host Scanner"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class VhostscanWrapper(ToolWrapper):
    BINARY = "virtual-host-discovery"; TOOL_NAME = "VHostScan"; TIMEOUT = 300
    INSTALL_CMD = "gem install virtual-host-discovery"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "--target", target]
        if options.get("ip"):       cmd += ["--ip", options["ip"]]
        if options.get("wordlist"): cmd += ["--wordlist", options["wordlist"]]
        if options.get("port"):     cmd += ["--port", str(options["port"])]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        vhosts = []
        for line in raw.splitlines():
            if "Found" in line or "[+]" in line:
                vhosts.append(line.strip())
        return {"vhosts": vhosts, "count": len(vhosts), "target": target}

