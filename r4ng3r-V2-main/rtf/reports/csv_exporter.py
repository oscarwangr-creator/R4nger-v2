"""RTF v2.0 — Reports: CSV Exporter (findings + entities sheets)"""
from __future__ import annotations
import csv, io, json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

class CsvExporter:
    def generate(self, data: Dict[str, Any], output_path: str) -> str:
        p = Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
        findings = data.get("findings", [])
        # Write findings CSV
        with p.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["severity","title","target","description","tags","evidence","timestamp"])
            for f in findings:
                writer.writerow([
                    str(f.get("severity","")),
                    str(f.get("title","")),
                    str(f.get("target","")),
                    str(f.get("description",""))[:500],
                    "|".join(str(t) for t in f.get("tags",[])),
                    json.dumps(f.get("evidence",{}),default=str)[:200],
                    str(f.get("timestamp",datetime.utcnow().isoformat())),
                ])
        # Write entities CSV if any
        entities = data.get("entities",{})
        if entities:
            ep = Path(str(p).replace(".csv","_entities.csv"))
            with ep.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["type","value"])
                for etype, values in entities.items():
                    for v in (list(values) if hasattr(values,"__iter__") and not isinstance(values,str) else [values]):
                        writer.writerow([etype, str(v)])
        return str(p.resolve())
