from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from framework.intelligence.tool_wrapper import ToolWrapper


@dataclass
class WrappedToolSpec:
    name: str
    category: str
    websites: int = 0
    mode: str = "cli"
    notes: str = ""


class TitanToolWrapper(ToolWrapper):
    category: str = "generic"

    async def parse_output(self, raw: str) -> Dict[str, Any]:
        return super().parse_output(raw)

    async def validate(self, data: Dict[str, Any]) -> bool:
        return super().validate(data)

    async def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        records = data.get("records", []) if isinstance(data, dict) else []
        return {
            "tool": self.tool_name,
            "category": self.category,
            "records": records,
            "record_count": len(records),
        }

    async def run(self, target: str) -> Dict[str, Any]:
        result = await super().run(target)
        parsed = await self.parse_output(result.get("raw_output", ""))
        result["parsed"] = parsed
        result["valid"] = await self.validate(parsed)
        result["normalized"] = await self.normalize(parsed)
        return result


class StaticToolCatalog:
    USERNAME_DISCOVERY = [
        WrappedToolSpec("sherlock", "username_discovery", 400, "cli"),
        WrappedToolSpec("maigret", "username_discovery", 500, "cli"),
        WrappedToolSpec("nexfil", "username_discovery", 350, "cli"),
        WrappedToolSpec("blackbird", "username_discovery", 500, "cli"),
        WrappedToolSpec("social-analyzer", "username_discovery", 1000, "cli"),
        WrappedToolSpec("whatsmyname", "username_discovery", 500, "dataset"),
        WrappedToolSpec("checkusernames", "username_discovery", 150, "web"),
        WrappedToolSpec("namechk", "username_discovery", 100, "web"),
        WrappedToolSpec("socialscan", "username_discovery", 2, "api"),
        WrappedToolSpec("snoop", "username_discovery", 400, "cli"),
        WrappedToolSpec("osrframework", "username_discovery", 200, "cli"),
        WrappedToolSpec("profil3r", "username_discovery", 150, "cli"),
    ]
    SOCIAL_SCRAPERS = [
        WrappedToolSpec("twint", "social_scraping"),
        WrappedToolSpec("instaloader", "social_scraping"),
        WrappedToolSpec("snscrape", "social_scraping"),
        WrappedToolSpec("toutatis", "social_scraping"),
        WrappedToolSpec("gitfive", "social_scraping"),
        WrappedToolSpec("reddit-user-analyser", "social_scraping"),
    ]
    SEARCH_ENGINES = [
        WrappedToolSpec("google", "search_scraping"),
        WrappedToolSpec("duckduckgo", "search_scraping"),
        WrappedToolSpec("bing", "search_scraping"),
        WrappedToolSpec("brave", "search_scraping"),
        WrappedToolSpec("yahoo", "search_scraping"),
        WrappedToolSpec("startpage", "search_scraping"),
        WrappedToolSpec("qwant", "search_scraping"),
        WrappedToolSpec("swisscows", "search_scraping"),
        WrappedToolSpec("yandex", "search_scraping"),
        WrappedToolSpec("baidu", "search_scraping"),
    ]
    EMAIL_BREACH = [
        WrappedToolSpec("dehashed", "email_breach_intelligence", mode="api"),
        WrappedToolSpec("snusbase", "email_breach_intelligence", mode="api"),
        WrappedToolSpec("intelx", "email_breach_intelligence", mode="api"),
        WrappedToolSpec("breach-parse", "email_breach_intelligence", mode="cli"),
        WrappedToolSpec("haveibeenpwned", "email_breach_intelligence", mode="api"),
    ]
    DOMAIN_INTEL = [
        WrappedToolSpec("subfinder", "domain_intelligence"),
        WrappedToolSpec("amass", "domain_intelligence"),
        WrappedToolSpec("httpx", "domain_intelligence"),
        WrappedToolSpec("naabu", "domain_intelligence"),
        WrappedToolSpec("nmap", "domain_intelligence"),
        WrappedToolSpec("nuclei", "domain_intelligence"),
    ]
    CODE_INTEL = [
        WrappedToolSpec("gitfive", "code_intelligence"),
        WrappedToolSpec("trufflehog", "code_intelligence"),
        WrappedToolSpec("gitleaks", "code_intelligence"),
    ]

    @classmethod
    def summary(cls) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "username_discovery": [vars(item) for item in cls.USERNAME_DISCOVERY],
            "social_scrapers": [vars(item) for item in cls.SOCIAL_SCRAPERS],
            "search_engines": [vars(item) for item in cls.SEARCH_ENGINES],
            "email_breach": [vars(item) for item in cls.EMAIL_BREACH],
            "domain_intel": [vars(item) for item in cls.DOMAIN_INTEL],
            "code_intel": [vars(item) for item in cls.CODE_INTEL],
        }
