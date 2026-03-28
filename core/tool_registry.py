"""Tool registry for external command integrations."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import which
from typing import Dict, List


@dataclass(slots=True)
class ToolInfo:
    name: str
    binary: str
    category: str
    required: bool = True


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolInfo] = {}

    def register(self, tool: ToolInfo) -> None:
        self._tools[tool.name] = tool

    def register_defaults(self) -> None:
        defaults = [
            ToolInfo("spiderfoot", "spiderfoot", "osint", False),
            ToolInfo("recon-ng", "recon-ng", "osint", False),
            ToolInfo("theHarvester", "theHarvester", "osint", False),
            ToolInfo("amass", "amass", "osint", False),
            ToolInfo("nmap", "nmap", "recon", True),
            ToolInfo("nuclei", "nuclei", "recon", False),
            ToolInfo("msfconsole", "msfconsole", "exploit", False),
            ToolInfo("hydra", "hydra", "exploit", False),
            ToolInfo("sqlmap", "sqlmap", "exploit", False),
            ToolInfo("photon", "photon", "recon", False),
            ToolInfo("reconftw", "reconftw", "recon", False),
            ToolInfo("sn1per", "sn1per", "recon", False),
            ToolInfo("axiom-scan", "axiom-scan", "recon", False),
            ToolInfo("xsstrike", "xsstrike", "exploit", False),
            ToolInfo("onionscan", "onionscan", "osint", False),
            ToolInfo("intelowl", "intelowl", "osint", False),
            ToolInfo("sleuthkit-fls", "fls", "post-exploit", False),
        ]
        for tool in defaults:
            self.register(tool)

        github_root = Path("tools/github")
        if github_root.exists():
            for repo_dir in sorted(path for path in github_root.iterdir() if path.is_dir()):
                slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in repo_dir.name).strip("-")
                binary = slug.split("-")[0] if slug else repo_dir.name.lower()
                self.register(
                    ToolInfo(
                        name=f"github:{repo_dir.name}",
                        binary=binary,
                        category="github-expansion",
                        required=False,
                    )
                )

    def status(self) -> List[dict]:
        return [
            {
                "name": t.name,
                "binary": t.binary,
                "category": t.category,
                "required": t.required,
                "installed": which(t.binary) is not None,
            }
            for t in self._tools.values()
        ]

    def get(self, name: str) -> dict:
        t = self._tools[name]
        return {
            "name": t.name,
            "binary": t.binary,
            "category": t.category,
            "required": t.required,
            "installed": which(t.binary) is not None,
        }
