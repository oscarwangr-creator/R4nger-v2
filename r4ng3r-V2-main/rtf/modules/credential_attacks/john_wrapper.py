"""RTF — Credential: John the Ripper password cracker"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class JohnWrapper(ToolWrapper):
    BINARY = "john"; TOOL_NAME = "John the Ripper"; TIMEOUT = 3600
    INSTALL_CMD = "apt install john"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, target]
        if options.get("wordlist"): cmd += [f"--wordlist={options['wordlist']}"]
        if options.get("format"):   cmd += [f"--format={options['format']}"]
        if options.get("rules"):    cmd.append("--rules")
        if options.get("incremental"): cmd.append("--incremental")
        if options.get("fork"):     cmd += [f"--fork={options['fork']}"]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        cracked = []
        for line in raw.splitlines():
            m = re.match(r"(.+?)\s+\((.+?)\)", line)
            if m: cracked.append({"password": m.group(1), "hash_id": m.group(2)})
        return {"cracked": cracked, "count": len(cracked), "target": target}

