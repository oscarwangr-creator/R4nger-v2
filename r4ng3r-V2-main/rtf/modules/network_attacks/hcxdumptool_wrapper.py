"""RTF — Network: Hcxdumptool WPA2 capture"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class HcxdumptoolWrapper(ToolWrapper):
    BINARY = "hcxdumptool"; TOOL_NAME = "hcxdumptool"; TIMEOUT = 120
    INSTALL_CMD = "apt install hcxdumptool"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        iface    = options.get("interface", "wlan0")
        out      = options.get("output", "/tmp/capture.pcapng")
        duration = options.get("duration", 60)
        cmd = [self.BINARY, "-i", iface, "-o", out, "--active_beacon", "--enable_status=1"]
        if options.get("bssid"): cmd += ["--filterlist_ap=" + options["bssid"], "--filtermode=2"]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import os
        out = "/tmp/capture.pcapng"
        return {"capture_file": out if os.path.exists(out) else "",
                "size": os.path.getsize(out) if os.path.exists(out) else 0,
                "target": target}

