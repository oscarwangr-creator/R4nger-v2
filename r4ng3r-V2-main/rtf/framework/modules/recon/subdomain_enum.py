"""RedTeam Framework - Module: recon/subdomain_enum"""
from __future__ import annotations
import asyncio
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class SubdomainEnumModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"subdomain_enum","description":"Enumerate subdomains using subfinder + assetfinder in parallel, resolve live hosts via httpx.","author":"RTF Core Team","category":"recon","version":"1.1","references":["https://github.com/projectdiscovery/subfinder","https://github.com/tomnomnom/assetfinder"]}

    def _declare_options(self) -> None:
        self._register_option("target","Target domain to enumerate",required=True)
        self._register_option("output_file","Write results to this file",required=False,default="")
        self._register_option("resolve_live","Pipe results through httpx to find live hosts",required=False,default=True,type=bool)
        self._register_option("timeout","Per-tool timeout in seconds",required=False,default=300,type=int)

    async def run(self) -> ModuleResult:
        target: str = self.get("target")
        timeout: int = self.get("timeout")
        output_file: str = self.get("output_file")
        resolve_live: bool = self.get("resolve_live")
        subdomains: set = set()
        tasks = []
        try:
            self.require_tool("subfinder")
            tasks.append(self._run_subfinder(target, timeout))
        except Exception:
            self.log.warning("subfinder not found — skipping")
        try:
            self.require_tool("assetfinder")
            tasks.append(self._run_assetfinder(target, timeout))
        except Exception:
            self.log.warning("assetfinder not found — skipping")
        if not tasks:
            return ModuleResult(success=False, error="No enumeration tools available (subfinder / assetfinder)")
        results: List[List[str]] = await asyncio.gather(*tasks, return_exceptions=False)
        for batch in results:
            if isinstance(batch, list):
                subdomains.update(batch)
        subdomains = {s.strip().lower() for s in subdomains if target in s}
        self.log.info(f"Found {len(subdomains)} unique subdomains")
        live_hosts: List[str] = []
        if resolve_live and subdomains:
            try:
                self.require_tool("httpx")
                live_hosts = await self._resolve_live(list(subdomains), timeout)
                self.log.info(f"Live hosts: {len(live_hosts)}")
            except Exception as exc:
                self.log.warning(f"httpx not available: {exc}")
                live_hosts = list(subdomains)
        else:
            live_hosts = list(subdomains)
        if output_file:
            with open(output_file, "w") as fh:
                fh.write("\n".join(sorted(subdomains)))
        findings: List[Finding] = []
        for sub in subdomains:
            findings.append(self.make_finding(title=f"Subdomain discovered: {sub}",target=sub,severity=Severity.INFO,description=f"Subdomain of {target} found during enumeration.",evidence={"subdomain":sub,"live":sub in live_hosts},tags=["recon","subdomain"]))
        return ModuleResult(success=True,output={"subdomains":sorted(subdomains),"live_hosts":sorted(live_hosts),"total":len(subdomains)},findings=findings)

    async def _run_subfinder(self, domain: str, timeout: int) -> List[str]:
        stdout, stderr, rc = await self.run_command_async(["subfinder","-d",domain,"-silent","-all"],timeout=timeout)
        return [line.strip() for line in stdout.splitlines() if line.strip()]

    async def _run_assetfinder(self, domain: str, timeout: int) -> List[str]:
        stdout, stderr, rc = await self.run_command_async(["assetfinder","--subs-only",domain],timeout=timeout)
        return [line.strip() for line in stdout.splitlines() if line.strip()]

    async def _resolve_live(self, hosts: List[str], timeout: int) -> List[str]:
        proc = await asyncio.create_subprocess_exec("httpx","-silent","-no-color",stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL)
        stdin_data = "\n".join(hosts).encode()
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(input=stdin_data), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return []
        return [line.strip() for line in stdout.decode().splitlines() if line.strip()]
