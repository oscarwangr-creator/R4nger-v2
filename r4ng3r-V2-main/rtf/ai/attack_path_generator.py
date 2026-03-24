"""RTF v2.0 — AI: Attack Path Generator (rule-based + Claude AI)"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

MITRE_CHAINS = {
    "external_to_rce": {
        "name": "External → RCE",
        "steps": ["Subdomain/port recon","Identify exposed web services",
                  "Exploit public-facing application (T1190)","Web shell/RCE",
                  "Establish C2 foothold"],
        "mitre": ["TA0043","T1190","T1059","TA0011"],
        "tools": ["nuclei","sqlmap","dalfox","metasploit"],
    },
    "ad_kerberoast": {
        "name": "Kerberoasting → Domain Admin",
        "steps": ["LDAP enum for SPNs (T1558.003)","Request TGS tickets",
                  "Offline hash cracking","Use cracked creds for lateral movement",
                  "BloodHound path to Domain Admin","DCSync / pass-the-hash"],
        "mitre": ["T1558.003","T1110.002","T1550.002","T1003.006"],
        "tools": ["kerbrute","impacket","hashcat","bloodhound"],
    },
    "phishing_to_da": {
        "name": "Spearphishing → Domain Admin",
        "steps": ["OSINT for target emails","Craft phishing email (T1566.001)",
                  "Initial access via macro/link","Privilege escalation (T1068)",
                  "Lateral movement (T1021)","Domain Admin persistence"],
        "mitre": ["TA0043","T1566.001","T1068","T1021","TA0003"],
        "tools": ["theharvester","identity_fusion","metasploit"],
    },
    "cloud_escalation": {
        "name": "Cloud Misconfiguration → Full Account Compromise",
        "steps": ["Discover public S3 / exposed metadata","Extract IAM keys (T1552.005)",
                  "Enumerate permissions (T1580)","Privilege escalation via IAM",
                  "Data exfiltration"],
        "mitre": ["T1580","T1552.005","T1537"],
        "tools": ["aws_enum","pacu","prowler"],
    },
    "supply_chain": {
        "name": "Supply Chain → Persistent Access",
        "steps": ["Code repo recon (GitHub/GitLab)","Find leaked secrets (T1552.001)",
                  "Access internal systems via token","Implant backdoor in dependency"],
        "mitre": ["TA0043","T1552.001","T1195"],
        "tools": ["trufflehog","gitleaks","gitfive"],
    },
}

class AttackPathGenerator:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def generate_from_findings(self, findings: List[Dict], entities: Dict,
                                target: str = "") -> List[Dict]:
        """Generate attack paths from findings and entity data."""
        paths: List[Dict] = []
        # Rule-based path selection from finding tags
        all_tags = set()
        sev_counts: Dict[str,int] = {}
        for f in findings:
            for t in f.get("tags",[]):
                all_tags.add(str(t).lower())
            sev = str(f.get("severity","info")).lower()
            sev_counts[sev] = sev_counts.get(sev,0)+1

        if any(t in all_tags for t in ("sqli","xss","rce","web","api")):
            paths.append(dict(MITRE_CHAINS["external_to_rce"],
                              likelihood="HIGH" if sev_counts.get("critical",0)>0 else "MEDIUM",
                              impact="CRITICAL"))
        if any(t in all_tags for t in ("kerberoast","ad","ldap","bloodhound")):
            paths.append(dict(MITRE_CHAINS["ad_kerberoast"],
                              likelihood="HIGH", impact="CRITICAL"))
        if any(t in all_tags for t in ("cloud","aws","azure","gcp","s3","iam")):
            paths.append(dict(MITRE_CHAINS["cloud_escalation"],
                              likelihood="MEDIUM", impact="HIGH"))
        if any(t in all_tags for t in ("github","git","secret","leak","trufflehog")):
            paths.append(dict(MITRE_CHAINS["supply_chain"],
                              likelihood="MEDIUM", impact="HIGH"))
        if any(t in all_tags for t in ("email","osint","phish")):
            paths.append(dict(MITRE_CHAINS["phishing_to_da"],
                              likelihood="MEDIUM", impact="CRITICAL"))

        # Enhance with Claude if available
        if self.api_key and findings:
            try:
                from ai.claude_integration import ClaudeCorrelationEngine
                engine = ClaudeCorrelationEngine(self.api_key)
                ai_paths = engine.generate_attack_path({
                    "target": target, "findings": findings[:10], "entities": entities,
                })
                if ai_paths:
                    for ap in ai_paths:
                        ap["ai_generated"] = True
                    paths = ai_paths + paths  # AI paths first
            except Exception:
                pass

        # Deduplicate by name
        seen, deduped = set(), []
        for ap in paths:
            n = ap.get("name","")
            if n not in seen:
                seen.add(n); deduped.append(ap)
        return deduped[:8]

    def get_all_chains(self) -> List[Dict]:
        """Return all built-in MITRE attack chains."""
        return [{"id": k, **v} for k,v in MITRE_CHAINS.items()]

    def get_chain(self, chain_id: str) -> Optional[Dict]:
        chain = MITRE_CHAINS.get(chain_id)
        return {"id": chain_id, **chain} if chain else None
