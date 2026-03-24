from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from framework.modules.base import Finding, Severity
from framework.modules.external_tool import ExternalToolModule


class SocialAnalyzerModule(ExternalToolModule):
    tool_name = "social_analyzer"
    tool_description = "Run social_analyzer from the CLI and parse JSON output."
    tool_category = "osint"
    tool_binary = "social-analyzer"
    tool_refs = ['https://github.com/qeeqbox/social-analyzer']
    target_option_name = "username"
    target_option_desc = "Username or profile to enumerate"
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
        json_path, temp_output = self._ensure_json_output_path(output_file)
        cmd.append(str(target))
        if json_output:
            cmd.extend(["--json", json_path])
        return cmd, temp_output

    def parse_output(self, raw_output: str, **_: Any) -> Any:
        data = self._parse_json_blob(raw_output)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("results") or data.get("accounts") or data.get("findings") or [data]
        return [{"value": data}]

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
