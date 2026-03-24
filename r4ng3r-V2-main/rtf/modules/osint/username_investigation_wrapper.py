"""RTF — OSINT: Username investigation (aggregated cross-tool username lookup)"""
from __future__ import annotations
import re, shutil, asyncio
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper, WrapperResult

class UsernameInvestigationWrapper(ToolWrapper):
    """
    Aggregates results from multiple username-lookup tools:
    sherlock, maigret, social-analyzer, whatsmyname, nexfil.
    Runs whichever are installed and merges results.
    """
    BINARY      = "sherlock"        # primary tool
    TOOL_NAME   = "Username Investigation"
    TIMEOUT     = 600
    INSTALL_CMD = "pipx install sherlock-project && pipx install maigret"

    _SUB_TOOLS = [
        ("sherlock",         ["sherlock", "{username}", "--print-found", "--no-color"]),
        ("maigret",          ["maigret",  "{username}", "--no-color", "-a"]),
        ("nexfil",           ["nexfil",   "-u", "{username}"]),
        ("whatsmyname",      ["python3",  "whatsmyname.py", "-u", "{username}"]),
        ("social-analyzer",  ["social-analyzer", "--analyze", "{username}", "--output", "json"]),
    ]

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        return ["sherlock", target, "--print-found", "--no-color"]

    def run(self, target: str, options: Optional[Dict] = None) -> WrapperResult:
        import time
        options = options or {}
        t0      = time.monotonic()
        all_accounts: List[Dict] = []
        tools_run: List[str]     = []
        raw_combined             = ""

        for tool_name, cmd_template in self._SUB_TOOLS:
            binary = cmd_template[0]
            if not shutil.which(binary):
                continue
            cmd = [c.replace("{username}", target) for c in cmd_template]
            try:
                import subprocess
                proc = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=options.get("timeout", 180))
                raw = proc.stdout + proc.stderr
                raw_combined += f"\n[{tool_name}]\n{raw[:2000]}"
                tools_run.append(tool_name)
                parsed = self._parse_tool(tool_name, raw, target)
                all_accounts.extend(parsed)
            except Exception:
                pass

        # Deduplicate by URL
        seen, deduped = set(), []
        for acc in all_accounts:
            key = acc.get("url", acc.get("platform", "")).lower()
            if key and key not in seen:
                seen.add(key); deduped.append(acc)

        result = WrapperResult(
            tool=self.TOOL_NAME, target=target,
            success=bool(deduped),
            data={
                "username":   target,
                "accounts":   deduped,
                "found_count": len(deduped),
                "tools_used": tools_run,
            },
            raw_output=raw_combined[:8000],
            duration_s=round(time.monotonic()-t0, 2),
            error="" if tools_run else "No username investigation tools installed",
        )
        self._last_result = result
        return result

    def _parse_tool(self, tool: str, raw: str, username: str) -> List[Dict]:
        accounts = []
        if tool == "sherlock":
            for line in raw.splitlines():
                m = re.search(r"\[\+\]\s+(\S+):\s+(https?://\S+)", line)
                if m:
                    accounts.append({"platform": m.group(1), "url": m.group(2), "source": "sherlock"})
        elif tool == "maigret":
            for line in raw.splitlines():
                m = re.search(r"\[\+\]\s+(\S+)\s+-\s+(https?://\S+)", line)
                if m:
                    accounts.append({"platform": m.group(1), "url": m.group(2), "source": "maigret"})
        elif tool == "nexfil":
            for line in raw.splitlines():
                if "http" in line and "[+]" in line:
                    url_m = re.search(r"(https?://\S+)", line)
                    if url_m:
                        accounts.append({"url": url_m.group(1), "source": "nexfil"})
        else:
            for line in raw.splitlines():
                url_m = re.search(r"(https?://\S+)", line)
                if url_m and ("+]" in line or "Found" in line or "found" in line):
                    accounts.append({"url": url_m.group(1), "source": tool})
        return accounts

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return self._parse_tool("generic", raw, target) and {"raw": raw[:500]} or {}
