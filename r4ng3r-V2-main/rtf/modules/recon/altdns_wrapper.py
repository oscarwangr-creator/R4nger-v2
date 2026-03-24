"""RTF — Recon: Altdns subdomain permutation"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class AltdnsWrapper(ToolWrapper):
    BINARY = "altdns"; TOOL_NAME = "Altdns"; TIMEOUT = 300
    INSTALL_CMD = "pip install altdns"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        wordlist = options.get("wordlist", "/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt")
        out = options.get("output", "/tmp/altdns_out.txt")
        subdomains = options.get("subdomains", "/tmp/subdomains.txt")
        return [self.BINARY, "-i", subdomains, "-o", out, "-w", wordlist]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        out = "/tmp/altdns_out.txt"
        permutations = []
        if os.path.exists(out):
            permutations = [l.strip() for l in open(out).read().splitlines() if l.strip()]
        return {"permutations": permutations, "count": len(permutations), "target": target}

