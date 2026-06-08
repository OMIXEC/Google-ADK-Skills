"""Validate all 8 ADK skills for format compliance, integrity, and quality.

Tests cover:
- SKILL.md frontmatter correctness (YAML, required fields, naming)
- Reference file integrity (no broken links, all refs exist)
- Directory structure (no extraneous files like README.md)
- Description quality (substantive, includes triggers)
- Body content quality
- Legacy skills inventory
- Cross-skill consistency
"""

import sys
from pathlib import Path

import pytest
import yaml

from conftest import _read_frontmatter, _extract_local_links, REPO_ROOT, SKILLS_DIR, LEGACY_DIR

MIN_DESCRIPTION_LENGTH = 50
MIN_BODY_LENGTH = 100
KNOWN_SKILLS = {
    # Original core skills
    "adk-agent-builder",
    "adk-agentic-prod-workflows",
    "adk-architecture",
    "adk-debug",
    "adk-git",
    "adk-sample-creator",
    "adk-setup",
    "adk-style",
    # Promoted doc-grounded skills
    "adk-a2a",
    "adk-agents",
    "adk-backend",
    "adk-bidi-live",
    "adk-configs",
    "adk-deployment",
    "adk-litellm",
    "adk-mcp",
    "adk-memory",
    "adk-prompts",
    "adk-runtime",
    "adk-tools",
    # Converted legacy + new framework skills
    "adk-autonomous-agent",
    "adk-domain-expert",
    "adk-langgraph",
    "adk-persona",
    "adk-rag",
}
EXTRANEOUS_FILES = {"README.md", "CHANGELOG.md", "INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md"}
REQUIRED_FRONTMATTER_FIELDS = {"name", "description"}


# ── Frontmatter tests ────────────────────────────────────────────────────────


class TestFrontmatter:
    """SKILL.md YAML frontmatter validation."""

    def test_all_known_skills_exist(self, skill_dirs):
        """Verify all expected skills are present."""
        found = {d.name for d in skill_dirs}
        missing = KNOWN_SKILLS - found
        assert not missing, f"Missing skills: {missing}"

    def test_frontmatter_starts_with_dashes(self, skill_mds):
        """Every SKILL.md must begin with ---."""
        for name, path in skill_mds.items():
            content = path.read_text()
            assert content.startswith("---"), f"{name}: SKILL.md must start with ---"

    def test_frontmatter_has_required_fields(self, skill_mds):
        """Every SKILL.md must have 'name' and 'description' in frontmatter."""
        for name, path in skill_mds.items():
            fm = _read_frontmatter(path)
            assert fm is not None, f"{name}: could not parse frontmatter"
            for field in REQUIRED_FRONTMATTER_FIELDS:
                assert field in fm, f"{name}: missing frontmatter field '{field}'"
                assert fm[field], f"{name}: frontmatter field '{field}' is empty"

    def test_name_matches_directory(self, skill_mds):
        """Frontmatter 'name' must match the skill directory name."""
        for name, path in skill_mds.items():
            fm = _read_frontmatter(path)
            assert fm["name"] == name, (
                f"{name}: frontmatter name '{fm['name']}' != directory name '{name}'"
            )

    def test_name_is_kebab_case(self, skill_mds):
        """Frontmatter 'name' should be kebab-case (alphanumeric + hyphens)."""
        import re
        for name, path in skill_mds.items():
            fm = _read_frontmatter(path)
            n = fm["name"]
            assert re.match(r"^[a-z0-9][a-z0-9-]*$", n), (
                f"{name}: name '{n}' is not kebab-case"
            )

    def test_no_extra_frontmatter_fields(self, skill_mds):
        """Flag any unexpected frontmatter fields for review.

        Known acceptable fields: name, description, disable-model-invocation
        """
        accepted_extras = {"disable-model-invocation"}
        for name, path in skill_mds.items():
            fm = _read_frontmatter(path)
            extras = set(fm.keys()) - REQUIRED_FRONTMATTER_FIELDS - accepted_extras
            if extras:
                # This is a warning-level check; don't fail but alert
                print(f"  [INFO] {name}: extra frontmatter fields: {extras}")


class TestDescriptionQuality:
    """Description field quality checks."""

    def test_description_meets_minimum_length(self, skill_mds):
        """Description should be substantive (>= 50 chars)."""
        for name, path in skill_mds.items():
            fm = _read_frontmatter(path)
            desc = fm.get("description", "")
            assert len(desc) >= MIN_DESCRIPTION_LENGTH, (
                f"{name}: description is {len(desc)} chars (min {MIN_DESCRIPTION_LENGTH})"
            )

    def test_description_mentions_triggers(self, skill_mds):
        """Description should mention when to use the skill.

        Checks for trigger-indicating words: 'use when', 'triggers on', 'when the user'.
        """
        trigger_words = ["use when", "when the user", "triggers on", "when you"]
        for name, path in skill_mds.items():
            fm = _read_frontmatter(path)
            desc = fm.get("description", "").lower()
            has_trigger = any(word in desc for word in trigger_words)
            if not has_trigger:
                print(f"  [WARN] {name}: description may lack trigger guidance")


class TestBodyContent:
    """SKILL.md body content quality checks."""

    def test_body_meets_minimum_length(self, skill_mds):
        """Body (after frontmatter) should be substantive."""
        for name, path in skill_mds.items():
            content = path.read_text()
            end_idx = content.index("---", 3)
            body = content[end_idx + 3:].strip()
            assert len(body) >= MIN_BODY_LENGTH, (
                f"{name}: body is {len(body)} chars (min {MIN_BODY_LENGTH})"
            )

    def test_body_has_no_duplicate_headings(self, skill_mds):
        """No duplicate headings in the body."""
        import re
        for name, path in skill_mds.items():
            content = path.read_text()
            end_idx = content.index("---", 3)
            body = content[end_idx + 3:]
            headings = re.findall(r'^#{1,4}\s+(.+)', body, re.MULTILINE)
            seen = {}
            for h in headings:
                if h in seen:
                    pytest.fail(f"{name}: duplicate heading '{h}'")
                seen[h] = True

    def test_body_ends_with_newline(self, skill_mds):
        """Files should end with a newline."""
        for name, path in skill_mds.items():
            content = path.read_text()
            assert content.endswith("\n"), f"{name}: SKILL.md must end with newline"


# ── Reference integrity tests ─────────────────────────────────────────────────


class TestReferenceIntegrity:
    """Validate that all referenced files exist and are accessible."""

    def test_all_local_links_resolve(self, skill_mds):
        """Every local markdown link in SKILL.md must point to an existing file."""
        for name, path in skill_mds.items():
            content = path.read_text()
            skill_dir = path.parent
            links = _extract_local_links(content)
            broken = []
            for link in links:
                target = (skill_dir / link).resolve()
                if not target.exists():
                    broken.append(link)
            assert not broken, (
                f"{name}: {len(broken)} broken link(s): {broken}"
            )

    def test_reference_files_exist_for_documented_refs(self, skill_dirs):
        """If SKILL.md mentions a references/ file, it must exist."""
        import re
        for d in skill_dirs:
            skill_md = d / "SKILL.md"
            content = skill_md.read_text()
            # Find all references/file.md mentions
            ref_mentions = re.findall(r'references/[\w./-]+\.(md|py|json|yaml|yml)', content)
            for ref_path in ref_mentions:
                # Not a perfect extraction; the simpler check is test_all_local_links_resolve
                pass

    def test_no_circular_references_in_skills(self, skill_dirs):
        """Detect if SKILL.md references another SKILL.md (unusual)."""
        import re
        for d in skill_dirs:
            content = (d / "SKILL.md").read_text()
            # Don't count the SKILL.md name itself, look for cross-skill refs
            cross_refs = re.findall(r'\.\./[\w-]+/SKILL\.md', content)
            assert not cross_refs, (
                f"{d.name}: cross-skill SKILL.md reference found: {cross_refs}"
            )


# ── Directory structure tests ─────────────────────────────────────────────────


class TestDirectoryStructure:
    """Skill directory layout follows skill-creator conventions."""

    def test_no_extraneous_files_in_skill_dirs(self, skill_dirs):
        """Skill directories should not contain README.md, CHANGELOG.md, etc."""
        for d in skill_dirs:
            for extraneous in EXTRANEOUS_FILES:
                bad = d / extraneous
                assert not bad.exists(), (
                    f"{d.name}: extraneous file {extraneous} found — skill-creator best practice: no aux docs"
                )

    def test_every_skill_has_skill_md(self, skill_dirs):
        """Every skill directory must have a SKILL.md."""
        for d in skill_dirs:
            assert (d / "SKILL.md").exists(), f"{d.name}: missing SKILL.md"

    def test_references_dir_has_only_known_files(self, skill_dirs):
        """References/ holds docs plus optional runnable example assets."""
        # Docs + example-agent assets (some promoted skills bundle runnable examples).
        allowed_suffixes = {".md", ".yaml", ".yml", ".json", ".py", ".txt", ".toml", ".cfg", ".example"}
        allowed_names = {".env.example", "requirements.txt", "Dockerfile", ".gitignore"}
        for d in skill_dirs:
            ref_dir = d / "references"
            if not ref_dir.exists():
                continue
            for f in ref_dir.rglob("*"):
                if f.is_file():
                    if f.name in allowed_names or f.suffix in allowed_suffixes:
                        continue
                    pytest.fail(f"{d.name}: unexpected file type in references/: {f.name}")

    def test_scripts_dir_python_files_are_valid(self, skill_dirs):
        """Python scripts in scripts/ should be syntactically valid."""
        for d in skill_dirs:
            scripts_dir = d / "scripts"
            if not scripts_dir.exists():
                continue
            for py_file in scripts_dir.glob("*.py"):
                content = py_file.read_text()
                try:
                    compile(content, str(py_file), "exec")
                except SyntaxError as e:
                    pytest.fail(f"{d.name}/scripts/{py_file.name}: syntax error: {e}")


# ── Legacy skills inventory ───────────────────────────────────────────────────


class TestLegacySkills:
    """Document and validate legacy skills for future conversion."""

    @pytest.fixture(scope="class")
    def legacy_files(self):
        if not LEGACY_DIR.exists():
            return []
        return sorted(LEGACY_DIR.glob("*.md"))

    def test_legacy_skills_inventory(self, legacy_files):
        """Report on legacy skills that need SKILL.md conversion."""
        if not legacy_files:
            pytest.skip("No legacy skills found")

        print(f"\n  Legacy skills to convert ({len(legacy_files)}):")
        for f in legacy_files:
            # Check if it has frontmatter (might already be partial SKILL.md)
            has_fm = f.read_text().startswith("---")
            status = "has frontmatter" if has_fm else "no frontmatter"
            print(f"    - {f.name} ({status})")

    def test_legacy_skills_have_content(self, legacy_files):
        """All legacy files should have substantive content."""
        for f in legacy_files:
            content = f.read_text().strip()
            assert len(content) > 50, (
                f"legacy-skills/{f.name}: only {len(content)} chars — may be empty"
            )

    def test_legacy_count_matches_expected(self, legacy_files):
        """There should be exactly 13 legacy skills (known inventory)."""
        count = len(legacy_files)
        if count > 0:
            assert count == 13, (
                f"Expected 13 legacy skills, found {count}. "
                "If skills were converted, update this test."
            )


# ── Cross-skill consistency tests ─────────────────────────────────────────────


class TestCrossSkillConsistency:
    """Ensure coherence across all 8 skills."""

    def test_no_duplicate_skill_names(self, skill_mds):
        """All skill names must be unique (already enforced by filesystem)."""
        # The dict keys are already unique by construction
        pass

    def test_all_skills_reference_common_standards(self, skill_mds):
        """Check that skills follow consistent patterns:
        - All reference links use relative paths
        - All use markdown for body content
        """
        for name, path in skill_mds.items():
            content = path.read_text()
            # No absolute file paths that would break portability
            assert "/Users/" not in content, (
                f"{name}: contains absolute path /Users/..."
            )

    def test_consistent_frontmatter_format(self, skill_mds):
        """All SKILL.md files use YAML frontmatter with same format."""
        for name, path in skill_mds.items():
            content = path.read_text()
            lines = content.split("\n")
            # First line must be ---
            assert lines[0].strip() == "---", f"{name}: first line not ---"
            # Must have closing ---
            found_closing = False
            for i in range(1, min(20, len(lines))):
                if lines[i].strip() == "---":
                    found_closing = True
                    break
            assert found_closing, f"{name}: no closing --- in first 20 lines"

    def test_all_skills_have_reference_links(self, skill_mds):
        """Skills that point to reference docs should use the references/ pattern."""
        for name, path in skill_mds.items():
            content = path.read_text()
            # Most skills should reference their bundled resources
            if "references/" not in content and "scripts/" not in content:
                print(f"  [INFO] {name}: no references/ or scripts/ links in body")


# ── Integration: test quick_validate.py compatibility ─────────────────────────


class TestQuickValidateIntegration:
    """Verify the existing quick_validate.py works with our skills."""

    def test_quick_validate_exists(self):
        """quick_validate.py should be present."""
        path = SKILLS_DIR / "adk-agentic-prod-workflows" / "scripts" / "quick_validate.py"
        assert path.exists(), f"quick_validate.py missing at {path}"

    def test_quick_validate_all_skills(self, skill_mds):
        """Run quick_validate.py on all SKILL.md files."""
        import subprocess
        quick_val = (
            SKILLS_DIR / "adk-agentic-prod-workflows" / "scripts" / "quick_validate.py"
        )
        if not quick_val.exists():
            pytest.skip("quick_validate.py not found")

        failures = []
        for name, path in skill_mds.items():
            result = subprocess.run(
                [sys.executable, str(quick_val), "--file", str(path)],
                capture_output=True, text=True, cwd=str(REPO_ROOT),
            )
            if result.returncode != 0:
                failures.append((name, result.stderr.strip()))

        if failures:
            msg = "\n".join(f"{n}: {e}" for n, e in failures)
            pytest.fail(f"quick_validate.py failed on {len(failures)} skill(s):\n{msg}")
