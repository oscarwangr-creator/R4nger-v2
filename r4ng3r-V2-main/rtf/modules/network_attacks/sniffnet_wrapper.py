"""RTF — Network: Sniffnet network traffic monitor"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class SniffnetWrapper(ToolWrapper):
    BINARY = "sniffnet"; TOOL_NAME = "Sniffnet"; TIMEOUT = 60
    INSTALL_CMD = "cargo install sniffnet"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        """Sniffnet is GUI-based; this wrapper captures a brief traffic summary."""
        from modules.base_wrapper import WrapperResult
        r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                          error="Sniffnet is a GUI application. Use interactively or use tcpdump/tshark for CLI capture.")
        self._last_result = r; return r

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return {"output": raw[:2000]}

