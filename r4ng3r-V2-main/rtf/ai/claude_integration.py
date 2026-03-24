"""
RTF v2.0 — AI: Claude Integration
Provides Claude AI capabilities for:
- Stage J correlation and attack path generation
- Vulnerability prioritization
- OSINT identity correlation
- Anomaly detection
- Natural language query interface
"""
from __future__ import annotations
import json, os
from datetime import datetime
from typing import Any, Dict, List, Optional

MODEL = "claude-sonnet-4-20250514"


def _call_claude(messages: List[Dict], system: str = "", max_tokens: int = 4096,
                 api_key: str = "") -> Optional[str]:
    """Low-level Claude API call. Returns text or None on error."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        kwargs: Dict[str, Any] = {
            "model":      MODEL,
            "max_tokens": max_tokens,
            "messages":   messages,
        }
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        return resp.content[0].text if resp.content else None
    except Exception as exc:
        return None


class ClaudeCorrelationEngine:
    """Stage J — AI-powered OSINT and finding correlation engine."""

    SYSTEM_PROMPT = """You are an expert red team analyst and OSINT specialist embedded in RTF v2.0.
You receive raw intelligence data and produce structured analysis.

Rules:
- Be concise and actionable
- Always output valid JSON when asked
- Flag genuine anomalies, not noise
- Prioritize findings by exploitability and business impact
- Map findings to MITRE ATT&CK when relevant
- Never hallucinate — if data is insufficient, say so"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def correlate_osint(self, entities: Dict, profiles: List[Dict],
                        search_results: List[Dict]) -> Dict[str, Any]:
        """Correlate OSINT data and produce identity analysis."""
        payload = {
            "entities": {k: list(v)[:30] if hasattr(v,"__iter__") and not isinstance(v,str) else v
                         for k,v in entities.items()},
            "profiles_sample": profiles[:5],
            "web_results_sample": [
                {"engine": r.get("engine"), "title": r.get("title"), "url": r.get("url"),
                 "snippet": r.get("snippet","")[:150]}
                for r in search_results[:10]
            ],
        }
        prompt = f"""Analyze this OSINT intelligence and produce a JSON correlation report.

DATA:
{json.dumps(payload, indent=2, default=str)[:6000]}

Respond with ONLY valid JSON containing:
{{
  "confidence_score": <0-100>,
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "identity_summary": "<2-3 sentence synthesis>",
  "primary_aliases": ["<most used handles>"],
  "cross_platform_timeline": [
    {{"platform":"<name>","handle":"<handle>","estimated_date":"<YYYY or range>"}}
  ],
  "location_indicators": ["<geographic clues>"],
  "bio_consistency_score": <0-100>,
  "anomalies": ["<suspicious discrepancies>"],
  "top_pivots": ["<5 next investigative actions>"],
  "mitre_techniques": ["<T-IDs if applicable>"]
}}"""
        response = _call_claude(
            [{"role":"user","content": prompt}],
            system=self.SYSTEM_PROMPT,
            max_tokens=2048,
            api_key=self.api_key,
        )
        if not response:
            return self._fallback_osint(entities, profiles)
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = "\n".join(clean.split("\n")[1:-1])
            return json.loads(clean)
        except (json.JSONDecodeError, ValueError):
            return self._fallback_osint(entities, profiles)

    def correlate_findings(self, findings: List[Dict], entities: Dict,
                           target: str, profile: str) -> Dict[str, Any]:
        """Stage J — Correlate pentest findings and generate prioritized attack paths."""
        top = sorted(findings, key=lambda f: {"critical":0,"high":1,"medium":2,"low":3,"info":4}.get(
            str(f.get("severity","info")).lower(),4))[:20]

        payload = {
            "target":   target,
            "profile":  profile,
            "findings": [{"severity":f.get("severity"),"title":f.get("title"),
                          "tags":f.get("tags",[])} for f in top],
            "entities": {k: list(v)[:10] if hasattr(v,"__iter__") and not isinstance(v,str) else v
                         for k,v in entities.items()},
        }
        prompt = f"""You are analyzing red team findings. Produce a JSON correlation.

FINDINGS DATA:
{json.dumps(payload, indent=2, default=str)[:5000]}

Respond with ONLY valid JSON:
{{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "executive_summary": "<3-4 sentence executive summary>",
  "confidence_score": <0-100>,
  "critical_attack_paths": [
    {{
      "name": "<path name>",
      "steps": ["<step1>","<step2>","..."],
      "likelihood": "LOW|MEDIUM|HIGH",
      "impact": "LOW|MEDIUM|HIGH|CRITICAL",
      "mitre_chain": ["<TA/T IDs>"]
    }}
  ],
  "priority_vulns": ["<top 5 most critical findings>"],
  "remediation_priority": ["<ordered remediation list>"],
  "top_pivots": ["<next 5 investigative actions>"],
  "anomalies": ["<anything unusual>"]
}}"""
        response = _call_claude(
            [{"role":"user","content": prompt}],
            system=self.SYSTEM_PROMPT,
            max_tokens=3000,
            api_key=self.api_key,
        )
        if not response:
            return self._fallback_findings(findings, target)
        try:
            clean = response.strip()
            if clean.startswith("```"): clean = "\n".join(clean.split("\n")[1:-1])
            return json.loads(clean)
        except Exception:
            return self._fallback_findings(findings, target)

    def generate_attack_path(self, context: Dict) -> List[Dict]:
        """Generate attack paths from current context."""
        prompt = f"""Given this red team context, generate 3 concrete attack paths.

CONTEXT: {json.dumps(context, default=str)[:3000]}

Respond with ONLY a JSON array of attack path objects:
[
  {{
    "name": "<descriptive name>",
    "steps": ["<actionable step 1>","<step 2>","..."],
    "tools": ["<tool1>","<tool2>"],
    "likelihood": "LOW|MEDIUM|HIGH",
    "impact": "LOW|MEDIUM|HIGH|CRITICAL",
    "mitre_chain": ["TA0001","T1190"],
    "prerequisites": "<what is needed>",
    "notes": "<any caveats>"
  }}
]"""
        response = _call_claude(
            [{"role":"user","content": prompt}],
            system=self.SYSTEM_PROMPT,
            max_tokens=2000,
            api_key=self.api_key,
        )
        if not response:
            return []
        try:
            clean = response.strip()
            if clean.startswith("```"): clean = "\n".join(clean.split("\n")[1:-1])
            result = json.loads(clean)
            return result if isinstance(result, list) else []
        except Exception:
            return []

    def ask(self, question: str, context: Optional[str] = None) -> str:
        """Natural language query interface."""
        messages = []
        if context:
            messages.append({"role":"user","content": f"Context:\n{context[:2000]}\n\nQuestion: {question}"})
        else:
            messages.append({"role":"user","content": question})
        return _call_claude(messages, system=self.SYSTEM_PROMPT,
                            max_tokens=1000, api_key=self.api_key) or \
               "AI unavailable — check ANTHROPIC_API_KEY environment variable."

    def _fallback_osint(self, entities: Dict, profiles: List[Dict]) -> Dict:
        """Rule-based fallback when Claude API is unavailable."""
        usernames = list(entities.get("usernames",[]))
        emails    = list(entities.get("emails",[]))
        platforms = [p.get("platform","") for p in profiles if p.get("platform")]
        return {
            "confidence_score": min(30 + len(usernames)*5 + len(emails)*10, 85),
            "risk_level": "MEDIUM",
            "identity_summary": (
                f"Found {len(usernames)} username(s), {len(emails)} email(s), "
                f"{len(platforms)} platform presence(s). Manual review recommended."
            ),
            "primary_aliases": usernames[:3],
            "cross_platform_timeline": [],
            "location_indicators": [],
            "bio_consistency_score": 50,
            "anomalies": [],
            "top_pivots": [
                f"Verify email(s): {', '.join(emails[:2])}" if emails else "Search for additional email addresses",
                "Check breach databases for discovered emails",
                "Review discovered account bios for contact info",
                "Reverse image search profile photos",
                "Check linked accounts in profile bios",
            ],
            "mitre_techniques": ["TA0043"],
            "ai_used": False,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _fallback_findings(self, findings: List[Dict], target: str) -> Dict:
        """Rule-based fallback for finding correlation."""
        from collections import Counter
        sev = Counter(str(f.get("severity","info")).lower() for f in findings)
        risk = sev["critical"]*10 + sev["high"]*5 + sev["medium"]*2 + sev["low"]
        rl = "CRITICAL" if risk>=20 else "HIGH" if risk>=10 else "MEDIUM" if risk>=5 else "LOW"
        top = sorted(findings, key=lambda f: {"critical":0,"high":1,"medium":2,"low":3,"info":4}.get(
            str(f.get("severity","info")).lower(),4))[:5]
        return {
            "risk_level": rl,
            "executive_summary": (
                f"Assessment of {target} identified {len(findings)} findings "
                f"({sev['critical']} critical, {sev['high']} high, {sev['medium']} medium). "
                f"Risk score: {risk}. Immediate remediation required for critical/high findings."
            ),
            "confidence_score": 70,
            "critical_attack_paths": [],
            "priority_vulns": [f.get("title","") for f in top],
            "remediation_priority": [f.get("title","") for f in top],
            "top_pivots": ["Review critical findings first", "Check for credential exposure",
                           "Test for lateral movement paths", "Review cloud permissions"],
            "anomalies": [],
            "ai_used": False,
            "generated_at": datetime.utcnow().isoformat(),
        }


# Module-level singleton
_engine: Optional[ClaudeCorrelationEngine] = None

def get_engine(api_key: str = "") -> ClaudeCorrelationEngine:
    global _engine
    if _engine is None:
        _engine = ClaudeCorrelationEngine(api_key=api_key)
    return _engine
