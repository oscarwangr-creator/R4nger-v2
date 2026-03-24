"""RTF — TI: ThreatIngestor threat feed aggregator"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class ThreatingestorWrapper(ToolWrapper):
    BINARY = "threatingestor"; TOOL_NAME = "ThreatIngestor"; TIMEOUT = 120
    INSTALL_CMD = "pip install threatingestor"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        config = options.get("config", "threatingestor_config.yml")
        return [self.BINARY, config]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        iocs = {"ips": self._extract_ips(raw), "domains": self._extract_domains(raw),
                "urls": self._extract_urls(raw), "emails": self._extract_emails(raw)}
        return {"iocs": iocs, "target": target}

