"""
RedTeam Framework v2.0 - Base Module
All framework modules inherit from BaseModule.
"""
from __future__ import annotations

import abc
import asyncio
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from framework.core.exceptions import (
    ModuleExecutionError, OptionValidationError, ToolNotInstalledError,
)
from framework.core.logger import get_logger


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Option:
    name: str
    description: str
    required: bool = True
    default: Any = None
    type: type = str
    choices: Optional[List[Any]] = None

    def coerce(self, value: Any) -> Any:
        if value is None:
            return self.default
        if self.type is bool and isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return self.type(value)


@dataclass
class Finding:
    title: str
    target: str
    category: str
    severity: Severity = Severity.INFO
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title, "target": self.target, "category": self.category,
            "severity": self.severity.value, "description": self.description,
            "evidence": self.evidence, "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ModuleResult:
    success: bool
    output: Any = None
    findings: List[Finding] = field(default_factory=list)
    raw_output: str = ""
    error: Optional[str] = None
    elapsed: float = 0.0
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success, "output": self.output,
            "findings": [f.to_dict() for f in self.findings],
            "raw_output": self.raw_output[:5000] if self.raw_output else "",
            "error": self.error, "elapsed": round(self.elapsed, 3), "job_id": self.job_id,
        }


class BaseModule(abc.ABC):
    def __init__(self) -> None:
        self._options: Dict[str, Any] = {}
        self._option_defs: Dict[str, Option] = {}
        self._results: List[ModuleResult] = []
        self.log = get_logger(f"rtf.module.{self.info().get('name','unknown')}")
        self._declare_options()
        for opt in self._option_defs.values():
            if opt.default is not None:
                self._options[opt.name] = opt.default

    @abc.abstractmethod
    def info(self) -> Dict[str, Any]: ...

    @abc.abstractmethod
    def _declare_options(self) -> None: ...

    @abc.abstractmethod
    async def run(self) -> ModuleResult: ...

    def _register_option(self, name: str, description: str, required: bool = True,
                          default: Any = None, type: type = str, choices: Optional[List[Any]] = None) -> None:
        self._option_defs[name] = Option(name=name, description=description, required=required,
                                          default=default, type=type, choices=choices)

    def set(self, key: str, value: Any) -> None:
        if key not in self._option_defs:
            raise OptionValidationError(key, f"Unknown option '{key}' for module {self.info().get('name','?')}")
        opt = self._option_defs[key]
        coerced = opt.coerce(value)
        if opt.choices and coerced not in opt.choices:
            raise OptionValidationError(key, f"Value '{coerced}' not in allowed choices: {opt.choices}")
        self._options[key] = coerced

    def get(self, key: str) -> Any:
        return self._options.get(key)

    def show_options(self) -> List[Dict[str, Any]]:
        return [{"name": name, "current_value": self._options.get(name, ""),
                 "required": opt.required, "default": opt.default, "description": opt.description}
                for name, opt in self._option_defs.items()]

    def validate(self) -> None:
        for name, opt in self._option_defs.items():
            if opt.required and self._options.get(name) in (None, "", []):
                raise OptionValidationError(name)

    def set_options(self, options: Dict[str, Any]) -> None:
        for k, v in options.items():
            if k in self._option_defs:
                self.set(k, v)

    async def execute(self, options: Optional[Dict[str, Any]] = None) -> ModuleResult:
        if options:
            self.set_options(options)
        meta = self.info()
        self.log.info(f"→ Running module: {meta.get('name','?')}")
        start = datetime.utcnow()
        try:
            self.validate()
            result = await self.run()
        except ToolNotInstalledError as exc:
            result = ModuleResult(success=False, error=f"Required tool not installed: {exc.tool_name}")
        except (OptionValidationError, ModuleExecutionError) as exc:
            result = ModuleResult(success=False, error=str(exc))
        except Exception as exc:
            self.log.exception(f"Unhandled exception in {meta.get('name','?')}")
            result = ModuleResult(success=False, error=str(exc))
        result.elapsed = (datetime.utcnow() - start).total_seconds()
        self._results.append(result)
        status = "✓ OK" if result.success else "✗ FAILED"
        self.log.info(f"{status} | elapsed={result.elapsed:.2f}s | findings={len(result.findings)}")
        return result

    def require_tool(self, binary: str) -> str:
        path = shutil.which(binary)
        if not path:
            raise ToolNotInstalledError(binary)
        return path

    def run_command(self, cmd: List[str], timeout: int = 300, capture: bool = True,
                    cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        self.log.debug(f"CMD: {' '.join(cmd)}")
        return subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout, cwd=cwd)

    async def run_command_async(self, cmd: List[str], timeout: int = 300,
                                 cwd: Optional[str] = None) -> tuple:
        self.log.debug(f"ASYNC CMD: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.communicate()
            except Exception:
                pass
            raise ModuleExecutionError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        return (stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
                proc.returncode)

    def make_finding(self, title: str, target: str, severity: Severity = Severity.INFO,
                      description: str = "", evidence: Optional[Dict] = None,
                      tags: Optional[List[str]] = None) -> Finding:
        return Finding(title=title, target=target, category=self.info().get("category", "general"),
                       severity=severity, description=description, evidence=evidence or {},
                       tags=tags or [])

    def __repr__(self) -> str:
        meta = self.info()
        return f"<Module [{meta.get('category','?')}] {meta.get('name','?')}>"
