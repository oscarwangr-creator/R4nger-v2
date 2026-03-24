"""RTF — OSINT: Intelligence X API wrapper"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class IntelligenceXWrapper(ToolWrapper):
    BINARY = ""; TOOL_NAME = "Intelligence-X"; TIMEOUT = 60
    INSTALL_CMD = "pip install intelx"
    BASE_URL = "https://2.intelx.io"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        from modules.base_wrapper import WrapperResult
        import time
        options = options or {}
        api_key = options.get("api_key", "")
        if not api_key:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error="Intelligence-X requires api_key option")
            self._last_result = r; return r
        t0 = time.monotonic()
        try:
            import httpx
            headers = {"x-key": api_key}
            payload = {"term": target, "buckets": [], "lookuplevel": 0,
                       "maxresults": options.get("limit", 10), "timeout": 5,
                       "datefrom": "", "dateto": "", "sort": 4, "media": 0,
                       "terminate": []}
            with httpx.Client(timeout=self.TIMEOUT) as client:
                r1 = client.post(f"{self.BASE_URL}/intelligent/search", json=payload, headers=headers)
                sid = r1.json().get("id", "")
                time.sleep(2)
                r2 = client.get(f"{self.BASE_URL}/intelligent/search/result?id={sid}", headers=headers)
                data = r2.json()
            parsed = self.parse_output(json.dumps(data), target, options)
            result = WrapperResult(tool=self.TOOL_NAME, target=target, success=True,
                                   data=parsed, duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            result = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                                   error=str(exc), duration_s=time.monotonic()-t0)
        self._last_result = result; return result

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            data = json.loads(raw)
            records = data.get("records", [])
            return {"results": records[:20], "count": len(records), "query": target}
        except Exception:
            return {"raw": raw[:2000], "query": target}

