from __future__ import annotations

from typing import Dict

from framework.intelligence.tool_wrapper import ToolWrapper


class Wafw00fWrapper(ToolWrapper):
    tool_name = "waf_detector"
    binary = "wafw00f"
    timeout = 60

    def build_command(self, target: str):
        return [self.binary, target, "-a"]

    def parse_output(self, raw: str) -> Dict:
        detections = []
        for line in raw.splitlines():
            text = line.strip()
            if not text:
                continue
            if "is behind" in text or "WAF" in text.upper():
                detections.append(text)
        return {"detections": detections, "raw_lines": [line for line in raw.splitlines() if line.strip()]}

    def validate(self, data: Dict) -> bool:
        return "detections" in data
