# Changelog

Semantic versioning applies to the **skill library**, not to ADK. A rename or a
removal is a breaking change for anyone who routes on skill names or installs a
subset with `--skills`.

Format based on Keep a Changelog. Dates are UTC.

## Versioning policy

- **Major** — a skill is renamed or removed; a skill's contract changes in a
  way that invalidates existing installs or routing tables.
- **Minor** — a skill is added; a skill gains coverage without changing its
  trigger surface.
- **Patch** — content corrections, link fixes, description wording, and
  documentation that does not move a trigger.

The library's version is recorded in `.claude-plugin/plugin.json` and the
marketplace entry. It is deliberately independent of every ADK version.

---

## [1.0.0] — 2026-10-19

The restructure release. The taxonomy changed, so routing tables, subsets, and
cached installs must be updated.

### Added

- `adk-skills-authoring` — the ADK skills subsystem: `Skill`, `Frontmatter`,
  `Resources`, `Script`, the loader, `SkillRegistry`, and `SkillToolset` with
  eager/lazy discovery and the two lifecycle switches.
- `adk-graph-workflows`, `adk-agent-architecture`, and `adk-deploy-production`
  — the three-way split of the former 844K `adk-agentic-prod-workflows`.
- `adk-typescript-go-parity` — the only Go/TypeScript surface, carrying the
  templates and parity notes.
- `adk-agent-personas` — `adk-persona` merged with `adk-domain-expert`.
- `adk-agent-orchestration` — `adk-autonomous-agent` merged with
  `adk-langgraph`, keeping LangGraph's context7-first documentation discipline.
- `contributing/` — 8 contributor-only skills ported from
  `google/adk-python@v2.12.0`, with provenance headers. Not installed by
  default; opt in with `install.sh --with-contributing`.
- `scripts/validate_skills.py` — the repo-owned contract validator, with 36
  tests. CI runs it with `--strict` over `skills/`.
- `SOURCES.md`, `COMPATIBILITY.md`, and this changelog.
- `compatibility: google-adk>=2.9.2,<3` on every skill.

### Changed

- Every description now carries a positive trigger and a negative trigger that
  names the sibling skill owning the excluded case.
- `skills.sh.json`, the `CLAUDE.md` router table, the README table, the
  subagents, and the commands all follow the new taxonomy. Tests fail if any of
  those surfaces drifts from the filesystem.
- `adk-agent-builder`, `adk-architecture`, and `adk-debug` were reconciled onto
  the upstream `v2.12.0` base. `adk-debug`'s long symptom catalogue moved into
  `references/`.
- The Claude plugin is a supported install channel, not experimental.
- `adk-migration` now targets the 2.12.0 range instead of 2.3.
- Every skill is self-contained: no skill reads `../../docs/`.

### Removed

- `adk-agentic-prod-workflows` — superseded by the three split skills plus the
  parity skill.
- `adk-persona`, `adk-domain-expert`, `adk-autonomous-agent`, `adk-langgraph` —
  merged into `adk-agent-personas` and `adk-agent-orchestration`.
- `adk-git`, `adk-setup`, `adk-style`, `adk-sample-creator` from `skills/` —
  moved to `contributing/`.
- `bin/cli.js` and `package.json` — the npm wrapper was never published under
  either name, and its documented command returned 404.
- 77 broken relative links and 3 dead image references that predated the
  restructure.

### Fixed

- `README.md` no longer calls the installer "the skills.sh CLI" and no longer
  claims an unverified skills.sh listing effect.
- The 14 removed or renamed skills no longer appear in routing tables,
  subagents, or commands.

---

## [0.1.0] — 2026-10-14

Baseline release, commit `5275610`.

### Changed

- Purged 196 MB of vendored and generated material; repository working tree
  370 MB → 4.5 MB, `.git` 171 MB → 1.7 MB.
- Retired vestigial formats and aligned the library on ADK 2.9.2–2.12.0.
- Rewrote CI with the ADK version × Python matrix.

### Known issues at this tag

- CI red: it required `compatibility` on every skill and no skill had it.
- 13 skills read `../../docs/python-adk-2.md`, so they could not be installed
  standalone.
- `adk-agentic-prod-workflows` was 92 files and ~90% of all skill bytes.
- The skills subsystem had no coverage at all.
