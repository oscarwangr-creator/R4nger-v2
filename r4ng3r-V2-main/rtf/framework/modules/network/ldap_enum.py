"""RedTeam Framework - Module: network/ldap_enum — AD LDAP enumeration"""
from __future__ import annotations
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class LDAPEnumModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"ldap_enum","description":"Active Directory LDAP enumeration: users, groups, domain admins, password policy, GPOs.","author":"RTF Core Team","category":"network","version":"1.1","tags":["ldap","active_directory","enumeration"]}
    def _declare_options(self) -> None:
        self._register_option("dc_ip","Domain Controller IP",required=True)
        self._register_option("domain","Domain FQDN (e.g. corp.local)",required=True)
        self._register_option("username","Bind username (DOMAIN\\user or user@domain)",required=True)
        self._register_option("password","Bind password",required=True)
        self._register_option("checks","Comma-separated: users,admins,policy,gpos,computers,spns",required=False,default="users,admins,policy,computers")
        self._register_option("use_ssl","Use LDAPS (port 636)",required=False,default=False,type=bool)
        self._register_option("output_file","Save JSON results",required=False,default="")
    async def run(self) -> ModuleResult:
        dc_ip=self.get("dc_ip"); domain=self.get("domain")
        username=self.get("username"); password=self.get("password")
        checks=[c.strip() for c in self.get("checks").split(",")]
        use_ssl=self.get("use_ssl"); output_file=self.get("output_file")
        results={}; findings=[]
        try:
            import ldap3
        except ImportError:
            return ModuleResult(success=False,error="ldap3 not installed. Run: pip install ldap3")
        try:
            server=ldap3.Server(dc_ip,use_ssl=use_ssl,get_info=ldap3.ALL)
            conn=ldap3.Connection(server,user=username,password=password,auto_bind=True)
            dn_parts=domain.split(".")
            base_dn=",".join(f"DC={p}" for p in dn_parts)
            if "users" in checks:
                conn.search(base_dn,"(objectClass=user)",attributes=["sAMAccountName","displayName","mail","pwdLastSet","userAccountControl","lastLogon"])
                users=[{"sam":str(e.sAMAccountName),"display":str(e.displayName),"mail":str(e.mail)} for e in conn.entries]
                results["users"]=users; results["user_count"]=len(users)
                if users:
                    findings.append(self.make_finding(title=f"LDAP: {len(users)} domain users enumerated",target=dc_ip,severity=Severity.MEDIUM,description=f"Enumerated {len(users)} domain users.",evidence={"count":len(users)},tags=["ldap","users","active_directory"]))
                # Find accounts with no expiry or disabled
                conn.search(base_dn,"(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=65536))",attributes=["sAMAccountName"])
                no_exp=[str(e.sAMAccountName) for e in conn.entries]
                if no_exp:
                    findings.append(self.make_finding(title=f"AD: {len(no_exp)} accounts with non-expiring passwords",target=dc_ip,severity=Severity.MEDIUM,description=f"Accounts: {no_exp[:10]}",evidence={"accounts":no_exp},tags=["ldap","password_policy"]))
            if "admins" in checks:
                conn.search(base_dn,"(&(objectClass=group)(cn=Domain Admins))",attributes=["member"])
                if conn.entries:
                    members=conn.entries[0].member.values if hasattr(conn.entries[0].member,"values") else list(conn.entries[0].member)
                    results["domain_admins"]=[str(m) for m in members]
                    findings.append(self.make_finding(title=f"Domain Admins group: {len(members)} members",target=dc_ip,severity=Severity.HIGH,description=f"Domain Admins: {results['domain_admins'][:10]}",evidence={"members":results["domain_admins"]},tags=["ldap","domain_admins","privilege"]))
            if "policy" in checks:
                conn.search(base_dn,"(objectClass=domainDNS)",attributes=["minPwdLength","lockoutThreshold","maxPwdAge","minPwdAge"])
                if conn.entries:
                    e=conn.entries[0]
                    policy={"min_password_length":int(str(e.minPwdLength)) if e.minPwdLength else 0,"lockout_threshold":int(str(e.lockoutThreshold)) if e.lockoutThreshold else 0}
                    results["password_policy"]=policy
                    if policy.get("min_password_length",0) < 10:
                        findings.append(self.make_finding(title=f"Weak password policy: min length {policy.get('min_password_length')}",target=dc_ip,severity=Severity.MEDIUM,description="Domain password policy has low minimum length.",evidence=policy,tags=["ldap","password_policy","weak"]))
                    if policy.get("lockout_threshold",0) == 0:
                        findings.append(self.make_finding(title="No account lockout policy configured",target=dc_ip,severity=Severity.HIGH,description="Account lockout threshold is 0, allowing unlimited password attempts.",evidence=policy,tags=["ldap","lockout","brute_force"]))
            conn.unbind()
        except Exception as exc:
            return ModuleResult(success=False,error=f"LDAP error: {exc}")
        import json as _json
        if output_file:
            with open(output_file,"w") as fh: _json.dump(results,fh,indent=2,default=str)
        return ModuleResult(success=True,output=results,findings=findings)
