"""RedTeam Framework - Module: recon/ssl_scan"""
from __future__ import annotations
import datetime
import socket
import ssl
from typing import Any, Dict, List

from framework.modules.base import BaseModule, Finding, ModuleResult, Severity


class SSLScanModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {
            "name": "ssl_scan",
            "description": "TLS/SSL certificate and protocol analysis. Uses tlsx (primary) with stdlib fallback.",
            "author": "RTF Core Team",
            "category": "recon",
            "version": "1.0",
            "tags": ["ssl", "tls", "certificates"],
        }

    def _declare_options(self) -> None:
        self._register_option("target", "Target hostname or IP", required=True)
        self._register_option("port", "Target port", required=False, default=443, type=int)
        self._register_option("check_expiry", "Check certificate expiry", required=False, default=True, type=bool)
        self._register_option("check_protocols", "Check for weak protocols", required=False, default=True, type=bool)
        self._register_option("expiry_warn_days", "Days before expiry to warn", required=False, default=30, type=int)
        self._register_option("timeout", "Connection timeout", required=False, default=30, type=int)

    async def run(self) -> ModuleResult:
        target = self.get("target")
        port = self.get("port")
        timeout = self.get("timeout")
        check_expiry = self.get("check_expiry")
        check_protocols = self.get("check_protocols")
        warn_days = self.get("expiry_warn_days")
        results: Dict[str, Any] = {}
        findings: List[Finding] = []

        # --- Try tlsx first ---
        tlsx_success = False
        try:
            self.require_tool("tlsx")
            import json as _json
            stdout, stderr, rc = await self.run_command_async(
                ["tlsx", "-u", f"{target}:{port}", "-json", "-silent"],
                timeout=timeout,
            )
            if rc == 0 and stdout.strip():
                for line in stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = _json.loads(line)
                        results.update(data)
                    except Exception:
                        continue
                    # Expiry check
                    not_after = data.get("not_after", "")
                    if not_after:
                        try:
                            expiry = datetime.datetime.strptime(not_after, "%Y-%m-%dT%H:%M:%SZ")
                            days_left = (expiry - datetime.datetime.utcnow()).days
                            results["days_until_expiry"] = days_left
                            if days_left < 0:
                                findings.append(self.make_finding(
                                    title=f"Expired certificate on {target}:{port}",
                                    target=target,
                                    severity=Severity.CRITICAL,
                                    description=f"Certificate expired {abs(days_left)} days ago.",
                                    evidence={"expiry": str(expiry), "days": days_left},
                                    tags=["ssl", "expired", "certificate"],
                                ))
                            elif days_left < warn_days:
                                findings.append(self.make_finding(
                                    title=f"Certificate expiring soon on {target}:{port}",
                                    target=target,
                                    severity=Severity.MEDIUM,
                                    description=f"Certificate expires in {days_left} days.",
                                    evidence={"expiry": str(expiry), "days": days_left},
                                    tags=["ssl", "expiry"],
                                ))
                        except Exception:
                            pass
                    # Weak protocol check
                    ver = data.get("version", "")
                    if ver in ("tls10", "tls11", "ssl20", "ssl30"):
                        findings.append(self.make_finding(
                            title=f"Weak TLS protocol: {ver} on {target}",
                            target=target,
                            severity=Severity.HIGH,
                            description=f"Server supports deprecated protocol: {ver}",
                            evidence={"protocol": ver},
                            tags=["ssl", "weak_protocol"],
                        ))
                tlsx_success = True
        except Exception:
            pass

        if tlsx_success:
            return ModuleResult(success=True, output=results, findings=findings)

        # --- Stdlib fallback ---
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((target, port), timeout=timeout) as raw_sock:
                with ctx.wrap_socket(raw_sock, server_hostname=target) as ssock:
                    cert = ssock.getpeercert()
                    cipher_info = ssock.cipher()
                    protocol = ssock.version() or ""
                    results["cipher"] = cipher_info[0] if cipher_info else ""
                    results["protocol"] = protocol
                    results["target"] = target
                    results["port"] = port
                    # Expiry from stdlib cert
                    if cert and check_expiry:
                        not_after_str = cert.get("notAfter", "")
                        if not_after_str:
                            try:
                                expiry = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
                                days_left = (expiry - datetime.datetime.utcnow()).days
                                results["days_until_expiry"] = days_left
                                if days_left < 0:
                                    findings.append(self.make_finding(
                                        title=f"Expired certificate on {target}:{port}",
                                        target=target,
                                        severity=Severity.CRITICAL,
                                        description=f"Expired {abs(days_left)} days ago.",
                                        evidence={"expiry": str(expiry)},
                                        tags=["ssl", "expired"],
                                    ))
                                elif days_left < warn_days:
                                    findings.append(self.make_finding(
                                        title=f"Certificate expiring in {days_left} days",
                                        target=target,
                                        severity=Severity.MEDIUM,
                                        description=f"Expiry: {expiry}",
                                        evidence={"days": days_left},
                                        tags=["ssl", "expiry"],
                                    ))
                            except Exception:
                                pass
                    # Weak protocol
                    if check_protocols and protocol in ("TLSv1", "TLSv1.1", "SSLv2", "SSLv3"):
                        findings.append(self.make_finding(
                            title=f"Weak protocol: {protocol} on {target}",
                            target=target,
                            severity=Severity.HIGH,
                            description=f"Deprecated TLS/SSL protocol: {protocol}",
                            evidence={"protocol": protocol},
                            tags=["ssl", "weak_protocol"],
                        ))
        except Exception as exc:
            return ModuleResult(success=False, error=str(exc))

        return ModuleResult(success=True, output=results, findings=findings)
