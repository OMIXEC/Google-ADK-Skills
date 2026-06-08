"""Shared fixtures for ADK Skills test suite."""

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
LEGACY_DIR = REPO_ROOT / "legacy-skills"


def _read_frontmatter(path: Path) -> dict | None:
    """Parse YAML frontmatter from a markdown file. Returns dict or None."""
    content = path.read_text()
    if not content.startswith("---"):
        return None
    try:
        end_idx = content.index("---", 3)
        fm_text = content[3:end_idx].strip()
        return yaml.safe_load(fm_text) or {}
    except (ValueError, yaml.YAMLError):
        return None


def _extract_local_links(content: str) -> list[str]:
    """Extract local markdown links (references/... or scripts/...) from content."""
    import re
    # Match [text](relative/path.md) or [text](relative/path.py)
    # But not external URLs
    links = []
    for match in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', content):
        target = match.group(2)
        if not target.startswith(('http://', 'https://', '#', 'mailto:')):
            links.append(target.split('#')[0])  # strip anchor
    return links


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def skills_dir():
    return SKILLS_DIR


@pytest.fixture(scope="session")
def legacy_dir():
    return LEGACY_DIR


@pytest.fixture(scope="session")
def skill_dirs():
    """Return list of all skill directories (containing SKILL.md)."""
    dirs = []
    if SKILLS_DIR.exists():
        for d in sorted(SKILLS_DIR.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                dirs.append(d)
    return dirs


@pytest.fixture(scope="session")
def skill_mds(skill_dirs):
    """Return dict of skill_name -> SKILL.md Path."""
    return {d.name: d / "SKILL.md" for d in skill_dirs}


@pytest.fixture(scope="session")
def read_frontmatter():
    """Fixture providing the _read_frontmatter function."""
    return _read_frontmatter


@pytest.fixture(scope="session")
def extract_links():
    """Fixture providing the _extract_local_links function."""
    return _extract_local_links
