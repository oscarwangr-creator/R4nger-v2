"""RTF — Recon: Httprobe (probe live HTTP/HTTPS hosts)"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class HttprobeWrapper(ToolWrapper):
    BINARY = "httprobe"; TOOL_NAME = "Httprobe"; TIMEOUT = 180
    INSTALL_CMD = "go install github.com/tomnomnom/httprobe@latest"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        options = options or {}
        # httprobe reads from stdin — write subdomains list
        import subprocess, time, shutil
        if not shutil.which(self.BINARY):
            from modules.base_wrapper import WrapperResult
            return WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                                 error=f"{self.BINARY} not installed")
        domains = options.get("domains", [target])
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                [self.BINARY] + (["-c", str(options.get("concurrency",50))] if options.get("concurrency") else []),
                input="\n".join(domains), capture_output=True, text=True, timeout=self.TIMEOUT
            )
            raw = proc.stdout
            from modules.base_wrapper import WrapperResult
            parsed = self.parse_output(raw, target, options)
            result = WrapperResult(tool=self.TOOL_NAME, target=target, success=True,
                                   data=parsed, raw_output=raw[:4000],
                                   duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            from modules.base_wrapper import WrapperResult
            result = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                                   error=str(exc), duration_s=time.monotonic()-t0)
        self._last_result = result
        return result

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        live = list(dict.fromkeys(l.strip() for l in raw.splitlines() if l.startswith("http")))
        return {"live_hosts": live, "count": len(live)}

