"""RTF — AI: Claude AI analysis integration"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper, WrapperResult

class ClaudeIntegration(ToolWrapper):
    BINARY = ""; TOOL_NAME = "Claude-AI"; TIMEOUT = 60
    INSTALL_CMD = "pip install anthropic"

    def run(self, target: str, options: Optional[Dict] = None) -> WrapperResult:
        import time
        options = options or {}
        t0 = time.monotonic()
        prompt = options.get("prompt", f"Analyse this security finding: {target}")
        model  = options.get("model", "claude-sonnet-4-20250514")
        context = options.get("context", {})
        try:
            import httpx
            payload = {
                "model": model, "max_tokens": options.get("max_tokens", 2000),
                "messages": [{"role":"user","content":
                    f"{prompt}\n\nContext:\n{json.dumps(context, indent=2) if context else target}"}]
            }
            with httpx.Client(timeout=self.TIMEOUT) as client:
                resp = client.post("https://api.anthropic.com/v1/messages", json=payload,
                                   headers={"Content-Type":"application/json",
                                            "anthropic-version":"2023-06-01"})
                data = resp.json()
            content = "".join(b.get("text","") for b in data.get("content",[]) if b.get("type")=="text")
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=True,
                              data=self.parse_output(content, target, options),
                              duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error=str(exc), duration_s=time.monotonic()-t0)
        self._last_result = r; return r

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return {"analysis": raw, "length": len(raw), "target": target}

