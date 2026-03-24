"""RedTeam Framework - Module: osint/email_harvest"""
from __future__ import annotations
import json, os
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class EmailHarvestModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"email_harvest","description":"Harvest emails, subdomains, hosts from public sources using theHarvester.","author":"RTF Core Team","category":"osint","version":"1.1","references":["https://github.com/laramies/theHarvester"]}

    def _declare_options(self) -> None:
        self._register_option("domain","Target domain",required=True)
        self._register_option("sources","Comma-separated data sources (default: all)",required=False,default="all")
        self._register_option("limit","Max results per source",required=False,default=200,type=int)
        self._register_option("output_file","Save JSON output to file",required=False,default="")
        self._register_option("timeout","Timeout in seconds",required=False,default=600,type=int)

    async def run(self) -> ModuleResult:
        domain: str = self.get("domain")
        sources: str = self.get("sources")
        limit: int = self.get("limit")
        output_file: str = self.get("output_file")
        timeout: int = self.get("timeout")
        self.require_tool("theHarvester")
        json_out = output_file or f"/tmp/harvester_{domain}.json"
        cmd = ["theHarvester","-d",domain,"-l",str(limit),"-b",sources,"-f",json_out.replace(".json","")]
        stdout, stderr, rc = await self.run_command_async(cmd, timeout=timeout)
        emails: List[str] = []
        hosts: List[str] = []
        ips: List[str] = []
        if os.path.exists(json_out):
            try:
                with open(json_out) as fh:
                    data = json.load(fh)
                emails = data.get("emails", [])
                hosts = data.get("hosts", [])
                ips = data.get("ips", [])
            except Exception:
                pass
        if not emails and not hosts:
            for line in stdout.splitlines():
                line = line.strip()
                if "@" in line and domain in line:
                    emails.append(line)
                elif domain in line and "." in line:
                    hosts.append(line)
        findings: List[Finding] = []
        for email in set(emails):
            findings.append(self.make_finding(title=f"Email discovered: {email}",target=email,severity=Severity.INFO,description=f"Email associated with {domain}",evidence={"email":email,"domain":domain},tags=["osint","email"]))
        for host in set(hosts):
            findings.append(self.make_finding(title=f"Host discovered: {host}",target=host,severity=Severity.INFO,description=f"Host/subdomain of {domain}",evidence={"host":host},tags=["osint","host","subdomain"]))
        self.log.info(f"Harvest complete — emails: {len(emails)}, hosts: {len(hosts)}, IPs: {len(ips)}")
        return ModuleResult(success=True,output={"domain":domain,"emails":sorted(set(emails)),"hosts":sorted(set(hosts)),"ips":sorted(set(ips))},findings=findings,raw_output=stdout)
