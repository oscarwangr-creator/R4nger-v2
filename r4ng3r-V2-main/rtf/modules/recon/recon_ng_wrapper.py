"""RTF — Recon: Recon-ng framework wrapper"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class ReconNgWrapper(ToolWrapper):
    BINARY = "recon-ng"; TOOL_NAME = "Recon-ng"; TIMEOUT = 600
    INSTALL_CMD = "git clone https://github.com/lanmaster53/recon-ng && cd recon-ng && pip install -r requirements.txt"

    def run(self, target: str, options: Optional[Dict] = None) -> Any:
        """Run recon-ng with a resource file or scripted commands."""
        from modules.base_wrapper import WrapperResult
        import subprocess, time, shutil, tempfile
        options = options or {}
        if not shutil.which(self.BINARY):
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error=f"{self.BINARY} not installed. {self.INSTALL_CMD}")
            self._last_result = r; return r
        modules = options.get("modules", ["recon/domains-hosts/hackertarget"])
        commands = [f"workspaces create {target.replace('.','_')}"]
        commands += [f"add domains {target}"]
        for mod in modules:
            commands += [f"modules load {mod}", f"options set SOURCE {target}", "run"]
        commands.append("exit")
        rc_file = tempfile.NamedTemporaryFile(mode="w", suffix=".rc", delete=False)
        rc_file.write("\n".join(commands) + "\n"); rc_file.close()
        t0 = time.monotonic()
        try:
            proc = subprocess.run([self.BINARY, "-r", rc_file.name],
                                  capture_output=True, text=True, timeout=self.TIMEOUT)
            raw = proc.stdout + proc.stderr
            parsed = self.parse_output(raw, target, options)
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=proc.returncode==0,
                              data=parsed, raw_output=raw[:6000], duration_s=round(time.monotonic()-t0,2))
        except Exception as exc:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error=str(exc), duration_s=time.monotonic()-t0)
        finally:
            import os; os.unlink(rc_file.name)
        self._last_result = r; return r

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return {"hosts": self._extract_domains(raw), "ips": self._extract_ips(raw),
                "emails": self._extract_emails(raw), "target": target}

