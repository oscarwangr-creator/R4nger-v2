"""RedTeam Framework - Module: web/misconfig_scanner"""
from __future__ import annotations

import ssl
import urllib.request
from typing import Any, Dict, List
from urllib.parse import urlparse

from framework.intelligence.wrappers.waybackurls_wrapper import WaybackUrlsWrapper
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity


class MisconfigScannerModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"misconfig_scanner","description":"Inspect web security headers, TLS posture, and historical URL exposure for misconfiguration signals.","author":"OpenAI","category":"web","version":"1.0"}

    def _declare_options(self) -> None:
        self._register_option("target", "Target URL", required=True)
        self._register_option("timeout", "Request timeout", required=False, default=15, type=int)

    async def run(self) -> ModuleResult:
        target = self.get("target").strip()
        timeout = self.get("timeout")
        request = urllib.request.Request(target, headers={"User-Agent": "RTF-MisconfigScanner/1.0"})
        headers: Dict[str, str] = {}
        status = 0
        error = ""
        try:
            with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
                headers = dict(response.headers.items())
                status = getattr(response, "status", 0)
        except Exception as exc:
            error = str(exc)
        archive = await WaybackUrlsWrapper().run(urlparse(target).netloc or target)
        findings = self._build_findings(target, headers, status, archive)
        return ModuleResult(success=True, output={"target": target, "status": status, "headers": headers, "archive": archive.get("parsed", {}), "error": error}, findings=findings, raw_output=str(headers))

    def _build_findings(self, target: str, headers: Dict[str, str], status: int, archive: Dict[str, Any]) -> List[Finding]:
        normalized = {k.lower(): v for k, v in headers.items()}
        findings: List[Finding] = []
        missing = {
            "content-security-policy": "Missing Content-Security-Policy header increases script injection blast radius.",
            "strict-transport-security": "Missing HSTS leaves downgrade opportunities in front of users or proxies.",
            "x-frame-options": "Missing X-Frame-Options allows easy clickjacking attempts.",
            "x-content-type-options": "Missing X-Content-Type-Options can enable MIME confusion.",
        }
        for header, desc in missing.items():
            if header not in normalized:
                findings.append(self.make_finding(
                    title=f"Missing security header: {header}",
                    target=target,
                    severity=Severity.MEDIUM,
                    description=desc,
                    evidence={"status": status, "missing_header": header},
                    tags=["web", "misconfig", "header"],
                ))
        archived = archive.get("parsed", {}).get("urls", []) if isinstance(archive, dict) else []
        if len(archived) > 25:
            findings.append(self.make_finding(
                title="Large historical URL footprint discovered",
                target=target,
                severity=Severity.LOW,
                description="Wayback-style historical exposure suggests broad attack-surface drift.",
                evidence={"archived_urls": archived[:25], "count": len(archived)},
                tags=["web", "misconfig", "exposure"],
            ))
        return findings
