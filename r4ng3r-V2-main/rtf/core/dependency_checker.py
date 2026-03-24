"""
RTF v2.0 — Core Dependency Checker
Verify tool installations, check versions, and update if outdated.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


@dataclass
class ToolStatus:
    name:            str
    installed:       bool
    binary_path:     str   = ""
    installed_version: str = ""
    latest_version:  str   = ""
    needs_update:    bool  = False
    install_method:  str   = ""
    error:           str   = ""
    last_checked:    str   = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


# Full tool catalogue: (name, binary, version_flag, install_method, install_cmd)
TOOL_CATALOGUE: List[Tuple[str, str, str, str, str]] = [
    # Recon
    ("amass",        "amass",         "--version", "go",     "go install github.com/owasp-amass/amass/v4/...@latest"),
    ("subfinder",    "subfinder",     "-version",  "go",     "go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"),
    ("naabu",        "naabu",         "-version",  "go",     "go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"),
    ("assetfinder",  "assetfinder",   "",          "go",     "go install github.com/tomnomnom/assetfinder@latest"),
    ("httprobe",     "httprobe",      "",          "go",     "go install github.com/tomnomnom/httprobe@latest"),
    ("gobuster",     "gobuster",      "version",   "go",     "go install github.com/OJ/gobuster/v3@latest"),
    ("ffuf",         "ffuf",          "-V",        "go",     "go install github.com/ffuf/ffuf/v2@latest"),
    ("whatweb",      "whatweb",       "--version", "gem",    "gem install whatweb"),
    ("photon",       "photon",        "",          "git",    "https://github.com/s0md3v/Photon"),
    ("altdns",       "altdns",        "--version", "pip",    "pip install altdns"),
    ("dirsearch",    "dirsearch",     "",          "git",    "https://github.com/maurosoria/dirsearch"),
    ("recon-ng",     "recon-ng",      "",          "git",    "https://github.com/lanmaster53/recon-ng"),
    ("spiderfoot",   "spiderfoot",    "",          "git",    "https://github.com/smicallef/spiderfoot"),
    ("rengine",      "rengine",       "",          "git",    "https://github.com/yogeshojha/rengine"),
    ("vhostscan",    "virtual-host-discovery", "", "gem",   "gem install virtual-host-discovery"),
    # OSINT
    ("sherlock",     "sherlock",      "",          "pipx",   "pipx install sherlock-project"),
    ("social-analyzer","social-analyzer","",       "pipx",   "pipx install social-analyzer"),
    ("osintgram",    "osintgram",     "",          "git",    "https://github.com/Datalux/Osintgram"),
    ("phoneinfoga",  "phoneinfoga",   "--version", "go",     "go install github.com/sundowndev/phoneinfoga/v2/cmd/phoneinfoga@latest"),
    ("profil3r",     "profil3r",      "",          "git",    "https://github.com/Rog3rSm1th/Profil3r"),
    ("maigret",      "maigret",       "--version", "pipx",   "pipx install maigret"),
    ("holehe",       "holehe",        "",          "pipx",   "pipx install holehe"),
    ("h8mail",       "h8mail",        "",          "pipx",   "pipx install h8mail"),
    # Scanning
    ("nuclei",       "nuclei",        "-version",  "go",     "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"),
    ("trivy",        "trivy",         "--version", "apt",    "apt install trivy"),
    ("kubescape",    "kubescape",     "version",   "curl",   "curl -s https://raw.githubusercontent.com/kubescape/kubescape/master/install.sh | /bin/bash"),
    ("lynis",        "lynis",         "--version", "apt",    "apt install lynis"),
    # Web exploitation
    ("sqlmap",       "sqlmap",        "--version", "apt",    "apt install sqlmap"),
    ("dalfox",       "dalfox",        "version",   "go",     "go install github.com/hahwul/dalfox/v2@latest"),
    ("commix",       "commix",        "--version", "git",    "https://github.com/commixproject/commix"),
    ("wfuzz",        "wfuzz",         "--version", "pip",    "pip install wfuzz"),
    ("wpscan",       "wpscan",        "--version", "gem",    "gem install wpscan"),
    ("ssrfmap",      "ssrfmap",       "",          "git",    "https://github.com/swisskyrepo/SSRFmap"),
    ("nosqlmap",     "nosqlmap",      "",          "git",    "https://github.com/codingo/NoSQLMap"),
    ("cmseek",       "cmseek",        "",          "git",    "https://github.com/Tuhinshubhra/CMSeek"),
    # Credential attacks
    ("hydra",        "hydra",         "--version", "apt",    "apt install hydra"),
    ("kerbrute",     "kerbrute",      "version",   "go",     "go install github.com/ropnop/kerbrute@latest"),
    ("hashcat",      "hashcat",       "--version", "apt",    "apt install hashcat"),
    ("john",         "john",          "--version", "apt",    "apt install john"),
    ("ncrack",       "ncrack",        "--version", "apt",    "apt install ncrack"),
    # Exploitation
    ("msfconsole",   "msfconsole",    "--version", "apt",    "apt install metasploit-framework"),
    # Post-exploitation
    ("evil-winrm",   "evil-winrm",    "--version", "gem",    "gem install evil-winrm"),
    ("bloodhound-python","bloodhound-python","",   "pip",    "pip install bloodhound"),
    # RE
    ("radare2",      "r2",            "--version", "apt",    "apt install radare2"),
    ("rizin",        "rizin",         "--version", "apt",    "apt install rizin"),
    # Network/MITM
    ("mitmproxy",    "mitmproxy",     "--version", "pipx",   "pipx install mitmproxy"),
    ("bettercap",    "bettercap",     "--version", "apt",    "apt install bettercap"),
    ("wifiphisher",  "wifiphisher",   "--version", "git",    "https://github.com/wifiphisher/wifiphisher"),
    ("hcxdumptool",  "hcxdumptool",   "--version", "apt",    "apt install hcxdumptool"),
    ("hcxtools",     "hcxdumptool",   "--version", "apt",    "apt install hcxtools"),
    # Threat intelligence
    ("intelowl",     "intelowl",      "",          "docker", "docker pull intelowlproject/intelowl"),
    # Infra
    ("nmap",         "nmap",          "--version", "apt",    "apt install nmap"),
    ("masscan",      "masscan",       "--version", "apt",    "apt install masscan"),
    ("httpx",        "httpx",         "-version",  "go",     "go install github.com/projectdiscovery/httpx/cmd/httpx@latest"),
    ("dnsx",         "dnsx",          "-version",  "go",     "go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest"),
    ("katana",       "katana",        "-version",  "go",     "go install github.com/projectdiscovery/katana/cmd/katana@latest"),
    ("feroxbuster",  "feroxbuster",   "--version", "cargo",  "cargo install feroxbuster"),
    ("rustscan",     "rustscan",      "--version", "cargo",  "cargo install rustscan"),
]


class DependencyChecker:
    """Check, verify, and update tool installations."""

    def __init__(self) -> None:
        self._statuses: Dict[str, ToolStatus] = {}
        self._last_full_check: Optional[str] = None

    # ─── Core checks ────────────────────────────────────────────────

    def check_installed_tools(self, tools: Optional[List[str]] = None) -> Dict[str, ToolStatus]:
        """Check which tools are installed. Optionally filter by name list."""
        catalogue = [(n,b,vf,im,ic) for n,b,vf,im,ic in TOOL_CATALOGUE
                     if tools is None or n in tools]
        for name, binary, version_flag, install_method, install_cmd in catalogue:
            path = shutil.which(binary)
            installed_version = ""
            error = ""
            if path and version_flag:
                try:
                    result = subprocess.run(
                        [binary, version_flag],
                        capture_output=True, text=True, timeout=8
                    )
                    out = (result.stdout + result.stderr).strip()
                    # Extract version from output
                    m = re.search(r"(\d+\.\d+[\.\d]*)", out)
                    if m:
                        installed_version = m.group(1)
                    else:
                        installed_version = out.split("\n")[0][:40]
                except Exception as exc:
                    error = str(exc)[:80]
            self._statuses[name] = ToolStatus(
                name=name, installed=path is not None, binary_path=path or "",
                installed_version=installed_version, install_method=install_method,
                error=error,
            )
        self._last_full_check = datetime.utcnow().isoformat()
        return self._statuses

    async def compare_latest_versions(self, tools: Optional[List[str]] = None) -> Dict[str, ToolStatus]:
        """Compare installed vs latest versions for Go/GitHub tools."""
        if not _HAS_HTTPX:
            return self._statuses
        statuses = self._statuses or {}
        if not statuses:
            self.check_installed_tools(tools)
            statuses = self._statuses
        for name, binary, version_flag, install_method, install_cmd in TOOL_CATALOGUE:
            if tools and name not in tools:
                continue
            status = statuses.get(name)
            if not status or not status.installed:
                continue
            # For Go tools, check pkg.go.dev
            if install_method == "go" and "@latest" in install_cmd:
                pkg = install_cmd.replace("go install ", "").replace("@latest", "").strip()
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        resp = await client.get(f"https://proxy.golang.org/{pkg}/@latest")
                        if resp.status_code == 200:
                            data = resp.json()
                            latest = data.get("Version","").lstrip("v")
                            status.latest_version = latest
                            if latest and status.installed_version:
                                status.needs_update = latest != status.installed_version
                except Exception:
                    pass
        return self._statuses

    async def update_if_outdated(self, tools: Optional[List[str]] = None) -> Dict[str, bool]:
        """Update tools that need updating. Returns {name: success}."""
        results: Dict[str, bool] = {}
        for name, status in self._statuses.items():
            if tools and name not in tools:
                continue
            if not status.needs_update:
                continue
            # Find install command
            install_cmd = next((ic for n,b,vf,im,ic in TOOL_CATALOGUE if n==name), "")
            if not install_cmd or install_cmd.startswith("http"):
                continue
            parts = install_cmd.split()
            try:
                result = subprocess.run(parts, capture_output=True, text=True, timeout=300)
                results[name] = result.returncode == 0
            except Exception:
                results[name] = False
        return results

    # ─── Reporting ──────────────────────────────────────────────────

    def summary_report(self) -> str:
        if not self._statuses:
            self.check_installed_tools()
        installed = [s for s in self._statuses.values() if s.installed]
        missing   = [s for s in self._statuses.values() if not s.installed]
        outdated  = [s for s in installed if s.needs_update]
        lines = [
            f"Tool Status Report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"{'─'*55}",
            f"Installed : {len(installed)}/{len(self._statuses)}",
            f"Missing   : {len(missing)}",
            f"Outdated  : {len(outdated)}",
            "", "INSTALLED:",
        ]
        for s in sorted(installed, key=lambda x: x.name):
            upd = " [UPDATE AVAILABLE]" if s.needs_update else ""
            lines.append(f"  ✓ {s.name:20} {s.installed_version[:20]}{upd}")
        lines.append("\nMISSING:")
        for s in sorted(missing, key=lambda x: x.name):
            lines.append(f"  ✗ {s.name:20} (install via {s.install_method})")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {"checked_at": self._last_full_check,
             "tools": {n: s.to_dict() for n, s in self._statuses.items()}},
            indent=2,
        )

    def missing_critical(self) -> List[str]:
        """Return names of critical tools that are not installed."""
        critical = {"nmap","subfinder","nuclei","httpx","ffuf","sqlmap","hydra","sherlock","amass"}
        return [n for n in critical if n in self._statuses and not self._statuses[n].installed]


# Module-level singleton
dependency_checker = DependencyChecker()
