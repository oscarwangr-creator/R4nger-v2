"""RTF — Network: Bettercap network attack framework"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class BettercapWrapper(ToolWrapper):
    BINARY = "bettercap"; TOOL_NAME = "Bettercap"; TIMEOUT = 120
    INSTALL_CMD = "apt install bettercap"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        iface = options.get("interface", "eth0")
        caplet = options.get("caplet", "")
        cmd = [self.BINARY, "-iface", iface, "-eval"]
        if caplet:
            cmd[-1] = "-caplet"; cmd.append(caplet)
        else:
            attack = options.get("attack","net.probe on; net.show; exit")
            cmd.append(attack)
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        hosts = []
        import re
        for line in raw.splitlines():
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+(\w{2}:\w{2}:\w{2}:\w{2}:\w{2}:\w{2})", line)
            if m: hosts.append({"ip": m.group(1), "mac": m.group(2)})
        return {"discovered_hosts": hosts, "count": len(hosts), "target": target}

