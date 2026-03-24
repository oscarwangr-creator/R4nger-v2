"""RedTeam Framework - Module: osint/username_enum"""
from __future__ import annotations
import re
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class UsernameEnumModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"username_enum","description":"Search for a username across 300+ social networks using Sherlock.","author":"RTF Core Team","category":"osint","version":"1.1","references":["https://github.com/sherlock-project/sherlock"]}

    def _declare_options(self) -> None:
        self._register_option("username","Target username to search",required=True)
        self._register_option("timeout","HTTP timeout per site in seconds",required=False,default=10,type=int)
        self._register_option("output_file","Save results to file",required=False,default="")
        self._register_option("tor","Route through Tor",required=False,default=False,type=bool)

    async def run(self) -> ModuleResult:
        username: str = self.get("username")
        timeout: int = self.get("timeout")
        output_file: str = self.get("output_file")
        use_tor: bool = self.get("tor")
        self.require_tool("sherlock")
        cmd = ["sherlock",username,"--timeout",str(timeout),"--print-found"]
        if use_tor:
            cmd += ["--tor"]
        if output_file:
            cmd += ["--output",output_file]
        stdout, stderr, rc = await self.run_command_async(cmd, timeout=600)
        found_urls: List[str] = []
        for line in stdout.splitlines():
            m = re.match(r"\[\+\]\s+\S+:\s+(https?://\S+)", line.strip())
            if m:
                found_urls.append(m.group(1))
        findings: List[Finding] = []
        for url in found_urls:
            findings.append(self.make_finding(title=f"Account found: {username} @ {url}",target=username,severity=Severity.INFO,description=f"Username '{username}' discovered on: {url}",evidence={"url":url,"username":username},tags=["osint","username","social-media"]))
        self.log.info(f"Found {len(found_urls)} accounts for '{username}'")
        return ModuleResult(success=True,output={"username":username,"accounts":found_urls,"total":len(found_urls)},findings=findings,raw_output=stdout)
