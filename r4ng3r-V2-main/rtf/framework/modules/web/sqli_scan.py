"""RedTeam Framework - Module: web/sqli_scan"""
from __future__ import annotations
import os
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class SQLiScanModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"sqli_scan","description":"Automated SQL injection detection using sqlmap.","author":"RTF Core Team","category":"web","version":"1.0"}
    def _declare_options(self) -> None:
        self._register_option("url","Target URL",required=True)
        self._register_option("data","POST data string",required=False,default="")
        self._register_option("cookies","Cookie string",required=False,default="")
        self._register_option("level","Sqlmap test level (1-5)",required=False,default=2,type=int)
        self._register_option("risk","Sqlmap risk level (1-3)",required=False,default=1,type=int)
        self._register_option("batch","Non-interactive mode",required=False,default=True,type=bool)
        self._register_option("threads","Number of threads",required=False,default=5,type=int)
        self._register_option("output_dir","Directory for sqlmap output",required=False,default="/tmp/sqlmap_output")
        self._register_option("timeout","Timeout in seconds",required=False,default=600,type=int)
    async def run(self) -> ModuleResult:
        url=self.get("url"); data=self.get("data"); cookies=self.get("cookies")
        level=self.get("level"); risk=self.get("risk"); batch=self.get("batch")
        threads=self.get("threads"); output_dir=self.get("output_dir"); timeout=self.get("timeout")
        self.require_tool("sqlmap"); os.makedirs(output_dir,exist_ok=True)
        cmd=["sqlmap","-u",url,f"--level={level}",f"--risk={risk}",f"--threads={threads}",f"--output-dir={output_dir}"]
        if batch: cmd.append("--batch")
        if data: cmd+=["--data",data]
        if cookies: cmd+=["--cookie",cookies]
        stdout,stderr,rc = await self.run_command_async(cmd, timeout=timeout)
        vulnerable=any(x in stdout for x in ["is vulnerable","appears to be injectable"])
        findings=[]
        if vulnerable:
            findings.append(self.make_finding(title=f"SQL Injection confirmed: {url}",target=url,severity=Severity.CRITICAL,description="SQL injection vulnerability detected. Review output_dir for details.",evidence={"url":url,"output_dir":output_dir},tags=["sqli","injection","web","critical"]))
        return ModuleResult(success=True,output={"vulnerable":vulnerable,"url":url,"output_dir":output_dir},findings=findings,raw_output=stdout)
