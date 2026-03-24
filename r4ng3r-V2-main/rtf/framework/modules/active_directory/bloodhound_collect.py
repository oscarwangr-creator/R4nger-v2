"""RedTeam Framework - Module: active_directory/bloodhound_collect"""
from __future__ import annotations
import os
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class BloodHoundCollectModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"bloodhound_collect","description":"Collect Active Directory data for BloodHound via bloodhound-python.","author":"RTF Core Team","category":"active_directory","version":"1.0","references":["https://github.com/dirkjanm/BloodHound.py"]}
    def _declare_options(self) -> None:
        self._register_option("domain","AD domain FQDN",required=True)
        self._register_option("dc_ip","Domain Controller IP",required=True)
        self._register_option("username","Domain username",required=True)
        self._register_option("password","Domain password",required=True)
        self._register_option("collection_method","Collection methods",required=False,default="All",choices=["All","DCOnly","Session","LoggedOn","Trusts","Default"])
        self._register_option("output_dir","Directory to save BloodHound JSON zip",required=False,default="/tmp/bloodhound_output")
        self._register_option("timeout","Collection timeout in seconds",required=False,default=3600,type=int)
    async def run(self) -> ModuleResult:
        domain=self.get("domain"); dc_ip=self.get("dc_ip"); username=self.get("username")
        password=self.get("password"); collection=self.get("collection_method")
        output_dir=self.get("output_dir"); timeout=self.get("timeout")
        os.makedirs(output_dir, exist_ok=True)
        self.require_tool("bloodhound-python")
        cmd=["bloodhound-python","-d",domain,"-u",username,"-p",password,"-dc",dc_ip,"-c",collection,"--zip","-o",output_dir]
        stdout,stderr,rc = await self.run_command_async(cmd, timeout=timeout)
        if rc != 0:
            return ModuleResult(success=False,error=f"bloodhound-python failed (rc={rc}): {stderr[:500]}")
        zip_files=[os.path.join(output_dir,f) for f in os.listdir(output_dir) if f.endswith(".zip")]
        findings=[self.make_finding(title=f"BloodHound data collected from {domain}",target=domain,severity=Severity.HIGH,description=f"AD enumeration completed. Collection: {collection}. Output: {output_dir}",evidence={"domain":domain,"dc_ip":dc_ip,"zip_files":zip_files},tags=["active_directory","bloodhound"])]
        return ModuleResult(success=True,output={"domain":domain,"output_dir":output_dir,"zip_files":zip_files},findings=findings,raw_output=stdout)
