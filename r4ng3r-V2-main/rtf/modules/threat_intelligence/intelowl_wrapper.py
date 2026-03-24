"""RTF — TI: IntelOwl threat intelligence platform"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class IntelOwlWrapper(ToolWrapper):
    BINARY = ""; TOOL_NAME = "IntelOwl"; TIMEOUT = 120
    INSTALL_CMD = "docker pull intelowlproject/intelowl:latest"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        """Query IntelOwl via REST API."""
        from modules.base_wrapper import WrapperResult
        import time
        options = options or {}
        api_key = options.get("api_key","")
        host    = options.get("host","http://localhost:80")
        if not api_key:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error="IntelOwl requires api_key option. Deploy: docker compose up intelowl")
            self._last_result = r; return r
        t0 = time.monotonic()
        try:
            import httpx
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            payload = {"md5": target, "analyzers_requested": options.get("analyzers","ALL"),
                       "is_sample": options.get("is_sample", False),
                       "observable_name": target,
                       "observable_classification": options.get("classification","domain")}
            with httpx.Client(timeout=self.TIMEOUT) as client:
                resp = client.post(f"{host}/api/analyze_observable", json=payload, headers=headers)
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
            return {"job_id": data.get("id",""), "status": data.get("status",""),
                    "analyzers": data.get("analyzers_to_execute",[]),
                    "target": target}
        except Exception:
            return {"raw": raw[:2000], "target": target}

