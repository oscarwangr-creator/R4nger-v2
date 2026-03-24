"""Module registry for R4nger V3."""
from __future__ import annotations

from core.module_loader import ModuleLoader
from modules.exploit.hydra_module import HydraModule
from modules.exploit.metasploit_module import MetasploitModule
from modules.exploit.nuclei_exploitation_module import NucleiExploitationModule
from modules.exploit.sqlmap_module import SqlmapModule
from modules.exploit.xss_probe_module import XssProbeModule
from modules.osint.amass_module import AmassModule
from modules.osint.github_dork_module import GitHubDorkModule
from modules.osint.recon_ng_module import ReconNgModule
from modules.osint.shodan_module import ShodanModule
from modules.osint.spiderfoot_module import SpiderFootModule
from modules.osint.theharvester_module import TheHarvesterModule
from modules.post_exploit.credential_dump_module import CredentialDumpModule
from modules.post_exploit.lateral_movement_module import LateralMovementModule
from modules.post_exploit.persistence_module import PersistenceModule
from modules.post_exploit.privilege_escalation_module import PrivilegeEscalationModule
from modules.recon.dns_enum_module import DnsEnumModule
from modules.recon.http_fingerprint_module import HttpFingerprintModule
from modules.recon.nmap_module import NmapModule
from modules.recon.nuclei_module import NucleiReconModule
from modules.recon.ssl_scan_module import SslScanModule
from modules.recon.subdomain_discovery_module import SubdomainDiscoveryModule
from modules.reporting.html_report_module import HtmlReportModule
from modules.reporting.json_report_module import JsonReportModule
from modules.reporting.pdf_report_module import PdfReportModule


def build_module_registry() -> dict:
    """Build a stable module registry with explicit ordering."""
    modules = [
        SpiderFootModule(), ReconNgModule(), TheHarvesterModule(), AmassModule(), ShodanModule(), GitHubDorkModule(),
        NmapModule(), NucleiReconModule(), DnsEnumModule(), SubdomainDiscoveryModule(), HttpFingerprintModule(), SslScanModule(),
        MetasploitModule(), HydraModule(), SqlmapModule(), NucleiExploitationModule(), XssProbeModule(),
        PrivilegeEscalationModule(), PersistenceModule(), LateralMovementModule(), CredentialDumpModule(),
        HtmlReportModule(), JsonReportModule(), PdfReportModule(),
    ]
    return {m.metadata.name: m for m in modules}


def build_discovered_module_registry() -> dict:
    """Build registry from dynamic discovery, falling back to explicit registry if needed."""
    discovered = ModuleLoader("modules").discover()
    return discovered or build_module_registry()
