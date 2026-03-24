"""RTF — Scanning: Scan4All integrated scanner"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class Scan4AllWrapper(ToolWrapper):
    BINARY = "scan4all"; TOOL_NAME = "Scan4All"; TIMEOUT = 600
    INSTALL_CMD = "go install github.com/hktalent/scan4all@latest"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "-t", target, "-tp", "4", "-o", "json"]
        if options.get("no_poc"): cmd.append("-noPoc")
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        findings = []
        for line in raw.splitlines():
            try:
                item = json.loads(line)
                findings.append(item)
            except Exception:
                if line.strip() and "[" in line: findings.append({"raw": line.strip()})
        return {"findings": findings, "count": len(findings), "target": target}

