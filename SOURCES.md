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

## Gemini model catalog

| What | Source | Retrieved |
|---|---|---|
| Model IDs, capabilities, context/output limits | [Gemini API models](https://ai.google.dev/gemini-api/docs/models) | 2026-10-19 (page updated 2026-10-13) |
| Shutdown dates, replacements, redirects | [Gemini API deprecations](https://ai.google.dev/gemini-api/docs/deprecations) | 2026-10-19 (page updated 2026-10-12) |
| Gemini 3.8 Live contract (limits, capabilities, migration) | [Gemini 3.8 Live model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live) | 2026-10-19 (page updated 2026-09-15) |
| Machine-readable snapshot | `skills/adk-agent-architecture/references/model-cache.json` | regenerated 2026-10-19 by `fetch_models.py` |

The catalog is refreshed, not remembered: `fetch_models.py` parses the model
cards and endpoint tables on the models page and the per-model tables on the
deprecations page. `--check-only` fails when a model is added, removed, or
changes status.

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

## 2026-10-19 correctness sweep

The library's code samples were re-checked against the pinned source and a live
`google-adk[a2a,mcp]==2.12.0` install. The check was mechanical (every
`google.adk.*` import resolved against the tag) plus a construct-and-import
smoke test for each documented class.

Verified in this sweep:

| Claim | Verified against |
|---|---|
| `RunConfig` and `StreamingMode` live in `google.adk.agents.run_config` | `agents/run_config.py`; importing from `google.adk.runners` raises `AttributeError` |
| `EventsCompactionConfig` is in `google.adk.apps.app`, not the `google.adk.apps` package export | `apps/_configs.py`, `apps/__init__.py` |
| `ContextCacheConfig` minimums and defaults | `agents/context_cache_config.py` |
| Compaction requires one complete trigger pair | `EventsCompactionConfig._validate_trigger_params` |
| `RunConfig.max_llm_calls` defaults to 500, `ADK_MAX_LLM_CALLS` overrides it | `agents/run_config.py` |
| `ToolThreadPoolConfig.max_workers` defaults to 4 | `agents/run_config.py` |
| `HttpRetryOptions` defaults (5 attempts, 1.0 s initial, 60 s max, 6 status codes) | `google.genai.types` |
| `InMemoryRunner` / `Runner` signatures and the sync `run` proxy | `runners.py` |
| `BaseSessionService` has `append_event`; there is no `update_session` / `update_session_state` | `sessions/base_session_service.py` |
| Firestore and Redis session services live under `google.adk.integrations.*` | `integrations/firestore`, `integrations/redis` |
| `SqliteSessionService` is not re-exported from `google.adk.sessions` | `sessions/__init__.py` |
| `RemoteA2aAgent` spelling, URL/path `agent_card`, experimental status | `a2a/agent/_remote_a2a_agent.py` |
| A2A server is built by `to_a2a`, not `A2AServer` | `a2a/utils/agent_to_a2a.py` |
| `AgentCard` fields come from `a2a.types`; the card is served at `/.well-known/agent-card.json` | installed `a2a` package |
| `McpToolset`, `StdioConnectionParams`, `SseConnectionParams` | `tools/mcp_tool/` |
| `CalendarToolset`, not `calendar_tool_set` | `tools/google_api_tool/google_api_toolsets.py` |
| `maybe_set_otel_providers` is the telemetry entry point; `setup_telemetry` does not exist | `telemetry/setup.py` |
| Native eval: `EvalSet` / `EvalCase` / `EvalConfig`, `AgentEvaluator.evaluate`, `PrebuiltMetrics` | `evaluation/` |
| Model Armor lives in `google.adk.integrations.model_armor` and needs the `gcp` extra | `integrations/model_armor/_plugin.py` |
| `SequentialAgent`, `ParallelAgent`, `LoopAgent` emit `DeprecationWarning` in 2.12 | live warning capture on construction |
| `LoopAgent` has `max_iterations` only; termination is `exit_loop` | `agents/loop_agent.py`, `tools/exit_loop` |
| `adk api_server` / `adk web` take the agents directory positionally; there is no `--app-dir` | `adk api_server --help` |
| `adk deploy` subcommands are `cloud_run`, `agent_engine`, `gke`, `docker` | `adk deploy --help` |

When a source and a skill disagree, the source wins. Open an issue with the
tag, the file, and the line.
