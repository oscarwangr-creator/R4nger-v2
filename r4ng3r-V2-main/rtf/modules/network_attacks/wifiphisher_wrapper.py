"""RTF — Network: Wifiphisher rogue AP / credential capture"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class WifiphisherWrapper(ToolWrapper):
    BINARY = "wifiphisher"; TOOL_NAME = "Wifiphisher"; TIMEOUT = 300
    INSTALL_CMD = "git clone https://github.com/wifiphisher/wifiphisher && python setup.py install"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        iface  = options.get("interface","wlan0")
        essid  = options.get("essid", target)
        phish  = options.get("phishing_page","wifi_connect")
        cmd = [self.BINARY, "-e", essid, "-p", phish, "-kB"]
        if options.get("jamming_iface"): cmd += ["-jI", options["jamming_iface"]]
        if options.get("lure10_exploit"): cmd.append("--lure10-exploit")
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        creds = self._extract_emails(raw)
        psk = []
        import re
        for m in re.finditer(r"WPA2? PSK: (\S+)", raw, re.I):
            psk.append(m.group(1))
        return {"captured_credentials": creds, "captured_psk": psk, "target": target}

