from __future__ import annotations

from typing import Any, Dict

from core.base_module import BaseModule, ModuleMetadata
from utils.scraped_toolkit import build_scraped_result


class PhotonReconModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="photon_recon",
            category="Recon",
            description="Photon integration for crawl-based web surface discovery",
            tags=["recon", "crawler", "url-discovery"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("photon", payload, self.metadata.name)


class AmassScrapedReconModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="amass_scraped_recon",
            category="Recon",
            description="Scraped Amass profile integration for DNS asset expansion",
            tags=["recon", "dns", "subdomains"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("amass_scraped", payload, self.metadata.name)


class ReconFTWReconModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="reconftw_recon",
            category="Recon",
            description="ReconFTW integration for broad recon automation",
            tags=["recon", "automation", "surface-mapping"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("reconftw", payload, self.metadata.name)


class ReconFTWSnapshotReconModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="reconftw_snapshot_recon",
            category="Recon",
            description="ReconFTW snapshot integration for reproducible recon runs",
            tags=["recon", "snapshot", "automation"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("reconftw_snapshot", payload, self.metadata.name)


class Sn1perReconModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="sn1per_recon",
            category="Recon",
            description="Sn1per integration for coordinated recon and vulnerability probing",
            tags=["recon", "vuln-scan", "automation"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("sn1per", payload, self.metadata.name)


class Sn1per1N3ReconModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="sn1per_1n3_recon",
            category="Recon",
            description="1N3 Sn1per variant integration for attack-surface reconnaissance",
            tags=["recon", "sn1per", "1n3"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("1n3_sn1per", payload, self.metadata.name)


class AxiomReconModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = ModuleMetadata(
            name="axiom_recon",
            category="Recon",
            description="Axiom integration for distributed recon task execution",
            tags=["recon", "distributed", "orchestration"],
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_scraped_result("axiom", payload, self.metadata.name)
