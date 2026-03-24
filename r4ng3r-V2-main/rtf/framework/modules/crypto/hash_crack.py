"""RedTeam Framework - Module: crypto/hash_crack"""
from __future__ import annotations
import os
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

_HASH_MODES={"md5":"0","sha1":"100","sha256":"1400","sha512":"1700","ntlm":"1000","netntlmv1":"5500","netntlmv2":"5600","bcrypt":"3200","kerberoast":"13100","asreproast":"18200","wpa2":"22000"}
_ATTACK_MODES={"dictionary":"0","combinator":"1","bruteforce":"3","hybrid_wordlist_mask":"6","hybrid_mask_wordlist":"7"}

class HashCrackModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"hash_crack","description":"GPU/CPU accelerated offline password cracking using hashcat.","author":"RTF Core Team","category":"crypto","version":"1.1"}
    def _declare_options(self) -> None:
        self._register_option("hash_file","Path to file containing hashes (one per line)",required=True)
        self._register_option("hash_type",f"Hash type: {', '.join(_HASH_MODES.keys())} or hashcat mode number",required=True)
        self._register_option("wordlist","Path to wordlist file",required=False,default="/usr/share/wordlists/rockyou.txt")
        self._register_option("rules","Path to hashcat rules file",required=False,default="")
        self._register_option("attack_mode","Attack mode",required=False,default="dictionary",choices=list(_ATTACK_MODES.keys()))
        self._register_option("mask","Mask for brute-force",required=False,default="")
        self._register_option("workload","Workload profile (1-4)",required=False,default=2,type=int)
        self._register_option("output_file","Save cracked hashes to file",required=False,default="")
        self._register_option("timeout","Cracking timeout in seconds",required=False,default=3600,type=int)
    async def run(self) -> ModuleResult:
        hash_file=self.get("hash_file"); hash_type_raw=self.get("hash_type"); wordlist=self.get("wordlist")
        rules=self.get("rules"); attack_mode=self.get("attack_mode"); mask=self.get("mask")
        workload=self.get("workload"); output_file=self.get("output_file"); timeout=self.get("timeout")
        self.require_tool("hashcat")
        if not os.path.exists(hash_file):
            return ModuleResult(success=False,error=f"Hash file not found: {hash_file}")
        mode=_HASH_MODES.get(hash_type_raw.lower(),hash_type_raw)
        attack_mode_num=_ATTACK_MODES.get(attack_mode,"0")
        pot_file=output_file or f"/tmp/hashcat_{abs(hash(hash_file))}.pot"
        cmd=["hashcat",f"--hash-type={mode}",f"--attack-mode={attack_mode_num}",f"--workload-profile={workload}",f"--potfile-path={pot_file}","--status","--status-timer=30",hash_file]
        if attack_mode in ("dictionary","hybrid_wordlist_mask","combinator"): cmd.append(wordlist)
        if mask or attack_mode=="bruteforce": cmd.append(mask or "?a?a?a?a?a?a?a?a")
        if rules and os.path.exists(rules): cmd+=["-r",rules]
        stdout,stderr,rc = await self.run_command_async(cmd, timeout=timeout)
        cracked=self._parse_potfile(pot_file)
        findings=[]
        if cracked:
            findings.append(self.make_finding(title=f"Passwords cracked: {len(cracked)} hashes",target=hash_file,severity=Severity.CRITICAL,description=f"{len(cracked)} hash(es) cracked from {hash_file} using {hash_type_raw} mode.",evidence={"cracked_count":len(cracked),"sample":cracked[:3],"potfile":pot_file},tags=["crypto","password-cracking","hash"]))
        return ModuleResult(success=True,output={"cracked":len(cracked),"potfile":pot_file,"results":cracked},findings=findings,raw_output=stdout)
    @staticmethod
    def _parse_potfile(path: str) -> List[Dict[str, str]]:
        cracked=[]
        try:
            with open(path) as fh:
                for line in fh:
                    line=line.strip()
                    if ":" in line:
                        parts=line.rsplit(":",1)
                        if len(parts)==2: cracked.append({"hash":parts[0],"plaintext":parts[1]})
        except FileNotFoundError: pass
        return cracked
