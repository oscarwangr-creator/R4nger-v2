"""RTF — Recon: Photon web crawler"""
from __future__ import annotations
import json, os
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class PhotonWrapper(ToolWrapper):
    BINARY = "photon"; TOOL_NAME = "Photon"; TIMEOUT = 300
    INSTALL_CMD = "git clone https://github.com/s0md3v/Photon && cd Photon && pip install -r requirements.txt"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        out_dir = options.get("output", "/tmp/photon_output")
        cmd = ["python3", "~/tools/Photon/photon.py", "-u", target,
               "-o", out_dir, "--export=json"]
        if options.get("level"):  cmd += ["-l", str(options["level"])]
        if options.get("threads"):cmd += ["-t", str(options["threads"])]
        if options.get("delay"):  cmd += ["--delay", str(options["delay"])]
        return cmd

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        out_dir = options.get("output", "/tmp/photon_output") if options else "/tmp/photon_output"
        data: Dict = {"urls": [], "emails": [], "keys": [], "intel": []}
        for fname in ("urls.txt","emails.txt","keys.txt","intel.txt"):
            fpath = os.path.join(out_dir, fname)
            key = fname.replace(".txt","")
            if os.path.exists(fpath):
                data[key] = [l.strip() for l in open(fpath).read().splitlines() if l.strip()]
        data["target"] = target
        return data

