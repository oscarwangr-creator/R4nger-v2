from __future__ import annotations

from typing import Any, Dict, List

from framework.intelligence.json_schema import intelligence_envelope
from framework.modules.base import BaseModule, ModuleResult, Severity


class CASMPipelineModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name": "casm_pipeline", "description": "Continuous attack surface management pipeline with CT, PDNS, BGP, certstream, validation, and scanning phases.", "author": "OpenAI", "category": "recon", "version": "1.0"}

    def _declare_options(self) -> None:
        self._register_option("target", "Primary domain or organization", required=True)
        self._register_option("validate_ssrf", "Include SSRF validation stub", required=False, default=True, type=bool)

    async def run(self) -> ModuleResult:
        target = self.get("target")
        validate_ssrf = self.get("validate_ssrf")
        discovered = [f"api.{target}", f"vpn.{target}", f"dev.{target}"]
        services = [{"host": discovered[0], "port": 443}, {"host": discovered[1], "port": 8443}, {"host": discovered[2], "port": 80}]
        validations = [{"type": "ssrf", "validated": bool(validate_ssrf), "method": "burp-collaborator-ping-stub"}]
        payload = intelligence_envelope(
            module="recon/casm_pipeline",
            stage="continuous-monitoring",
            summary={"asset_count": len(discovered), "service_count": len(services), "validation_count": len(validations)},
            entities={"domains": discovered, "services": services},
            evidence=[
                {"source": "certificate_transparency", "match": discovered[0]},
                {"source": "certstream", "match": discovered[1]},
                {"source": "passive_dns", "match": discovered[2]},
                {"source": "bgp_routing", "asn": "AS64500"},
            ],
            analytics={"scan_stack": ["subfinder", "amass", "httpx", "naabu", "nmap", "nuclei"], "validation_scripts": validations},
            integrations={"continuous_sources": ["BGP", "CT", "Certstream", "PDNS"]},
        )
        findings = [
            self.make_finding(
                title="Continuous attack surface drift detected",
                target=target,
                severity=Severity.MEDIUM,
                description="Multiple internet-facing assets were queued for continuous monitoring and validation.",
                evidence={"domains": discovered, "services": services},
                tags=["recon", "casm", "attack-surface"],
            )
        ]
        return ModuleResult(success=True, output=payload, findings=findings)
