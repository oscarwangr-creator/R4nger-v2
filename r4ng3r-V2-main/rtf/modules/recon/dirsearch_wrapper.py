"""RTF — Recon: Dirsearch directory brute-forcer"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class DirsearchWrapper(ToolWrapper):
    BINARY = "dirsearch"; TOOL_NAME = "Dirsearch"; TIMEOUT = 600
    INSTALL_CMD = "pip install dirsearch"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "-u", target, "--plain-text-report=/tmp/dirsearch_out.txt"]
        if options.get("extensions"): cmd += ["-e", options["extensions"]]
        if options.get("wordlist"):   cmd += ["-w", options["wordlist"]]
        if options.get("threads"):    cmd += ["-t", str(options["threads"])]
        if options.get("exclude"):    cmd += ["--exclude-status", options["exclude"]]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        found = []
        import os
        out_file = "/tmp/dirsearch_out.txt"
        if os.path.exists(out_file):
            for line in open(out_file).read().splitlines():
                m = re.search(r"(\d{3})\s+(\S+)\s+(.+)", line)
                if m: found.append({"status": int(m.group(1)), "size": m.group(2), "path": m.group(3)})
            os.remove(out_file)
        if not found:
            for line in raw.splitlines():
                m = re.search(r"(\d{3})\s+-\s+\S+\s+-\s+(/.+)", line)
                if m: found.append({"status": int(m.group(1)), "path": m.group(2)})
        return {"results": found, "count": len(found), "target": target}

