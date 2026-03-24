"""RedTeam Framework - Module: recon/tech_stack_fingerprinter"""
from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, List
from urllib.parse import urlparse

from framework.intelligence.wrappers.wafw00f_wrapper import Wafw00fWrapper
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity


class TechStackFingerprinterModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"tech_stack_fingerprinter","description":"Fingerprint exposed web technologies, headers, and WAF indicators.","author":"OpenAI","category":"recon","version":"1.0","references":["https://github.com/EnableSecurity/wafw00f"]}

    def _declare_options(self) -> None:
        self._register_option("target", "Target URL or host", required=True)
        self._register_option("timeout", "HTTP timeout in seconds", required=False, default=15, type=int)

    async def run(self) -> ModuleResult:
        target = self.get("target").strip()
        timeout = self.get("timeout")
        url = target if target.startswith(("http://", "https://")) else f"https://{target}"
        http_data = self._fetch_headers(url, timeout)
        waf_result = await Wafw00fWrapper().run(url)
        technologies = self._identify_stack(http_data)
        findings: List[Finding] = []
        for tech in technologies:
            findings.append(self.make_finding(
                title=f"Technology fingerprint: {tech['name']}",
                target=urlparse(url).netloc or target,
                severity=Severity.INFO,
                description=tech["reason"],
                evidence=tech,
                tags=["recon", "web", "fingerprint"],
            ))
        for detection in waf_result.get("parsed", {}).get("detections", []):
            findings.append(self.make_finding(
                title="WAF detected",
                target=url,
                severity=Severity.INFO,
                description=detection,
                evidence={"detection": detection},
                tags=["recon", "web", "waf"],
            ))
        return ModuleResult(success=True, output={"target": target, "headers": http_data, "technologies": technologies, "waf": waf_result.get("parsed", {})}, findings=findings, raw_output=json.dumps(http_data, indent=2))

    def _fetch_headers(self, url: str, timeout: int) -> Dict[str, Any]:
        request = urllib.request.Request(url, headers={"User-Agent": "RTF-TechFingerprinter/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                headers = dict(response.headers.items())
                body = response.read(4096).decode("utf-8", errors="replace")
                return {"status": getattr(response, "status", 0), "headers": headers, "body_snippet": body[:512]}
        except Exception as exc:
            return {"status": 0, "headers": {}, "body_snippet": "", "error": str(exc)}

    def _identify_stack(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        headers = {k.lower(): v for k, v in data.get("headers", {}).items()}
        body = (data.get("body_snippet") or "").lower()
        matches: List[Dict[str, str]] = []
        if "server" in headers:
            matches.append({"name": headers["server"], "reason": "HTTP Server header exposed."})
        if "x-powered-by" in headers:
            matches.append({"name": headers["x-powered-by"], "reason": "X-Powered-By header disclosed application runtime."})
        if "wp-content" in body:
            matches.append({"name": "WordPress", "reason": "Body snippet references wp-content assets."})
        if "__next" in body:
            matches.append({"name": "Next.js", "reason": "Body snippet exposes __NEXT data marker."})
        if "content-security-policy" not in headers:
            matches.append({"name": "Missing CSP", "reason": "Content-Security-Policy header absent."})
        return matches
