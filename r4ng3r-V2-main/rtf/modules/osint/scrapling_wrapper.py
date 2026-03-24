"""RTF — OSINT: Scrapling wrapper (adaptive web scraping)"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper, WrapperResult

class ScraplingWrapper(ToolWrapper):
    BINARY      = "scrapling"
    TOOL_NAME   = "Scrapling"
    TIMEOUT     = 120
    INSTALL_CMD = "pip install scrapling"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        cmd = [self.BINARY, "fetch", target]
        if options.get("js"):       cmd += ["--js"]
        if options.get("stealth"):  cmd += ["--stealth"]
        if options.get("output"):   cmd += ["-o", options["output"]]
        if options.get("extract"):  cmd += ["--extract", options["extract"]]
        return cmd

    def run(self, target: str, options: Optional[Dict] = None) -> WrapperResult:
        """Also support Python API mode if binary not found."""
        import shutil, time
        options = options or {}
        if not shutil.which(self.BINARY):
            # Try Python API
            try:
                return self._run_python_api(target, options)
            except ImportError:
                pass
        return super().run(target, options)

    def _run_python_api(self, target: str, options: Dict) -> WrapperResult:
        import time
        t0 = time.monotonic()
        from scrapling import Fetcher
        fetcher = Fetcher(auto_match=options.get("auto_match", True))
        page    = fetcher.get(target, timeout=self.TIMEOUT)
        html    = str(page.html_content) if hasattr(page, "html_content") else str(page)
        parsed  = self.parse_output(html, target, options)
        from modules.base_wrapper import WrapperResult
        return WrapperResult(
            tool=self.TOOL_NAME, target=target, success=True,
            data=parsed, raw_output=html[:4000], duration_s=round(time.monotonic()-t0, 2)
        )

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        emails  = list(dict.fromkeys(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", raw)))
        phones  = list(dict.fromkeys(re.findall(r"\+?[\d\-\(\)\s]{9,20}", raw)))[:10]
        links   = list(dict.fromkeys(re.findall(r"https?://[^\s\"'<>]{5,200}", raw)))[:50]
        titles  = re.findall(r"<title[^>]*>([^<]{3,200})</title>", raw, re.I)
        return {
            "url":     target,
            "emails":  emails,
            "phones":  phones,
            "links":   links,
            "title":   titles[0] if titles else "",
            "length":  len(raw),
        }
