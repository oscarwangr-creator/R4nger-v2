"""RedTeam Framework - Module: osint/breach_correlation"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from framework.intelligence.wrappers.breach_correlation_wrapper import BreachCorrelationWrapper
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BreachCorrelationModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"breach_correlation","description":"Correlate breached identities and reuse indicators from email or username pivots.","author":"OpenAI","category":"osint","version":"1.0","references":["https://github.com/khast3x/h8mail"]}

    def _declare_options(self) -> None:
        self._register_option("query", "Email address or username to correlate", required=True)
        self._register_option("confidence_threshold", "Minimum heuristic confidence", required=False, default=0.55, type=float)

    async def run(self) -> ModuleResult:
        query = self.get("query").strip()
        threshold = self.get("confidence_threshold")
        wrapper = BreachCorrelationWrapper()
        wrapper_result = await wrapper.run(query)
        breaches = wrapper_result.get("parsed", {}).get("breaches", []) if wrapper_result.get("success") else []
        findings: List[Finding] = []

        if not breaches:
            heuristics = self._heuristic_signals(query)
            for signal in heuristics:
                if signal["confidence"] >= threshold:
                    findings.append(self.make_finding(
                        title=f"Potential breach correlation: {query}",
                        target=query,
                        severity=Severity.MEDIUM if signal["confidence"] >= 0.75 else Severity.LOW,
                        description=signal["summary"],
                        evidence=signal,
                        tags=["osint", "breach", "credential"],
                    ))
            return ModuleResult(success=True, output={"query": query, "tool_available": False, "breaches": [], "heuristics": heuristics}, findings=findings, raw_output=wrapper_result.get("raw_output", ""))

        for breach in breaches:
            summary = breach.get("summary") if isinstance(breach, dict) else str(breach)
            findings.append(self.make_finding(
                title=f"Breach exposure linked to {query}",
                target=query,
                severity=Severity.HIGH,
                description=summary[:240],
                evidence=breach if isinstance(breach, dict) else {"summary": summary},
                tags=["osint", "breach", "credential"],
            ))
        return ModuleResult(success=True, output={"query": query, "tool_available": True, "breaches": breaches}, findings=findings, raw_output=wrapper_result.get("raw_output", ""))

    def _heuristic_signals(self, query: str) -> List[Dict[str, Any]]:
        signals: List[Dict[str, Any]] = []
        if EMAIL_RE.match(query):
            local, domain = query.split("@", 1)
            signals.append({"type": "email_pattern", "confidence": 0.68, "summary": f"Email local-part '{local}' is reusable across breach corpora for domain {domain}."})
            if any(token in local.lower() for token in ("admin", "support", "it", "helpdesk")):
                signals.append({"type": "privileged_alias", "confidence": 0.81, "summary": "Address appears to represent a role account, which often correlates with broad credential reuse."})
        else:
            base = query.lower().replace("_", "").replace("-", "")
            signals.append({"type": "username_reuse", "confidence": 0.61, "summary": f"Username stem '{base[:12]}' is suitable for cross-platform breach correlation pivots."})
            if any(ch.isdigit() for ch in query):
                signals.append({"type": "patterned_suffix", "confidence": 0.58, "summary": "Numeric suffixes suggest a predictable username variant strategy across services."})
        return signals
