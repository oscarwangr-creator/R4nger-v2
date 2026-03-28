from __future__ import annotations

from typing import Any, Dict

from core.base_module import BaseModule, ModuleMetadata
from utils.github_tool_catalog import GitHubToolProfile, load_github_tool_profiles


class GitHubToolModule(BaseModule):
    """Generic integration module backed by a discovered GitHub tool profile."""

    def __init__(self, profile: GitHubToolProfile) -> None:
        super().__init__()
        self.profile = profile
        self.metadata = ModuleMetadata(
            name=profile.module_name,
            category=profile.category,
            description=profile.description,
            tags=profile.tags,
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "target": payload["target"],
            "module": self.metadata.name,
            "summary": (
                f"Integrated GitHub repository {self.profile.repo_name} into "
                f"{self.profile.stage} stage orchestration."
            ),
            "source": {
                "repository_folder": self.profile.source_path,
                "integration_mode": "framework-bridge",
            },
            "execution": {
                "simulated": True,
                "stage": self.profile.stage,
                "timestamp": payload.get("timestamp", "runtime"),
            },
            "tags": self.profile.tags,
        }


def build_github_tool_modules() -> dict[str, GitHubToolModule]:
    modules = [GitHubToolModule(profile) for profile in load_github_tool_profiles()]
    return {module.metadata.name: module for module in modules}
