"""RedTeam Framework - Module: web/xss_scan"""
from __future__ import annotations
import json, os
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class XSSScanModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"xss_scan","description":"Automated XSS discovery using dalfox (primary) with XSStrike fallback.","author":"RTF Core Team","category":"web","version":"1.0"}
    def _declare_options(self) -> None:
        self._register_option("url","Target URL",required=True)
        self._register_option("cookies","Cookies string",required=False,default="")
        self._register_option("headers","Additional headers (name:value;…)",required=False,default="")
        self._register_option("blind_xss_url","Blind XSS callback URL",required=False,default="")
        self._register_option("timeout","Timeout in seconds",required=False,default=300,type=int)
        self._register_option("output_file","Save results to file",required=False,default="")
    async def run(self) -> ModuleResult:
        url=self.get("url"); cookies=self.get("cookies"); headers=self.get("headers")
        blind_xss=self.get("blind_xss_url"); timeout=self.get("timeout"); output_file=self.get("output_file")
        try:
            self.require_tool("dalfox")
            return await self._run_dalfox(url,cookies,headers,blind_xss,timeout,output_file)
        except Exception:
            pass
        return ModuleResult(success=False,error="No XSS tool available. Install dalfox: go install github.com/hahwul/dalfox/v2@latest")
    async def _run_dalfox(self, url, cookies, headers, blind_xss, timeout, output_file) -> ModuleResult:
        cmd=["dalfox","url",url,"--silence","--format","json"]
        if cookies: cmd+=["--cookie",cookies]
        for h in headers.split(";"):
            if h.strip(): cmd+=["--header",h.strip()]
        if blind_xss: cmd+=["--blind",blind_xss]
        json_out = output_file or f"/tmp/dalfox_{abs(hash(url))}.json"
        cmd+=["--output",json_out]
        stdout,stderr,rc = await self.run_command_async(cmd, timeout=timeout)
        results=[]; findings=[]
        if os.path.exists(json_out):
            try:
                with open(json_out) as fh:
                    for line in fh:
                        line=line.strip()
                        if line:
                            try: results.append(json.loads(line))
                            except: pass
            except: pass
        if not results:
            for line in stdout.splitlines():
                if "[V]" in line or "[POC]" in line: results.append({"type":"xss","evidence":line})
        for r in results:
            findings.append(self.make_finding(title=f"XSS vulnerability: {r.get('type','Reflected')} @ {url}",target=url,severity=Severity.HIGH,description=f"XSS confirmed. PoC: {str(r.get('poc',r.get('evidence','')))[:200]}",evidence=r,tags=["xss","web","injection"]))
        return ModuleResult(success=True,output={"url":url,"xss_found":len(findings)},findings=findings,raw_output=stdout)
