"""RTF — Scanning: OpenVAS / GVM vulnerability scanner"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class OpenvasWrapper(ToolWrapper):
    BINARY = "gvm-cli"; TOOL_NAME = "OpenVAS/GVM"; TIMEOUT = 1200
    INSTALL_CMD = "apt install gvm && gvm-setup"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        """OpenVAS via gvm-cli TLS connection or gvm-script."""
        from modules.base_wrapper import WrapperResult
        import subprocess, time, shutil
        options = options or {}
        if not shutil.which(self.BINARY):
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error="gvm-cli not installed. Run: apt install gvm && gvm-setup")
            self._last_result = r; return r
        host  = options.get("host", "127.0.0.1")
        port  = options.get("port", 9390)
        user  = options.get("username", "admin")
        pwd   = options.get("password", "")
        xml_cmd = f'<create_task><name>RTF Scan {target}</name><config id="daba56c8-73ec-11df-a475-002264764cea"/><target id="{target}"/></create_task>'
        cmd = [self.BINARY, "--protocol=GMP", f"--socketpath=/var/run/gvm/gvmd.sock",
               "socket", "--xml", f"<authenticate><credentials><username>{user}</username><password>{pwd}</password></credentials></authenticate>"]
        t0 = time.monotonic()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.TIMEOUT)
            raw = proc.stdout + proc.stderr
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=proc.returncode==0,
                              data=self.parse_output(raw, target, options),
                              raw_output=raw[:4000], duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error=str(exc), duration_s=time.monotonic()-t0)
        self._last_result = r; return r

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        vulns = []
        for m in re.finditer(r"<name>(.+?)</name>.*?<severity>(.+?)</severity>", raw, re.DOTALL):
            vulns.append({"name": m.group(1), "severity": m.group(2)})
        return {"vulnerabilities": vulns[:50], "count": len(vulns), "target": target}

