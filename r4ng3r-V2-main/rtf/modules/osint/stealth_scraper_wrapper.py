from __future__ import annotations

from typing import Any, Dict, List

from modules.base_wrapper import ToolWrapper


class StealthScraperWrapper(ToolWrapper):
    BINARY = "node"
    TOOL_NAME = "stealth_scraper"
    INSTALL_CMD = "npm install puppeteer-extra puppeteer-extra-plugin-stealth"

    def _build_cmd(self, target: str, options: Dict[str, Any]) -> List[str]:
        return [self.BINARY, "-e", "console.log('stealth profile prepared')"]

    def run(self, target: str, options: Dict[str, Any] | None = None):
        options = options or {}
        profile = {
            "target": target,
            "framework": "puppeteer-extra-plugin-stealth",
            "proxy_rotation": bool(options.get("proxy_rotation", True)),
            "user_agent_rotation": bool(options.get("user_agent_rotation", True)),
            "session_mode": options.get("session_mode", "automated-login"),
            "supported_platforms": ["linkedin", "facebook", "instagram"],
        }
        result = super().run(target, options)
        result.data = profile if result.success else {"profile": profile, "warning": result.error}
        return result
