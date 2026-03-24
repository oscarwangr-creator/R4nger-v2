"""RedTeam Framework - Module: web/api_security"""
from __future__ import annotations
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class APISecurityModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"api_security","description":"API security testing: security headers, dangerous HTTP methods, GraphQL introspection, Swagger/OpenAPI exposure.","author":"RTF Core Team","category":"web","version":"1.0"}
    def _declare_options(self) -> None:
        self._register_option("url","Target base URL",required=True)
        self._register_option("check_methods","Test dangerous HTTP methods",required=False,default=True,type=bool)
        self._register_option("check_graphql","Test GraphQL introspection",required=False,default=True,type=bool)
        self._register_option("check_swagger","Check for OpenAPI/Swagger exposure",required=False,default=True,type=bool)
        self._register_option("check_headers","Check security headers",required=False,default=True,type=bool)
        self._register_option("timeout","Timeout per request",required=False,default=30,type=int)
    async def run(self) -> ModuleResult:
        url=self.get("url").rstrip("/"); timeout=self.get("timeout")
        findings=[]; results={}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=timeout,verify=False,follow_redirects=True) as client:
                if self.get("check_headers"):
                    r=await client.get(url)
                    missing=[]
                    for h in ["Strict-Transport-Security","X-Content-Type-Options","X-Frame-Options","Content-Security-Policy","X-XSS-Protection"]:
                        if h.lower() not in {k.lower() for k in r.headers}:
                            missing.append(h)
                    results["missing_security_headers"]=missing
                    if missing:
                        findings.append(self.make_finding(title=f"Missing security headers ({len(missing)})",target=url,severity=Severity.MEDIUM,description=f"Missing: {', '.join(missing)}",evidence={"missing":missing},tags=["web","headers","security"]))
                if self.get("check_methods"):
                    dangerous=[]
                    for method in ["PUT","DELETE","TRACE","CONNECT","OPTIONS"]:
                        try:
                            r=await client.request(method,url)
                            if r.status_code not in (405,501):
                                dangerous.append({"method":method,"status":r.status_code})
                        except Exception: pass
                    if dangerous:
                        findings.append(self.make_finding(title=f"Dangerous HTTP methods enabled",target=url,severity=Severity.MEDIUM,description=f"Methods: {[d['method'] for d in dangerous]}",evidence={"methods":dangerous},tags=["web","methods","api"]))
                if self.get("check_graphql"):
                    for gql_path in ["/graphql","/api/graphql","/query"]:
                        try:
                            r=await client.post(url+gql_path,json={"query":"{__schema{types{name}}}"},headers={"Content-Type":"application/json"})
                            if r.status_code==200 and "__schema" in r.text:
                                findings.append(self.make_finding(title=f"GraphQL introspection enabled: {url+gql_path}",target=url+gql_path,severity=Severity.MEDIUM,description="GraphQL schema introspection is enabled, leaking API structure.",evidence={"path":gql_path},tags=["graphql","api","introspection"]))
                                break
                        except Exception: pass
                if self.get("check_swagger"):
                    for sw_path in ["/swagger.json","/openapi.json","/api-docs","/swagger-ui.html","/api/swagger.json","/v1/swagger.json","/v2/swagger.json"]:
                        try:
                            r=await client.get(url+sw_path)
                            if r.status_code==200 and any(k in r.text for k in ["swagger","openapi","paths"]):
                                findings.append(self.make_finding(title=f"API documentation exposed: {url+sw_path}",target=url+sw_path,severity=Severity.LOW,description="OpenAPI/Swagger documentation is publicly accessible.",evidence={"path":sw_path},tags=["swagger","openapi","disclosure"]))
                                break
                        except Exception: pass
        except ImportError:
            return ModuleResult(success=False,error="httpx not installed. Run: pip install httpx")
        except Exception as exc:
            return ModuleResult(success=False,error=str(exc))
        return ModuleResult(success=True,output=results,findings=findings)
