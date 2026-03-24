"""Distributed execution primitives for worker node orchestration."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


@dataclass
class WorkerNode:
    worker_id: str
    capacity: int
    status: str = "online"
    last_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DistributedExecutor:
    def __init__(self) -> None:
        self.workers: Dict[str, WorkerNode] = {}

    def register_worker(self, worker_id: str, capacity: int = 2) -> WorkerNode:
        node = WorkerNode(worker_id=worker_id, capacity=capacity)
        self.workers[worker_id] = node
        return node

    def list_workers(self) -> List[dict]:
        return [w.__dict__ for w in self.workers.values()]

    def execute_parallel(self, jobs: List[Callable[[], Dict[str, Any]]], max_workers: int = 4) -> List[dict]:
        results: List[dict] = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(job) for job in jobs]
            for fut in as_completed(futures):
                try:
                    results.append({"status": "success", "result": fut.result()})
                except Exception as exc:  # noqa: BLE001
                    results.append({"status": "error", "error": str(exc)})
        return results
