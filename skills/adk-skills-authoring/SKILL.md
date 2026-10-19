---
name: adk-skills-authoring
description: >-
  Authors ADK agent skills: the SKILL.md contract, folder layout, frontmatter limits,
  the loader, SkillRegistry, and SkillToolset with its discovery and lifecycle modes.
  Use when creating a skill, deciding what belongs in SKILL.md versus references, wiring
  skills into an agent, or debugging a skill that will not load. Don't use for Claude
  Code or other harness-specific skill packs, for general prompt writing (use
  adk-prompts), or for tool design outside the skills subsystem (use adk-tools).
compatibility: google-adk>=2.9.2,<3
---

# Authoring ADK Skills

A skill is a directory the agent can load on demand. Three levels:

| Level | What | When it loads |
|---|---|---|
| **L1** | `frontmatter` — `name`, `description` | Every turn, for discovery |
| **L2** | `instructions` — the `SKILL.md` body | When the model loads the skill |
| **L3** | `resources` — `references/`, `assets/`, `scripts/` | One file at a time, on request |

Everything below was checked against `google/adk-python@v2.12.0`
(SHA `38381f65f2bee0f70a89f938ee64e51b34916fa7`).

## Directory contract

```text
my-skill/
├── SKILL.md          # required, at the folder root
├── references/       # optional markdown loaded by name
├── assets/           # optional non-instruction files
└── scripts/          # optional executables
```

- The **folder name is the skill name**. `load_skill_from_dir` raises
  `ValueError` when `frontmatter.name` differs.
- Only those three subdirectory names are read. Anything else is silently
  ignored — not an error, but invisible to the agent.
- Files recurse: `references/guides/setup.md` is addressable as
  `references/guides/setup.md`.
- `SKILL.md` must open with YAML frontmatter delimited by `---`. Missing,
  unclosed, non-mapping, or invalid YAML all raise `ValueError`.

## Frontmatter

```yaml
---
name: my-skill
description: >-
  What it does, when to use it, and what it is not for. Name the sibling skill
  that owns the excluded case.
compatibility: google-adk>=2.9.2,<3
license: Apache-2.0          # optional
allowed-tools: read_file     # optional, experimental
metadata:                    # optional
  adk_inject_state: true
---
```

| Field | Rule |
|---|---|
| `name` | ≤64 chars, lowercase kebab-case `^[a-z0-9]+(-[a-z0-9]+)*$`. Snake_case only with the `SNAKE_CASE_SKILL_NAME` feature flag; never mix delimiters. |
| `description` | Non-empty, ≤1024 chars. This is the routing surface: say what it does, when to use it, and when **not** to. |
| `compatibility` | Optional, ≤500 chars. **Parsed and inert** — no runtime reader. It is documentation for humans. |
| `license` | Optional string. |
| `allowed-tools` | Optional, experimental. Space-delimited pre-approved tools. |
| `metadata` | Arbitrary keys. `adk_additional_tools` must be a list of strings; `adk_inject_state` must be a bool. |

Unknown frontmatter keys are allowed (`extra="allow"`), so a harness-specific
field will not fail the load — but ADK ignores it. Do not rely on one.

### `description` is the whole game

The model sees only L1 until it decides to load. Write the description as
positive triggers plus negative triggers with a destination:

```yaml
description: >-
  Designs ADK workflow graphs. Use when deciding how nodes connect or
  scaffolding a workflow. Don't use for agent internals (use
  adk-agent-architecture) or deployment (use adk-deploy-production).
```

A description without a negative trigger routes everything to one skill.

## Writing the body

- **State the job in the first two lines.** No persona theater.
- **Lead with decisions, not background.** Tables beat paragraphs for choice.
- **Keep the body under ~5k tokens.** Everything longer goes to a reference.
- **One question per reference file.** Name it after the question it answers
  (`failure-modes.md`, `deployment-matrix.md`), not after a section number.
- **Never link outside the skill root.** `../../docs/x.md` breaks the moment
  the skill is installed alone. Duplicate the slice into `references/`.
- **Show the command, not the description of the command.** Runnable snippets
  age better than prose.
- **No secrets, no absolute home paths, no `latest` model aliases.**

## Loading a skill

```python
from google.adk.skills import load_skill_from_dir, load_skills_from_dir, list_skills_in_dir

one = load_skill_from_dir("skills/my-skill")
everything = load_skills_from_dir("skills")
names = list_skills_in_dir("skills")   # Frontmatter only, no L2/L3
```

`load_skills_from_dir` skips subdirectories with no `SKILL.md` and fails the
whole call if any skill it does find is invalid. Async and GCS variants exist
under the same names with `_async` / `_gcs_dir` suffixes.

## Wiring it into an agent

```python
from google.adk import Agent
from google.adk.skills import load_skills_from_dir
from google.adk.tools.skill_toolset import SkillToolset

toolset = SkillToolset(skills=load_skills_from_dir("skills"))
root_agent = Agent(
    name="assistant",
    model="gemini-3.8-flash",
    instruction="Load a skill before answering a task it covers.",
    tools=[toolset],
)
```

The toolset exposes up to six tools, and which ones exist depends on the
configuration:

| Tool | Offered when |
|---|---|
| `list_skills` | `discovery_mode=LAZY` (default) |
| `load_skill` | Always |
| `load_skill_resource` | Always |
| `run_skill_script` | A `code_executor` or `environment` is configured |
| `search_skills` | A `registry` is configured |
| `unload_skill` | `ADK_ENABLE_SKILL_LIFECYCLE=1` |

`discovery_mode=EAGER` drops `list_skills` and injects the catalog into the
system instruction instead. Use it for a small, stable catalog; use `LAZY` for
a large or changing one.

## Two independent lifecycle switches

These are easy to conflate because both sound like "enable lifecycle":

| Switch | Default | Gates |
|---|---|---|
| `ADK_ENABLE_SKILL_LIFECYCLE=1` (feature flag, experimental) | **off** | Only `unload_skill` and instruction pruning. |
| `SkillLifecycleConfig.enabled` | **on** | `BOUNDED` / `EPHEMERAL` behaviour and eviction. |

A skill can be `EPHEMERAL` with the feature flag off; it just cannot be
unloaded explicitly. `SkillLifecycleMode`: `PERSISTENT` (default, never
counted), `BOUNDED` (counted, evicted oldest first), `EPHEMERAL` (expires at
the end of the turn that loaded it; ignored under `run_live`).

`max_active_skills` defaults to **5**, caps **BOUNDED only**, is per agent,
and raises `ValueError` below 1.

`references/skill-toolset.md` has the full constructor, registry interface,
resource error codes, and script-execution rules.

## Author checklist

1. Folder name equals `name`, kebab-case, ≤64.
2. Description has a positive trigger and a negative trigger that names a
   sibling.
3. Body is under ~5k tokens; detail is in `references/`.
4. No `../..` anywhere; every relative link resolves inside the skill.
5. `references/`, `assets/`, `scripts/` only — no extra top-level folders.
6. Scripts run: `python scripts/foo.py --help` succeeds before you ship it.
7. Load it once through `load_skill_from_dir` — a skill that has never been
   loaded has never been tested.
8. No secrets, no absolute paths, no retired model IDs.

## References

| File | Load when |
|---|---|
| `references/skill-toolset.md` | Configuring the toolset, lifecycle, registry, or script execution |
