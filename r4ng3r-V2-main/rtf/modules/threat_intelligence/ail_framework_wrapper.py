"""RTF — TI: AIL Framework paste/leak analysis"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class AilFrameworkWrapper(ToolWrapper):
    BINARY = ""; TOOL_NAME = "AIL Framework"; TIMEOUT = 60
    INSTALL_CMD = "git clone https://github.com/ail-project/ail-framework && pip install -r requirements.txt"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        """Query AIL Framework REST API."""
        from modules.base_wrapper import WrapperResult
        import time
        options = options or {}
        api_key = options.get("api_key","")
        host    = options.get("host","http://localhost:7000")
        if not api_key:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error="AIL Framework requires api_key option")
            self._last_result = r; return r
        t0 = time.monotonic()
        try:
            import httpx
            headers = {"Authorization": api_key}
            with httpx.Client(timeout=self.TIMEOUT) as client:
                resp = client.get(f"{host}/api/v1/search/item", params={"query":target}, headers=headers)
                data = resp.json()
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=True,
                              data=self.parse_output(json.dumps(data), target, options),
                              duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error=str(exc), duration_s=time.monotonic()-t0)
        self._last_result = r; return r

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            data = json.loads(raw)
            return {"items": data.get("items",[])[:20], "count": data.get("total",0), "target": target}
        except Exception:
            return {"raw": raw[:2000], "target": target}

