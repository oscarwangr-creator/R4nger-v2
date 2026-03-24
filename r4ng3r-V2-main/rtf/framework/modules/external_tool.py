"""Shared helpers for external-tool-backed framework modules."""
from __future__ import annotations

import abc
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from framework.modules.base import BaseModule, ModuleResult, Finding, Severity


class ExternalToolModule(BaseModule):
    """Base class for modules that wrap external OSINT/recon binaries."""

    tool_name: str = ""
    tool_description: str = ""
    tool_category: str = "osint"
    tool_author: str = "RTF Core Team"
    tool_version: str = "1.0"
    tool_binary: str = ""
    tool_refs: List[str] = []
    default_timeout: int = 300
    target_option_name: str = "target"
    target_option_desc: str = "Target passed to the underlying tool"

    def info(self) -> Dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": self.tool_description,
            "author": self.tool_author,
            "category": self.tool_category,
            "version": self.tool_version,
            "references": self.tool_refs,
        }

    def _declare_options(self) -> None:
        self._register_option(self.target_option_name, self.target_option_desc, required=True)
        self._register_option("extra_args", "Additional CLI arguments appended verbatim (comma-separated string or JSON list)", required=False, default="")
        self._register_option("timeout", "Execution timeout in seconds", required=False, default=self.default_timeout, type=int)
        self._register_option("output_file", "Optional output path for raw or JSON output", required=False, default="")
        self._declare_tool_options()

    def _declare_tool_options(self) -> None:
        pass

    async def run(self) -> ModuleResult:
        binary = self.tool_binary or self.tool_name
        self.require_tool(binary)
        target = self.get(self.target_option_name)
        timeout = self.get("timeout")
        output_file = self.get("output_file")
        cmd, temp_output = self.build_command(target, output_file)
        extra_args = self._parse_extra_args(self.get("extra_args"))
        cmd.extend(extra_args)
        stdout, stderr, rc = await self.run_command_async(cmd, timeout=timeout)
        raw_output = self._load_output(output_file, temp_output, stdout, stderr)
        parsed = self.parse_output(raw_output, stdout=stdout, stderr=stderr, return_code=rc, target=target)
        findings = self.build_findings(target, parsed)
        output = {
            "tool": self.tool_name,
            "binary": binary,
            "target": target,
            "command": cmd,
            "return_code": rc,
            "stderr": stderr.strip(),
            "results": parsed,
            "result_count": len(parsed) if isinstance(parsed, list) else (len(parsed.get("results", [])) if isinstance(parsed, dict) else 0),
        }
        if temp_output:
            try:
                os.unlink(temp_output)
            except OSError:
                pass
        return ModuleResult(success=rc == 0, output=output, findings=findings, raw_output=raw_output, error=None if rc == 0 else stderr.strip() or f"{binary} exited with status {rc}")

    @abc.abstractmethod
    def build_command(self, target: str, output_file: str) -> Tuple[List[str], Optional[str]]:
        raise NotImplementedError

    def parse_output(self, raw_output: str, **_: Any) -> Any:
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        return [{"value": line} for line in lines]

    def build_findings(self, target: str, parsed: Any) -> List[Finding]:
        items = parsed if isinstance(parsed, list) else parsed.get("results", []) if isinstance(parsed, dict) else []
        findings: List[Finding] = []
        for item in items[:100]:
            findings.append(self.make_finding(
                title=f"{self.tool_name} result for {target}",
                target=str(target),
                severity=Severity.INFO,
                description=str(item)[:500],
                evidence=item if isinstance(item, dict) else {"value": item},
                tags=[self.tool_category, self.tool_name],
            ))
        return findings

    def _load_output(self, output_file: str, temp_output: Optional[str], stdout: str, stderr: str) -> str:
        chosen = output_file or temp_output
        if chosen and Path(chosen).exists():
            try:
                return Path(chosen).read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
        return stdout if stdout.strip() else stderr

    def _parse_extra_args(self, extra_args: Any) -> List[str]:
        if not extra_args:
            return []
        if isinstance(extra_args, list):
            return [str(item) for item in extra_args]
        text = str(extra_args).strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                value = json.loads(text)
                if isinstance(value, list):
                    return [str(item) for item in value]
            except json.JSONDecodeError:
                pass
        return [part.strip() for part in text.split(",") if part.strip()]

    def _ensure_json_output_path(self, output_file: str, suffix: str = ".json") -> Tuple[str, Optional[str]]:
        if output_file:
            return output_file, None
        handle = tempfile.NamedTemporaryFile(prefix=f"rtf_{self.tool_name}_", suffix=suffix, delete=False)
        handle.close()
        return handle.name, handle.name

    def _parse_json_lines(self, raw_output: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for line in raw_output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            results.append(obj if isinstance(obj, dict) else {"value": obj})
        return results

    def _parse_json_blob(self, raw_output: str) -> Any:
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            return {"results": self.parse_output(raw_output)}
