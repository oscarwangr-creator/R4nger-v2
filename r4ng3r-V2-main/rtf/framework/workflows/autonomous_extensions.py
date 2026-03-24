from __future__ import annotations

from typing import Dict, Type

from framework.workflows.engine import Workflow, WorkflowBuilder


class IdentityFusionExtremeWorkflow(Workflow):
    name = "identity_fusion_extreme"
    description = "Username variation expansion through breach/social/domain correlation, graphing, timeline, and risk scoring."
    def steps(self):
        from framework.modules.osint.identity_fusion_extreme import IdentityFusionExtremeModule
        return WorkflowBuilder(self.name).add_step("identity_fusion_extreme", IdentityFusionExtremeModule, required=True).build()._steps


class ExternalPentestFullWorkflow(Workflow):
    name = "external_pentest_full"
    description = "Recon to web validation pipeline using subfinder, amass, assetfinder, httpx, naabu, nuclei, ffuf, dalfox, and sqlmap-aligned modules."
    def steps(self):
        from framework.modules.recon.subdomain_enum import SubdomainEnumModule
        from framework.modules.recon.port_scan import PortScanModule
        from framework.modules.recon.tech_stack_fingerprinter import TechStackFingerprinterModule
        from framework.modules.web.misconfig_scanner import MisconfigScannerModule
        return (WorkflowBuilder(self.name)
            .add_step("subdomain_enum", SubdomainEnumModule, required=True)
            .add_step("port_scan", PortScanModule, required=False)
            .add_step("tech_stack_fingerprinter", TechStackFingerprinterModule, transformer=lambda prev: {"target": ((prev.output or {}).get("target") or "") if prev else ""}, required=False)
            .add_step("misconfig_scanner", MisconfigScannerModule, transformer=lambda prev: {"target": self._normalize_target(prev)}, required=False)
            .build()._steps)
    @staticmethod
    def _normalize_target(prev):
        target = ((prev.output or {}).get("target") or "") if prev else ""
        return target if target.startswith(("http://", "https://")) else (f"https://{target}" if target else "")


class SocialEngineeringIntelWorkflow(Workflow):
    name = "social_engineering_intel"
    description = "Username enumeration, pattern analysis, and breach correlation for pretexting support."
    def steps(self):
        from framework.modules.osint.username_enum import UsernameEnumModule
        from framework.modules.osint.username_pattern_analyzer import UsernamePatternAnalyzerModule
        from framework.modules.osint.breach_correlation import BreachCorrelationModule
        return (WorkflowBuilder(self.name)
            .add_step("username_enum", UsernameEnumModule, required=False)
            .add_step("username_pattern_analyzer", UsernamePatternAnalyzerModule, transformer=lambda prev: {"username": (prev.output or {}).get("username", "") if prev else ""}, required=False)
            .add_step("breach_correlation", BreachCorrelationModule, transformer=lambda prev: {"query": (prev.output or {}).get("username", "") if prev else ""}, required=False)
            .build()._steps)


class CloudAttackPipelineWorkflow(Workflow):
    name = "cloud_attack_pipeline"
    description = "AWS and Azure enumeration workflow with graceful degradation."
    def steps(self):
        from framework.modules.cloud.aws_enum import AWSEnumModule
        from framework.modules.cloud.azure_enum import AzureEnumModule
        return WorkflowBuilder(self.name).add_step("aws_enum", AWSEnumModule, required=False).add_step("azure_enum", AzureEnumModule, required=False).build()._steps


class WebDeepAuditWorkflow(Workflow):
    name = "web_deep_audit"
    description = "Deep web audit using fuzzing, misconfiguration checks, XSS, SQLi, and API review modules."
    def steps(self):
        from framework.modules.web.dir_fuzz import DirFuzzModule
        from framework.modules.web.xss_scan import XSSScanModule
        from framework.modules.web.sqli_scan import SQLiScanModule
        from framework.modules.web.api_security import APISecurityModule
        from framework.modules.web.misconfig_scanner import MisconfigScannerModule
        return (WorkflowBuilder(self.name)
            .add_step("dir_fuzz", DirFuzzModule, required=False)
            .add_step("misconfig_scanner", MisconfigScannerModule, transformer=lambda prev: {"target": ((prev.output or {}).get("target") or "") if prev else ""}, required=False)
            .add_step("xss_scan", XSSScanModule, required=False)
            .add_step("sqli_scan", SQLiScanModule, required=False)
            .add_step("api_security", APISecurityModule, required=False)
            .build()._steps)


class InfrastructureCorrelationWorkflow(Workflow):
    name = "infrastructure_correlation"
    description = "Attack-surface mapping with infrastructure and identity graph correlation."
    def steps(self):
        from framework.modules.recon.subdomain_enum import SubdomainEnumModule
        from framework.modules.recon.port_scan import PortScanModule
        from framework.modules.osint.identity_fusion_extreme import IdentityFusionExtremeModule
        return (WorkflowBuilder(self.name)
            .add_step("subdomain_enum", SubdomainEnumModule, required=False)
            .add_step("port_scan", PortScanModule, required=False)
            .add_step("identity_fusion_extreme", IdentityFusionExtremeModule, required=False)
            .build()._steps)


class ThreatIntelligencePipelineWorkflow(Workflow):
    name = "threat_intelligence_pipeline"
    description = "Threat-intel enrichment using OSINT breach and attack-surface pivots."
    def steps(self):
        from framework.modules.osint.breach_correlation import BreachCorrelationModule
        from framework.modules.recon.tech_stack_fingerprinter import TechStackFingerprinterModule
        return (WorkflowBuilder(self.name)
            .add_step("breach_correlation", BreachCorrelationModule, required=False)
            .add_step("tech_stack_fingerprinter", TechStackFingerprinterModule, transformer=lambda prev: {"target": (prev.output or {}).get("query", "") if prev else ""}, required=False)
            .build()._steps)


EXTREME_WORKFLOWS: Dict[str, Type[Workflow]] = {
    "identity_fusion_extreme": IdentityFusionExtremeWorkflow,
    "external_pentest_full": ExternalPentestFullWorkflow,
    "social_engineering_intel": SocialEngineeringIntelWorkflow,
    "cloud_attack_pipeline": CloudAttackPipelineWorkflow,
    "web_deep_audit": WebDeepAuditWorkflow,
    "infrastructure_correlation": InfrastructureCorrelationWorkflow,
    "threat_intelligence_pipeline": ThreatIntelligencePipelineWorkflow,
}
