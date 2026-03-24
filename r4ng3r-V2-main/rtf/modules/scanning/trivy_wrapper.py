"""RTF — Scanning: Trivy container/code vulnerability scanner"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class TrivyWrapper(ToolWrapper):
    BINARY = "trivy"; TOOL_NAME = "Trivy"; TIMEOUT = 300
    INSTALL_CMD = "apt install trivy || brew install trivy"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        scan_type = options.get("type", "image")  # image, fs, repo, sbom
        cmd = [self.BINARY, scan_type, "--format", "json", "--quiet", target]
        if options.get("severity"):   cmd += ["--severity", options["severity"].upper()]
        if options.get("ignore_unfixed"): cmd.append("--ignore-unfixed")
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        vulnerabilities = []
        try:
            data = json.loads(raw)
            for result in data.get("Results", []):
                for vuln in result.get("Vulnerabilities", []):
                    vulnerabilities.append({
                        "cve": vuln.get("VulnerabilityID",""),
                        "package": vuln.get("PkgName",""),
                        "version": vuln.get("InstalledVersion",""),
                        "fixed": vuln.get("FixedVersion",""),
                        "severity": vuln.get("Severity",""),
                        "title": vuln.get("Title","")[:100],
                    })
        except Exception:
            vulnerabilities = [{"raw_line": l} for l in raw.splitlines() if "CRITICAL" in l or "HIGH" in l]
        by_severity: Dict[str,int] = {}
        for v in vulnerabilities:
            s = v.get("severity","UNKNOWN")
            by_severity[s] = by_severity.get(s,0) + 1
        return {"vulnerabilities": vulnerabilities, "count": len(vulnerabilities),
                "by_severity": by_severity, "target": target}

