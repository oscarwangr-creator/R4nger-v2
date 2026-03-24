"""RTF — AI: Statistical anomaly detection across findings"""
from __future__ import annotations
import json, statistics
from typing import Any, Dict, List, Optional
from modules.base_wrapper import ToolWrapper, WrapperResult

class AnomalyDetection(ToolWrapper):
    BINARY = "python3"; TOOL_NAME = "Anomaly-Detection"; TIMEOUT = 30
    INSTALL_CMD = "pip install scipy numpy"

    def run(self, target: str, options: Optional[Dict] = None) -> WrapperResult:
        import time
        options = options or {}
        t0 = time.monotonic()
        findings = options.get("findings", [])
        if not findings:
            r = WrapperResult(tool=self.TOOL_NAME, target=target, success=False,
                              error="No findings provided. Pass findings=[] in options.")
            self._last_result = r; return r
        anomalies = self._detect(findings, options)
        r = WrapperResult(tool=self.TOOL_NAME, target=target, success=True,
                          data={"anomalies": anomalies, "analyzed": len(findings),
                                "anomaly_count": len(anomalies)},
                          duration_s=round(time.monotonic()-t0,2))
        self._last_result = r; return r

    def _detect(self, findings: List[Dict], options: Dict) -> List[Dict]:
        """Z-score based anomaly detection on CVSS scores and port numbers."""
        anomalies = []
        scores = []
        for f in findings:
            score = f.get("cvss") or f.get("severity_score") or 0
            try: scores.append(float(score))
            except Exception: scores.append(0.0)
        if len(scores) >= 3:
            mean = statistics.mean(scores)
            stdev = statistics.stdev(scores) or 1
            for i, (f, s) in enumerate(zip(findings, scores)):
                z = abs(s - mean) / stdev
                if z > 2.0:
                    anomalies.append({"finding": f, "score": s, "z_score": round(z,2),
                                      "reason": "Unusually high/low severity score"})
        return anomalies

    def parse_output(self, raw: str, target: str = "", options: Optional[Dict] = None) -> Dict[str, Any]:
        return {"raw": raw, "target": target}

