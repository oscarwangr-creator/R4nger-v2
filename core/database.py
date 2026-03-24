"""Lightweight persistence layer for jobs and workflow history."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class JobDatabase:
    def __init__(self, db_path: str = "data/r4nger.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id INTEGER PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT,
                    result_json TEXT
                )
                """
            )
            conn.commit()

    def save_job(self, job: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs (job_id, job_type, name, created_at, payload_json, result_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job["job_id"],
                    job["type"],
                    job["name"],
                    job["created_at"],
                    json.dumps(job.get("payload", {})),
                    json.dumps(job.get("result", {})),
                ),
            )
            conn.commit()

    def list_jobs(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT job_id, job_type, name, created_at, payload_json, result_json FROM jobs ORDER BY job_id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        jobs: List[Dict[str, Any]] = []
        for row in rows:
            jobs.append(
                {
                    "job_id": row[0],
                    "type": row[1],
                    "name": row[2],
                    "created_at": row[3],
                    "payload": json.loads(row[4] or "{}"),
                    "result": json.loads(row[5] or "{}"),
                }
            )
        return jobs
