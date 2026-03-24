"""
RTF v2.0 — Core Pipeline Orchestrator
Manages the full A-K engagement pipeline with entity graph integration.

Stages:
  A — Target normalization & entity graph init
  B — Passive + active reconnaissance
  C — OSINT correlation
  D — Vulnerability discovery
  E — Web exploitation scanning
  F — Credential attacks (with method recommendation)
  G — Exploitation (Metasploit)
  H — Post-exploitation (privesc + lateral movement)
  I — Threat intelligence enrichment
  J — AI correlation & attack path generation
  K — Multi-format reporting
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from core.entity_graph import EntityGraph, EntityType, RelationshipType, entity_graph as _default_graph


# ─────────────────────────────────────────────────────────────────────────────
# Stage result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StageResult:
    stage:      str
    success:    bool
    tools_run:  int  = 0
    tools_ok:   int  = 0
    findings:   List[Dict[str, Any]] = field(default_factory=list)
    entities:   Dict[str, int]       = field(default_factory=dict)
    data:       Dict[str, Any]       = field(default_factory=dict)
    errors:     List[str]            = field(default_factory=list)
    duration_s: float = 0.0
    skipped:    bool  = False
    skip_reason: str  = ""

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class PipelineResult:
    pipeline_id:  str
    target:       str
    profile:      str
    stages_run:   List[str]
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    findings:     List[Dict[str, Any]]    = field(default_factory=list)
    entity_graph: Optional[Dict]          = None
    attack_paths: str = ""
    report_files: List[str]               = field(default_factory=list)
    started_at:   str = ""
    finished_at:  str = ""
    total_duration_s: float = 0.0
    success:      bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = {k: v for k, v in self.__dict__.items() if k != "stage_results"}
        d["stage_results"] = {k: v.to_dict() for k, v in self.stage_results.items()}
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class PipelineOrchestrator:
    """
    Orchestrates the full A-K red team pipeline.

    Usage:
        from core.pipeline_orchestrator import PipelineOrchestrator
        orch = PipelineOrchestrator(profile="full")
        result = asyncio.run(orch.run({
            "domain":   "example.com",
            "username": "jsmith",
            "email":    "jsmith@example.com",
            "ip":       "10.0.0.1",
        }))
    """

    ALL_STAGES = ["A","B","C","D","E","F","G","H","I","J","K"]

    # Tool selections per profile
    PROFILES = {
        "core": {
            "B": ["subfinder","naabu"],
            "C": ["sherlock","holehe"],
            "D": ["nuclei"],
            "E": ["sqlmap","dalfox"],
            "F": ["hydra"],
            "G": ["metasploit"],
            "H": ["linenum"],
            "I": [],
        },
        "full": {
            "B": ["subfinder","amass","naabu","httprobe","gobuster","whatweb","ffuf"],
            "C": ["sherlock","maigret","holehe","phoneinfoga","osintgram","social-analyzer"],
            "D": ["nuclei","trivy","lynis","scan4all"],
            "E": ["sqlmap","dalfox","wpscan","wfuzz","commix","ssrfmap"],
            "F": ["hydra","kerbrute","hashcat"],
            "G": ["metasploit","kubesploit"],
            "H": ["bloodhound","linenum","evil-winrm"],
            "I": ["intelowl"],
        },
        "aggressive": {
            "B": ["subfinder","amass","naabu","httprobe","gobuster","ffuf","whatweb",
                  "dirsearch","photon","spiderfoot","vhostscan","assetfinder","altdns"],
            "C": ["sherlock","maigret","holehe","phoneinfoga","osintgram","social-analyzer",
                  "profil3r","intelligence-x"],
            "D": ["nuclei","trivy","lynis","kubescape","scan4all","openvas","vuls"],
            "E": ["sqlmap","dalfox","xsstrike","wpscan","wfuzz","commix","ssrfmap",
                  "nosqlmap","joomscan","droopescan","cmseek"],
            "F": ["hydra","kerbrute","hashcat","john","ncrack","brutespray"],
            "G": ["metasploit","autosploit","kubesploit","owtf"],
            "H": ["bloodhound","linenum","evil-winrm","winpwn"],
            "I": ["intelowl","threatingestor","ail-framework"],
        },
        "ai_autonomous": {
            # AI selects tools dynamically based on discovered data
            "B": "AI_SELECT", "C": "AI_SELECT", "D": "AI_SELECT",
            "E": "AI_SELECT", "F": "AI_SELECT", "G": "AI_SELECT",
            "H": "AI_SELECT", "I": "AI_SELECT",
        },
    }

    def __init__(
        self,
        profile:    str = "full",
        stages:     Optional[List[str]] = None,
        graph:      Optional[EntityGraph] = None,
        output_dir: str = "/tmp/rtf_pipeline",
        report_formats: List[str] = None,
        log_fn:     Optional[Callable] = None,
        interactive: bool = False,
    ) -> None:
        self.profile    = profile
        self.stages     = stages or self.ALL_STAGES
        self.graph      = graph or EntityGraph()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_formats = report_formats or ["json","html"]
        self.log         = log_fn or print
        self.interactive = interactive
        self._findings:  List[Dict[str, Any]] = []
        self._pipeline_id = str(uuid.uuid4())[:8]

    # ─── Main entry ──────────────────────────────────────────────────

    async def run(self, targets: Dict[str, str], options: Optional[Dict] = None) -> PipelineResult:
        """
        Run the pipeline for a set of targets.

        targets: {"domain":"example.com","ip":"10.0.0.1","email":"x@y.com","username":"x"}
        options: override per-stage options
        """
        options = options or {}
        t0 = time.monotonic()
        started = datetime.utcnow().isoformat()
        result = PipelineResult(
            pipeline_id=self._pipeline_id,
            target=targets.get("domain") or targets.get("ip") or "unknown",
            profile=self.profile,
            stages_run=self.stages,
            started_at=started,
        )

        self.log(f"\n{'='*60}")
        self.log(f"RTF Pipeline [{self._pipeline_id}] — Profile: {self.profile}")
        self.log(f"Target: {result.target} | Stages: {','.join(self.stages)}")
        self.log(f"{'='*60}\n")

        stage_map = {
            "A": self._stage_a_init,
            "B": self._stage_b_recon,
            "C": self._stage_c_osint,
            "D": self._stage_d_vuln_scan,
            "E": self._stage_e_web,
            "F": self._stage_f_credentials,
            "G": self._stage_g_exploitation,
            "H": self._stage_h_post_exploit,
            "I": self._stage_i_threat_intel,
            "J": self._stage_j_ai_correlation,
            "K": self._stage_k_reporting,
        }

        for stage_id in self.stages:
            fn = stage_map.get(stage_id)
            if not fn:
                self.log(f"[!] Unknown stage: {stage_id}")
                continue
            self.log(f"\n[Stage {stage_id}] Starting…")
            stage_t0 = time.monotonic()
            try:
                sr = await fn(targets, options)
                sr.duration_s = round(time.monotonic() - stage_t0, 2)
            except Exception as exc:
                sr = StageResult(stage=stage_id, success=False,
                                 errors=[str(exc)],
                                 duration_s=round(time.monotonic()-stage_t0,2))
                self.log(f"[Stage {stage_id}] ERROR: {exc}")
            result.stage_results[stage_id] = sr
            result.findings.extend(sr.findings)
            if sr.skipped:
                self.log(f"[Stage {stage_id}] Skipped: {sr.skip_reason}")
            else:
                self.log(f"[Stage {stage_id}] Done — {sr.tools_ok}/{sr.tools_run} tools OK | "
                         f"{len(sr.findings)} findings | {sr.duration_s}s")

        result.entity_graph = self.graph.to_dict()
        result.findings = self._findings
        result.finished_at = datetime.utcnow().isoformat()
        result.total_duration_s = round(time.monotonic() - t0, 2)

        self.log(f"\n{'='*60}")
        self.log(f"Pipeline complete in {result.total_duration_s}s")
        self.log(f"Total findings: {len(result.findings)}")
        self.log(self.graph.summary())

        return result

    # ─── Stage implementations ───────────────────────────────────────

    async def _stage_a_init(self, targets: Dict, options: Dict) -> StageResult:
        """Stage A: Normalize inputs, populate entity graph."""
        sr = StageResult(stage="A", success=True)
        mapping = {
            "domain":   EntityType.DOMAIN,
            "ip":       EntityType.IP,
            "email":    EntityType.EMAIL,
            "username": EntityType.USERNAME,
            "phone":    EntityType.PHONE,
        }
        for key, etype in mapping.items():
            val = targets.get(key,"").strip()
            if val:
                self.graph.add_entity(etype, val, source="seed", stage="A", confidence=1.0)
                sr.entities[etype.value] = sr.entities.get(etype.value,0) + 1
        sr.data["entities_initialized"] = sum(sr.entities.values())
        sr.data["graph_session"] = self.graph.session_id
        return sr

    async def _stage_b_recon(self, targets: Dict, options: Dict) -> StageResult:
        """Stage B: Passive recon (subfinder, amass) then active (naabu, httpx)."""
        sr = StageResult(stage="B", success=True)
        domain = targets.get("domain","")
        ip     = targets.get("ip","")
        if not domain and not ip:
            sr.skipped = True; sr.skip_reason = "No domain or IP target"; return sr

        tool_results = {}
        # Subfinder
        try:
            from modules.recon.subfinder_wrapper import SubfinderWrapper
            w = SubfinderWrapper()
            if w.is_installed() and domain:
                sr.tools_run += 1
                res = w.run(domain, options.get("subfinder",{}))
                if res.success:
                    sr.tools_ok += 1
                    subs = res.data.get("subdomains",[])
                    for s in subs:
                        self.graph.add_entity(EntityType.DOMAIN, s, source="subfinder", stage="B")
                    tool_results["subfinder"] = {"count": len(subs), "sample": subs[:5]}
        except Exception as e:
            sr.errors.append(f"subfinder: {e}")

        # Naabu port scan
        try:
            from modules.recon.naabu_wrapper import NaabuWrapper
            w = NaabuWrapper()
            scan_target = ip or domain
            if w.is_installed() and scan_target:
                sr.tools_run += 1
                res = w.run(scan_target, options.get("naabu",{"ports":"top-100"}))
                if res.success:
                    sr.tools_ok += 1
                    ports = res.data.get("open_ports",[])
                    for p in ports:
                        self.graph.add_entity(EntityType.SERVICE,
                                              f"{scan_target}:{p['port']}", source="naabu", stage="B")
                    tool_results["naabu"] = {"open_ports": len(ports), "ports": ports[:20]}
                    sr.findings += [{"title":f"Open port {p['port']} on {scan_target}",
                                     "severity":"info","source":"naabu","data":p}
                                    for p in ports]
        except Exception as e:
            sr.errors.append(f"naabu: {e}")

        sr.data = tool_results
        sr.entities = self.graph.entity_count()
        return sr

    async def _stage_c_osint(self, targets: Dict, options: Dict) -> StageResult:
        """Stage C: OSINT correlation across all discovered entities."""
        sr = StageResult(stage="C", success=True)
        username = targets.get("username","")
        email    = targets.get("email","")
        tool_results = {}

        # Sherlock username search
        if username:
            try:
                from modules.osint.sherlock_wrapper import SherlockWrapper
                w = SherlockWrapper()
                if w.is_installed():
                    sr.tools_run += 1
                    res = w.run(username, options.get("sherlock",{}))
                    if res.success:
                        sr.tools_ok += 1
                        accts = res.data.get("accounts",[])
                        for a in accts:
                            self.graph.add_entity(EntityType.URL, a["url"],
                                                  source="sherlock", stage="C",
                                                  metadata={"platform": a.get("platform","")})
                        tool_results["sherlock"] = {"accounts_found": len(accts)}
                        sr.findings += [{"title":f"Account found on {a.get('platform','')}",
                                         "severity":"info","url":a.get("url",""),"source":"sherlock"}
                                        for a in accts]
            except Exception as e:
                sr.errors.append(f"sherlock: {e}")

        # Holehe email check
        if email:
            try:
                from modules.osint.holehe_wrapper import HoleheWrapper
                w = HoleheWrapper()
                if w.is_installed():
                    sr.tools_run += 1
                    res = w.run(email, options.get("holehe",{}))
                    if res.success:
                        sr.tools_ok += 1
                        regs = res.data.get("registered_on",[])
                        tool_results["holehe"] = {"registered_on": regs}
                        sr.findings += [{"title":f"Email registered on {site}",
                                         "severity":"info","source":"holehe"}
                                        for site in regs]
            except Exception as e:
                sr.errors.append(f"holehe: {e}")

        sr.data = tool_results
        sr.entities = self.graph.entity_count()
        return sr

    async def _stage_d_vuln_scan(self, targets: Dict, options: Dict) -> StageResult:
        """Stage D: Vulnerability discovery with Nuclei + Trivy."""
        sr = StageResult(stage="D", success=True)
        domain = targets.get("domain","")
        ip     = targets.get("ip","")
        scan_target = f"https://{domain}" if domain else ip
        if not scan_target:
            sr.skipped = True; sr.skip_reason = "No scan target"; return sr

        try:
            from modules.scanning.nuclei_wrapper import NucleiWrapper
            w = NucleiWrapper()
            if w.is_installed():
                sr.tools_run += 1
                sev = options.get("nuclei",{}).get("severity","critical,high,medium")
                res = w.run(scan_target, {"severity": sev})
                if res.success:
                    sr.tools_ok += 1
                    findings = res.data.get("findings",[])
                    for f in findings:
                        sr.findings.append({
                            "title": f.get("name",""),
                            "severity": f.get("severity","info"),
                            "url": f.get("url",""),
                            "template": f.get("template_id",""),
                            "source": "nuclei",
                        })
                    self._findings.extend(sr.findings)
                    sr.data["nuclei"] = {"count": len(findings),
                                         "by_severity": res.data.get("by_severity",{})}
        except Exception as e:
            sr.errors.append(f"nuclei: {e}")

        sr.entities = self.graph.entity_count()
        return sr

    async def _stage_e_web(self, targets: Dict, options: Dict) -> StageResult:
        """Stage E: Web exploitation scanning."""
        sr = StageResult(stage="E", success=True)
        domain = targets.get("domain","")
        url    = targets.get("url","") or (f"https://{domain}" if domain else "")
        if not url:
            sr.skipped = True; sr.skip_reason = "No URL target"; return sr

        try:
            from modules.web_exploitation.dalfox_wrapper import DalfoxWrapper
            w = DalfoxWrapper()
            if w.is_installed():
                sr.tools_run += 1
                res = w.run(url, options.get("dalfox",{}))
                if res.success:
                    sr.tools_ok += 1
                    if res.data.get("xss_found"):
                        vulns = res.data.get("vulnerabilities",[])
                        sr.findings += [{"title":"XSS vulnerability found","severity":"high",
                                         "url":url,"source":"dalfox","data":v} for v in vulns]
        except Exception as e:
            sr.errors.append(f"dalfox: {e}")

        self._findings.extend(sr.findings)
        sr.entities = self.graph.entity_count()
        return sr

    async def _stage_f_credentials(self, targets: Dict, options: Dict) -> StageResult:
        """
        Stage F: Credential attacks with method recommendation.
        Analyses discovered services and recommends the best attack method.
        Respects 'skip' flag in options.
        """
        sr = StageResult(stage="F", success=True)
        if options.get("skip_stage_f"):
            sr.skipped = True; sr.skip_reason = "Explicitly skipped by operator"; return sr

        # Analyse available attack vectors
        domain   = targets.get("domain","")
        ip       = targets.get("ip","")
        services = options.get("open_services",[])  # e.g. [{"port":22,"service":"ssh"}]

        recommendation = self._recommend_credential_attack(services, domain, ip)
        sr.data["recommendation"] = recommendation

        # In interactive mode, ask operator to confirm
        if self.interactive:
            self.log(f"\n[Stage F] Credential Attack Recommendation:")
            self.log(f"  Method: {recommendation['method']}")
            self.log(f"  Reason: {recommendation['reason']}")
            self.log(f"  Tools:  {', '.join(recommendation['tools'])}")
            self.log(f"  Options: {recommendation['options']}")
            if not options.get("auto_confirm"):
                self.log("  [Skipping credential attack — set 'auto_confirm':true to run]")
                sr.skipped = True
                sr.skip_reason = "Awaiting operator confirmation (interactive mode)"
                return sr

        # Execute recommended attack
        method = recommendation["method"]
        if method == "kerberoast":
            try:
                from modules.credential_attacks.kerbrute_wrapper import KerbruteWrapper
                w = KerbruteWrapper()
                if w.is_installed() and domain:
                    sr.tools_run += 1
                    res = w.run(domain, options.get("kerbrute",{"mode":"userenum"}))
                    if res.success:
                        sr.tools_ok += 1
                        users = res.data.get("valid_users",[])
                        sr.data["kerbrute"] = {"valid_users": users}
                        sr.findings += [{"title":f"Valid AD user found: {u}","severity":"medium",
                                         "source":"kerbrute"} for u in users]
            except Exception as e:
                sr.errors.append(f"kerbrute: {e}")
        elif method == "ssh_bruteforce":
            try:
                from modules.credential_attacks.hydra_wrapper import HydraWrapper
                w = HydraWrapper()
                if w.is_installed():
                    sr.tools_run += 1
                    res = w.run(ip or domain, options.get("hydra",{"service":"ssh"}))
                    if res.success:
                        sr.tools_ok += 1
                        cracked = res.data.get("cracked",[])
                        sr.findings += [{"title":f"Credential: {c['user']}:{c['pass']}",
                                         "severity":"critical","source":"hydra"} for c in cracked]
            except Exception as e:
                sr.errors.append(f"hydra: {e}")

        self._findings.extend(sr.findings)
        sr.entities = self.graph.entity_count()
        return sr

    def _recommend_credential_attack(
        self, services: List[Dict], domain: str, ip: str
    ) -> Dict[str, Any]:
        """Analyse services and recommend best credential attack method."""
        port_map = {s.get("port"):s.get("service","") for s in services}
        if 88 in port_map or 389 in port_map or 636 in port_map or domain.endswith(".local"):
            return {"method":"kerberoast","reason":"Kerberos/LDAP port detected — AD environment",
                    "tools":["kerbrute","impacket-GetUserSPNs"],
                    "options":{"mode":"userenum","then":"kerberoast_spn"}}
        if 22 in port_map:
            return {"method":"ssh_bruteforce","reason":"SSH port 22 is open",
                    "tools":["hydra","ncrack"],
                    "options":{"service":"ssh","wordlist":"rockyou.txt","threads":4}}
        if 3389 in port_map:
            return {"method":"rdp_bruteforce","reason":"RDP port 3389 is open",
                    "tools":["hydra","ncrack"],
                    "options":{"service":"rdp","threads":4}}
        if 21 in port_map:
            return {"method":"ftp_bruteforce","reason":"FTP port 21 is open",
                    "tools":["hydra"],
                    "options":{"service":"ftp"}}
        if 80 in port_map or 443 in port_map or 8080 in port_map:
            return {"method":"web_credential_stuffing",
                    "reason":"HTTP/HTTPS services found — try credential stuffing on login forms",
                    "tools":["hydra","wfuzz"],
                    "options":{"service":"http-post-form"}}
        return {"method":"dictionary_attack",
                "reason":"No specific service identified — generic dictionary attack",
                "tools":["hydra","john"],
                "options":{"wordlist":"rockyou.txt"}}

    async def _stage_g_exploitation(self, targets: Dict, options: Dict) -> StageResult:
        """Stage G: Exploitation using Metasploit."""
        sr = StageResult(stage="G", success=True)
        if not self._findings:
            sr.skipped = True; sr.skip_reason = "No findings to exploit"; return sr
        crit = [f for f in self._findings if f.get("severity") in ("critical","high")]
        if not crit:
            sr.skipped = True; sr.skip_reason = "No critical/high findings"; return sr

        try:
            from modules.exploitation_frameworks.metasploit_wrapper import MetasploitWrapper
            w = MetasploitWrapper()
            if w.is_installed() and options.get("enable_exploitation"):
                sr.tools_run += 1
                target = targets.get("ip") or targets.get("domain","")
                msf_opts = options.get("metasploit", {})
                res = w.run(target, msf_opts)
                if res.success:
                    sr.tools_ok += 1
                    sr.data["metasploit"] = res.data
                    if res.data.get("exploited"):
                        sr.findings.append({"title":"System compromised via Metasploit",
                                            "severity":"critical","source":"metasploit",
                                            "sessions": res.data.get("sessions",[])})
            else:
                sr.data["note"] = "Exploitation disabled. Set enable_exploitation=true to run."
                sr.skipped = True
                sr.skip_reason = "Exploitation not enabled (set enable_exploitation:true)"
        except Exception as e:
            sr.errors.append(f"metasploit: {e}")

        self._findings.extend(sr.findings)
        return sr

    async def _stage_h_post_exploit(self, targets: Dict, options: Dict) -> StageResult:
        """Stage H: Post-exploitation (privilege escalation + lateral movement)."""
        sr = StageResult(stage="H", success=True)
        sessions = options.get("sessions",[])
        if not sessions and not options.get("local_privesc"):
            sr.data["note"] = "No active sessions. Run linenum locally for privesc check."
        try:
            from modules.post_exploitation.linenum_wrapper import LinenumWrapper
            w = LinenumWrapper()
            if w.is_installed() and options.get("run_linenum"):
                sr.tools_run += 1
                res = w.run("localhost", options.get("linenum",{}))
                if res.success:
                    sr.tools_ok += 1
                    interesting = res.data.get("interesting",[])
                    sr.findings += [{"title":"Privilege escalation vector found",
                                     "severity":"high","source":"linenum","detail":i}
                                    for i in interesting[:10]]
        except Exception as e:
            sr.errors.append(f"linenum: {e}")

        self._findings.extend(sr.findings)
        return sr

    async def _stage_i_threat_intel(self, targets: Dict, options: Dict) -> StageResult:
        """Stage I: Threat intelligence enrichment."""
        sr = StageResult(stage="I", success=True)
        api_key = options.get("intelowl_api_key","")
        if not api_key:
            sr.data["note"] = "No IntelOwl API key. Configure with intelowl_api_key option."
            sr.skipped = True
            sr.skip_reason = "No TI API keys configured"
            return sr

        domain = targets.get("domain","")
        try:
            from modules.threat_intelligence.intelowl_wrapper import IntelOwlWrapper
            w = IntelOwlWrapper()
            sr.tools_run += 1
            res = w.run(domain, {"api_key": api_key, "classification": "domain",
                                  **options.get("intelowl",{})})
            if res.success:
                sr.tools_ok += 1
                sr.data["intelowl"] = res.data
        except Exception as e:
            sr.errors.append(f"intelowl: {e}")

        return sr

    async def _stage_j_ai_correlation(self, targets: Dict, options: Dict) -> StageResult:
        """Stage J: AI correlation, attack path generation, anomaly detection."""
        sr = StageResult(stage="J", success=True)
        # Attack path generation
        try:
            from modules.ai_analysis.attack_path_generator import AttackPathGenerator
            gen = AttackPathGenerator()
            res = gen.run(
                targets.get("domain",""),
                {"findings": self._findings[:30],
                 "entities": self.graph.entity_count(),
                 "graph_data": self.graph.to_dict()},
            )
            if res.success:
                sr.data["attack_paths"] = res.data.get("attack_paths","")
                sr.data["ai_source"]    = res.data.get("source","")
        except Exception as e:
            sr.errors.append(f"attack_path_gen: {e}")

        # Anomaly detection
        try:
            from modules.ai_analysis.anomaly_detection import AnomalyDetection
            det = AnomalyDetection()
            res = det.run("anomaly_check", {"findings": self._findings})
            if res.success:
                sr.data["anomalies"] = res.data.get("anomalies",[])
        except Exception as e:
            sr.errors.append(f"anomaly_detection: {e}")

        return sr

    async def _stage_k_reporting(self, targets: Dict, options: Dict) -> StageResult:
        """Stage K: Generate all report formats."""
        sr = StageResult(stage="K", success=True)
        out_dir = self.output_dir / self._pipeline_id
        out_dir.mkdir(parents=True, exist_ok=True)
        formats  = options.get("report_formats", self.report_formats)
        target   = targets.get("domain") or targets.get("ip","unknown")

        report_data = {
            "pipeline_id": self._pipeline_id,
            "target": target,
            "profile": self.profile,
            "findings": self._findings,
            "entities": self.graph.entity_count(),
            "entity_graph": self.graph.to_dict(),
            "generated_at": datetime.utcnow().isoformat(),
        }

        files = []
        for fmt in formats:
            fname = out_dir / f"report_{target.replace('.','_')}_{self._pipeline_id}.{fmt}"
            try:
                if fmt == "json":
                    fname.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")
                elif fmt == "html":
                    from reports.html_reporter import HtmlReporter
                    HtmlReporter().generate(report_data, str(fname))
                elif fmt == "pdf":
                    from reports.pdf_reporter import PdfReporter
                    PdfReporter().generate(report_data, str(fname))
                elif fmt == "csv":
                    from reports.csv_exporter import CsvExporter
                    CsvExporter().generate(report_data, str(fname))
                elif fmt == "docx":
                    # Use existing reporting engine if available
                    try:
                        from framework.reporting.engine import ReportEngine
                        ReportEngine().generate("docx", report_data, str(fname))
                    except ImportError:
                        self.log(f"[!] DOCX reporting requires python-docx")
                files.append(str(fname))
                sr.tools_ok += 1
                self.log(f"  Report saved: {fname}")
            except Exception as e:
                sr.errors.append(f"report_{fmt}: {e}")
            sr.tools_run += 1

        sr.data["report_files"] = files
        return sr
