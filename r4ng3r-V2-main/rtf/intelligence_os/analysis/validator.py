from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml

from intelligence_os.tooling.catalog import load_framework_manifest
from intelligence_os.tooling.registry import registry


@dataclass
class ValidationIssue:
    severity: str
    message: str
    location: str


@dataclass
class ValidationReport:
    status: str
    metrics: Dict[str, Any]
    issues: List[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'metrics': self.metrics,
            'issues': [asdict(issue) for issue in self.issues],
        }


class FrameworkValidator:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parents[1])
        self.pipeline_dir = self.root / 'pipelines'
        self.module_dir = self.root / 'modules'
        self.manifest = load_framework_manifest()

    def _validate_pipelines(self) -> tuple[List[ValidationIssue], Dict[str, Any]]:
        issues: List[ValidationIssue] = []
        stage_counts: Dict[str, int] = {}
        recursive_ready = 0
        ai_ready = 0
        report_ready = 0
        for path in sorted(self.pipeline_dir.glob('*.yaml')):
            data = yaml.safe_load(path.read_text()) or {}
            stages = data.get('stages', [])
            stage_counts[path.stem] = len(stages)
            if len(stages) < 8:
                issues.append(ValidationIssue('error', f'Pipeline has fewer than 8 stages ({len(stages)}).', str(path.relative_to(self.root))))
            if data.get('recursive_pivoting'):
                recursive_ready += 1
            else:
                issues.append(ValidationIssue('warning', 'Pipeline missing recursive_pivoting flag.', str(path.relative_to(self.root))))
            if data.get('ai_assisted'):
                ai_ready += 1
            else:
                issues.append(ValidationIssue('warning', 'Pipeline missing ai_assisted flag.', str(path.relative_to(self.root))))
            output = data.get('output', {}) if isinstance(data.get('output', {}), dict) else {}
            if output.get('formats'):
                report_ready += 1
            else:
                issues.append(ValidationIssue('warning', 'Pipeline missing output formats.', str(path.relative_to(self.root))))
        metrics = {
            'total_pipelines': len(stage_counts),
            'stage_counts': stage_counts,
            'recursive_ready': recursive_ready,
            'ai_ready': ai_ready,
            'report_ready': report_ready,
        }
        return issues, metrics

    def _validate_manifest_alignment(self) -> tuple[List[ValidationIssue], Dict[str, Any]]:
        issues: List[ValidationIssue] = []
        manifest_pipelines = {entry['name'] for entry in self.manifest.get('pipelines', [])}
        disk_pipelines = {path.stem for path in self.pipeline_dir.glob('*.yaml')}
        missing_on_disk = sorted(manifest_pipelines - disk_pipelines)
        untracked_on_disk = sorted(disk_pipelines - manifest_pipelines)
        if missing_on_disk:
            issues.append(ValidationIssue('error', f'Manifest pipelines missing on disk: {missing_on_disk[:10]}', 'manifests/framework_manifest.json'))
        if untracked_on_disk:
            issues.append(ValidationIssue('warning', f'Pipelines present on disk but missing in manifest: {untracked_on_disk[:10]}', 'manifests/framework_manifest.json'))
        summary = registry.summary()
        metrics = {
            'manifest_modules': len(self.manifest.get('modules', [])),
            'manifest_tools': len(self.manifest.get('tools', [])),
            'manifest_pipelines': len(manifest_pipelines),
            'workflow_families': len(self.manifest.get('workflows', [])),
            'registry_tools': summary['total_tools'],
        }
        return issues, metrics

    def _validate_module_packs(self) -> tuple[List[ValidationIssue], Dict[str, Any]]:
        issues: List[ValidationIssue] = []
        required_files = {'module.py', 'config.yaml', 'requirements.txt', 'README.md'}
        discovered = 0
        complete = 0
        for module_path in sorted(self.module_dir.iterdir() if self.module_dir.exists() else []):
            if not module_path.is_dir():
                continue
            discovered += 1
            present = {item.name for item in module_path.iterdir() if item.is_file()}
            missing = required_files - present
            if missing:
                issues.append(ValidationIssue('warning', f'Module pack missing files: {sorted(missing)}', str(module_path.relative_to(self.root))))
            else:
                complete += 1
        return issues, {'module_packs': discovered, 'complete_module_packs': complete}

    def validate(self) -> ValidationReport:
        issues: List[ValidationIssue] = []
        pipeline_issues, pipeline_metrics = self._validate_pipelines()
        manifest_issues, manifest_metrics = self._validate_manifest_alignment()
        module_issues, module_metrics = self._validate_module_packs()
        issues.extend(pipeline_issues)
        issues.extend(manifest_issues)
        issues.extend(module_issues)
        status = 'ok' if not any(issue.severity == 'error' for issue in issues) else 'degraded'
        return ValidationReport(
            status=status,
            metrics={
                **pipeline_metrics,
                **manifest_metrics,
                **module_metrics,
            },
            issues=issues,
        )
