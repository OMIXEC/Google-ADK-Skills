"""Tests for scripts/validate_skills.py.

The validator is the repo's only gate for the ADK skill contract, so each
rule gets a positive and a negative case. Fixtures are built on disk because
the checks are filesystem-shaped (link resolution, nested SKILL.md, subdirs).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "validate_skills.py"

_spec = importlib.util.spec_from_file_location("validate_skills", SCRIPT)
validate_skills = importlib.util.module_from_spec(_spec)
sys.modules["validate_skills"] = validate_skills
_spec.loader.exec_module(validate_skills)


def write_skill(
    root: Path,
    name: str,
    *,
    description: str = "Builds agents. Use when building. Don't use for debugging (use adk-debug).",
    compatibility: str | None = "google-adk>=2.9.2,<3",
    body: str = "# Skill\n\nBody.\n",
    extra_frontmatter: str = "",
    extra_files: dict[str, str] | None = None,
) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    fm = [f"name: {name}", f"description: {description}"]
    if compatibility is not None:
        fm.append(f"compatibility: {compatibility}")
    if extra_frontmatter:
        fm.append(extra_frontmatter)
    (skill_dir / "SKILL.md").write_text("---\n" + "\n".join(fm) + "\n---\n\n" + body)
    for rel, content in (extra_files or {}).items():
        path = skill_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return skill_dir


def validate(root: Path):
    return validate_skills.SkillValidator(root).run()


def codes(issues, severity=None):
    return {i.code for i in issues if severity is None or i.severity == severity}


def test_valid_skill_has_no_issues(tmp_path):
    write_skill(tmp_path, "adk-good")
    assert validate(tmp_path) == []


def test_name_must_match_directory(tmp_path):
    skill = write_skill(tmp_path, "adk-wrong")
    text = (skill / "SKILL.md").read_text().replace("name: adk-wrong", "name: adk-other")
    (skill / "SKILL.md").write_text(text)
    assert "name-folder" in codes(validate(tmp_path), "error")


@pytest.mark.parametrize("bad", ["Adk-Bad", "adk_bad", "adk--bad", "adk bad"])
def test_name_must_be_kebab_case(tmp_path, bad):
    skill = write_skill(tmp_path, "adk-placeholder")
    text = (skill / "SKILL.md").read_text().replace("name: adk-placeholder", f"name: {bad}")
    (skill / "SKILL.md").write_text(text)
    assert "name-kebab" in codes(validate(tmp_path), "error")


def test_name_length_is_capped(tmp_path):
    long_name = "a" * 65
    write_skill(tmp_path, long_name)
    assert "name-length" in codes(validate(tmp_path), "error")


def test_missing_compatibility_fails(tmp_path):
    write_skill(tmp_path, "adk-good", compatibility=None)
    assert "compatibility-missing" in codes(validate(tmp_path), "error")


def test_compatibility_length_is_capped(tmp_path):
    write_skill(tmp_path, "adk-good", compatibility="g" * 501)
    assert "compatibility-length" in codes(validate(tmp_path), "error")


def test_description_negative_trigger_is_advisory(tmp_path):
    write_skill(tmp_path, "adk-good", description="Builds agents when asked.")
    issues = validate(tmp_path)
    assert "description-no-negative-trigger" in codes(issues, "warn")
    assert "description-no-negative-trigger" not in codes(issues, "error")


def test_description_length_is_capped(tmp_path):
    write_skill(tmp_path, "adk-good", description="x" * 1025)
    assert "description-length" in codes(validate(tmp_path), "error")


def test_description_must_not_be_empty(tmp_path):
    write_skill(tmp_path, "adk-good", description="''")
    assert "description-missing" in codes(validate(tmp_path), "error")


def test_nested_skill_md_fails(tmp_path):
    skill = write_skill(tmp_path, "adk-good")
    nested = skill / "references" / "nested" / "SKILL.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("---\nname: nested\ndescription: n\n---\n")
    assert "nested-skill-md" in codes(validate(tmp_path), "error")


def test_unknown_subdirectory_fails(tmp_path):
    write_skill(tmp_path, "adk-good", extra_files={"docs/guide.md": "hi"})
    assert "unknown-subdir" in codes(validate(tmp_path), "error")


def test_allowed_subdirectories_pass(tmp_path):
    write_skill(
        tmp_path,
        "adk-good",
        extra_files={
            "references/a.md": "a",
            "assets/b.txt": "b",
            "scripts/c.py": "print('c')\n",
        },
    )
    assert validate(tmp_path) == []


def test_path_escape_fails(tmp_path):
    write_skill(tmp_path, "adk-good", body="See [baseline](../../docs/python-adk-2.md).\n")
    assert "path-escape" in codes(validate(tmp_path), "error")


def test_path_escape_in_fenced_code_is_ignored(tmp_path):
    write_skill(tmp_path, "adk-good", body="```bash\ncd ../../elsewhere\n```\n")
    assert "path-escape" not in codes(validate(tmp_path), "error")


def test_broken_link_fails(tmp_path):
    write_skill(tmp_path, "adk-good", body="See [missing](references/nope.md).\n")
    assert "link-broken" in codes(validate(tmp_path), "error")


def test_existing_relative_link_passes(tmp_path):
    write_skill(
        tmp_path,
        "adk-good",
        body="See [guide](references/guide.md).\n",
        extra_files={"references/guide.md": "# Guide\n"},
    )
    assert validate(tmp_path) == []


@pytest.mark.parametrize(
    "target", ["https://example.com/x.md", "mailto:a@b.c", "#anchor", "/absolute/path.md"]
)
def test_external_and_absolute_links_are_skipped(tmp_path, target):
    write_skill(tmp_path, "adk-good", body=f"See [x]({target}).\n")
    assert validate(tmp_path) == []


def test_oversized_body_warns(tmp_path):
    write_skill(tmp_path, "adk-good", body="# Skill\n\n" + ("word " * 6000))
    assert "l2-budget" in codes(validate(tmp_path), "warn")


def test_harness_only_field_warns(tmp_path):
    write_skill(tmp_path, "adk-good", extra_frontmatter="disable-model-invocation: true")
    assert "harness-only-field" in codes(validate(tmp_path), "warn")


def test_missing_frontmatter_fails(tmp_path):
    skill = write_skill(tmp_path, "adk-good")
    (skill / "SKILL.md").write_text("# No frontmatter\n")
    assert "frontmatter-missing" in codes(validate(tmp_path), "error")


def test_invalid_yaml_fails(tmp_path):
    skill = write_skill(tmp_path, "adk-good")
    (skill / "SKILL.md").write_text("---\nname: [unclosed\n---\n\nBody\n")
    assert "frontmatter-invalid" in codes(validate(tmp_path), "error")


def test_directory_without_skill_md_fails(tmp_path):
    (tmp_path / "adk-empty").mkdir()
    assert "missing-skill-md" in codes(validate(tmp_path), "error")


def test_empty_root_fails(tmp_path):
    assert "no-skills" in codes(validate(tmp_path), "error")


def test_main_fails_closed_on_errors(tmp_path, capsys):
    write_skill(tmp_path, "adk-good", compatibility=None)
    assert validate_skills.main([str(tmp_path)]) == 1


def test_main_passes_with_warnings_by_default(tmp_path):
    write_skill(tmp_path, "adk-good", description="Builds agents when asked.")
    assert validate_skills.main([str(tmp_path)]) == 0


def test_main_strict_promotes_warnings(tmp_path):
    write_skill(tmp_path, "adk-good", description="Builds agents when asked.")
    assert validate_skills.main([str(tmp_path), "--strict"]) == 1


def test_main_missing_path_is_usage_error(tmp_path):
    assert validate_skills.main([str(tmp_path / "absent")]) == 2
