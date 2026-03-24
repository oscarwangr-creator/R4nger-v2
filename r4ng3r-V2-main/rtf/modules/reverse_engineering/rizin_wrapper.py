"""RTF — RE: Rizin binary analysis"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class RizinWrapper(ToolWrapper):
    BINARY = "rizin"; TOOL_NAME = "Rizin"; TIMEOUT = 120
    INSTALL_CMD = "apt install rizin"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmds = options.get("commands", ["aaa","iz","afl"])
        return [self.BINARY, "-q0", "-c", ";".join(cmds), target]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import re
        functions = list(dict.fromkeys(re.findall(r"(fcn\.\S+)", raw)))
        strings = re.findall(r"\d+\s+\d+\s+\w+\s+(\S.+)", raw)
        return {"functions": functions[:30], "strings": strings[:50], "target": target}

