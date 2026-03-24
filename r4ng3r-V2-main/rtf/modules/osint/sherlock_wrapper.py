"""RTF — OSINT: Sherlock username search"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class SherlockWrapper(ToolWrapper):
    BINARY = "sherlock"; TOOL_NAME = "Sherlock"; TIMEOUT = 300
    INSTALL_CMD = "pipx install sherlock-project"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, target, "--print-found", "--no-color"]
        if options.get("timeout"): cmd += ["--timeout", str(options["timeout"])]
        if options.get("output"):  cmd += ["--output", options["output"]]
        if options.get("site"):    cmd += ["--site", options["site"]]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        found = []
        for line in raw.splitlines():
            m = re.search(r"\[.\]\s+(\S+):\s+(https?://\S+)", line)
            if m and "+" in line:
                found.append({"platform": m.group(1), "url": m.group(2)})
        not_found = sum(1 for l in raw.splitlines() if "Not Found" in l or "[-]" in l)
        return {"accounts": found, "found_count": len(found), "not_found": not_found,
                "username": target}

