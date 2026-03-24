"""RTF — RE: Radare2 reverse engineering framework"""
from __future__ import annotations
import re, json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class Radare2Wrapper(ToolWrapper):
    BINARY = "r2"; TOOL_NAME = "Radare2"; TIMEOUT = 120
    INSTALL_CMD = "apt install radare2"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        """Analyse a binary with radare2."""
        from modules.base_wrapper import WrapperResult
        import subprocess, time, shutil
        options = options or {}
        if not shutil.which(self.BINARY):
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error="r2 not installed"); self._last_result = r; return r
        # Build radare2 pipe commands
        cmds = options.get("commands", ["aaa","iz","afl","s main","pdf"])
        cmd_str = ";".join(cmds)
        t0 = time.monotonic()
        try:
            proc = subprocess.run([self.BINARY, "-q0", "-e", "bin.relocs.apply=true",
                                   "-c", cmd_str, target],
                                  capture_output=True, text=True, timeout=self.TIMEOUT)
            raw = proc.stdout + proc.stderr
            parsed = self.parse_output(raw, target, options)
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=proc.returncode==0,
                              data=parsed, raw_output=raw[:8000], duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error=str(exc), duration_s=time.monotonic()-t0)
        self._last_result = r; return r

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        strings = re.findall(r"\d+\s+\d+\s+\w+\s+(\S.+)", raw)
        functions = re.findall(r"(fcn\.\S+|sym\.\S+)", raw)
        imports = re.findall(r"sym\.imp\.(\S+)", raw)
        return {"strings": strings[:50], "functions": list(dict.fromkeys(functions))[:30],
                "imports": list(dict.fromkeys(imports))[:20], "target": target}

