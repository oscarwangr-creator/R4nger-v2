from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from framework.modules.base import Finding, Severity
from framework.modules.external_tool import ExternalToolModule


class BaiduSearchModule(ExternalToolModule):
    tool_name = "baidu"
    tool_description = "Run baidu search engine queries and normalize result entries."
    tool_category = "osint"
    tool_binary = "baidu"
    tool_refs = ['https://www.baidu.com']
    target_option_name = "query"
    target_option_desc = "Search query"
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
        if limit:
            cmd.extend(["--limit", str(limit)])
        if output_file:
            cmd.extend(["--output", output_file])
        return cmd, temp_output

    def parse_output(self, raw_output: str, **_: Any) -> Any:
        results = []
        for idx, line in enumerate(raw_output.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            parts = [part.strip() for part in re.split(r"\s+-\s+|\s+\|\s+", line, maxsplit=2)]
            title = parts[0] if parts else line
            url_match = re.search(r"https?://\S+", line)
            results.append({"rank": idx, "title": title, "url": url_match.group(0) if url_match else "", "raw": line})
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
