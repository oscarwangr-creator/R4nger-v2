"""RedTeam Framework - Module: web/dir_fuzz"""
from __future__ import annotations
import json, os
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

_STATUS_SEV = {200:Severity.INFO,301:Severity.INFO,302:Severity.INFO,401:Severity.LOW,403:Severity.LOW,500:Severity.MEDIUM}

class DirFuzzModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"dir_fuzz","description":"High-speed directory/file fuzzing using ffuf.","author":"RTF Core Team","category":"web","version":"1.1"}
    def _declare_options(self) -> None:
        self._register_option("url","Target URL with FUZZ keyword",required=True)
        self._register_option("wordlist","Path to wordlist",required=False,default="/usr/share/seclists/Discovery/Web-Content/common.txt")
        self._register_option("extensions","Comma-separated extensions",required=False,default="")
        self._register_option("threads","Number of concurrent threads",required=False,default=40,type=int)
        self._register_option("rate","Max requests per second (0=unlimited)",required=False,default=0,type=int)
        self._register_option("filter_status","HTTP status codes to filter OUT",required=False,default="404,400")
        self._register_option("match_status","HTTP status codes to match",required=False,default="")
        self._register_option("recursive","Enable recursive fuzzing",required=False,default=False,type=bool)
        self._register_option("output_file","Save JSON output to file",required=False,default="")
        self._register_option("timeout","Scan timeout in seconds",required=False,default=600,type=int)
    async def run(self) -> ModuleResult:
        url=self.get("url"); wordlist=self.get("wordlist"); extensions=self.get("extensions")
        threads=self.get("threads"); rate=self.get("rate"); filter_status=self.get("filter_status")
        match_status=self.get("match_status"); recursive=self.get("recursive")
        output_file=self.get("output_file"); timeout=self.get("timeout")
        self.require_tool("ffuf")
        if not os.path.exists(wordlist):
            for alt in ["/usr/share/wordlists/dirb/common.txt","/usr/share/dirbuster/wordlists/directory-list-2.3-small.txt"]:
                if os.path.exists(alt): wordlist = alt; break
            else:
                return ModuleResult(success=False,error=f"Wordlist not found: {wordlist}")
        json_out = output_file or f"/tmp/ffuf_{abs(hash(url))}.json"
        cmd=["ffuf","-u",url,"-w",wordlist,"-t",str(threads),"-o",json_out,"-of","json","-noninteractive"]
        if extensions: cmd+=["-e",extensions]
        if rate > 0: cmd+=["-rate",str(rate)]
        if recursive: cmd+=["-recursion"]
        if match_status: cmd+=["-mc",match_status]
        elif filter_status: cmd+=["-fc",filter_status]
        stdout,stderr,rc = await self.run_command_async(cmd, timeout=timeout)
        results: List[Dict] = []
        if os.path.exists(json_out):
            try:
                with open(json_out) as fh: data=json.load(fh); results=data.get("results",[])
            except Exception: pass
        findings=[self.make_finding(title=f"[{r.get('status',0)}] {r.get('url','')}",target=url,severity=_STATUS_SEV.get(r.get('status',0),Severity.INFO),description=f"HTTP {r.get('status',0)} | Size: {r.get('length',0)}",evidence=r,tags=["web","fuzzing","directory"]) for r in results]
        self.log.info(f"ffuf found {len(results)} paths on {url}")
        return ModuleResult(success=True,output={"url":url,"results":results,"total":len(results)},findings=findings,raw_output=stdout)
