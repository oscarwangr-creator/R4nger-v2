"""RedTeam Framework v2.0 - Task Scheduler"""
from __future__ import annotations
import asyncio, uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional
from framework.core.logger import get_logger
log = get_logger("rtf.scheduler")

class JobStatus(str, Enum):
    PENDING="pending"; RUNNING="running"; COMPLETED="completed"
    FAILED="failed"; CANCELLED="cancelled"; SCHEDULED="scheduled"

@dataclass
class Job:
    id: str; name: str; coro_factory: Callable[[], Coroutine]
    status: JobStatus = JobStatus.PENDING; priority: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None; finished_at: Optional[datetime] = None
    result: Any = None; error: Optional[str] = None; timeout: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    interval_seconds: Optional[int] = None; run_at: Optional[datetime] = None
    next_run: Optional[datetime] = None
    _task: Optional[asyncio.Task] = field(default=None, repr=False, compare=False)

    @property
    def elapsed(self) -> Optional[float]:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "status": self.status.value,
                "priority": self.priority, "created_at": self.created_at.isoformat(),
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "finished_at": self.finished_at.isoformat() if self.finished_at else None,
                "elapsed": self.elapsed, "error": self.error, "tags": self.tags,
                "interval_seconds": self.interval_seconds}

class Scheduler:
    def __init__(self, max_workers: int = 10) -> None:
        self._max_workers = max_workers
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._jobs: Dict[str, Job] = {}
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._running = True
        self._worker_tasks = [asyncio.create_task(self._worker(i)) for i in range(self._max_workers)]
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        log.info(f"Scheduler started with {self._max_workers} workers")

    async def stop(self, timeout: float = 30.0) -> None:
        self._running = False
        if self._scheduler_task: self._scheduler_task.cancel()
        for task in self._worker_tasks: task.cancel()
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

    def submit(self, name: str, coro_factory: Callable[[], Coroutine], priority: int = 5,
               timeout: Optional[int] = None, tags: Optional[List[str]] = None) -> Job:
        job = Job(id=str(uuid.uuid4()), name=name, coro_factory=coro_factory,
                  priority=priority, timeout=timeout, tags=tags or [])
        self._jobs[job.id] = job
        self._queue.put_nowait((priority, datetime.utcnow().timestamp(), job.id))
        return job

    def schedule_interval(self, name: str, coro_factory: Callable[[], Coroutine],
                           interval_seconds: int, run_immediately: bool = True,
                           priority: int = 5, tags: Optional[List[str]] = None) -> Job:
        next_run = datetime.utcnow() if run_immediately else datetime.utcnow() + timedelta(seconds=interval_seconds)
        job = Job(id=str(uuid.uuid4()), name=name, coro_factory=coro_factory,
                  status=JobStatus.SCHEDULED, priority=priority, interval_seconds=interval_seconds,
                  next_run=next_run, tags=tags or [])
        self._jobs[job.id] = job
        return job

    async def wait_for(self, job_id: str, poll_interval: float = 0.5) -> Job:
        while True:
            job = self._jobs.get(job_id)
            if job is None: raise KeyError(f"Unknown job: {job_id}")
            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED): return job
            await asyncio.sleep(poll_interval)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job: return False
        if job._task and not job._task.done(): job._task.cancel()
        job.status = JobStatus.CANCELLED
        return True

    def get_job(self, job_id: str) -> Optional[Job]: return self._jobs.get(job_id)

    def list_jobs(self, status: Optional[JobStatus] = None, tag: Optional[str] = None) -> List[Job]:
        jobs = list(self._jobs.values())
        if status: jobs = [j for j in jobs if j.status == status]
        if tag: jobs = [j for j in jobs if tag in j.tags]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def stats(self) -> Dict[str, int]:
        all_jobs = list(self._jobs.values())
        return {s.value: sum(1 for j in all_jobs if j.status == s) for s in JobStatus} | {"total": len(all_jobs)}

    async def _worker(self, worker_id: int) -> None:
        while self._running:
            try:
                _, _, job_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError: continue
            except asyncio.CancelledError: break
            job = self._jobs.get(job_id)
            if not job or job.status == JobStatus.CANCELLED:
                self._queue.task_done(); continue
            await self._execute_job(job)
            self._queue.task_done()

    async def _execute_job(self, job: Job) -> None:
        job.status = JobStatus.RUNNING; job.started_at = datetime.utcnow()
        try:
            coro = job.coro_factory()
            job.result = await (asyncio.wait_for(coro, timeout=job.timeout) if job.timeout else coro)
            job.status = JobStatus.COMPLETED
        except asyncio.CancelledError: job.status = JobStatus.CANCELLED
        except asyncio.TimeoutError: job.status = JobStatus.FAILED; job.error = f"Timeout after {job.timeout}s"
        except Exception as exc: job.status = JobStatus.FAILED; job.error = str(exc)
        finally: job.finished_at = datetime.utcnow()

    async def _scheduler_loop(self) -> None:
        while self._running:
            now = datetime.utcnow()
            for job in list(self._jobs.values()):
                if job.status != JobStatus.SCHEDULED: continue
                if job.next_run and job.next_run <= now:
                    job.status = JobStatus.PENDING
                    self._queue.put_nowait((job.priority, now.timestamp(), job.id))
                    if job.interval_seconds:
                        next_job = Job(id=str(uuid.uuid4()), name=job.name, coro_factory=job.coro_factory,
                                       status=JobStatus.SCHEDULED, priority=job.priority,
                                       interval_seconds=job.interval_seconds,
                                       next_run=now + timedelta(seconds=job.interval_seconds), tags=job.tags)
                        self._jobs[next_job.id] = next_job
            await asyncio.sleep(1.0)

scheduler = Scheduler()
