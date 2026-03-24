"""RTF — Credential: Hashcat GPU hash cracker"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

HASH_TYPE_MAP = {
    "md5": 0, "sha1": 100, "sha256": 1400, "sha512": 1700,
    "ntlm": 1000, "netntlmv2": 5600, "kerberoast": 13100,
    "asreproast": 18200, "wpa2": 22000, "bcrypt": 3200,
    "md5crypt": 500, "sha512crypt": 1800, "mysql": 300,
    "mssql": 131, "oracle": 112, "lm": 3000, "des": 1500,
}

class HashcatWrapper(ToolWrapper):
    BINARY = "hashcat"; TOOL_NAME = "Hashcat"; TIMEOUT = 3600
    INSTALL_CMD = "apt install hashcat"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        hash_type = options.get("hash_type", "ntlm")
        mode = HASH_TYPE_MAP.get(hash_type.lower(), options.get("mode_id", 1000))
        attack = options.get("attack_mode", 0)  # 0=dict, 3=brute, 6=hybrid
        wordlist = options.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        cmd = [self.BINARY, "-m", str(mode), "-a", str(attack),
               "--outfile=/tmp/hashcat_out.txt", "--status", "--quiet", target]
        if attack in (0,6): cmd.append(wordlist)
        if attack == 3:     cmd.append(options.get("mask","?a?a?a?a?a?a?a?a"))
        if options.get("rules"): cmd += ["-r", options["rules"]]
        if options.get("workload"): cmd += ["-w", str(options["workload"])]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import os
        cracked = []
        out = "/tmp/hashcat_out.txt"
        if os.path.exists(out):
            for line in open(out).read().splitlines():
                if ":" in line:
                    parts = line.rsplit(":", 1)
                    cracked.append({"hash": parts[0], "plaintext": parts[1] if len(parts)>1 else ""})
            os.remove(out)
        recovered = sum(1 for l in raw.splitlines() if "Recovered" in l)
        return {"cracked": cracked, "count": len(cracked), "target": target}

