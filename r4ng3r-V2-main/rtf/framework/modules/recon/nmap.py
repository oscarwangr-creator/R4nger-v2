from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from framework.modules.base import Finding, Severity
from framework.modules.external_tool import ExternalToolModule


class NmapModule(ExternalToolModule):
    tool_name = "nmap"
    tool_description = "Run nmap from the CLI and normalize open port results."
    tool_category = "recon"
    tool_binary = "nmap"
    tool_refs = ['https://nmap.org']
    target_option_name = "target"
    target_option_desc = "Target host or network"
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
        cmd.extend(["-Pn", "-oG", "-", str(target)])
        return cmd, temp_output

    def parse_output(self, raw_output: str, **_: Any) -> Any:
        results: List[Dict[str, Any]] = []
        for line in raw_output.splitlines():
            if "Ports:" not in line:
                continue
            host_match = re.search(r"Host: (\S+)", line)
            ports_match = re.search(r"Ports: (.+)$", line)
            if not ports_match:
                continue
            host = host_match.group(1) if host_match else ""
            for part in ports_match.group(1).split(","):
                fields = [item.strip() for item in part.split("/")]
                if len(fields) < 5 or fields[1] != "open":
                    continue
                results.append({"host": host, "port": int(fields[0]), "protocol": fields[2], "service": fields[4]})
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
