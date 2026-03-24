"""RedTeam Framework - Tool Registry"""
from __future__ import annotations
import json, shutil, subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from framework.core.logger import get_logger

log = get_logger("rtf.registry")

class InstallType(str, Enum):
    APT = "apt"; GO = "go"; CARGO = "cargo"; PIPX = "pipx"
    PIP = "pip"; GIT = "git"; BINARY = "binary"; DOCKER = "docker"; MANUAL = "manual"

class ToolCategory(str, Enum):
    RECON = "recon"; OSINT = "osint"; EXPLOIT = "exploit"
    AD = "active_directory"; CLOUD = "cloud"; WIRELESS = "wireless"
    CRYPTO = "crypto"; C2 = "c2"; POST = "post_exploitation"
    WEB = "web"; RE = "reverse_engineering"; FORENSICS = "forensics"
    LAB = "lab"; WORDLIST = "wordlist"; UTILITY = "utility"

@dataclass
class ToolEntry:
    name: str; category: ToolCategory; install_type: InstallType; binary: str
    description: str = ""; repo_url: str = ""; install_cmd: str = ""
    apt_package: str = ""; installed: bool = False; version: str = ""
    binary_path: str = ""; last_checked: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["install_type"] = self.install_type.value
        return d

TOOL_CATALOGUE: List[Dict[str, Any]] = [
    # Recon
    {"name":"nmap","category":ToolCategory.RECON,"install_type":InstallType.APT,"binary":"nmap","apt_package":"nmap","description":"Network port scanner"},
    {"name":"masscan","category":ToolCategory.RECON,"install_type":InstallType.APT,"binary":"masscan","apt_package":"masscan","description":"Internet-scale port scanner"},
    {"name":"naabu","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"naabu","install_cmd":"go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest","description":"Fast port scanner"},
    {"name":"nuclei","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"nuclei","install_cmd":"go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest","description":"Template-based vulnerability scanner"},
    {"name":"httpx","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"httpx","install_cmd":"go install github.com/projectdiscovery/httpx/cmd/httpx@latest","description":"HTTP toolkit"},
    {"name":"subfinder","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"subfinder","install_cmd":"go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest","description":"Subdomain enumeration"},
    {"name":"assetfinder","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"assetfinder","install_cmd":"go install github.com/tomnomnom/assetfinder@latest","description":"Asset discovery"},
    {"name":"amass","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"amass","install_cmd":"go install github.com/owasp-amass/amass/v4/...@latest","description":"Attack surface mapping"},
    {"name":"katana","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"katana","install_cmd":"go install github.com/projectdiscovery/katana/cmd/katana@latest","description":"Web crawler"},
    {"name":"dnsx","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"dnsx","install_cmd":"go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest","description":"DNS toolkit"},
    {"name":"tlsx","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"tlsx","install_cmd":"go install github.com/projectdiscovery/tlsx/cmd/tlsx@latest","description":"TLS/SSL scanner"},
    {"name":"waybackurls","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"waybackurls","install_cmd":"go install github.com/tomnomnom/waybackurls@latest","description":"Fetch Wayback URLs"},
    {"name":"gau","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"gau","install_cmd":"go install github.com/lc/gau/v2/cmd/gau@latest","description":"Get All URLs"},
    {"name":"hakrawler","category":ToolCategory.RECON,"install_type":InstallType.GO,"binary":"hakrawler","install_cmd":"go install github.com/hakluke/hakrawler@latest","description":"Web spider"},
    # Web
    {"name":"ffuf","category":ToolCategory.WEB,"install_type":InstallType.GO,"binary":"ffuf","install_cmd":"go install github.com/ffuf/ffuf/v2@latest","description":"Web fuzzer"},
    {"name":"gobuster","category":ToolCategory.WEB,"install_type":InstallType.GO,"binary":"gobuster","install_cmd":"go install github.com/OJ/gobuster/v3@latest","description":"Directory brute-forcer"},
    {"name":"feroxbuster","category":ToolCategory.WEB,"install_type":InstallType.CARGO,"binary":"feroxbuster","install_cmd":"cargo install feroxbuster","description":"Fast directory brute-forcer"},
    {"name":"sqlmap","category":ToolCategory.WEB,"install_type":InstallType.APT,"binary":"sqlmap","apt_package":"sqlmap","description":"SQL injection automation"},
    {"name":"dalfox","category":ToolCategory.WEB,"install_type":InstallType.GO,"binary":"dalfox","install_cmd":"go install github.com/hahwul/dalfox/v2@latest","description":"XSS scanner"},
    {"name":"arjun","category":ToolCategory.WEB,"install_type":InstallType.PIPX,"binary":"arjun","install_cmd":"pipx install arjun","description":"HTTP parameter discovery"},
    {"name":"wafw00f","category":ToolCategory.WEB,"install_type":InstallType.PIPX,"binary":"wafw00f","install_cmd":"pipx install wafw00f","description":"WAF fingerprinting"},
    {"name":"nikto","category":ToolCategory.WEB,"install_type":InstallType.APT,"binary":"nikto","apt_package":"nikto","description":"Web server vulnerability scanner"},
    # OSINT
    {"name":"sherlock","category":ToolCategory.OSINT,"install_type":InstallType.GIT,"binary":"sherlock","repo_url":"https://github.com/sherlock-project/sherlock","description":"Username enumeration"},
    {"name":"theHarvester","category":ToolCategory.OSINT,"install_type":InstallType.GIT,"binary":"theHarvester","repo_url":"https://github.com/laramies/theHarvester","description":"Email/domain intelligence"},
    {"name":"spiderfoot","category":ToolCategory.OSINT,"install_type":InstallType.GIT,"binary":"sf.py","repo_url":"https://github.com/smicallef/spiderfoot","description":"OSINT automation framework"},
    {"name":"holehe","category":ToolCategory.OSINT,"install_type":InstallType.PIPX,"binary":"holehe","install_cmd":"pipx install holehe","description":"Email account checker"},
    {"name":"maigret","category":ToolCategory.OSINT,"install_type":InstallType.GIT,"binary":"maigret","repo_url":"https://github.com/soxoj/maigret","description":"Username OSINT"},
    {"name":"trufflehog","category":ToolCategory.OSINT,"install_type":InstallType.PIPX,"binary":"trufflehog","install_cmd":"pipx install trufflehog","description":"Secret scanner"},
    {"name":"gitleaks","category":ToolCategory.OSINT,"install_type":InstallType.PIPX,"binary":"gitleaks","install_cmd":"pipx install gitleaks","description":"Git secret scanner"},
    {"name":"phoneinfoga","category":ToolCategory.OSINT,"install_type":InstallType.GIT,"binary":"phoneinfoga","repo_url":"https://github.com/sundowndev/PhoneInfoga","description":"Phone OSINT"},
    {"name":"h8mail","category":ToolCategory.OSINT,"install_type":InstallType.PIPX,"binary":"h8mail","install_cmd":"pipx install h8mail","description":"Email breach hunter"},
    {"name":"socialscan","category":ToolCategory.OSINT,"install_type":InstallType.PIPX,"binary":"socialscan","install_cmd":"pipx install socialscan","description":"Username/email availability check"},
    {"name":"instaloader","category":ToolCategory.OSINT,"install_type":InstallType.PIPX,"binary":"instaloader","install_cmd":"pipx install instaloader","description":"Instagram OSINT"},
    {"name":"redis-server","category":ToolCategory.UTILITY,"install_type":InstallType.APT,"binary":"redis-server","apt_package":"redis-server","description":"Redis message broker for NEXUS"},
    {"name":"rabbitmq-server","category":ToolCategory.UTILITY,"install_type":InstallType.APT,"binary":"rabbitmq-server","apt_package":"rabbitmq-server","description":"RabbitMQ message broker for NEXUS"},
    {"name":"neo4j","category":ToolCategory.UTILITY,"install_type":InstallType.APT,"binary":"neo4j","apt_package":"neo4j","description":"Graph database for identity resolution"},
    {"name":"urh","category":ToolCategory.WIRELESS,"install_type":InstallType.APT,"binary":"urh","apt_package":"urh","description":"Universal Radio Hacker SDR toolkit"},
    {"name":"puppeteer","category":ToolCategory.OSINT,"install_type":InstallType.MANUAL,"binary":"node","description":"Node runtime for stealth scraping stack"},
    # AD
    {"name":"bloodhound-python","category":ToolCategory.AD,"install_type":InstallType.PIP,"binary":"bloodhound-python","install_cmd":"pip install bloodhound","description":"BloodHound Python ingestor"},
    {"name":"crackmapexec","category":ToolCategory.AD,"install_type":InstallType.APT,"binary":"crackmapexec","apt_package":"crackmapexec","description":"AD network attacks"},
    {"name":"evil-winrm","category":ToolCategory.AD,"install_type":InstallType.APT,"binary":"evil-winrm","apt_package":"evil-winrm","description":"WinRM shell"},
    {"name":"impacket-scripts","category":ToolCategory.AD,"install_type":InstallType.APT,"binary":"GetUserSPNs.py","apt_package":"impacket-scripts","description":"Impacket AD tools"},
    {"name":"certipy","category":ToolCategory.AD,"install_type":InstallType.GIT,"binary":"certipy","repo_url":"https://github.com/ly4k/Certipy","description":"AD Certificate attacks"},
    {"name":"kerbrute","category":ToolCategory.AD,"install_type":InstallType.GO,"binary":"kerbrute","install_cmd":"go install github.com/ropnop/kerbrute@latest","description":"Kerberos brute-forcing"},
    # Crypto
    {"name":"hashcat","category":ToolCategory.CRYPTO,"install_type":InstallType.APT,"binary":"hashcat","apt_package":"hashcat","description":"GPU password cracker"},
    {"name":"john","category":ToolCategory.CRYPTO,"install_type":InstallType.APT,"binary":"john","apt_package":"john","description":"John the Ripper"},
    {"name":"hydra","category":ToolCategory.CRYPTO,"install_type":InstallType.APT,"binary":"hydra","apt_package":"hydra","description":"Network login brute-forcer"},
    # Wireless
    {"name":"aircrack-ng","category":ToolCategory.WIRELESS,"install_type":InstallType.APT,"binary":"aircrack-ng","apt_package":"aircrack-ng","description":"Wireless auditing suite"},
    {"name":"bettercap","category":ToolCategory.WIRELESS,"install_type":InstallType.APT,"binary":"bettercap","apt_package":"bettercap","description":"Network attack framework"},
    {"name":"hcxtools","category":ToolCategory.WIRELESS,"install_type":InstallType.APT,"binary":"hcxdumptool","apt_package":"hcxtools","description":"WPA/WPA2 tools"},
    # Cloud
    {"name":"pacu","category":ToolCategory.CLOUD,"install_type":InstallType.GIT,"binary":"pacu","repo_url":"https://github.com/RhinoSecurityLabs/pacu","description":"AWS exploitation"},
    {"name":"scoutsuite","category":ToolCategory.CLOUD,"install_type":InstallType.GIT,"binary":"scout","repo_url":"https://github.com/nccgroup/ScoutSuite","description":"Multi-cloud security audit"},
    # C2
    {"name":"sliver","category":ToolCategory.C2,"install_type":InstallType.GIT,"binary":"sliver","repo_url":"https://github.com/BishopFox/sliver","description":"Cross-platform C2"},
    {"name":"empire","category":ToolCategory.C2,"install_type":InstallType.GIT,"binary":"empire","repo_url":"https://github.com/BC-SECURITY/Empire","description":"PowerShell C2"},
    # RE
    {"name":"ghidra","category":ToolCategory.RE,"install_type":InstallType.APT,"binary":"ghidra","apt_package":"ghidra","description":"NSA RE suite"},
    {"name":"radare2","category":ToolCategory.RE,"install_type":InstallType.APT,"binary":"r2","apt_package":"radare2","description":"RE framework"},
    {"name":"binwalk","category":ToolCategory.RE,"install_type":InstallType.APT,"binary":"binwalk","apt_package":"binwalk","description":"Firmware extraction"},
    # Utility
    {"name":"rustscan","category":ToolCategory.UTILITY,"install_type":InstallType.CARGO,"binary":"rustscan","install_cmd":"cargo install rustscan","description":"Fast port scanner"},
    {"name":"wireshark","category":ToolCategory.UTILITY,"install_type":InstallType.APT,"binary":"wireshark","apt_package":"wireshark","description":"Network packet analyser"},
    {"name":"exiftool","category":ToolCategory.UTILITY,"install_type":InstallType.APT,"binary":"exiftool","apt_package":"libimage-exiftool-perl","description":"Metadata extractor"},
]

class ToolRegistry:
    def __init__(self) -> None:
        self._entries: Dict[str, ToolEntry] = {}
        self._load_catalogue()

    def refresh(self, check_versions: bool = False) -> None:
        """Only shutil.which() by default (fast). Pass check_versions=True for subprocess version checks."""
        for entry in self._entries.values():
            self._check_installed(entry, check_versions=check_versions)

    def get(self, name: str) -> Optional[ToolEntry]:
        return self._entries.get(name)

    def list_all(self, category: Optional[ToolCategory] = None) -> List[ToolEntry]:
        entries = list(self._entries.values())
        if category:
            entries = [e for e in entries if e.category == category]
        return sorted(entries, key=lambda e: e.name)

    def list_installed(self) -> List[ToolEntry]:
        return [e for e in self._entries.values() if e.installed]

    def list_missing(self) -> List[ToolEntry]:
        return [e for e in self._entries.values() if not e.installed]

    def categories(self) -> List[str]:
        return sorted({e.category.value for e in self._entries.values()})

    def is_installed(self, name: str) -> bool:
        entry = self._entries.get(name)
        if entry is None:
            return bool(shutil.which(name))
        return entry.installed

    def install(self, name: str, force: bool = False) -> bool:
        entry = self._entries.get(name)
        if not entry:
            log.warning(f"Unknown tool: {name}")
            return False
        if entry.installed and not force:
            return True
        return self._do_install(entry)

    def summary(self) -> Dict[str, Any]:
        installed = sum(1 for e in self._entries.values() if e.installed)
        by_cat: Dict[str, Dict[str, int]] = {}
        for e in self._entries.values():
            cat = e.category.value
            by_cat.setdefault(cat, {"total": 0, "installed": 0})
            by_cat[cat]["total"] += 1
            if e.installed:
                by_cat[cat]["installed"] += 1
        return {"total_tools": len(self._entries), "installed": installed,
                "missing": len(self._entries) - installed, "by_category": by_cat}

    def to_json(self) -> str:
        return json.dumps({n: e.to_dict() for n, e in self._entries.items()}, indent=2)

    def _load_catalogue(self) -> None:
        for spec in TOOL_CATALOGUE:
            spec = dict(spec)
            name = spec["name"]
            entry = ToolEntry(**{k: v for k, v in spec.items() if k in ToolEntry.__dataclass_fields__})
            self._entries[name] = entry

    def _check_installed(self, entry: ToolEntry, check_versions: bool = False) -> None:
        path = shutil.which(entry.binary)
        entry.installed = path is not None
        entry.binary_path = path or ""
        entry.last_checked = datetime.utcnow().isoformat()
        if path and check_versions:
            entry.version = self._get_version(entry.binary)

    def _get_version(self, binary: str) -> str:
        """2s hard timeout per flag, stops at first result. Skips known slow tools."""
        _SKIP = {"msfconsole", "openvas", "gvm", "nessusd", "nessus", "java", "neo4j", "docker"}
        if binary in _SKIP:
            return "installed"
        for flag in ("--version", "-V", "-version"):
            try:
                r = subprocess.run(
                    [binary, flag], capture_output=True, text=True,
                    timeout=2, start_new_session=True
                )
                out = (r.stdout + r.stderr).strip().split("\n")[0]
                if out and len(out) > 1:
                    return out[:80]
            except Exception:
                pass
        return "installed"

    def _do_install(self, entry: ToolEntry) -> bool:
        log.info(f"Installing {entry.name} via {entry.install_type.value}")
        try:
            from framework.core.config import config
            if entry.install_type == InstallType.APT and entry.apt_package:
                cmd = ["sudo", "apt", "install", "-y", entry.apt_package]
            elif entry.install_type in (InstallType.GO, InstallType.CARGO, InstallType.PIPX, InstallType.PIP) and entry.install_cmd:
                cmd = entry.install_cmd.split()
            elif entry.install_type == InstallType.GIT and entry.repo_url:
                tools_dir = config.get("tools_dir", "tools")
                dest = Path(tools_dir) / entry.name
                cmd = ["git", "clone", "--depth=1", entry.repo_url, str(dest)] if not dest.exists() else ["git", "-C", str(dest), "pull"]
            else:
                return False
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                self._check_installed(entry)
                return True
            log.error(f"Install failed for {entry.name}: {result.stderr[:200]}")
            return False
        except Exception as exc:
            log.error(f"Exception installing {entry.name}: {exc}")
            return False

tool_registry = ToolRegistry()
