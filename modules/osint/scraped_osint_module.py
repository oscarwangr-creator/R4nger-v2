from __future__ import annotations

from typing import Any, Dict

from core.base_module import BaseModule, ModuleMetadata
from utils.scraped_toolkit import build_scraped_result


class SpiderFootScrapedModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="spiderfoot_scraped_osint",
            category="OSINT",
            description="SpiderFoot scraped profile integration for intelligence fusion",
            tags=["osint", "spiderfoot", "scraped"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("spiderfoot_scraped", payload, self.metadata.name)


class ReconNgScrapedModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="recon_ng_scraped_osint",
            category="OSINT",
            description="Recon-ng scraped profile integration for workspace-driven enrichment",
            tags=["osint", "recon-ng", "scraped"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("recon_ng_scraped", payload, self.metadata.name)


class IntelOwlModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="intelowl_osint",
            category="OSINT",
            description="IntelOwl integration for indicator lookups and enrichment",
            tags=["osint", "threat-intel", "ioc"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("intelowl", payload, self.metadata.name)


class OnionScanModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="onionscan_osint",
            category="OSINT",
            description="OnionScan integration for onion service reconnaissance",
            tags=["osint", "darkweb", "onion"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("onionscan", payload, self.metadata.name)


class SentinelAIModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="sentinelai_osint",
            category="OSINT",
            description="SentinelAI integration for anomaly-led intelligence scoring",
            tags=["osint", "anomaly-detection", "ai"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("sentinelai", payload, self.metadata.name)


class IntelQMModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="intelqm_osint",
            category="OSINT",
            description="IntelQM integration for query-centric threat intelligence management",
            tags=["osint", "intel", "query"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("intelqm", payload, self.metadata.name)
