"""Utilities for integrating scraped external tools as framework modules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True, slots=True)
class ScrapedToolProfile:
    key: str
    display_name: str
    source_file: str
    category_hint: str
    capabilities: List[str]
    preferred_stage: str


SCRAPED_TOOL_PROFILES: Dict[str, ScrapedToolProfile] = {
    "1n3_sn1per": ScrapedToolProfile(
        key="1n3_sn1per",
        display_name="1N3 Sn1per",
        source_file="tools-to-add/1N3_Sn1per.txt",
        category_hint="Recon",
        capabilities=["attack surface reconnaissance", "service fingerprinting", "automated scan orchestration"],
        preferred_stage="recon",
    ),
    "sentinelai": ScrapedToolProfile(
        key="sentinelai",
        display_name="SentinelAI",
        source_file="tools-to-add/Aayush9808_SentinelAI.txt",
        category_hint="OSINT",
        capabilities=["anomaly detection", "signal enrichment", "risk scoring"],
        preferred_stage="osint",
    ),
    "pentestgpt": ScrapedToolProfile(
        key="pentestgpt",
        display_name="PentestGPT",
        source_file="tools-to-add/GreyDGL_PentestGPT.txt",
        category_hint="Exploit",
        capabilities=["assessment planning", "attack path assistance", "operator decision support"],
        preferred_stage="exploit",
    ),
    "photon": ScrapedToolProfile(
        key="photon",
        display_name="Photon",
        source_file="tools-to-add/PHOTON.txt",
        category_hint="Recon",
        capabilities=["web crawling", "URL discovery", "intelligence extraction"],
        preferred_stage="recon",
    ),
    "amass_scraped": ScrapedToolProfile(
        key="amass_scraped",
        display_name="Amass (Scraped Profile)",
        source_file="tools-to-add/amass.txt",
        category_hint="Recon",
        capabilities=["subdomain enumeration", "asset mapping", "DNS correlation"],
        preferred_stage="recon",
    ),
    "ankush_framework": ScrapedToolProfile(
        key="ankush_framework",
        display_name="Ankush Pentesting Framework",
        source_file="tools-to-add/ankushbhagats_pentesting-framework.txt",
        category_hint="Exploit",
        capabilities=["attack workflow automation", "toolchain composition", "execution playbooks"],
        preferred_stage="exploit",
    ),
    "axiom": ScrapedToolProfile(
        key="axiom",
        display_name="Axiom",
        source_file="tools-to-add/axiom.txt",
        category_hint="Recon",
        capabilities=["distributed execution", "parallel scanning", "fleet tasking"],
        preferred_stage="recon",
    ),
    "intelowl": ScrapedToolProfile(
        key="intelowl",
        display_name="IntelOwl",
        source_file="tools-to-add/intelowlproject-intelowl-8a5edab282632443.txt",
        category_hint="OSINT",
        capabilities=["threat intel lookups", "IOC enrichment", "multi-engine analysis"],
        preferred_stage="osint",
    ),
    "intelqm": ScrapedToolProfile(
        key="intelqm",
        display_name="IntelQM",
        source_file="tools-to-add/intelqm.txt",
        category_hint="OSINT",
        capabilities=["query management", "intel normalization", "indicator triage"],
        preferred_stage="osint",
    ),
    "recon_ng_scraped": ScrapedToolProfile(
        key="recon_ng_scraped",
        display_name="Recon-ng (Scraped Profile)",
        source_file="tools-to-add/lanmaster53-recon-ng-8a5edab282632443.txt",
        category_hint="OSINT",
        capabilities=["workspace correlation", "contact discovery", "host intelligence"],
        preferred_stage="osint",
    ),
    "onionscan": ScrapedToolProfile(
        key="onionscan",
        display_name="OnionScan",
        source_file="tools-to-add/onionscan.txt",
        category_hint="OSINT",
        capabilities=["darkweb enumeration", "onion service profiling", "hidden service metadata"],
        preferred_stage="osint",
    ),
    "metasploit_framework": ScrapedToolProfile(
        key="metasploit_framework",
        display_name="Metasploit Framework (Scraped Profile)",
        source_file="tools-to-add/rapid7-metasploit-framework-8a5edab282632443.txt",
        category_hint="Exploit",
        capabilities=["exploit modules", "payload generation", "post modules"],
        preferred_stage="exploit",
    ),
    "reconftw": ScrapedToolProfile(
        key="reconftw",
        display_name="ReconFTW",
        source_file="tools-to-add/reconftw.txt",
        category_hint="Recon",
        capabilities=["recon automation", "subdomain intel", "web surface profiling"],
        preferred_stage="recon",
    ),
    "xsstrike": ScrapedToolProfile(
        key="xsstrike",
        display_name="XSStrike",
        source_file="tools-to-add/s0md3v_XSStrike.txt",
        category_hint="Exploit",
        capabilities=["XSS payload crafting", "context analysis", "reflection testing"],
        preferred_stage="exploit",
    ),
    "reconftw_snapshot": ScrapedToolProfile(
        key="reconftw_snapshot",
        display_name="ReconFTW (Snapshot)",
        source_file="tools-to-add/six2dez-reconftw-8a5edab282632443.txt",
        category_hint="Recon",
        capabilities=["pipeline-ready recon", "evidence aggregation", "batch enumeration"],
        preferred_stage="recon",
    ),
    "sleuthkit": ScrapedToolProfile(
        key="sleuthkit",
        display_name="Sleuth Kit",
        source_file="tools-to-add/sleuthkit-sleuthkit-8a5edab282632443.txt",
        category_hint="Post-Exploit",
        capabilities=["filesystem forensics", "artifact recovery", "timeline analysis"],
        preferred_stage="post_exploit",
    ),
    "sn1per": ScrapedToolProfile(
        key="sn1per",
        display_name="Sn1per",
        source_file="tools-to-add/sn1per.txt",
        category_hint="Recon",
        capabilities=["vulnerability scanning", "port analysis", "asset discovery"],
        preferred_stage="recon",
    ),
    "spiderfoot_scraped": ScrapedToolProfile(
        key="spiderfoot_scraped",
        display_name="SpiderFoot (Scraped Profile)",
        source_file="tools-to-add/spiderfoot.txt",
        category_hint="OSINT",
        capabilities=["multi-source collection", "entity relationship discovery", "automated enrichment"],
        preferred_stage="osint",
    ),
    "viper": ScrapedToolProfile(
        key="viper",
        display_name="Viper",
        source_file="tools-to-add/viper.txt",
        category_hint="Exploit",
        capabilities=["operator workflow documentation", "red-team process support", "knowledge base automation"],
        preferred_stage="exploit",
    ),
}


def build_scraped_result(profile_key: str, payload: Dict[str, Any], module_name: str) -> Dict[str, Any]:
    profile = SCRAPED_TOOL_PROFILES[profile_key]
    return {
        "target": payload["target"],
        "module": module_name,
        "summary": f"Integrated {profile.display_name} capabilities into {profile.preferred_stage} stage.",
        "source": {
            "scraped_profile": profile.source_file,
            "category_hint": profile.category_hint,
        },
        "capabilities": profile.capabilities,
        "execution": {
            "simulated": True,
            "timestamp": payload.get("timestamp", "runtime"),
        },
    }
