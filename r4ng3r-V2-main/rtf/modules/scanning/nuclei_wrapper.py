"""RTF — Scanning: Nuclei template-based scanner"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class NucleiWrapper(ToolWrapper):
    BINARY = "nuclei"; TOOL_NAME = "Nuclei"; TIMEOUT = 600
    INSTALL_CMD = "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "-u", target, "-j", "-silent"]
        if options.get("severity"): cmd += ["-s", options["severity"]]
        if options.get("tags"):     cmd += ["-tags", options["tags"]]
        if options.get("templates"):cmd += ["-t", options["templates"]]
        if options.get("rate"):     cmd += ["-rl", str(options["rate"])]
        if options.get("concurrency"): cmd += ["-c", str(options["concurrency"])]
        if options.get("exclude_tags"): cmd += ["-etags", options["exclude_tags"]]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        findings = []
        for line in raw.splitlines():
            try:
                item = json.loads(line)
                findings.append({
                    "template_id": item.get("template-id",""),
                    "name": item.get("info",{}).get("name",""),
                    "severity": item.get("info",{}).get("severity","info"),
                    "url": item.get("matched-at",""),
                    "description": item.get("info",{}).get("description",""),
                    "tags": item.get("info",{}).get("tags",[]),
                    "cvss": item.get("info",{}).get("classification",{}).get("cvss-score",""),
                })
            except Exception: pass
        by_severity: Dict[str,int] = {}
        for f in findings:
            s = f["severity"]
            by_severity[s] = by_severity.get(s,0) + 1
        return {"findings": findings, "count": len(findings), "by_severity": by_severity, "target": target}

