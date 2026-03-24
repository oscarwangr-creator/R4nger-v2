"""
RTF v2.0 — Base Tool Wrapper
All new modules/  wrappers inherit from ToolWrapper.

Standard interface:
  run(target, options)   — execute the tool, return structured dict
  parse_output(raw)      — parse raw stdout/stderr → structured dict
  return_json()          — return last result as JSON string
"""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class WrapperResult:
    tool:        str
    target:      str
    success:     bool
    data:        Dict[str, Any]      = field(default_factory=dict)
    findings:    List[Dict[str, Any]] = field(default_factory=list)
    raw_output:  str  = ""
    error:       str  = ""
    duration_s:  float = 0.0
    run_id:      str  = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp:   str  = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class ToolWrapper:
    """Base class for every tool wrapper in modules/."""

    BINARY: str = ""                      # override in subclass
    TOOL_NAME: str = ""                   # human-readable name
    INSTALL_CMD: str = ""                 # how to install
    TIMEOUT: int = 300                    # default timeout seconds

    def __init__(self) -> None:
        self._last_result: Optional[WrapperResult] = None
        self._binary_path: str = shutil.which(self.BINARY) or ""

    # ─── Public interface ────────────────────────────────────────────

    def run(self, target: str, options: Optional[Dict[str, Any]] = None) -> WrapperResult:
        """
        Execute the tool synchronously.
        Subclasses override _build_cmd() and parse_output().
        """
        options = options or {}
        if not self._binary_path:
            result = WrapperResult(
                tool=self.TOOL_NAME or self.BINARY,
                target=target,
                success=False,
                error=f"{self.BINARY} not installed. Install: {self.INSTALL_CMD}",
            )
            self._last_result = result
            return result

        cmd = self._build_cmd(target, options)
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=options.get("timeout", self.TIMEOUT),
            )
            raw = proc.stdout + proc.stderr
            duration = time.monotonic() - t0
            parsed = self.parse_output(raw, target, options)
            result = WrapperResult(
                tool=self.TOOL_NAME or self.BINARY,
                target=target,
                success=proc.returncode == 0 or bool(parsed),
                data=parsed,
                raw_output=raw[:8000],
                duration_s=round(duration, 2),
                error="" if proc.returncode == 0 else proc.stderr[:400],
            )
        except subprocess.TimeoutExpired:
            result = WrapperResult(
                tool=self.TOOL_NAME or self.BINARY, target=target, success=False,
                error=f"Timeout after {options.get('timeout', self.TIMEOUT)}s",
                duration_s=time.monotonic() - t0,
            )
        except Exception as exc:
            result = WrapperResult(
                tool=self.TOOL_NAME or self.BINARY, target=target, success=False,
                error=str(exc), duration_s=time.monotonic() - t0,
            )
        self._last_result = result
        return result

    async def run_async(self, target: str, options: Optional[Dict[str, Any]] = None) -> WrapperResult:
        """Async variant — runs tool in executor to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, target, options or {})

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse raw stdout/stderr.  Override in every subclass.
        Default: return raw lines as list.
        """
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        return {"lines": lines, "count": len(lines)}

    def return_json(self) -> str:
        """Return last result as JSON.  Call after run()."""
        if self._last_result is None:
            return json.dumps({"error": "run() not called yet"})
        return self._last_result.to_json()

    def is_installed(self) -> bool:
        return bool(self._binary_path)

    def info(self) -> Dict[str, Any]:
        return {
            "tool":       self.TOOL_NAME or self.BINARY,
            "binary":     self.BINARY,
            "installed":  self.is_installed(),
            "path":       self._binary_path,
            "install":    self.INSTALL_CMD,
            "timeout":    self.TIMEOUT,
        }

    # ─── Internal helpers ────────────────────────────────────────────

    def _build_cmd(self, target: str, options: Dict[str, Any]) -> List[str]:
        """Build subprocess command list.  Override in every subclass."""
        return [self.BINARY, target]

    def _extract_ips(self, text: str) -> List[str]:
        import re
        return list(dict.fromkeys(
            re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
        ))

    def _extract_domains(self, text: str) -> List[str]:
        import re
        return list(dict.fromkeys(
            re.findall(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b", text)
        ))

    def _extract_emails(self, text: str) -> List[str]:
        import re
        return list(dict.fromkeys(
            re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
        ))

    def _extract_urls(self, text: str) -> List[str]:
        import re
        return list(dict.fromkeys(
            re.findall(r"https?://[^\s\"'<>]{4,}", text)
        ))

    def _extract_ports(self, text: str) -> List[Dict]:
        import re
        results = []
        for m in re.finditer(
            r"(\d+)/(tcp|udp)\s+(\w+)\s*([\w\-/]*)", text, re.I
        ):
            results.append({
                "port": int(m.group(1)), "protocol": m.group(2),
                "state": m.group(3), "service": m.group(4),
            })
        return results
