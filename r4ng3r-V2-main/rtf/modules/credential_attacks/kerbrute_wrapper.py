"""RTF — Credential: Kerbrute Kerberos brute-forcer"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class KerbruteWrapper(ToolWrapper):
    BINARY = "kerbrute"; TOOL_NAME = "Kerbrute"; TIMEOUT = 300
    INSTALL_CMD = "go install github.com/ropnop/kerbrute@latest"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        domain  = options.get("domain", target)
        dc      = options.get("dc", "")
        users   = options.get("userlist", "")
        passfile= options.get("passlist", "")
        mode    = options.get("mode", "userenum")  # userenum, bruteuser, bruteforce, passwordspray
        cmd = [self.BINARY, mode, "-d", domain, "--dc", dc or domain,
               "--output-file", "/tmp/kerbrute_out.txt"]
        if users:    cmd += ["--users", users]
        if passfile: cmd += ["-P", passfile]
        if options.get("username"): cmd += ["-u", options["username"]]
        if options.get("password"): cmd += ["-p", options["password"]]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        valid_users = []; cracked = []
        for line in raw.splitlines():
            if "VALID USERNAME" in line:
                m = re.search(r"VALID USERNAME:\s+(\S+)", line)
                if m: valid_users.append(m.group(1))
            if "VALID LOGIN" in line:
                m = re.search(r"VALID LOGIN:\s+(\S+):(\S+)", line)
                if m: cracked.append({"user": m.group(1), "pass": m.group(2)})
        return {"valid_users": valid_users, "cracked": cracked,
                "valid_count": len(valid_users), "target": target}

