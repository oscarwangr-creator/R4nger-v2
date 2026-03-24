"""RTF — Recon: WhatWeb technology fingerprinter"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class WhatwebWrapper(ToolWrapper):
    BINARY = "whatweb"; TOOL_NAME = "WhatWeb"; TIMEOUT = 120
    INSTALL_CMD = "gem install whatweb"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "--log-json=-", target]
        aggression = options.get("aggression", 1)
        cmd += [f"--aggression={aggression}"]
        if options.get("user_agent"): cmd += [f"--user-agent={options['user_agent']}"]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        technologies = []
        try:
            for line in raw.splitlines():
                if line.startswith("["):
                    data = json.loads(line)
                    for entry in (data if isinstance(data, list) else [data]):
                        techs = {k: v for k, v in entry.items()
                                 if k not in ("target", "http_status")}
                        technologies.append({"url": entry.get("target",""), "techs": techs})
        except Exception:
            m = re.findall(r"\[(.+?)\]", raw)
            technologies = [{"tech": t} for t in m]
        return {"technologies": technologies, "count": len(technologies), "target": target}

