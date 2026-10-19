#!/usr/bin/env python3
"""Repo-owned validator for the ADK skill library.

Encodes the `Skill` / `Frontmatter` contract read from
`google/adk-python@v2.12.0` (see SOURCES.md) plus this repo's self-containment
rules. CI calls this script instead of carrying an inline copy.

Usage:
    python scripts/validate_skills.py                 # skills/ (+ contributing/ if present)
    python scripts/validate_skills.py skills contributing
    python scripts/validate_skills.py skills/adk-mcp  # one skill
    python scripts/validate_skills.py --strict        # warnings become failures

Exit codes:
    0  no errors (warnings allowed unless --strict)
    1  at least one error (or a warning under --strict)
    2  usage or dependency problem
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Iterator, Sequence

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the CLI, not the tests
    sys.stderr.write(
        "pyyaml is required: run with `uv run --with pyyaml python scripts/validate_skills.py`\n"
    )
    raise SystemExit(2)

# ── Contract constants (verified from google/adk-python@v2.12.0) ─────────────

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME_CHARS = 64
MAX_DESCRIPTION_CHARS = 1024
MAX_COMPATIBILITY_CHARS = 500

# L2 = SKILL.md body. L1 = name + description, already capped above.
L2_WARN_TOKENS = 5_000
CHARS_PER_TOKEN = 4  # conservative prose estimate; advisory only

ALLOWED_SUBDIRS = {"references", "assets", "scripts"}
ANTI_TRIGGER_RE = re.compile(
    r"\b(?:don'?t|do not|never)\s+use\b|\bnot\s+for\b|\bavoid\s+using\b",
    re.IGNORECASE,
)

TEXT_SUFFIXES = {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".txt"}
FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_TARGET_RE = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
SKIP_TARGET_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:", "#", "/")
ESCAPE_RE = re.compile(r"\.\./\.\.")


@dataclass(frozen=True)
class Issue:
    severity: str  # "error" | "warn"
    skill: str
    path: str
    code: str
    message: str


class SkillValidator:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.issues: list[Issue] = []

    # ── reporting ────────────────────────────────────────────────────────────

    def _add(self, severity: str, skill: str, path: Path, code: str, message: str) -> None:
        try:
            display = str(path.relative_to(self.root.parent))
        except ValueError:
            display = str(path)
        self.issues.append(Issue(severity, skill, display, code, message))

    def error(self, skill: str, path: Path, code: str, message: str) -> None:
        self._add("error", skill, path, code, message)

    def warn(self, skill: str, path: Path, code: str, message: str) -> None:
        self._add("warn", skill, path, code, message)

    # ── discovery ────────────────────────────────────────────────────────────

    def skill_dirs(self) -> list[Path]:
        if (self.root / "SKILL.md").is_file():
            return [self.root]
        # Every immediate child directory is a candidate: a missing SKILL.md is
        # a defect worth reporting, not a reason to skip the directory.
        return [
            child
            for child in sorted(self.root.iterdir())
            if child.is_dir() and not child.name.startswith(".")
        ]

    # ── per-skill checks ─────────────────────────────────────────────────────

    def validate_skill(self, skill_dir: Path) -> None:
        name = skill_dir.name
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.is_file():
            self.error(name, skill_dir, "missing-skill-md", "no SKILL.md at the skill root")
            return

        nested = [p for p in skill_dir.rglob("SKILL.md") if p != skill_md]
        for path in nested:
            self.error(
                name,
                path,
                "nested-skill-md",
                "only one SKILL.md is allowed, at the skill root",
            )

        for entry in sorted(skill_dir.iterdir()):
            if entry.is_dir() and entry.name not in ALLOWED_SUBDIRS:
                self.error(
                    name,
                    entry,
                    "unknown-subdir",
                    f"only {sorted(ALLOWED_SUBDIRS)} are read by the ADK loader",
                )
            elif entry.is_file() and entry.name != "SKILL.md":
                self.warn(
                    name,
                    entry,
                    "extra-root-file",
                    "the ADK loader ignores files beside SKILL.md; move docs into references/",
                )

        text = skill_md.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(name, skill_md, text)
        if frontmatter is None:
            return

        self._check_name(name, skill_md, frontmatter)
        self._check_description(name, skill_md, frontmatter)
        self._check_compatibility(name, skill_md, frontmatter)
        self._check_advisory_fields(name, skill_md, frontmatter)
        self._check_token_budget(name, skill_md, body)
        self._check_files(name, skill_dir)

    def _split_frontmatter(
        self, name: str, path: Path, text: str
    ) -> tuple[dict | None, str]:
        match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.DOTALL)
        if not match:
            self.error(name, path, "frontmatter-missing", "SKILL.md must start with YAML frontmatter")
            return None, text
        raw = match.group(1)
        body = text[match.end():]
        try:
            parsed = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            self.error(name, path, "frontmatter-invalid", f"YAML does not parse: {exc}")
            return None, body
        if not isinstance(parsed, dict):
            self.error(name, path, "frontmatter-invalid", "frontmatter must be a mapping")
            return None, body
        return parsed, body

    def _check_name(self, folder: str, path: Path, fm: dict) -> None:
        value = fm.get("name")
        if value is None:
            self.error(folder, path, "name-missing", "frontmatter has no name")
            return
        if not isinstance(value, str):
            self.error(folder, path, "name-type", "name must be a string")
            return
        if value != folder:
            self.error(
                folder, path, "name-folder", f"name {value!r} does not match directory {folder!r}"
            )
        if not NAME_RE.match(value):
            self.error(folder, path, "name-kebab", f"name {value!r} is not kebab-case")
        if len(value) > MAX_NAME_CHARS:
            self.error(
                folder, path, "name-length", f"name is {len(value)} chars (max {MAX_NAME_CHARS})"
            )

    def _check_description(self, folder: str, path: Path, fm: dict) -> None:
        value = fm.get("description")
        if value is None or (isinstance(value, str) and not value.strip()):
            self.error(folder, path, "description-missing", "frontmatter has no description")
            return
        if not isinstance(value, str):
            self.error(folder, path, "description-type", "description must be a string")
            return
        if len(value) > MAX_DESCRIPTION_CHARS:
            self.error(
                folder,
                path,
                "description-length",
                f"description is {len(value)} chars (max {MAX_DESCRIPTION_CHARS})",
            )
        if not ANTI_TRIGGER_RE.search(value):
            self.warn(
                folder,
                path,
                "description-no-negative-trigger",
                "description has no negative trigger; name the excluded case and its sibling skill",
            )

    def _check_compatibility(self, folder: str, path: Path, fm: dict) -> None:
        if "compatibility" not in fm:
            self.error(folder, path, "compatibility-missing", "frontmatter has no compatibility")
            return
        value = fm["compatibility"]
        if not isinstance(value, str) or not value.strip():
            self.error(folder, path, "compatibility-type", "compatibility must be a non-empty string")
            return
        if len(value) > MAX_COMPATIBILITY_CHARS:
            self.error(
                folder,
                path,
                "compatibility-length",
                f"compatibility is {len(value)} chars (max {MAX_COMPATIBILITY_CHARS})",
            )
        if "google-adk" not in value:
            self.warn(
                folder,
                path,
                "compatibility-shape",
                "compatibility does not name google-adk; runtime ignores this field, humans do not",
            )

    def _check_advisory_fields(self, folder: str, path: Path, fm: dict) -> None:
        if "disable-model-invocation" in fm:
            self.warn(
                folder,
                path,
                "harness-only-field",
                "disable-model-invocation is a Claude Code field; ADK ignores it",
            )

    def _check_token_budget(self, folder: str, path: Path, body: str) -> None:
        estimate = max(1, round(len(body) / CHARS_PER_TOKEN))
        if estimate > L2_WARN_TOKENS:
            self.warn(
                folder,
                path,
                "l2-budget",
                f"SKILL.md body ~{estimate} tokens (soft budget {L2_WARN_TOKENS}); split the skill",
            )

    def _check_files(self, folder: str, skill_dir: Path) -> None:
        for path in sorted(skill_dir.rglob("*")):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if path.suffix == ".md":
                stripped = FENCE_RE.sub("", text)
                if ESCAPE_RE.search(stripped):
                    self.error(
                        folder,
                        path,
                        "path-escape",
                        "contains a `../..` reference; the skill must be self-contained",
                    )
                text = stripped
            self._check_links(folder, skill_dir, path, text)

    def _check_links(self, folder: str, skill_dir: Path, path: Path, text: str) -> None:
        root = skill_dir.resolve()
        targets = MD_LINK_RE.findall(text) + HTML_TARGET_RE.findall(text)
        for raw in targets:
            target = raw.strip().split()[0] if raw.strip() else ""
            if not target or target.startswith(SKIP_TARGET_PREFIXES):
                continue
            if "{" in target or "}" in target:
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if resolved != root and root not in resolved.parents:
                self.error(
                    folder,
                    path,
                    "link-escape",
                    f"{raw!r} resolves outside the skill root",
                )
            elif not resolved.exists():
                self.error(folder, path, "link-broken", f"{raw!r} does not exist")

    # ── driver ───────────────────────────────────────────────────────────────

    def run(self) -> list[Issue]:
        dirs = self.skill_dirs()
        if not dirs:
            self.error("<root>", self.root, "no-skills", "no skill directories found")
            return self.issues
        for skill_dir in dirs:
            self.validate_skill(skill_dir)
        return self.issues


def default_roots() -> list[Path]:
    repo = Path(__file__).resolve().parent.parent
    return [repo / name for name in ("skills", "contributing") if (repo / name).is_dir()]


def iter_issue_lines(issues: Sequence[Issue]) -> Iterator[str]:
    for issue in issues:
        yield f"{issue.severity.upper():5} [{issue.code}] {issue.path}: {issue.message}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the ADK skill library.")
    parser.add_argument("paths", nargs="*", help="skill roots (default: skills/ and contributing/)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    roots = [Path(p) for p in args.paths] or default_roots()
    missing = [root for root in roots if not root.exists()]
    if missing:
        sys.stderr.write(f"missing path(s): {', '.join(map(str, missing))}\n")
        return 2

    issues: list[Issue] = []
    for root in roots:
        issues.extend(SkillValidator(root).run())

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warn"]

    if args.json:
        print(json.dumps([asdict(i) for i in issues], indent=2))
    else:
        for line in iter_issue_lines(issues):
            print(line)
        skills = sum(len(SkillValidator(r).skill_dirs()) for r in roots)
        print(f"\n{skills} skill(s): {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
