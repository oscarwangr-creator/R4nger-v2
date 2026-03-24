"""RTF — Credential: BruteSpray nmap-to-hydra automation"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class BrutesprayWrapper(ToolWrapper):
    BINARY = "brutespray"; TOOL_NAME = "BruteSpray"; TIMEOUT = 600
    INSTALL_CMD = "pip install brutespray"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        # target should be nmap gnmap output file
        cmd = [self.BINARY, "-f", target, "-t", str(options.get("threads",5)),
               "-o", "/tmp/brutespray_out"]
        if options.get("userlist"):  cmd += ["-u", options["userlist"]]
        if options.get("passlist"):  cmd += ["-p", options["passlist"]]
        if options.get("service"):   cmd += ["--service", options["service"]]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import os
        cracked = []
        out_dir = "/tmp/brutespray_out"
        if os.path.isdir(out_dir):
            for f in os.listdir(out_dir):
                fpath = os.path.join(out_dir, f)
                for line in open(fpath).read().splitlines():
                    if "login:" in line.lower():
                        cracked.append({"source": f, "line": line.strip()})
        return {"cracked": cracked, "count": len(cracked), "target": target}

