"""RedTeam Framework - Module: recon/nuclei_scan"""
from __future__ import annotations
import json, os
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

_SEVERITY_MAP = {"critical":Severity.CRITICAL,"high":Severity.HIGH,"medium":Severity.MEDIUM,"low":Severity.LOW,"info":Severity.INFO}

class NucleiScanModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"nuclei_scan","description":"Template-based vulnerability scanning with Nuclei.","author":"RTF Core Team","category":"recon","version":"1.2","references":["https://github.com/projectdiscovery/nuclei"]}

    def _declare_options(self) -> None:
        self._register_option("targets","Comma-separated URLs/hosts or path to a file",required=True)
        self._register_option("severity","Comma-separated severity filter",required=False,default="critical,high,medium")
        self._register_option("tags","Comma-separated template tags",required=False,default="")
        self._register_option("templates_dir","Path to nuclei-templates directory",required=False,default="")
        self._register_option("rate_limit","Max requests per second",required=False,default=150,type=int)
        self._register_option("concurrency","Number of concurrent templates",required=False,default=25,type=int)
        self._register_option("output_file","Save raw JSON output to file",required=False,default="")
        self._register_option("timeout","Scan timeout in seconds",required=False,default=1800,type=int)

    async def run(self) -> ModuleResult:
        self.require_tool("nuclei")
        targets: str = self.get("targets")
        severity: str = self.get("severity")
        tags: str = self.get("tags")
        templates_dir: str = self.get("templates_dir")
        rate_limit: int = self.get("rate_limit")
        concurrency: int = self.get("concurrency")
        output_file: str = self.get("output_file")
        timeout: int = self.get("timeout")
        json_out = output_file or "/tmp/nuclei_rtf_out.json"
        cmd = ["nuclei","-json-export",json_out,"-silent","-no-color","-rate-limit",str(rate_limit),"-concurrency",str(concurrency),"-severity",severity]
        if os.path.isfile(targets):
            cmd += ["-l",targets]
        else:
            for t in targets.split(","):
                t = t.strip()
                if t:
                    cmd += ["-u",t]
        if tags:
            cmd += ["-tags",tags]
        if templates_dir and os.path.isdir(templates_dir):
            cmd += ["-t",templates_dir]
        stdout, stderr, rc = await self.run_command_async(cmd, timeout=timeout)
        findings: List[Finding] = []
        parsed: List[Dict] = []
        raw_json = stdout
        if os.path.exists(json_out):
            try:
                with open(json_out) as fh:
                    raw_json = fh.read()
            except Exception:
                pass
        for line in raw_json.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                parsed.append(entry)
                findings.append(self._entry_to_finding(entry))
            except json.JSONDecodeError:
                continue
        self.log.info(f"Nuclei: {len(findings)} findings (severity filter: {severity})")
        return ModuleResult(success=True,output={"findings_count":len(findings),"results":parsed},findings=findings,raw_output=stderr)

    def _entry_to_finding(self, entry: Dict) -> Finding:
        info_block = entry.get("info", {})
        severity_str = info_block.get("severity", "info").lower()
        severity = _SEVERITY_MAP.get(severity_str, Severity.INFO)
        return self.make_finding(title=info_block.get("name",entry.get("template-id","Unknown")),target=entry.get("host",entry.get("matched-at","unknown")),severity=severity,description=info_block.get("description",""),evidence={"template_id":entry.get("template-id"),"matched_at":entry.get("matched-at"),"curl_command":entry.get("curl-command")},tags=["nuclei"]+info_block.get("tags","").split(","))
