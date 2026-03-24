from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from framework.modules.base import Finding, Severity
from framework.modules.external_tool import ExternalToolModule


class TwintModule(ExternalToolModule):
    tool_name = "twint"
    tool_description = "Run twint from the CLI and parse JSON line output."
    tool_category = "osint"
    tool_binary = "twint"
    tool_refs = ['https://github.com/twintproject/twint']
    target_option_name = "query"
    target_option_desc = "Twitter/X search query or username"
    default_timeout = 600

    def _declare_tool_options(self) -> None:
        self._register_option("limit", "Maximum results to request or keep", required=False, default=50, type=int)
        self._register_option("mode", "Execution mode understood by the wrapped tool", required=False, default="")
        self._register_option("json_output", "Request native structured output when supported", required=False, default=True, type=bool)

    def build_command(self, target: str, output_file: str) -> Tuple[List[str], str | None]:
        limit = self.get("limit")
        mode = self.get("mode")
        json_output = self.get("json_output")
        cmd = [self.tool_binary or self.tool_name]
        temp_output = None
        if mode == "user":
            cmd.extend(["-u", str(target), "--json"])
        else:
            cmd.extend(["-s", str(target), "--json"])
        if limit:
            cmd.extend(["--limit", str(limit)])
        return cmd, temp_output

    def parse_output(self, raw_output: str, **_: Any) -> Any:
        return self._parse_json_lines(raw_output)

    def build_findings(self, target: str, parsed: Any) -> List[Finding]:
        findings: List[Finding] = []
        items = parsed if isinstance(parsed, list) else [parsed]
        for item in items[:100]:
            evidence = item if isinstance(item, dict) else {"value": item}
            title = evidence.get("url") or evidence.get("value") or evidence.get("title") or self.tool_name
            findings.append(self.make_finding(
                title=f"{self.tool_name}: {title}",
                target=str(target),
                severity=Severity.INFO,
                description=f"Normalized {self.tool_name} result for {target}",
                evidence=evidence,
                tags=[self.tool_category, self.tool_name],
            ))
        return findings
