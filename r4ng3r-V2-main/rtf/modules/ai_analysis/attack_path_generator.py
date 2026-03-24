"""RTF — AI: AI-powered attack path generation"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper, WrapperResult

class AttackPathGenerator(ToolWrapper):
    BINARY = ""; TOOL_NAME = "Attack-Path-Generator"; TIMEOUT = 60
    INSTALL_CMD = "pip install anthropic"

    def run(self, target: str, options: Optional[Dict] = None) -> WrapperResult:
        """Generate attack paths from entity graph + findings using Claude AI."""
        import time
        options = options or {}
        t0 = time.monotonic()
        findings   = options.get("findings", [])
        entities   = options.get("entities", {})
        graph_data = options.get("graph_data", {})
        context = {"target": target, "findings_count": len(findings),
                   "entities": entities, "sample_findings": findings[:10]}
        prompt = (
            "You are a senior red team operator. Based on the following recon and scanning data, "
            "generate a prioritised attack path with specific exploitation steps.\n\n"
            f"Target: {target}\n"
            f"Findings:\n{json.dumps(findings[:15], indent=2)}\n"
            f"Entities found: {json.dumps(entities, indent=2)}\n\n"
            "Provide:\n1. Most likely attack path (step-by-step)\n"
            "2. Alternative attack paths\n3. Priority vulnerabilities to exploit\n"
            "4. Recommended Metasploit modules\n5. Post-exploitation objectives"
        )
        try:
            import httpx
            payload = {"model":"claude-sonnet-4-20250514","max_tokens":2000,
                       "messages":[{"role":"user","content":prompt}]}
            with httpx.Client(timeout=self.TIMEOUT) as client:
                resp = client.post("https://api.anthropic.com/v1/messages", json=payload,
                                   headers={"Content-Type":"application/json",
                                            "anthropic-version":"2023-06-01"})
                data = resp.json()
            content = "".join(b.get("text","") for b in data.get("content",[]))
            result = WrapperResult(tool=self.TOOL_NAME, target=target, success=True,
                                   data={"attack_paths": content, "source": "claude-ai",
                                         "findings_analyzed": len(findings)},
                                   duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            paths = self._rule_based_paths(findings, entities, target)
            result = WrapperResult(tool=self.TOOL_NAME, target=target, success=True,
                                   data={"attack_paths": paths, "source": "rule-based",
                                         "findings_analyzed": len(findings), "ai_error": str(exc)},
                                   duration_s=time.monotonic()-t0)
        self._last_result = result; return result

    def _rule_based_paths(self, findings: List[Dict], entities: Dict, target: str) -> str:
        """Fallback rule-based attack path when AI is unavailable."""
        paths = [f"# Rule-Based Attack Paths for {target}", ""]
        sev_map = {"critical":[], "high":[], "medium":[]}
        for f in findings:
            sev = str(f.get("severity","")).lower()
            if sev in sev_map: sev_map[sev].append(f.get("name") or f.get("title",""))
        if sev_map["critical"]:
            paths += ["## Critical Path", f"1. Exploit critical: {sev_map['critical'][0]}",
                      "2. Gain initial access", "3. Escalate privileges", "4. Lateral movement"]
        elif sev_map["high"]:
            paths += ["## High Priority Path", f"1. Exploit: {sev_map['high'][0]}",
                      "2. Enumerate further", "3. Escalate if possible"]
        else:
            paths += ["## Standard Path", "1. Enumerate further", "2. Chain medium findings",
                      "3. Look for privilege escalation vectors"]
        return "\n".join(paths)

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return {"attack_paths": raw, "target": target}

