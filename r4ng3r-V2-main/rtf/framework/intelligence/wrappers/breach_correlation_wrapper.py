from __future__ import annotations

import json
from typing import Dict

from framework.intelligence.tool_wrapper import ToolWrapper


class BreachCorrelationWrapper(ToolWrapper):
    tool_name = "breach_correlation"
    binary = "h8mail"
    timeout = 120

    def build_command(self, target: str):
        return [self.binary, "-t", target, "-q"]

    def parse_output(self, raw: str) -> Dict:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        breaches = []
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                breaches = payload.get("breaches", []) or payload.get("records", [])
        except Exception:
            for line in lines:
                lower = line.lower()
                if any(word in lower for word in ("breach", "pwn", "paste", "compromised")):
                    breaches.append({"summary": line})
        return {"breaches": breaches, "raw_lines": lines[:100]}

    def validate(self, data: Dict) -> bool:
        return "breaches" in data
