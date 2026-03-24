"""RTF — RE: x64dbg Windows debugger (remote/scripted)"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class X64dbgWrapper(ToolWrapper):
    BINARY = "x64dbg"; TOOL_NAME = "x64dbg"; TIMEOUT = 120
    INSTALL_CMD = "Download from https://x64dbg.com"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        """x64dbg — Windows only, remote script via x64dbg script engine."""
        from modules.base_wrapper import WrapperResult
        import shutil
        options = options or {}
        if not shutil.which(self.BINARY):
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error="x64dbg is Windows-only. Download from https://x64dbg.com")
            self._last_result = r; return r
        return WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                             error="x64dbg scripted execution not supported from CLI wrapper. "
                                   "Use x64dbg GUI or x64dbg HTTP server plugin.")

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return {"output": raw[:2000], "target": target}

