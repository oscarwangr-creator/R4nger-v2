from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from framework.core.logger import get_logger


@dataclass
class ToolExecutionResult:
    tool: str
    target: str
    success: bool
    attempts: int
    return_code: int = 0
    raw_output: str = ""
    parsed: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    finished_at: str = ""
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "target": self.target,
            "success": self.success,
            "attempts": self.attempts,
            "return_code": self.return_code,
            "raw_output": self.raw_output[:5000],
            "parsed": self.parsed,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration": round(self.duration, 3),
            "metadata": self.metadata,
        }


class ToolWrapper:
    tool_name: str = "generic"
    binary: str = ""
    timeout: int = 60
    retries: int = 3

    def __init__(self) -> None:
        self.log = get_logger(f"rtf.intelligence.{self.tool_name}")

    def build_command(self, target: str) -> Sequence[str]:
        raise NotImplementedError

    async def run(self, target: str) -> Dict[str, Any]:
        attempts = 0
        last_error = ""
        raw = ""
        parsed: Dict[str, Any] = {}
        start = datetime.utcnow()
        return_code = 0

        if self.binary and not shutil.which(self.binary):
            result = ToolExecutionResult(
                tool=self.tool_name,
                target=target,
                success=False,
                attempts=0,
                error=f"Tool '{self.binary}' is not installed",
                metadata={"available": False},
                finished_at=datetime.utcnow().isoformat(),
            )
            return result.to_json()

        for attempt in range(1, self.retries + 1):
            attempts = attempt
            try:
                cmd = list(self.build_command(target))
                self.log.info("Running %s attempt %s against %s", self.tool_name, attempt, target)
                self.log.debug("Command: %s", " ".join(cmd))
                stdout, stderr, return_code = await self._safe_subprocess(cmd)
                raw = (stdout or "") + (("\n" + stderr) if stderr else "")
                parsed = self.parse_output(raw)
                if self.validate(parsed):
                    finished = datetime.utcnow()
                    return ToolExecutionResult(
                        tool=self.tool_name,
                        target=target,
                        success=True,
                        attempts=attempts,
                        return_code=return_code,
                        raw_output=raw,
                        parsed=parsed,
                        finished_at=finished.isoformat(),
                        duration=(finished - start).total_seconds(),
                        metadata={"available": True},
                    ).to_json()
                last_error = "Validation failed"
            except Exception as exc:
                last_error = str(exc)
                self.log.warning("%s attempt %s failed: %s", self.tool_name, attempt, exc)
                if attempt < self.retries:
                    await asyncio.sleep(min(2 * attempt, 5))

        finished = datetime.utcnow()
        return ToolExecutionResult(
            tool=self.tool_name,
            target=target,
            success=False,
            attempts=attempts,
            return_code=return_code,
            raw_output=raw,
            parsed=parsed,
            error=last_error,
            finished_at=finished.isoformat(),
            duration=(finished - start).total_seconds(),
            metadata={"available": True},
        ).to_json()

    async def _safe_subprocess(self, cmd: Sequence[str]) -> tuple[str, str, int]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError as exc:
            proc.kill()
            await proc.communicate()
            raise TimeoutError(f"{self.tool_name} timed out after {self.timeout}s") from exc
        return (
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            proc.returncode,
        )

    def parse_output(self, raw: str) -> Dict[str, Any]:
        raw = (raw or "").strip()
        if not raw:
            return {"records": []}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {"records": parsed}
        except Exception:
            return {"records": [line.strip() for line in raw.splitlines() if line.strip()]}

    def validate(self, data: Dict[str, Any]) -> bool:
        return isinstance(data, dict)

    def to_json(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "binary": self.binary,
            "timeout": self.timeout,
            "retries": self.retries,
        }
