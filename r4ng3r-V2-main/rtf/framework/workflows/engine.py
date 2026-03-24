"""
RedTeam Framework v2.0 - Workflow Engine
8 built-in workflows with DAG support, retry-per-step, output piping.

Workflows:
  full_recon         — subdomain → port_scan → nuclei → report
  ad_attack          — bloodhound → kerberoast → asreproast
  web_audit          — dir_fuzz → xss_scan → sqli_scan → api_security
  osint_person       — username_enum → email_harvest
  identity_fusion    — full 48-tool SOCMINT pipeline
  cloud_audit        — aws_enum → shodan_search
  full_ad_compromise — ldap_enum → bloodhound → kerberoast → asreproast
  ssl_web_recon      — ssl_scan → subdomain_enum → nuclei → api_security
"""
from __future__ import annotations
import asyncio, json, uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from framework.core.logger import get_logger
from framework.modules.base import BaseModule, ModuleResult

log = get_logger("rtf.workflow")

@dataclass
class StepResult:
    step_name: str; module_name: str; success: bool; result: Optional[ModuleResult]
    error: Optional[str] = None; elapsed: float = 0.0

@dataclass
class WorkflowResult:
    workflow_name: str; run_id: str; steps: List[StepResult] = field(default_factory=list)
    started_at: Optional[datetime] = None; finished_at: Optional[datetime] = None; success: bool = False

    @property
    def elapsed(self) -> float:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return 0.0

    @property
    def total_findings(self) -> int:
        return sum(len(s.result.findings) for s in self.steps if s.result)

    def to_dict(self) -> Dict[str, Any]:
        return {"workflow":self.workflow_name,"run_id":self.run_id,"success":self.success,"elapsed":round(self.elapsed,2),"total_findings":self.total_findings,"started_at":self.started_at.isoformat() if self.started_at else None,"finished_at":self.finished_at.isoformat() if self.finished_at else None,"steps":[{"name":s.step_name,"module":s.module_name,"success":s.success,"elapsed":round(s.elapsed,2),"findings":len(s.result.findings) if s.result else 0,"error":s.error} for s in self.steps]}

OptionTransformer = Callable[[Optional[ModuleResult]], Dict[str, Any]]

@dataclass
class Step:
    name: str; module_class: type; options: Dict[str, Any] = field(default_factory=dict)
    option_transformer: Optional[OptionTransformer] = None; required: bool = True
    depends_on_success: bool = True; retry_count: int = 0; retry_delay: float = 2.0
    pipe_key: Optional[str] = None; pipe_option: Optional[str] = None


class Workflow:
    name: str = "base_workflow"; description: str = ""

    def __init__(self, base_options: Optional[Dict[str, Any]] = None) -> None:
        self._base_options = base_options or {}
        self._steps: List[Step] = self.steps()

    def steps(self) -> List[Step]:
        return []

    async def run(self, initial_options: Optional[Dict[str, Any]] = None, output_dir: Optional[str] = None) -> WorkflowResult:
        opts = {**self._base_options, **(initial_options or {})}
        run_id = str(uuid.uuid4())
        result = WorkflowResult(workflow_name=self.name, run_id=run_id, started_at=datetime.utcnow())
        log.info(f"▶ Workflow: {self.name}  run={run_id[:8]}")
        previous_result: Optional[ModuleResult] = None; all_ok = True

        for step in self._steps:
            if step.depends_on_success and not all_ok:
                log.warning(f"  ⏭ Skipping step '{step.name}' (previous step failed)")
                result.steps.append(StepResult(step.name, step.module_class.__name__, False, None, "Skipped"))
                continue
            log.info(f"  ▷ Step: {step.name}")
            step_start = datetime.utcnow()
            step_opts = {**opts, **step.options}

            # Apply option transformer
            if step.option_transformer:
                try:
                    extra = step.option_transformer(previous_result)
                    step_opts.update(extra)
                except Exception as exc:
                    log.warning(f"  Option transformer failed for {step.name}: {exc}")

            # Pipe output from previous step
            if step.pipe_key and step.pipe_option and previous_result and previous_result.output:
                pipe_val = previous_result.output.get(step.pipe_key)
                if pipe_val:
                    if isinstance(pipe_val, list):
                        pipe_val = ",".join(str(v) for v in pipe_val[:20])
                    step_opts[step.pipe_option] = pipe_val

            # Execute with retry
            last_exc = None
            for attempt in range(max(1, step.retry_count + 1)):
                try:
                    module: BaseModule = step.module_class()
                    module_result = await module.execute(step_opts)
                    elapsed = (datetime.utcnow() - step_start).total_seconds()
                    step_result = StepResult(step_name=step.name, module_name=step.module_class.__name__, success=module_result.success, result=module_result, elapsed=elapsed)
                    if module_result.success:
                        previous_result = module_result; break
                    elif attempt < step.retry_count:
                        log.warning(f"  Retry {attempt+1}/{step.retry_count} for step '{step.name}'")
                        await asyncio.sleep(step.retry_delay * (attempt + 1))
                    else:
                        all_ok = False if step.required else all_ok
                        if step.required: log.error(f"  ✗ Required step '{step.name}' failed: {module_result.error}")
                        previous_result = module_result
                    break
                except Exception as exc:
                    last_exc = exc
                    elapsed = (datetime.utcnow() - step_start).total_seconds()
                    step_result = StepResult(step_name=step.name, module_name=step.module_class.__name__, success=False, result=None, error=str(exc), elapsed=elapsed)
                    if attempt < step.retry_count:
                        await asyncio.sleep(step.retry_delay * (attempt + 1))
                    else:
                        log.error(f"  ✗ Step '{step.name}' raised: {exc}")
                        all_ok = False
                        if step.required:
                            result.steps.append(step_result); break

            result.steps.append(step_result)

        result.finished_at = datetime.utcnow(); result.success = all_ok
        log.info(f"{'✓' if all_ok else '✗'} Workflow '{self.name}' done | elapsed={result.elapsed:.1f}s | findings={result.total_findings}")
        if output_dir:
            self._save_report(result, output_dir)
        return result

    def _save_report(self, result: WorkflowResult, output_dir: str) -> None:
        out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
        report_path = out / f"workflow_{result.run_id[:8]}.json"
        report_path.write_text(json.dumps(result.to_dict(), indent=2))
        md_path = out / f"workflow_{result.run_id[:8]}.md"
        lines = [f"# Workflow: {result.workflow_name}", f"**Status:** {'✅' if result.success else '❌'}", f"**Elapsed:** {result.elapsed:.1f}s", f"**Findings:** {result.total_findings}", "", "## Steps"]
        for s in result.steps:
            lines.append(f"- **{s.step_name}**: {'✓' if s.success else '✗'} ({s.elapsed:.1f}s)")
        md_path.write_text("\n".join(lines))


# ── Built-in Workflows ────────────────────────────────────────────────────────

class FullReconWorkflow(Workflow):
    name = "full_recon"; description = "Complete external recon: subdomain → ports → nuclei"
    def steps(self) -> List[Step]:
        from framework.modules.recon.subdomain_enum import SubdomainEnumModule
        from framework.modules.recon.port_scan import PortScanModule
        from framework.modules.recon.nuclei_scan import NucleiScanModule
        def ports_from_subs(prev):
            if prev and prev.output and prev.output.get("live_hosts"):
                hosts = prev.output["live_hosts"]
                return {"target": hosts[0] if len(hosts)==1 else ",".join(hosts[:50])}
            return {}
        def nuclei_from_ports(prev):
            if prev and prev.output and prev.output.get("open_ports"):
                urls=[]
                for p in prev.output["open_ports"][:30]:
                    port=p["port"]; host=p["host"]
                    scheme="https" if port in (443,8443) else "http"
                    urls.append(f"{scheme}://{host}:{port}")
                if urls: return {"targets":",".join(urls)}
            return {}
        return [
            Step(name="subdomain_enum", module_class=SubdomainEnumModule, required=True),
            Step(name="port_scan", module_class=PortScanModule, options={"ports":"top-100","service_detection":False}, option_transformer=ports_from_subs, required=False),
            Step(name="nuclei_scan", module_class=NucleiScanModule, options={"severity":"critical,high,medium"}, option_transformer=nuclei_from_ports, required=False),
        ]

class ADAttackWorkflow(Workflow):
    name = "ad_attack"; description = "AD attack chain: BloodHound → Kerberoast → ASREPRoast"
    def steps(self) -> List[Step]:
        from framework.modules.active_directory.bloodhound_collect import BloodHoundCollectModule
        from framework.modules.active_directory.kerberoast import KerberoastModule
        from framework.modules.active_directory.asreproast import ASREPRoastModule
        return [
            Step(name="bloodhound_collect", module_class=BloodHoundCollectModule, required=False),
            Step(name="kerberoast", module_class=KerberoastModule, required=False),
            Step(name="asreproast", module_class=ASREPRoastModule, required=False),
        ]

class WebAuditWorkflow(Workflow):
    name = "web_audit"; description = "Web audit: dir_fuzz → XSS → SQLi → API security"
    def steps(self) -> List[Step]:
        from framework.modules.web.dir_fuzz import DirFuzzModule
        from framework.modules.web.xss_scan import XSSScanModule
        from framework.modules.web.sqli_scan import SQLiScanModule
        from framework.modules.web.api_security import APISecurityModule
        return [
            Step(name="dir_fuzz", module_class=DirFuzzModule, required=False),
            Step(name="xss_scan", module_class=XSSScanModule, required=False),
            Step(name="sqli_scan", module_class=SQLiScanModule, required=False),
            Step(name="api_security", module_class=APISecurityModule, required=False),
        ]

class OSINTPersonWorkflow(Workflow):
    name = "osint_person"; description = "OSINT: username_enum → email_harvest"
    def steps(self) -> List[Step]:
        from framework.modules.osint.username_enum import UsernameEnumModule
        from framework.modules.osint.email_harvest import EmailHarvestModule
        return [
            Step(name="username_enum", module_class=UsernameEnumModule, required=True),
            Step(name="email_harvest", module_class=EmailHarvestModule, required=False),
        ]

class IdentityFusionWorkflow(Workflow):
    name = "identity_fusion"; description = "Full 9-stage SOCMINT identity investigation (90+ tools)"
    def steps(self) -> List[Step]:
        from framework.modules.osint.identity_fusion import IdentityFusionModule
        return [Step(name="identity_fusion", module_class=IdentityFusionModule, required=True)]


class OSINTToolkitWorkflow(Workflow):
    name = "osint_toolkit"; description = "Pipeline friendly OSINT suite for username, search, recon, secrets, and metadata modules"
    def steps(self) -> List[Step]:
        from framework.modules.osint.sherlock import SherlockModule
        from framework.modules.osint.maigret import MaigretModule
        from framework.modules.osint.snscrape import SnscrapeModule
        from framework.modules.osint.duckduckgo import DuckDuckGoSearchModule
        from framework.modules.recon.subfinder import SubfinderModule
        from framework.modules.recon.httpx import HttpxModule
        from framework.modules.recon.naabu import NaabuModule
        from framework.modules.recon.nuclei import NucleiModule
        from framework.modules.osint.trufflehog import TruffleHogModule
        from framework.modules.osint.exiftool import ExiftoolModule

        return [
            Step(name="sherlock", module_class=SherlockModule, required=False),
            Step(name="maigret", module_class=MaigretModule, required=False),
            Step(name="snscrape", module_class=SnscrapeModule, option_transformer=lambda _prev: {"query": self._base_options.get("username", ""), "mode": "twitter-user"}, required=False),
            Step(name="duckduckgo", module_class=DuckDuckGoSearchModule, option_transformer=lambda _prev: {"query": self._base_options.get("query") or self._base_options.get("username") or self._base_options.get("target", "")}, required=False),
            Step(name="subfinder", module_class=SubfinderModule, option_transformer=lambda _prev: {"target": self._base_options.get("domain", "")}, required=False),
            Step(name="httpx", module_class=HttpxModule, option_transformer=lambda _prev: {"target": self._base_options.get("domain") or self._base_options.get("target", "")}, required=False),
            Step(name="naabu", module_class=NaabuModule, option_transformer=lambda _prev: {"target": self._base_options.get("domain") or self._base_options.get("target", "")}, required=False),
            Step(name="nuclei", module_class=NucleiModule, option_transformer=lambda _prev: {"target": self._base_options.get("target") or self._base_options.get("domain", "")}, required=False),
            Step(name="trufflehog", module_class=TruffleHogModule, option_transformer=lambda _prev: {"target": self._base_options.get("path") or self._base_options.get("target", "")}, required=False),
            Step(name="exiftool", module_class=ExiftoolModule, option_transformer=lambda _prev: {"target": self._base_options.get("file") or self._base_options.get("target", "")}, required=False),
        ]

class CloudAuditWorkflow(Workflow):
    name = "cloud_audit"; description = "Cloud audit: aws_enum → shodan_search"
    def steps(self) -> List[Step]:
        from framework.modules.cloud.aws_enum import AWSEnumModule
        from framework.modules.recon.shodan_search import ShodanSearchModule
        return [
            Step(name="aws_enum", module_class=AWSEnumModule, required=False),
            Step(name="shodan_search", module_class=ShodanSearchModule, required=False),
        ]

class FullADCompromiseWorkflow(Workflow):
    name = "full_ad_compromise"; description = "Full AD compromise: ldap_enum → bloodhound → kerberoast → asreproast"
    def steps(self) -> List[Step]:
        from framework.modules.network.ldap_enum import LDAPEnumModule
        from framework.modules.active_directory.bloodhound_collect import BloodHoundCollectModule
        from framework.modules.active_directory.kerberoast import KerberoastModule
        from framework.modules.active_directory.asreproast import ASREPRoastModule
        return [
            Step(name="ldap_enum", module_class=LDAPEnumModule, required=False, retry_count=1),
            Step(name="bloodhound_collect", module_class=BloodHoundCollectModule, required=False),
            Step(name="kerberoast", module_class=KerberoastModule, required=False),
            Step(name="asreproast", module_class=ASREPRoastModule, required=False),
        ]

class SSLWebReconWorkflow(Workflow):
    name = "ssl_web_recon"; description = "SSL + web recon: ssl_scan → subdomain_enum → nuclei → api_security"
    def steps(self) -> List[Step]:
        from framework.modules.recon.ssl_scan import SSLScanModule
        from framework.modules.recon.subdomain_enum import SubdomainEnumModule
        from framework.modules.recon.nuclei_scan import NucleiScanModule
        from framework.modules.web.api_security import APISecurityModule
        return [
            Step(name="ssl_scan", module_class=SSLScanModule, required=False),
            Step(name="subdomain_enum", module_class=SubdomainEnumModule, required=False),
            Step(name="nuclei_scan", module_class=NucleiScanModule, options={"severity":"critical,high"}, required=False),
            Step(name="api_security", module_class=APISecurityModule, required=False),
        ]


class EngineMeshWorkflow(Workflow):
    name = "engine_mesh"; description = "Architecture mesh workflow that exercises the distributed engine registry through module-compatible engine adapters."
    def steps(self) -> List[Step]:
        from framework.modules.architecture.rtf_core_engine import RtfCoreEngineModule
        from framework.modules.architecture.rtf_osint_engine import RtfOsintEngineModule
        from framework.modules.architecture.rtf_graph_engine import RtfGraphEngineModule
        from framework.modules.architecture.rtf_ai_engine import RtfAiEngineModule
        from framework.modules.architecture.rtf_report_engine import RtfReportEngineModule
        return [
            Step(name="core_orchestration", module_class=RtfCoreEngineModule, required=True),
            Step(name="osint_collection", module_class=RtfOsintEngineModule, required=False),
            Step(name="graph_intelligence", module_class=RtfGraphEngineModule, required=False),
            Step(name="ai_correlation", module_class=RtfAiEngineModule, required=False),
            Step(name="report_synthesis", module_class=RtfReportEngineModule, required=False),
        ]


BUILTIN_WORKFLOWS: Dict[str, type] = {
    "full_recon": FullReconWorkflow,
    "ad_attack": ADAttackWorkflow,
    "web_audit": WebAuditWorkflow,
    "osint_person": OSINTPersonWorkflow,
    "identity_fusion": IdentityFusionWorkflow,
    "osint_toolkit": OSINTToolkitWorkflow,
    "cloud_audit": CloudAuditWorkflow,
    "full_ad_compromise": FullADCompromiseWorkflow,
    "ssl_web_recon": SSLWebReconWorkflow,
    "engine_mesh": EngineMeshWorkflow,
}

class WorkflowBuilder:
    def __init__(self, name: str) -> None:
        self._name = name; self._steps: List[Step] = []; self._base_opts: Dict[str, Any] = {}
    def with_options(self, **kwargs: Any) -> "WorkflowBuilder":
        self._base_opts.update(kwargs); return self
    def add_step(self, name: str, module_class: type, options: Optional[Dict]=None, transformer: Optional[OptionTransformer]=None, required: bool=False, retry_count: int=0, pipe_key: Optional[str]=None, pipe_option: Optional[str]=None) -> "WorkflowBuilder":
        self._steps.append(Step(name=name, module_class=module_class, options=options or {}, option_transformer=transformer, required=required, retry_count=retry_count, pipe_key=pipe_key, pipe_option=pipe_option))
        return self
    def build(self) -> Workflow:
        wf = Workflow(self._base_opts); wf.name = self._name; wf._steps = self._steps; return wf


try:
    from framework.workflows.extensions import EXTENDED_WORKFLOWS
    BUILTIN_WORKFLOWS.update(EXTENDED_WORKFLOWS)
except Exception:
    EXTENDED_WORKFLOWS = {}


def get_workflow(name: str, base_options: Optional[Dict[str, Any]] = None) -> Workflow:
    cls = BUILTIN_WORKFLOWS.get(name)
    if not cls:
        raise KeyError(f"Unknown workflow: '{name}'. Available: {list(BUILTIN_WORKFLOWS)}")
    return cls(base_options)
