"""RTF — Scanning: Nessus wrapper (via REST API or CLI export)"""
from __future__ import annotations
import json, re, time
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper, WrapperResult

class NessusWrapper(ToolWrapper):
    BINARY      = "nessuscli"
    TOOL_NAME   = "Nessus"
    TIMEOUT     = 3600
    INSTALL_CMD = (
        "# Download from https://www.tenable.com/downloads/nessus\n"
        "# dpkg -i Nessus-*.deb && systemctl start nessusd"
    )

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        # nessuscli scan --targets <ip> --policy <name>
        cmd = [self.BINARY, "scan", "--targets", target]
        if options.get("policy"):   cmd += ["--policy", options["policy"]]
        if options.get("name"):     cmd += ["--name",   options["name"]]
        return cmd

    def run(self, target: str, options: Optional[Dict] = None) -> WrapperResult:
        options = options or {}
        t0      = time.monotonic()

        # Prefer REST API if credentials given
        host    = options.get("host", "https://localhost:8834")
        api_key = options.get("access_key", "")
        secret  = options.get("secret_key", "")

        if api_key and secret:
            return self._run_rest_api(target, options, host, api_key, secret, t0)
        # Fall back to CLI
        return super().run(target, options)

    def _run_rest_api(self, target: str, options: Dict, host: str,
                      access_key: str, secret_key: str, t0: float) -> WrapperResult:
        try:
            import urllib.request, urllib.error, ssl
            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            headers = {
                "X-ApiKeys": f"accessKey={access_key}; secretKey={secret_key}",
                "Content-Type": "application/json",
            }
            # List scans
            req = urllib.request.Request(f"{host}/scans", headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                data = json.loads(resp.read())
            scans = data.get("scans", [])
            findings = []
            for scan in scans[:20]:
                findings.append({
                    "scan_id": scan.get("id"),
                    "name":    scan.get("name"),
                    "status":  scan.get("status"),
                    "target":  scan.get("targets", target),
                })
            result = WrapperResult(
                tool=self.TOOL_NAME, target=target, success=True,
                data={"scans": findings, "count": len(findings)},
                duration_s=round(time.monotonic()-t0, 2),
            )
        except Exception as exc:
            result = WrapperResult(
                tool=self.TOOL_NAME, target=target, success=False,
                error=f"Nessus REST API error: {exc}",
                duration_s=round(time.monotonic()-t0, 2),
            )
        self._last_result = result
        return result

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        vulns, hosts, info = [], [], []
        for line in raw.splitlines():
            line = line.strip()
            if re.search(r"Critical|High|Medium|Low", line, re.I):
                sev_m = re.search(r"(Critical|High|Medium|Low)", line, re.I)
                vulns.append({"severity": sev_m.group(1).lower() if sev_m else "info", "description": line[:200]})
            elif re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line):
                ip_m = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line)
                if ip_m: hosts.append(ip_m.group())
        return {
            "vulnerabilities": vulns, "hosts": list(dict.fromkeys(hosts)),
            "vuln_count": len(vulns), "target": target,
        }
