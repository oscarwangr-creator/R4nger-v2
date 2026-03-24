"""RTF — Scanning: Lynis security auditing"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class LynisWrapper(ToolWrapper):
    BINARY = "lynis"; TOOL_NAME = "Lynis"; TIMEOUT = 300
    INSTALL_CMD = "apt install lynis"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "audit", "system", "--no-log", "--no-colors", "--quiet"]
        if options.get("pentest"): cmd.append("--pentest")
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        warnings = []; suggestions = []; score = 0
        for line in raw.splitlines():
            if "Warning" in line or "[WARN]" in line: warnings.append(line.strip())
            if "Suggestion" in line:                  suggestions.append(line.strip())
            m = re.search(r"Hardening index.*?(\d+)", line)
            if m: score = int(m.group(1))
        return {"hardening_score": score, "warnings": warnings[:30],
                "suggestions": suggestions[:30], "target": target}

