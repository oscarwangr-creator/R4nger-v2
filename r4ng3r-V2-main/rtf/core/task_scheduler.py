"""
RTF v2.0 — Core Task Scheduler
Wraps PipelineOrchestrator with async queue, priority scheduling,
job tracking, and graceful cancellation.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.pipeline_orchestrator import PipelineOrchestrator, PipelineResult


class JobStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledJob:
    job_id:    str
    targets:   Dict[str, str]
    profile:   str  = "full"
    stages:    List[str] = field(default_factory=lambda: list("ABCDEFGHIJK"))
    options:   Dict[str, Any] = field(default_factory=dict)
    priority:  int  = 5          # 1 (highest) → 10 (lowest)
    status:    JobStatus = JobStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: str = ""
    finished_at: str = ""
    result:    Optional[PipelineResult] = None
    error:     str  = ""
    output_dir: str = "/tmp/rtf_pipeline"
    report_formats: List[str] = field(default_factory=lambda: ["json","html"])
    callback:  Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {k: v for k, v in self.__dict__.items()
             if k not in ("callback","result")}
        if self.result:
            d["result_summary"] = {
                "findings": len(self.result.findings),
                "stages": list(self.result.stage_results.keys()),
                "report_files": self.result.report_files,
            }
        return d


class TaskScheduler:
    """
    Async task scheduler for RTF pipeline jobs.

    Usage:
        sched = TaskScheduler(max_concurrent=2)
        job_id = sched.enqueue(targets={"domain":"example.com"}, profile="full")
        await sched.start()
        # or run a single job:
        result = await sched.run_now(targets={"domain":"example.com"}, profile="core")
    """

    def __init__(self, max_concurrent: int = 2, output_dir: str = "/tmp/rtf_pipeline") -> None:
        self.max_concurrent = max_concurrent
        self.output_dir     = output_dir
        self._jobs:    Dict[str, ScheduledJob] = {}
        self._queue:   asyncio.PriorityQueue   = asyncio.PriorityQueue()
        self._running: Dict[str, asyncio.Task] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._started  = False

    # ─── Public API ──────────────────────────────────────────────────

    def enqueue(
        self,
        targets: Dict[str, str],
        profile:  str = "full",
        stages:   Optional[List[str]] = None,
        options:  Optional[Dict] = None,
        priority: int = 5,
        report_formats: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
    ) -> str:
        """Queue a pipeline job. Returns job_id."""
        job = ScheduledJob(
            job_id=str(uuid.uuid4())[:12],
            targets=targets,
            profile=profile,
            stages=stages or list("ABCDEFGHIJK"),
            options=options or {},
            priority=priority,
            output_dir=self.output_dir,
            report_formats=report_formats or ["json","html"],
            callback=callback,
        )
        self._jobs[job.job_id] = job
        self._queue.put_nowait((priority, job.job_id))
        return job.job_id

    async def run_now(
        self,
        targets: Dict[str, str],
        profile: str = "full",
        stages:  Optional[List[str]] = None,
        options: Optional[Dict] = None,
        report_formats: Optional[List[str]] = None,
        log_fn:  Optional[Callable] = None,
    ) -> PipelineResult:
        """Run a pipeline job immediately without queueing."""
        orch = PipelineOrchestrator(
            profile=profile,
            stages=stages or list("ABCDEFGHIJK"),
            output_dir=self.output_dir,
            report_formats=report_formats or ["json","html"],
            log_fn=log_fn or print,
        )
        return await orch.run(targets, options or {})

    async def start(self) -> None:
        """Start the scheduler event loop — processes queued jobs."""
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._started = True
        while self._started or not self._queue.empty():
            try:
                priority, job_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            if job_id not in self._jobs:
                continue
            task = asyncio.create_task(self._execute(job_id))
            self._running[job_id] = task

    def stop(self) -> None:
        """Gracefully stop the scheduler after current jobs finish."""
        self._started = False
        for task in self._running.values():
            task.cancel()

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or running job."""
        job = self._jobs.get(job_id)
        if not job: return False
        if job.status == JobStatus.RUNNING:
            task = self._running.get(job_id)
            if task: task.cancel()
        job.status = JobStatus.CANCELLED
        return True

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, status: Optional[JobStatus] = None) -> List[ScheduledJob]:
        jobs = list(self._jobs.values())
        if status: jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def job_summary(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for job in self._jobs.values():
            counts[job.status.value] = counts.get(job.status.value,0) + 1
        return {"total": len(self._jobs), "by_status": counts,
                "running": list(self._running.keys())}

    # ─── Internal ────────────────────────────────────────────────────

    async def _execute(self, job_id: str) -> None:
        job = self._jobs[job_id]
        async with (self._semaphore or asyncio.Semaphore(1)):
            job.status     = JobStatus.RUNNING
            job.started_at = datetime.utcnow().isoformat()
            try:
                orch = PipelineOrchestrator(
                    profile=job.profile,
                    stages=job.stages,
                    output_dir=job.output_dir,
                    report_formats=job.report_formats,
                )
                result = await orch.run(job.targets, job.options)
                job.result     = result
                job.status     = JobStatus.COMPLETED
            except asyncio.CancelledError:
                job.status = JobStatus.CANCELLED
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.error  = str(exc)
            finally:
                job.finished_at = datetime.utcnow().isoformat()
                self._running.pop(job_id, None)
                if job.callback and callable(job.callback):
                    try: job.callback(job)
                    except Exception: pass

    def save_job_log(self, job_id: str, path: Optional[str] = None) -> str:
        job = self._jobs.get(job_id)
        if not job: raise ValueError(f"Job {job_id} not found")
        out = Path(path or f"{self.output_dir}/job_{job_id}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(job.to_dict(), indent=2, default=str), encoding="utf-8")
        return str(out)


# Module-level singleton
task_scheduler = TaskScheduler()
