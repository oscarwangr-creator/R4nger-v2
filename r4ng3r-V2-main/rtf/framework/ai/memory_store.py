from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
import sqlite3
from typing import Any, Dict, List, Optional

from framework.db.database import db


@dataclass
class MemoryRecord:
    goal: str
    action: str
    score: float
    result: Dict[str, Any]
    pivots: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MemoryStore:
    def __init__(self, database=None) -> None:
        self.db = database or db

    def store(self, goal: str, action: str, score: float, result: Dict[str, Any], pivots: Optional[List[Dict[str, Any]]] = None) -> MemoryRecord:
        record = MemoryRecord(goal=goal, action=action, score=score, result=result, pivots=list(pivots or []))
        try:
            self.db.add_target(f"memory::{goal}::{action}::{record.created_at}", "memory", tags="autonomous-agent")
        except sqlite3.OperationalError:
            pass
        return record

    def summarize(self, records: List[MemoryRecord]) -> Dict[str, Any]:
        return {
            "records": [asdict(record) for record in records[-20:]],
            "pivot_targets": [pivot for record in records[-20:] for pivot in record.pivots],
            "goals": sorted({record.goal for record in records}),
        }
