from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from framework.modules.base import Finding, Severity
from framework.modules.external_tool import ExternalToolModule


class SherlockModule(ExternalToolModule):
    tool_name = "sherlock"
    tool_description = "Run sherlock username discovery from the CLI and normalize discovered accounts."
    tool_category = "osint"
    tool_binary = "sherlock"
    tool_refs = ['https://github.com/sherlock-project/sherlock']
    target_option_name = "username"
    target_option_desc = "Username to enumerate"
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
        cmd.append(str(target))
        if self.tool_name == "sherlock":
            cmd.extend(["--print-found", "--no-color"])
        return cmd, temp_output

    def parse_output(self, raw_output: str, **_: Any) -> Any:
        results = []
        for line in raw_output.splitlines():
            text = line.strip()
            if not text:
                continue
            url_match = re.search(r"https?://\S+", text)
            platform = text.split(":", 1)[0].replace("[+]", "").replace("[*]", "").strip(" -[]")
            results.append({"platform": platform or self.tool_name, "url": url_match.group(0) if url_match else "", "raw": text})
        return results

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
