"""RTF — Recon: Ffuf fast web fuzzer"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class FfufWrapper(ToolWrapper):
    BINARY = "ffuf"; TOOL_NAME = "Ffuf"; TIMEOUT = 600
    INSTALL_CMD = "go install github.com/ffuf/ffuf/v2@latest"
    DEFAULT_WORDLIST = "/usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        url = target if "FUZZ" in target else target.rstrip("/") + "/FUZZ"
        wl  = options.get("wordlist", self.DEFAULT_WORDLIST)
        cmd = [self.BINARY, "-u", url, "-w", wl, "-of", "json",
               "-o", "/tmp/ffuf_out.json", "-s"]
        if options.get("extensions"): cmd += ["-e", options["extensions"]]
        if options.get("rate"):       cmd += ["-rate", str(options["rate"])]
        if options.get("mc"):         cmd += ["-mc", options["mc"]]
        if options.get("fc"):         cmd += ["-fc", options["fc"]]
        if options.get("threads"):    cmd += ["-t", str(options["threads"])]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import os
        results = []
        out_file = "/tmp/ffuf_out.json"
        if os.path.exists(out_file):
            try:
                data = json.loads(open(out_file).read())
                results = data.get("results", [])
                os.remove(out_file)
            except Exception: pass
        if not results:
            for line in raw.splitlines():
                m = re.search(r"\[Status: (\d+).*?\] (.+)", line)
                if m: results.append({"status": int(m.group(1)), "url": m.group(2).strip()})
        return {"results": results, "count": len(results), "target": target}

