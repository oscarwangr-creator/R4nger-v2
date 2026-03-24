"""RTF v2.0 — Reports: JSON Reporter"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

class JsonReporter:
    def generate(self, data: Dict[str, Any], output_path: str) -> str:
        p = Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
        out = {
            "rtf_version":   "2.0",
            "generated_at":  datetime.utcnow().isoformat(),
            "target":        data.get("target", ""),
            "profile":       data.get("profile", ""),
            "pipeline_id":   data.get("pipeline_id", ""),
            "operator":      data.get("operator", ""),
            "summary": {
                "total_findings": len(data.get("findings", [])),
                "by_severity":    self._count_severity(data.get("findings", [])),
                "risk_score":     self._risk_score(data.get("findings", [])),
            },
            "findings":       data.get("findings", []),
            "entities":       {k: list(v) if hasattr(v,"__iter__") and not isinstance(v,str) else v
                               for k,v in data.get("entities",{}).items()},
            "stage_results":  data.get("stage_results", {}),
            "ai_analysis":    data.get("ai_analysis", {}),
            "attack_paths":   data.get("attack_paths", []),
            "tool_runs":      data.get("tool_runs", []),
            "mitre_mapping":  data.get("mitre_mapping", {}),
        }
        p.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        return str(p.resolve())

    def _count_severity(self, findings) -> Dict[str, int]:
        counts = {"critical":0,"high":0,"medium":0,"low":0,"info":0}
        for f in findings:
            s = str(f.get("severity","info")).lower()
            counts[s] = counts.get(s,0)+1
        return counts

    def _risk_score(self, findings) -> int:
        w = {"critical":10,"high":5,"medium":2,"low":1,"info":0}
        return sum(w.get(str(f.get("severity","info")).lower(),0) for f in findings)
