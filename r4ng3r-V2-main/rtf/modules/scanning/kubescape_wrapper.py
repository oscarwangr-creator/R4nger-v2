"""RTF — Scanning: Kubescape Kubernetes security scanner"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class KubescapeWrapper(ToolWrapper):
    BINARY = "kubescape"; TOOL_NAME = "Kubescape"; TIMEOUT = 300
    INSTALL_CMD = "curl -s https://raw.githubusercontent.com/kubescape/kubescape/master/install.sh | /bin/bash"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        framework = options.get("framework", "nsa")
        cmd = [self.BINARY, "scan", "framework", framework, "--format", "json",
               "--output", "/tmp/kubescape_out.json"]
        if target and target not in ("local","cluster"): cmd += ["--kubeconfig", target]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        import os
        out = "/tmp/kubescape_out.json"
        if os.path.exists(out):
            try:
                data = json.loads(open(out).read()); os.remove(out)
                failed = data.get("summaryDetails", {}).get("frameworks", [{}])[0].get("failedResources", 0)
                score  = data.get("summaryDetails", {}).get("complianceScore", 0)
                return {"compliance_score": score, "failed_resources": failed,
                        "full_report": data.get("results", [])[:20], "target": target}
            except Exception: pass
        return {"raw_lines": raw.splitlines()[:30], "target": target}

