"""RTF — RE: Bytecode Viewer Java decompiler"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper

class BytecodeViewerWrapper(ToolWrapper):
    BINARY = "java"; TOOL_NAME = "Bytecode-Viewer"; TIMEOUT = 120
    INSTALL_CMD = "Download BCV.jar from https://github.com/Konloch/bytecode-viewer"

    def _build_cmd(self, target: str, options: Dict) -> List[str]:
        jar = options.get("jar_path", "~/tools/BCV.jar")
        out = options.get("output", "/tmp/bcv_out.jar")
        return ["java", "-jar", jar, "-t", target, "-o", out, "-clean"]

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return {"output": raw[:2000], "target": target}

