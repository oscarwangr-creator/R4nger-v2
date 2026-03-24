"""RedTeam Framework - Module: cloud/azure_enum — Azure AD/Entra enumeration"""
from __future__ import annotations
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class AzureEnumModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"azure_enum","description":"Enumerate Azure AD/Entra ID: users, groups, apps, service principals, subscriptions, storage. Uses MSAL/azure-mgmt.","author":"RTF Core Team","category":"cloud","version":"1.1","tags":["azure","cloud","entra","enumeration"]}
    def _declare_options(self) -> None:
        self._register_option("tenant_id","Azure Tenant ID",required=True)
        self._register_option("client_id","Application (client) ID",required=True)
        self._register_option("client_secret","Client secret or use device_code",required=False,default="")
        self._register_option("checks","Comma-separated: users,groups,apps,subscriptions,storage",required=False,default="users,groups,apps,subscriptions")
        self._register_option("output_file","Save JSON results",required=False,default="")
        self._register_option("timeout","Timeout in seconds",required=False,default=300,type=int)
    async def run(self) -> ModuleResult:
        tenant_id=self.get("tenant_id"); client_id=self.get("client_id"); client_secret=self.get("client_secret")
        checks=[c.strip() for c in self.get("checks").split(",")]; output_file=self.get("output_file")
        results={}; findings=[]
        try:
            import msal, httpx
        except ImportError:
            return ModuleResult(success=False,error="msal/httpx not installed. Run: pip install msal httpx")
        try:
            if client_secret:
                app = msal.ConfidentialClientApplication(client_id,authority=f"https://login.microsoftonline.com/{tenant_id}",client_credential=client_secret)
                token_result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            else:
                app = msal.PublicClientApplication(client_id,authority=f"https://login.microsoftonline.com/{tenant_id}")
                flow = app.initiate_device_flow(scopes=["https://graph.microsoft.com/.default"])
                self.log.info(f"Device code: {flow.get('message','')}")
                token_result = app.acquire_token_by_device_flow(flow)
            if "access_token" not in token_result:
                return ModuleResult(success=False,error=f"Failed to acquire token: {token_result.get('error_description','unknown')}")
            token = token_result["access_token"]
            graph_base = "https://graph.microsoft.com/v1.0"
            headers = {"Authorization":f"Bearer {token}","Content-Type":"application/json"}
            async with httpx.AsyncClient(timeout=60,headers=headers) as client:
                if "users" in checks:
                    r=await client.get(f"{graph_base}/users?$top=100&$select=displayName,userPrincipalName,jobTitle,department,accountEnabled")
                    if r.status_code==200:
                        users=r.json().get("value",[])
                        results["users"]=[{"name":u.get("displayName"),"upn":u.get("userPrincipalName"),"enabled":u.get("accountEnabled")} for u in users]
                        if users:
                            findings.append(self.make_finding(title=f"Azure AD: {len(users)} users enumerated",target="azure:users",severity=Severity.MEDIUM,description=f"Enumerated {len(users)} Azure AD users.",evidence={"user_count":len(users)},tags=["azure","users","enumeration"]))
                if "groups" in checks:
                    r=await client.get(f"{graph_base}/groups?$top=100&$select=displayName,mailEnabled,securityEnabled,description")
                    if r.status_code==200:
                        groups=r.json().get("value",[])
                        results["groups"]=[g.get("displayName") for g in groups]
                if "apps" in checks:
                    r=await client.get(f"{graph_base}/applications?$top=100&$select=displayName,appId,signInAudience")
                    if r.status_code==200:
                        apps=r.json().get("value",[])
                        results["applications"]=[{"name":a.get("displayName"),"appId":a.get("appId"),"audience":a.get("signInAudience")} for a in apps]
                        public_apps=[a for a in results.get("applications",[]) if "AzureAD" not in (a.get("audience") or "")]
                        if public_apps:
                            findings.append(self.make_finding(title=f"Azure: {len(public_apps)} apps with broad sign-in audience",target="azure:apps",severity=Severity.HIGH,description="Applications allow sign-in from multiple tenants or personal accounts.",evidence={"apps":public_apps[:5]},tags=["azure","apps","exposure"]))
        except Exception as exc:
            return ModuleResult(success=False,error=str(exc))
        import json as _json
        if output_file:
            with open(output_file,"w") as fh: _json.dump(results,fh,indent=2)
        return ModuleResult(success=True,output=results,findings=findings)
