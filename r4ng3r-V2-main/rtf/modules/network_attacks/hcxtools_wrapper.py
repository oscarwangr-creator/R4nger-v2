"""RTF — Network: HcxTools WPA hash converter"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class HcxtoolsWrapper(ToolWrapper):
    BINARY = "hcxpcapngtool"; TOOL_NAME = "hcxtools"; TIMEOUT = 60
    INSTALL_CMD = "apt install hcxtools"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        out = options.get("output", "/tmp/hashcat_wpa.hc22000")
        return [self.BINARY, "-o", out, target]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import os, re
        out = "/tmp/hashcat_wpa.hc22000"
        hashes = []
        if os.path.exists(out):
            hashes = [l.strip() for l in open(out).read().splitlines() if l.strip()]
        return {"hashcat_hashes": hashes, "count": len(hashes), "output_file": out, "target": target}

