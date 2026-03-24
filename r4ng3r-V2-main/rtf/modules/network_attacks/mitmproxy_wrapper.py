"""RTF — Network: mitmproxy HTTPS interceptor"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class MitmproxyWrapper(ToolWrapper):
    BINARY = "mitmproxy"; TOOL_NAME = "mitmproxy"; TIMEOUT = 60
    INSTALL_CMD = "pipx install mitmproxy"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        """Start mitmproxy in transparent or upstream mode briefly to capture flows."""
        from modules.base_wrapper import WrapperResult
        import subprocess, time, shutil
        options = options or {}
        if not shutil.which("mitmdump"):
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error="mitmdump not installed. pipx install mitmproxy")
            self._last_result = r; return r
        port     = options.get("port", 8080)
        out_file = options.get("output", "/tmp/mitmproxy_flows.json")
        script   = options.get("script","")
        duration = options.get("duration", 30)
        cmd = ["mitmdump", "-p", str(port), "-w", out_file]
        if script: cmd += ["-s", script]
        t0 = time.monotonic()
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(duration)
            proc.terminate()
            raw = (proc.stdout.read() or "") + (proc.stderr.read() or "")
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=True,
                              data=self.parse_output(raw, target, options),
                              raw_output=raw[:2000], duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error=str(exc), duration_s=time.monotonic()-t0)
        self._last_result = r; return r

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import json, os
        flows = []
        out = options.get("output","/tmp/mitmproxy_flows.json") if options else "/tmp/mitmproxy_flows.json"
        if os.path.exists(out):
            try:
                data = json.loads(open(out).read())
                flows = data if isinstance(data, list) else []
            except Exception: pass
        return {"flows": flows[:50], "count": len(flows), "target": target}

