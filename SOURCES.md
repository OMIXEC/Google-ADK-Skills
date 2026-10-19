# Sources

Every API claim in this library is traceable to one of these sources. Where a
skill states a signature, a limit, or a default, that value was read from the
source below — not inferred from a neighbouring API.

Retrieval date for every row: **2026-10-19**.

## Google ADK — Python

| What | Source | Pin |
|---|---|---|
| Skills subsystem, runtime API | [`google/adk-python`](https://github.com/google/adk-python) | tag `v2.12.0`, commit [`38381f65f2bee0f70a89f938ee64e51b34916fa7`](https://github.com/google/adk-python/commit/38381f65f2bee0f70a89f938ee64e51b34916fa7) |
| Contributor skills | `google/adk-python:.agents/skills` at the tag above | 11 skills |
| Skills contract | `src/google/adk/skills/models.py`, `_utils.py`, `skill_registry.py` | at the tag above |
| `SkillToolset` | `src/google/adk/tools/skill_toolset.py` | at the tag above |
| Package metadata | [PyPI `google-adk` 2.12.0](https://pypi.org/project/google-adk/2.12.0/) | `requires_python >=3.11`, uploaded 2026-10-13 |
| Version floor | [PyPI `google-adk` 2.9.2](https://pypi.org/project/google-adk/2.9.2/) | `requires_python >=3.10`, uploaded 2026-09-18 |
| Intermediate versions | [2.10.0](https://pypi.org/project/google-adk/2.10.0/) (2026-09-25), [2.11.0](https://pypi.org/project/google-adk/2.11.0/) (2026-10-02) | `requires_python >=3.10` |
| 1.x line | [PyPI `google-adk`](https://pypi.org/project/google-adk/) | latest `1.39.1` |

## Google ADK — Go and TypeScript

The non-Python runtimes version independently. Do not assume they match the
Python number.

| What | Source | Pin |
|---|---|---|
| Go module | [`google.golang.org/adk`](https://pkg.go.dev/google.golang.org/adk) | `v1.9.0`, 2026-10-15, commit [`08beb7834b66b689e982d8b79d7c3d2969445913`](https://github.com/google/adk-go/commit/08beb7834b66b689e982d8b79d7c3d2969445913) |
| TypeScript package | [npm `@google/adk`](https://www.npmjs.com/package/@google/adk) | `2.3.0`, repo [`google/adk-js`](https://github.com/google/adk-js), tag `main-v2.3.0`, commit [`ad0540e65706bc6593798bcfce35298448747df7`](https://github.com/google/adk-js/commit/ad0540e65706bc6593798bcfce35298448747df7) |

## Skills packaging and install

| What | Source | Pin |
|---|---|---|
| Canonical installer | [`vercel-labs/skills`](https://github.com/vercel-labs/skills) | npm `skills` `1.7.2` |
| Skill directory discovery | `package/dist/cli.mjs`, `findSkillMdPaths` in `skills@1.7.2` | read directly; only root `SKILL.md`, one-level dirs at the root, and `PRIORITY_PREFIXES` (`skills/`, `.agents/skills/`, …) are discovered |
| Skill specification referenced by ADK | [`agentskills.io/specification`](https://agentskills.io/specification) | as cited in `skills/models.py` docstrings at `v2.12.0` |
| Claude Code plugin channel | [Plugins overview](https://code.claude.com/docs/en/plugins.md) and [plugin components](https://code.claude.com/docs/en/plugins/components) | tested on Claude Code `2.1.300` |

## Documentation sources used for prose

| Source | Use |
|---|---|
| Context7 `/google/adk-docs` | `adk-litellm` and `adk-agent-orchestration` load these first when available; bundled `references/` are the fallback |
| [`google/adk-python` docs tree](https://github.com/google/adk-python/tree/v2.12.0) | A2A, MCP, deployment, and session behaviour stated in skill references |
| [Google Cloud ADK docs](https://cloud.google.com/vertex-ai/docs/agent-builder) | Agent Engine and Cloud Run deployment shapes |

## How the claims were checked

1. **Signatures and limits** — read from the tagged source files above, never
   from a blog post or a model's memory.
2. **Package facts** — read from the PyPI JSON API, the npm registry, and
   `proxy.golang.org` on the retrieval date.
3. **Skill discovery** — verified by running `skills@1.7.2` against a throwaway
   repository containing both `skills/alpha` and `contributing/beta`; only
   `alpha` was found.
4. **Plugin channel** — verified end to end on Claude Code `2.1.300` with an
   isolated `CLAUDE_CONFIG_DIR`: marketplace add, install, and component
   inventory.
5. **Loader behaviour** — verified by loading every skill in this repo through
   `google.adk.skills.load_skills_from_dir` under `google-adk==2.12.0`.

When a source and a skill disagree, the source wins. Open an issue with the
tag, the file, and the line.
