from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List
import ast
import json

import yaml


@dataclass
class AuditIssue:
    severity: str
    category: str
    message: str
    location: str


@dataclass
class RepositoryAuditReport:
    status: str
    metrics: Dict[str, Any]
    issues: List[AuditIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "metrics": self.metrics,
            "issues": [asdict(issue) for issue in self.issues],
        }


class RepositoryAuditor:
    """Performs a recursive static integration audit for the Intelligence OS tree."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def _iter_files(self) -> Iterable[Path]:
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if any(part.startswith(".") for part in path.parts):
                continue
            if path.suffix in {".pyc", ".pyo", ".db", ".wal", ".shm", ".log"}:
                continue
            yield path

    def _check_python(self, path: Path, issues: List[AuditIssue]) -> None:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (UnicodeDecodeError, SyntaxError) as exc:
            issues.append(AuditIssue("error", "python", f"Unable to parse Python file: {exc}", str(path.relative_to(self.root))))
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                        issues.append(
                            AuditIssue(
                                "warning",
                                "python",
                                "Broad exception handler may hide integration errors.",
                                f"{path.relative_to(self.root)}:{node.lineno}",
                            )
                        )

    def _check_yaml(self, path: Path, issues: List[AuditIssue]) -> None:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - parser failure branch
            issues.append(AuditIssue("error", "yaml", f"Invalid YAML: {exc}", str(path.relative_to(self.root))))
            return

        if isinstance(data, dict) and path.parent.name == "pipelines":
            if "stages" not in data:
                issues.append(AuditIssue("error", "pipeline", "Pipeline file is missing 'stages'.", str(path.relative_to(self.root))))
            if "name" not in data:
                issues.append(AuditIssue("error", "pipeline", "Pipeline file is missing 'name'.", str(path.relative_to(self.root))))

    def _check_json(self, path: Path, issues: List[AuditIssue]) -> None:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(AuditIssue("error", "json", f"Invalid JSON: {exc}", str(path.relative_to(self.root))))

    def run(self) -> RepositoryAuditReport:
        issues: List[AuditIssue] = []
        counts: Dict[str, int] = {
            "total_files": 0,
            "python_files": 0,
            "yaml_files": 0,
            "json_files": 0,
            "markdown_files": 0,
        }

        for file_path in self._iter_files():
            counts["total_files"] += 1
            suffix = file_path.suffix.lower()
            if suffix == ".py":
                counts["python_files"] += 1
                self._check_python(file_path, issues)
            elif suffix in {".yaml", ".yml"}:
                counts["yaml_files"] += 1
                self._check_yaml(file_path, issues)
            elif suffix == ".json":
                counts["json_files"] += 1
                self._check_json(file_path, issues)
            elif suffix in {".md", ".txt"}:
                counts["markdown_files"] += 1

        error_count = len([issue for issue in issues if issue.severity == "error"])
        warning_count = len([issue for issue in issues if issue.severity == "warning"])
        status = "ok" if error_count == 0 else "degraded"
        counts["error_count"] = error_count
        counts["warning_count"] = warning_count

        return RepositoryAuditReport(status=status, metrics=counts, issues=issues)
