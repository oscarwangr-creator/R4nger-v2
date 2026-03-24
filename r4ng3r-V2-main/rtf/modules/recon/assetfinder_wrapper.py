"""RTF — Recon: Assetfinder wrapper"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class AssetfinderWrapper(ToolWrapper):
    BINARY = "assetfinder"; TOOL_NAME = "Assetfinder"; TIMEOUT = 120
    INSTALL_CMD = "go install github.com/tomnomnom/assetfinder@latest"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY]
        if options.get("subs_only", True): cmd.append("--subs-only")
        cmd.append(target)
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        subs = list(dict.fromkeys(l.strip() for l in raw.splitlines() if l.strip()))
        return {"assets": subs, "count": len(subs), "target": target}

