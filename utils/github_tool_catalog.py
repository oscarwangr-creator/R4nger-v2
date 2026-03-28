"""Catalog helpers for integrating repositories from ``tools/github`` into framework primitives."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(frozen=True, slots=True)
class GitHubToolProfile:
    """Normalized profile built from a repository folder under ``tools/github``."""

    repo_name: str
    slug: str
    category: str
    stage: str
    module_name: str
    description: str
    tags: List[str]
    source_path: str


CATEGORY_HINTS: Dict[str, set[str]] = {
    "OSINT": {
        "osint",
        "ghunt",
        "holehe",
        "instaloader",
        "osintgram",
        "sherlock",
        "social",
        "theharvester",
        "twint",
        "user-scanner",
        "whatsmyname",
        "phoneinfoga",
        "profil3r",
        "github-scraper",
        "instagram",
        "infoga",
        "dork",
    },
    "Post-Exploit": {
        "autopsy",
        "forensic",
        "keylogger",
        "lazagne",
        "mimikatz",
        "responder",
        "sleuthkit",
        "velociraptor",
        "wireshark",
        "tcpdump",
        "usbpcap",
        "zeek",
        "device-activity-tracker",
    },
    "Exploit": {
        "aircrack",
        "bettercap",
        "empire",
        "exploit",
        "fiercephish",
        "gophish",
        "hydra",
        "metasploit",
        "nipe",
        "nosqlmap",
        "socialfish",
        "sqlmap",
        "wifiphisher",
        "xss",
        "zaproxy",
    },
}

STAGE_BY_CATEGORY = {
    "OSINT": "osint",
    "Recon": "recon",
    "Exploit": "exploit",
    "Post-Exploit": "post",
}


def _slugify(repo_name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in repo_name).strip("_")


def _infer_category(slug: str) -> str:
    for category, hints in CATEGORY_HINTS.items():
        if any(hint in slug for hint in hints):
            return category
    return "Recon"


def _infer_tags(repo_name: str, category: str) -> List[str]:
    tags = ["github", "integration", category.lower().replace("-", "_")]
    for token in _slugify(repo_name).split("_"):
        if token and token not in tags:
            tags.append(token)
    return tags[:8]


def load_github_tool_profiles(base_dir: str | Path = "tools/github") -> List[GitHubToolProfile]:
    root = Path(base_dir)
    if not root.exists():
        return []

    profiles: List[GitHubToolProfile] = []
    for repo_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        slug = _slugify(repo_dir.name)
        category = _infer_category(slug)
        stage = STAGE_BY_CATEGORY[category]
        profiles.append(
            GitHubToolProfile(
                repo_name=repo_dir.name,
                slug=slug,
                category=category,
                stage=stage,
                module_name=f"github_{slug}_{stage}",
                description=f"GitHub tool integration bridge for {repo_dir.name}.",
                tags=_infer_tags(repo_dir.name, category),
                source_path=str(repo_dir.as_posix()),
            )
        )

    return profiles


def grouped_profiles(base_dir: str | Path = "tools/github") -> Dict[str, List[GitHubToolProfile]]:
    grouped: Dict[str, List[GitHubToolProfile]] = {"osint": [], "recon": [], "exploit": [], "post": []}
    for profile in load_github_tool_profiles(base_dir):
        grouped[profile.stage].append(profile)
    return grouped


def module_names(base_dir: str | Path = "tools/github") -> Iterable[str]:
    return (profile.module_name for profile in load_github_tool_profiles(base_dir))
