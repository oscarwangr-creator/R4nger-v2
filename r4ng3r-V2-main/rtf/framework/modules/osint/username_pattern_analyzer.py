"""RedTeam Framework - Module: osint/username_pattern_analyzer"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

from framework.modules.base import BaseModule, Finding, ModuleResult, Severity


class UsernamePatternAnalyzerModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"username_pattern_analyzer","description":"Analyze username construction patterns and generate probable alternate handles.","author":"OpenAI","category":"osint","version":"1.0"}

    def _declare_options(self) -> None:
        self._register_option("username", "Primary username seed", required=True)
        self._register_option("related", "Comma-separated known variants", required=False, default="")

    async def run(self) -> ModuleResult:
        username = self.get("username").strip()
        related = [item.strip() for item in self.get("related").split(",") if item.strip()]
        variants = self._generate_variants(username, related)
        findings: List[Finding] = []
        for variant in variants[:10]:
            findings.append(self.make_finding(
                title=f"Derived username variant: {variant}",
                target=username,
                severity=Severity.INFO,
                description=f"Variant {variant} was derived from observed username composition rules.",
                evidence={"variant": variant, "source": username},
                tags=["osint", "username", "pattern"],
            ))
        return ModuleResult(success=True, output={"username": username, "variants": variants, "statistics": self._stats(username, related)}, findings=findings)

    def _generate_variants(self, username: str, related: List[str]) -> List[str]:
        tokens = re.split(r"[._\-]", username)
        collapsed = "".join(tokens)
        numeric = "".join(ch for ch in username if ch.isdigit())
        stems = {username.lower(), collapsed.lower(), *(item.lower() for item in related)}
        generated = set(stems)
        if len(tokens) > 1:
            generated.add("".join(tokens))
            generated.add("_".join(tokens))
            generated.add(".".join(tokens))
        if tokens:
            generated.add(tokens[0])
            generated.add(tokens[0] + (numeric or "01"))
        if len(tokens) >= 2:
            generated.add(tokens[0][0] + tokens[-1])
            generated.add(tokens[0] + tokens[-1][0])
        generated.add(collapsed + "1")
        generated.add(collapsed + "2024")
        return sorted(item for item in generated if item)

    def _stats(self, username: str, related: List[str]) -> Dict[str, Any]:
        delimiters = Counter(ch for ch in username if ch in "._-")
        return {
            "length": len(username),
            "has_numeric_suffix": username[-1:].isdigit(),
            "delimiter_usage": dict(delimiters),
            "related_count": len(related),
        }
