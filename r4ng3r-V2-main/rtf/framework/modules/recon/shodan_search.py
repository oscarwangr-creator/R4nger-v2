"""RedTeam Framework - Module: recon/shodan_search"""
from __future__ import annotations
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class ShodanSearchModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"shodan_search","description":"Shodan IP/host lookup and dork search for exposed services and CVEs.","author":"RTF Core Team","category":"recon","version":"1.0","tags":["shodan","recon","exposure"]}
    def _declare_options(self) -> None:
        self._register_option("query","IP address, hostname, or Shodan dork query",required=True)
        self._register_option("api_key","Shodan API key",required=False,default="")
        self._register_option("mode","host|search|count",required=False,default="host",choices=["host","search","count"])
        self._register_option("limit","Max search results",required=False,default=10,type=int)
        self._register_option("output_file","Save JSON results",required=False,default="")
    async def run(self) -> ModuleResult:
        query=self.get("query"); api_key=self.get("api_key") or ""; mode=self.get("mode")
        limit=self.get("limit"); output_file=self.get("output_file")
        try:
            import shodan
        except ImportError:
            return ModuleResult(success=False,error="shodan not installed. Run: pip install shodan")
        if not api_key:
            try:
                from framework.core.config import config
                api_key=config.get("shodan_api_key","")
            except Exception: pass
        if not api_key:
            return ModuleResult(success=False,error="No Shodan API key provided. Set api_key option or shodan_api_key in config.")
        api=shodan.Shodan(api_key); results={}; findings=[]
        try:
            if mode=="host":
                host=api.host(query)
                results["ip"]=host.get("ip_str"); results["org"]=host.get("org"); results["country"]=host.get("country_name")
                results["os"]=host.get("os"); results["open_ports"]=[p.get("port") for p in host.get("data",[])]
                results["vulns"]=list(host.get("vulns",{}).keys())
                if results["vulns"]:
                    findings.append(self.make_finding(title=f"Shodan: {len(results['vulns'])} CVEs on {query}",target=query,severity=Severity.HIGH,description=f"CVEs: {', '.join(results['vulns'][:10])}",evidence={"ip":query,"vulns":results["vulns"]},tags=["shodan","cve","exposure"]))
                if results["open_ports"]:
                    findings.append(self.make_finding(title=f"Shodan: {len(results['open_ports'])} open ports on {query}",target=query,severity=Severity.INFO,description=f"Open ports: {results['open_ports']}",evidence=results,tags=["shodan","ports"]))
            elif mode=="search":
                search_results=api.search(query,limit=limit)
                results["total"]=search_results.get("total",0)
                results["matches"]=[{"ip":m.get("ip_str"),"port":m.get("port"),"org":m.get("org"),"vulns":list(m.get("vulns",{}).keys())} for m in search_results.get("matches",[])]
                for match in results["matches"]:
                    if match.get("vulns"):
                        findings.append(self.make_finding(title=f"Vulnerable host: {match.get('ip')}:{match.get('port')}",target=match.get("ip","?"),severity=Severity.HIGH,description=f"CVEs: {', '.join(match['vulns'])}",evidence=match,tags=["shodan","cve","exposure"]))
        except Exception as exc:
            return ModuleResult(success=False,error=f"Shodan API error: {exc}")
        import json as _json
        if output_file:
            with open(output_file,"w") as fh: _json.dump(results,fh,indent=2)
        return ModuleResult(success=True,output=results,findings=findings)
