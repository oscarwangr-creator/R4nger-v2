from __future__ import annotations

from typing import Dict

from framework.intelligence.tool_wrapper import ToolWrapper


class WaybackUrlsWrapper(ToolWrapper):
    tool_name = "wayback_urls"
    binary = "waybackurls"
    timeout = 45

    def build_command(self, target: str):
        return [self.binary, target]

    def parse_output(self, raw: str) -> Dict:
        urls = [line.strip() for line in raw.splitlines() if line.strip().startswith(("http://", "https://"))]
        return {"urls": urls, "count": len(urls)}

    def validate(self, data: Dict) -> bool:
        return "urls" in data
