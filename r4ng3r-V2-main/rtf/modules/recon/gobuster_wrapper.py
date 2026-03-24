"""RTF — Recon: Gobuster directory/subdomain fuzzer"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class GobusterWrapper(ToolWrapper):
    BINARY = "gobuster"; TOOL_NAME = "Gobuster"; TIMEOUT = 600
    INSTALL_CMD = "go install github.com/OJ/gobuster/v3@latest"
    DEFAULT_WORDLIST = "/usr/share/seclists/Discovery/Web-Content/common.txt"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        mode = options.get("mode", "dir")
        wl = options.get("wordlist", self.DEFAULT_WORDLIST)
        cmd = [self.BINARY, mode, "-u" if mode=="dir" else "-d", target,
               "-w", wl, "-q", "--no-progress"]
        if options.get("extensions"): cmd += ["-x", options["extensions"]]
        if options.get("threads"):    cmd += ["-t", str(options["threads"])]
        if options.get("status"):     cmd += ["-s", options["status"]]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        found = []
        for line in raw.splitlines():
            m = re.search(r"(https?://\S+|/\S+)\s+\(Status:\s*(\d+)\)", line)
            if m: found.append({"path": m.group(1), "status": int(m.group(2))})
        return {"results": found, "count": len(found), "target": target}

