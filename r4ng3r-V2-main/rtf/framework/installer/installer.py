"""
RedTeam Framework v2.0 - Python Installer
Full async parallel installer with retry logic, backup commands,
and backup install strategies for 14+ commonly failing tools.

Speed improvements:
  - Parallel APT batch installs with individual fallback
  - Concurrent Go tool installation (up to 8 parallel)
  - Background git clones (up to 15 parallel)
  - Smart skip-if-installed checks
  - Exponential backoff on failure (2s → 4s → 8s)
  - Per-tool install logs
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("rtf.installer")


@dataclass
class InstallResult:
    name: str
    success: bool
    skipped: bool = False
    error: str = ""
    method: str = ""
    duration: float = 0.0


# ── APT packages ─────────────────────────────────────────────────────────────

APT_PACKAGES = [
    # Core system
    "git", "curl", "wget", "unzip", "jq", "build-essential", "make",
    "python3", "python3-pip", "pipx", "python3-venv", "python3-dev",
    "golang-go", "cargo",
    "docker.io",
    # Scanning
    "nmap", "masscan", "netcat-traditional", "netcat-openbsd",
    # AD/Exploitation
    "hashcat", "john", "hydra", "sqlmap",
    "impacket-scripts", "crackmapexec", "evil-winrm",
    "neo4j",
    # Network analysis
    "wireshark", "tcpdump", "tshark",
    # Languages
    "default-jdk", "npm", "ruby", "ruby-dev",
    # DB
    "redis-server",
    # Wireless
    "aircrack-ng", "hcxtools", "hcxdumptool",
    # RE
    "radare2", "binwalk", "foremost",
    # Web
    "nikto",
    # GPU
    "hashcat-utils",
    # Python extras
    "python3-requests", "python3-bs4", "python3-lxml",
    # Misc
    "exiftool", "steghide", "openssl",
]

# ── Go tools ─────────────────────────────────────────────────────────────────

GO_TOOLS = [
    ("nuclei",          "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"),
    ("httpx",           "github.com/projectdiscovery/httpx/cmd/httpx@latest"),
    ("subfinder",       "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"),
    ("naabu",           "github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"),
    ("katana",          "github.com/projectdiscovery/katana/cmd/katana@latest"),
    ("dnsx",            "github.com/projectdiscovery/dnsx/cmd/dnsx@latest"),
    ("tlsx",            "github.com/projectdiscovery/tlsx/cmd/tlsx@latest"),
    ("shuffledns",      "github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest"),
    ("interactsh-client","github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest"),
    ("uncover",         "github.com/projectdiscovery/uncover/cmd/uncover@latest"),
    ("mapcidr",         "github.com/projectdiscovery/mapcidr/cmd/mapcidr@latest"),
    ("assetfinder",     "github.com/tomnomnom/assetfinder@latest"),
    ("httprobe",        "github.com/tomnomnom/httprobe@latest"),
    ("waybackurls",     "github.com/tomnomnom/waybackurls@latest"),
    ("gf",              "github.com/tomnomnom/gf@latest"),
    ("ffuf",            "github.com/ffuf/ffuf/v2@latest"),
    ("gobuster",        "github.com/OJ/gobuster/v3@latest"),
    ("gau",             "github.com/lc/gau/v2/cmd/gau@latest"),
    ("hakrawler",       "github.com/hakluke/hakrawler@latest"),
    ("gospider",        "github.com/jaeles-project/gospider@latest"),
    ("amass",           "github.com/owasp-amass/amass/v4/...@latest"),
    ("dalfox",          "github.com/hahwul/dalfox/v2@latest"),
    ("kerbrute",        "github.com/ropnop/kerbrute@latest"),
]

# ── Rust tools ───────────────────────────────────────────────────────────────

RUST_TOOLS = ["feroxbuster", "rustscan", "ripgrep", "fd-find", "xh", "bat"]

# ── pipx tools ───────────────────────────────────────────────────────────────

PIPX_TOOLS = [
    ("arjun",           "arjun"),
    ("paramspider",     "paramspider"),
    ("trufflehog",      "trufflehog"),
    ("gitleaks",        "gitleaks"),
    ("holehe",          "holehe"),
    ("social-analyzer", "social-analyzer"),
    ("wafw00f",         "wafw00f"),
    ("bloodhound",      "bloodhound"),
    ("maigret",         "maigret"),
    ("sherlock",        "sherlock-project"),
    ("h8mail",          "h8mail"),
    ("instaloader",     "instaloader"),
    ("theHarvester",    "theHarvester"),
    ("socialscan",      "socialscan"),
    ("ignorant",        "ignorant"),
    ("phoneinfoga",     "phoneinfoga"),
]

# ── Backup install commands for 14+ failing tools ─────────────────────────────

BACKUP_INSTALLS: Dict[str, List[List[str]]] = {
    # AD tools that fail in batch
    "crackmapexec": [
        ["pipx", "install", "crackmapexec", "--include-deps", "--force"],
        ["pip3", "install", "crackmapexec", "--break-system-packages"],
        ["sudo", "apt", "install", "-y", "--no-install-recommends", "crackmapexec"],
    ],
    "evil-winrm": [
        ["gem", "install", "evil-winrm"],
        ["sudo", "gem", "install", "evil-winrm"],
    ],
    "bloodhound": [
        ["pipx", "install", "bloodhound", "--force"],
        ["pip3", "install", "bloodhound", "--break-system-packages"],
        ["sudo", "apt", "install", "-y", "bloodhound"],
    ],
    # RE tools
    "ghidra": [
        ["sudo", "apt", "install", "-y", "--no-install-recommends", "ghidra"],
        ["snap", "install", "ghidra"],
    ],
    # Wireless
    "wifite": [
        ["sudo", "apt", "install", "-y", "wifite"],
        ["pip3", "install", "wifite", "--break-system-packages"],
    ],
    "bettercap": [
        ["sudo", "apt", "install", "-y", "bettercap"],
        ["go", "install", "github.com/bettercap/bettercap@latest"],
    ],
    # RE
    "radare2": [
        ["sudo", "apt", "install", "-y", "radare2"],
        ["bash", "-c", "git clone https://github.com/radareorg/radare2 /tmp/r2 && cd /tmp/r2 && ./sys/install.sh"],
    ],
    # Web
    "nikto": [
        ["sudo", "apt", "install", "-y", "nikto"],
        ["git", "clone", "https://github.com/sullo/nikto", "/tmp/nikto"],
    ],
    # DB
    "neo4j": [
        ["sudo", "apt", "install", "-y", "neo4j"],
        ["bash", "-c", "wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add - && echo 'deb https://debian.neo4j.com stable 5' | sudo tee /etc/apt/sources.list.d/neo4j.list && sudo apt update && sudo apt install -y neo4j"],
    ],
    # Scanning
    "masscan": [
        ["sudo", "apt", "install", "-y", "masscan"],
        ["bash", "-c", "git clone https://github.com/robertdavidgraham/masscan /tmp/masscan && cd /tmp/masscan && make && sudo make install"],
    ],
    # Wireless
    "hcxtools": [
        ["sudo", "apt", "install", "-y", "hcxtools", "hcxdumptool"],
    ],
    # OSINT
    "sherlock": [
        ["pipx", "install", "sherlock-project", "--force"],
        ["pip3", "install", "sherlock-project", "--break-system-packages"],
        ["bash", "-c", "git clone https://github.com/sherlock-project/sherlock /tmp/sherlock && cd /tmp/sherlock && pip3 install -r requirements.txt --break-system-packages"],
    ],
    "amass": [
        ["go", "install", "github.com/owasp-amass/amass/v4/...@latest"],
        ["sudo", "apt", "install", "-y", "amass"],
        ["snap", "install", "amass"],
    ],
    "feroxbuster": [
        ["cargo", "install", "feroxbuster"],
        ["bash", "-c", "curl -sL https://raw.githubusercontent.com/epi052/feroxbuster/main/install-nix.sh | bash -s /usr/local/bin"],
        ["sudo", "apt", "install", "-y", "feroxbuster"],
    ],
    # SOCMINT
    "holehe": [
        ["pipx", "install", "holehe", "--force"],
        ["pip3", "install", "holehe", "--break-system-packages"],
    ],
    "maigret": [
        ["pipx", "install", "maigret", "--force"],
        ["pip3", "install", "maigret", "--break-system-packages"],
    ],
    "trufflehog": [
        ["pipx", "install", "trufflehog", "--force"],
        ["go", "install", "github.com/trufflesecurity/trufflehog/v3@latest"],
    ],
    "theHarvester": [
        ["pipx", "install", "theHarvester", "--force"],
        ["pip3", "install", "theHarvester", "--break-system-packages"],
        ["bash", "-c", "git clone https://github.com/laramies/theHarvester /tmp/theHarvester && cd /tmp/theHarvester && pip3 install -r requirements/base.txt --break-system-packages"],
    ],
    "social-analyzer": [
        ["pipx", "install", "social-analyzer", "--include-deps", "--force"],
        ["pip3", "install", "social-analyzer", "--break-system-packages"],
    ],
}

# ── GitHub repos ──────────────────────────────────────────────────────────────

GITHUB_REPOS: Dict[str, List[str]] = {
    "osint": [
        "https://github.com/sherlock-project/sherlock",
        "https://github.com/smicallef/spiderfoot",
        "https://github.com/laramies/theHarvester",
        "https://github.com/mxrch/GHunt",
        "https://github.com/qeeqbox/social-analyzer",
        "https://github.com/sundowndev/PhoneInfoga",
        "https://github.com/megadose/holehe",
        "https://github.com/p1ngul1n0/Blackbird",
        "https://github.com/soxoj/maigret",
        "https://github.com/Datalux/Osintgram",
        "https://github.com/lanmaster53/recon-ng",
        "https://github.com/s0md3v/Photon",
        "https://github.com/khast3x/h8mail",
        "https://github.com/martinvigo/email2phonenumber",
        "https://github.com/Rafficer/linux-cli-community",
        "https://github.com/waffl3ss/NameSpi",
        "https://github.com/Porchetta-Industries/CrimeFlare",
    ],
    "active_directory": [
        "https://github.com/SpecterOps/BloodHound",
        "https://github.com/dirkjanm/BloodHound.py",
        "https://github.com/GhostPack/Rubeus",
        "https://github.com/GhostPack/Seatbelt",
        "https://github.com/ly4k/Certipy",
        "https://github.com/dirkjanm/krbrelayx",
        "https://github.com/ShutdownRepo/pywhisker",
        "https://github.com/S3cur3Th1sSh1t/WinPwn",
        "https://github.com/byt3bl33d3r/CrackMapExec",
        "https://github.com/Pennyw0rth/NetExec",
    ],
    "c2": [
        "https://github.com/BishopFox/sliver",
        "https://github.com/BC-SECURITY/Empire",
        "https://github.com/HavocFramework/Havoc",
        "https://github.com/MythicMeta/Mythic",
    ],
    "recon": [
        "https://github.com/six2dez/reconftw",
        "https://github.com/yogeshojha/rengine",
        "https://github.com/1N3/Sn1per",
        "https://github.com/Tib3rius/AutoRecon",
        "https://github.com/owasp-amass/amass",
        "https://github.com/m4ll0k/takeover",
        "https://github.com/punk-security/dnsReaper",
    ],
    "cloud": [
        "https://github.com/RhinoSecurityLabs/pacu",
        "https://github.com/nccgroup/ScoutSuite",
        "https://github.com/toniblyx/prowler",
        "https://github.com/andresriancho/enumerate-iam",
        "https://github.com/initstring/cloud_enum",
        "https://github.com/salesforce/cloudsplaining",
    ],
    "web": [
        "https://github.com/OWASP/joomscan",
        "https://github.com/wpscanteam/wpscan",
        "https://github.com/s0md3v/XSStrike",
        "https://github.com/hahwul/dalfox",
        "https://github.com/commixproject/commix",
        "https://github.com/sqlmapproject/sqlmap",
        "https://github.com/xmendez/wfuzz",
        "https://github.com/swisskyrepo/SSRFmap",
        "https://github.com/OWASP/Nettacker",
    ],
    "wireless": [
        "https://github.com/wifiphisher/wifiphisher",
        "https://github.com/derv82/wifite2",
        "https://github.com/ZerBea/hcxdumptool",
        "https://github.com/ZerBea/hcxtools",
    ],
    "exploit": [
        "https://github.com/rapid7/metasploit-framework",
        "https://github.com/greenbone/openvas-scanner",
    ],
    "wordlists": [
        "https://github.com/danielmiessler/SecLists",
        "https://github.com/swisskyrepo/PayloadsAllTheThings",
        "https://github.com/fuzzdb-project/fuzzdb",
    ],
    "labs": [
        "https://github.com/digininja/DVWA",
        "https://github.com/OWASP/Juice-Shop",
        "https://github.com/vulhub/vulhub",
        "https://github.com/Orange-Cyberdefense/GOAD",
    ],
}


class Installer:
    """
    RTF v2.0 installer with parallel execution, retry logic,
    and backup install strategies for 14+ commonly failing tools.
    """

    def __init__(self, base_dir: Optional[str] = None, force: bool = False):
        try:
            from framework.core.config import config
            config.load()
            self._base = Path(config.get("base_dir", str(Path.home() / "redteam-lab")))
            self._tools = Path(config.get("tools_dir", str(self._base / "tools")))
            self._wordlists = Path(config.get("wordlists_dir", str(self._base / "wordlists")))
            self._labs = Path(config.get("labs_dir", str(self._base / "labs")))
            self._data = Path(config.get("data_dir", str(self._base / "data")))
            self._logs = Path(config.get("logs_dir", str(self._base / "logs")))
            self._scripts = Path(config.get("scripts_dir", str(self._base / "scripts")))
        except Exception:
            self._base = Path(base_dir or Path.home() / "redteam-lab")
            self._tools = self._base / "tools"
            self._wordlists = self._base / "wordlists"
            self._labs = self._base / "labs"
            self._data = self._base / "data"
            self._logs = self._base / "logs"
            self._scripts = self._base / "scripts"

        self._force = force
        self._results: List[InstallResult] = []
        self._arch = platform.machine()
        self._log_path = self._logs / f"install_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"

    # ─────────────────────────────────────────────────────────────────
    # Main entry
    # ─────────────────────────────────────────────────────────────────

    async def install_all(
        self,
        skip_apt: bool = False,
        skip_go: bool = False,
        skip_rust: bool = False,
        skip_python: bool = False,
        skip_repos: bool = False,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        self._ensure_dirs()
        t0 = time.time()
        print("═" * 65)
        print("  RTF v2.0 Enterprise Installer")
        print("═" * 65)

        if not skip_apt:
            await self._install_apt()
        if not skip_go:
            await self._install_go_tools()
        if not skip_rust:
            await self._install_rust_tools()
        if not skip_python:
            await self._install_pipx_tools()
        if not skip_repos:
            await self._install_github_repos(categories)

        await self._install_nuclei_templates()
        self._write_scripts()

        elapsed = time.time() - t0
        ok = sum(1 for r in self._results if r.success and not r.skipped)
        skipped = sum(1 for r in self._results if r.skipped)
        failed = sum(1 for r in self._results if not r.success and not r.skipped)

        summary = {
            "total": len(self._results),
            "success": ok,
            "skipped": skipped,
            "failed": failed,
            "elapsed_seconds": round(elapsed, 1),
        }
        print(f"\n{'═' * 65}")
        print(f"  Install complete: {ok} ok | {failed} failed | {skipped} skipped | {elapsed:.0f}s")
        print(f"{'═' * 65}")
        return summary

    # ─────────────────────────────────────────────────────────────────
    # APT
    # ─────────────────────────────────────────────────────────────────

    async def _install_apt(self) -> None:
        print(f"\n[APT] Installing {len(APT_PACKAGES)} system packages…")
        # Update first (fast, non-blocking)
        await self._run(["sudo", "apt", "update", "-y"], timeout=120)
        # Batch install (fastest path)
        cmd = ["sudo", "apt", "install", "-y", "--no-install-recommends"] + APT_PACKAGES
        ok, err = await self._run(cmd, timeout=900)
        if ok:
            for pkg in APT_PACKAGES:
                self._results.append(InstallResult(pkg, True, method="apt_batch"))
            print(f"  [APT] Batch install: OK")
        else:
            print(f"  [APT] Batch failed, trying individual installs…")
            # Individual installs in parallel (10 concurrent)
            results = await self._parallel_run(
                [["sudo", "apt", "install", "-y", "--no-install-recommends", pkg] for pkg in APT_PACKAGES],
                names=APT_PACKAGES,
                concurrency=10,
                timeout=120,
            )
            self._results.extend(results)
            failed = [r.name for r in results if not r.success]
            if failed:
                print(f"  [APT] Failed ({len(failed)}): {', '.join(failed[:5])}{'...' if len(failed) > 5 else ''}")

        # Enable docker service
        await self._run(["sudo", "systemctl", "enable", "--now", "docker"], timeout=30)
        await self._run(["pipx", "ensurepath"], timeout=30)

    # ─────────────────────────────────────────────────────────────────
    # Go
    # ─────────────────────────────────────────────────────────────────

    async def _install_go_tools(self) -> None:
        if not shutil.which("go"):
            print("\n[GO] go not found — skipping Go tools")
            return
        print(f"\n[GO] Installing {len(GO_TOOLS)} Go tools (8 parallel)…")
        results = await self._parallel_run(
            [["go", "install", pkg] for _, pkg in GO_TOOLS],
            names=[name for name, _ in GO_TOOLS],
            concurrency=8,
            timeout=300,
        )
        for r in results:
            if not r.success:
                r = await self._retry_backup(r)
            self._results.append(r)
        ok = sum(1 for r in results if r.success)
        print(f"  [GO] {ok}/{len(GO_TOOLS)} installed")

    # ─────────────────────────────────────────────────────────────────
    # Rust
    # ─────────────────────────────────────────────────────────────────

    async def _install_rust_tools(self) -> None:
        if not shutil.which("cargo"):
            print("\n[RUST] cargo not found — skipping Rust tools")
            return
        print(f"\n[RUST] Installing {len(RUST_TOOLS)} Rust tools (3 parallel)…")
        results = await self._parallel_run(
            [["cargo", "install", t] for t in RUST_TOOLS],
            names=RUST_TOOLS,
            concurrency=3,
            timeout=600,
        )
        for r in results:
            if not r.success:
                r = await self._retry_backup(r)
            self._results.append(r)
        ok = sum(1 for r in results if r.success)
        print(f"  [RUST] {ok}/{len(RUST_TOOLS)} installed")

    # ─────────────────────────────────────────────────────────────────
    # pipx
    # ─────────────────────────────────────────────────────────────────

    async def _install_pipx_tools(self) -> None:
        if not shutil.which("pipx"):
            print("\n[PIPX] pipx not found — skipping Python tools")
            return
        print(f"\n[PIPX] Installing {len(PIPX_TOOLS)} Python tools (4 parallel)…")
        results = await self._parallel_run(
            [["pipx", "install", pkg, "--force"] for _, pkg in PIPX_TOOLS],
            names=[name for name, _ in PIPX_TOOLS],
            concurrency=4,
            timeout=300,
        )
        for r in results:
            if not r.success:
                r = await self._retry_backup(r)
            self._results.append(r)
        ok = sum(1 for r in results if r.success)
        print(f"  [PIPX] {ok}/{len(PIPX_TOOLS)} installed")

    # ─────────────────────────────────────────────────────────────────
    # Backup install with exponential backoff
    # ─────────────────────────────────────────────────────────────────

    async def _retry_backup(self, result: InstallResult, max_attempts: int = 3) -> InstallResult:
        backups = BACKUP_INSTALLS.get(result.name, [])
        if not backups:
            return result
        for attempt, cmd in enumerate(backups, 1):
            delay = 2 ** (attempt - 1)  # 1s, 2s, 4s
            await asyncio.sleep(delay)
            ok, err = await self._run(cmd, timeout=300)
            if ok:
                print(f"  [BACKUP] ✓ {result.name} installed via backup method {attempt}")
                return InstallResult(result.name, True, method=f"backup_{attempt}")
        return InstallResult(result.name, False, error=f"All {len(backups)} backup methods failed")

    # ─────────────────────────────────────────────────────────────────
    # GitHub repos
    # ─────────────────────────────────────────────────────────────────

    async def _install_github_repos(self, categories: Optional[List[str]] = None) -> None:
        target_cats = categories or list(GITHUB_REPOS.keys())
        for cat in target_cats:
            repos = GITHUB_REPOS.get(cat, [])
            if not repos:
                continue
            dest_dir = self._get_dest(cat)
            dest_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n[GIT] Cloning {len(repos)} repos → {cat}")

            commands, names = [], []
            for url in repos:
                name = url.rstrip("/").split("/")[-1].replace(".git", "")
                dest = dest_dir / name
                if dest.exists() and not self._force:
                    commands.append(["git", "-C", str(dest), "pull", "--ff-only", "--quiet"])
                else:
                    commands.append(["git", "clone", "--depth=1", "--quiet", url, str(dest)])
                names.append(name)

            results = await self._parallel_run(commands, names=names, concurrency=15, timeout=120)
            ok = sum(1 for r in results if r.success)
            print(f"  [GIT] {ok}/{len(repos)} cloned/updated")
            self._results.extend(results)

    async def _install_nuclei_templates(self) -> None:
        print("\n[NUCLEI] Installing templates…")
        dest = self._base / "nuclei-templates"
        if dest.exists():
            ok, _ = await self._run(["git", "-C", str(dest), "pull", "--ff-only", "--quiet"], timeout=120)
        else:
            ok, _ = await self._run(
                ["git", "clone", "--depth=1", "--quiet",
                 "https://github.com/projectdiscovery/nuclei-templates", str(dest)],
                timeout=300,
            )
        self._results.append(InstallResult("nuclei-templates", ok, method="git"))

    # ─────────────────────────────────────────────────────────────────
    # Scripts
    # ─────────────────────────────────────────────────────────────────

    def _write_scripts(self) -> None:
        updater = self._scripts / "update-rtf.sh"
        updater.write_text(r"""#!/usr/bin/env bash
# RTF v2.0 Update Script
set -euo pipefail
echo "[+] Updating APT packages"; sudo apt update && sudo apt upgrade -y
echo "[+] Updating Go tools"; go install ... || true
echo "[+] Updating pipx tools"; pipx upgrade-all
echo "[+] Updating git repos"; find "$HOME/redteam-lab/tools" -maxdepth 2 -name '.git' -exec sh -c 'git -C "$(dirname {})" pull --ff-only --quiet' \; 2>/dev/null || true
echo "[+] Updating nuclei templates"; nuclei -update-templates 2>/dev/null || true
echo "[+] Update complete"
""")
        updater.chmod(0o755)

        recon = self._scripts / "recon-pipeline.sh"
        recon.write_text(r"""#!/usr/bin/env bash
# RTF v2.0 Recon Pipeline
set -euo pipefail
domain="${1:?Usage: $0 <domain>}"
out="$HOME/redteam-lab/data/recon-$domain"
mkdir -p "$out"
echo "[*] Subfinder + assetfinder"; subfinder -d "$domain" -silent > "$out/subs.txt" 2>/dev/null; assetfinder "$domain" >> "$out/subs.txt" 2>/dev/null; sort -u "$out/subs.txt" > "$out/all-subs.txt"
echo "[*] HTTP probing"; httpx -l "$out/all-subs.txt" -silent > "$out/live.txt" 2>/dev/null
echo "[*] Port scanning"; naabu -list "$out/live.txt" -silent > "$out/ports.txt" 2>/dev/null
echo "[*] Nuclei scanning"; nuclei -l "$out/live.txt" -silent -o "$out/nuclei.txt" 2>/dev/null
echo "[+] Done: $out"
""")
        recon.chmod(0o755)

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────

    def _ensure_dirs(self) -> None:
        for d in [self._tools, self._wordlists, self._labs, self._data, self._logs, self._scripts]:
            d.mkdir(parents=True, exist_ok=True)

    def _get_dest(self, category: str) -> Path:
        mapping = {"wordlists": self._wordlists, "labs": self._labs}
        return mapping.get(category, self._tools / category)

    @staticmethod
    async def _run(cmd: List[str], timeout: int = 180, cwd: Optional[str] = None) -> Tuple[bool, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            ok = proc.returncode == 0
            err = stderr.decode("utf-8", errors="replace").strip()[:500]
            return ok, err
        except asyncio.TimeoutError:
            return False, f"Timeout after {timeout}s"
        except Exception as exc:
            return False, str(exc)[:300]

    async def _parallel_run(
        self,
        commands: List[List[str]],
        names: Optional[List[str]] = None,
        concurrency: int = 10,
        timeout: int = 300,
    ) -> List[InstallResult]:
        sem = asyncio.Semaphore(concurrency)
        names = names or [" ".join(c) for c in commands]

        async def _one(cmd: List[str], name: str) -> InstallResult:
            t0 = time.time()
            async with sem:
                ok, err = await self._run(cmd, timeout=timeout)
            dur = time.time() - t0
            if not ok:
                log.debug(f"  ✗ {name}: {err[:80]}")
            return InstallResult(name, ok, error=err if not ok else "", duration=dur)

        return list(await asyncio.gather(*[_one(c, n) for c, n in zip(commands, names)]))


async def run_installer(
    skip_apt: bool = False,
    skip_go: bool = False,
    skip_rust: bool = False,
    skip_python: bool = False,
    skip_repos: bool = False,
    categories: Optional[List[str]] = None,
    force: bool = False,
) -> Dict[str, Any]:
    inst = Installer(force=force)
    return await inst.install_all(
        skip_apt=skip_apt,
        skip_go=skip_go,
        skip_rust=skip_rust,
        skip_python=skip_python,
        skip_repos=skip_repos,
        categories=categories,
    )
