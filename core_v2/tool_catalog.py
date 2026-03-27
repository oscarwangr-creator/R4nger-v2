from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


CATEGORY_HINTS: dict[str, tuple[str, ...]] = {
    "identity": ("identity", "person", "maltego", "profil", "name"),
    "username": ("username", "user", "maigret", "sherlock"),
    "email": ("email", "mail", "hunter", "hibp"),
    "phone": ("phone", "sms", "truecaller"),
    "domain": ("domain", "dns", "whois", "subdomain", "amass", "altdns"),
    "infrastructure": ("nmap", "naabu", "masscan", "zmap", "port"),
    "breach": ("breach", "leak", "paste", "pwn"),
    "credential": ("password", "hash", "hydra", "brute", "wordlist"),
    "socmint": ("social", "twitter", "reddit", "telegram", "linkedin"),
    "geoint": ("geo", "location", "map", "satellite"),
    "darkweb": ("dark", "tor", "onion"),
    "metadata": ("metadata", "exif", "forensic"),
    "document": ("pdf", "doc", "office"),
    "image": ("image", "photo", "stego"),
    "threatintel": ("cve", "threat", "vuln", "ioc"),
    "attack_surface": ("attack", "surface", "exposed", "asset"),
}


@dataclass
class ExternalToolSpec:
    name: str
    source: str
    category: str


class ExternalToolCatalog:
    def __init__(self, source_file: str = "r4ng3r-V2-main/cleaned_tools_list.txt"):
        self.source_file = Path(source_file)

    def load(self, limit: int = 750) -> List[ExternalToolSpec]:
        if not self.source_file.exists():
            return []

        specs: List[ExternalToolSpec] = []
        seen: set[str] = set()
        with self.source_file.open("r", encoding="utf-8", errors="ignore") as fh:
            for raw in fh:
                line = raw.strip()
                if not line:
                    continue

                if "github.com" in line:
                    name = self._tool_name_from_link(line)
                    source = line
                else:
                    name = self._tool_name_from_plain_line(line)
                    source = "kali-package-index"
                if not name or name in seen:
                    continue
                seen.add(name)
                if not name:
                    continue
                specs.append(
                    ExternalToolSpec(name=name, source=source, category=self._infer_category(name))
                )
                if len(specs) >= limit:
                    break

        return specs

    def stats(self, limit: int = 750) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for spec in self.load(limit=limit):
            counts[spec.category] = counts.get(spec.category, 0) + 1
        return counts

    @staticmethod
    def _tool_name_from_link(link: str) -> str:
        token = link.rstrip("/").split("/")[-1].replace(".git", "")
        return token.lower().replace(" ", "_")

    @staticmethod
    def _tool_name_from_plain_line(line: str) -> str:
        token = line.strip().lower()
        if token.endswith(":"):
            return ""
        if any(ch in token for ch in (" ", "\t", "http://", "https://")):
            return ""
        if not any(ch.isalpha() for ch in token):
            return ""
        return token

    @staticmethod
    def _infer_category(name: str) -> str:
        lowered = name.lower()
        for category, hints in CATEGORY_HINTS.items():
            if any(h in lowered for h in hints):
                return category
        return "threatintel"

    @staticmethod
    def serialize(specs: List[ExternalToolSpec]) -> List[Dict[str, str]]:
        return [asdict(spec) for spec in specs]
