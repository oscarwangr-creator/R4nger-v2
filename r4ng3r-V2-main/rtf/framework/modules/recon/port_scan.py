"""RedTeam Framework - Module: recon/port_scan"""
from __future__ import annotations
import json, re
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class PortScanModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"port_scan","description":"Fast port discovery using naabu, enriched with nmap service detection.","author":"RTF Core Team","category":"recon","version":"1.1","references":["https://github.com/projectdiscovery/naabu","https://nmap.org"]}

    def _declare_options(self) -> None:
        self._register_option("target","Target host / IP / CIDR",required=True)
        self._register_option("ports","Port range (top-100, top-1000, or '80,443,8080')",required=False,default="top-100")
        self._register_option("service_detection","Run nmap -sV on open ports",required=False,default=False,type=bool)
        self._register_option("rate","Packets-per-second rate",required=False,default=1000,type=int)
        self._register_option("timeout","Scan timeout in seconds",required=False,default=600,type=int)
        self._register_option("output_file","Save results to file",required=False,default="")

    async def run(self) -> ModuleResult:
        target: str = self.get("target")
        ports: str = self.get("ports")
        service_detection: bool = self.get("service_detection")
        rate: int = self.get("rate")
        timeout: int = self.get("timeout")
        output_file: str = self.get("output_file")
        naabu_cmd = ["naabu","-host",target,"-rate",str(rate),"-silent","-json"]
        if ports == "top-100":
            naabu_cmd += ["-top-ports","100"]
        elif ports == "top-1000":
            naabu_cmd += ["-top-ports","1000"]
        else:
            naabu_cmd += ["-p",ports]
        try:
            self.require_tool("naabu")
        except Exception:
            self.log.warning("naabu not found — falling back to nmap")
            return await self._nmap_fallback(target, ports, timeout)
        stdout, stderr, rc = await self.run_command_async(naabu_cmd, timeout=timeout)
        open_ports: List[Dict[str, Any]] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                open_ports.append({"host":entry.get("ip",target),"port":entry.get("port"),"protocol":entry.get("protocol","tcp")})
            except json.JSONDecodeError:
                if ":" in line:
                    h, p = line.rsplit(":", 1)
                    try:
                        open_ports.append({"host":h,"port":int(p),"protocol":"tcp"})
                    except ValueError:
                        pass
        self.log.info(f"Open ports on {target}: {len(open_ports)}")
        if service_detection and open_ports:
            port_list = ",".join(str(p["port"]) for p in open_ports)
            open_ports = await self._nmap_service_detect(target, port_list, timeout)
        if output_file:
            with open(output_file, "w") as fh:
                for p in open_ports:
                    fh.write(f"{p['host']}:{p['port']}\n")
        findings: List[Finding] = []
        for port_info in open_ports:
            port_num = port_info["port"]
            service = port_info.get("service","unknown")
            severity = self._port_severity(port_num, service)
            findings.append(self.make_finding(title=f"Open port {port_num}/{port_info.get('protocol','tcp')} on {target}",target=str(port_info["host"]),severity=severity,description=f"Service: {service}  Version: {port_info.get('version','')}",evidence=port_info,tags=["recon","port-scan"]))
        return ModuleResult(success=True,output={"open_ports":open_ports,"total":len(open_ports)},findings=findings)

    async def _nmap_fallback(self, target: str, ports: str, timeout: int) -> ModuleResult:
        self.require_tool("nmap")
        port_arg = "1-1000" if ports in ("top-100","top-1000") else ports
        stdout, _, rc = await self.run_command_async(["nmap","-T4","-Pn","-p",port_arg,target],timeout=timeout)
        open_ports = self._parse_nmap_output(stdout, target)
        return ModuleResult(success=True,output={"open_ports":open_ports,"total":len(open_ports)})

    async def _nmap_service_detect(self, target: str, ports: str, timeout: int) -> List[Dict[str, Any]]:
        try:
            self.require_tool("nmap")
        except Exception:
            return []
        stdout, _, _ = await self.run_command_async(["nmap","-sV","-Pn","-p",ports,target,"--open"],timeout=timeout)
        return self._parse_nmap_output(stdout, target)

    @staticmethod
    def _parse_nmap_output(output: str, target: str) -> List[Dict[str, Any]]:
        ports = []
        for line in output.splitlines():
            m = re.match(r"(\d+)/(tcp|udp)\s+open\s+(\S+)(?:\s+(.+))?", line.strip())
            if m:
                ports.append({"host":target,"port":int(m.group(1)),"protocol":m.group(2),"service":m.group(3),"version":(m.group(4) or "").strip()})
        return ports

    @staticmethod
    def _port_severity(port: int, service: str) -> Severity:
        risky = {21,22,23,25,53,110,111,135,139,143,161,389,445,512,513,514,1433,1521,2049,3306,3389,5432,5900,5985,6379,8080,8443,27017}
        return Severity.MEDIUM if port in risky else Severity.INFO
