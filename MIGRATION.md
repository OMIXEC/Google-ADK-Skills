# Migration & Restructure Record

Status: **current.** The bundle targets ADK **2.9.2 → 2.12.0** (`google-adk>=2.9.2,<3`) and tracks the **1.x line in parallel** (still shipping; latest 1.39.1, 2026-08-27).

Python floor: **3.10** for ADK 2.9.2–2.11.0, **3.11** for 2.12.0 (2.12.0 raised `requires_python`). Supported through 3.15.

## The SDK is never vendored

`google-adk` installs from PyPI. There is **no** local `adk-python/` folder, no `adk-python-v1/` helper tree, and no committed source mirror. Do not path-import the SDK — always import from the installed `google.adk.*` package.

Canonical sources for API confirmation:

- Context7 `/google/adk-docs`
- The installed `google.adk` package
- `google/adk-python` at the matching tag (sparse local checkout only, gitignored)

## What moved in this restructure

| Path | Before | Now |
|---|---|---|
| `docs/adk-course/` | 196 MB of committed PDFs and zips (84 files) | **Deleted.** Referenced by nothing; not in `package.json.files`. |
| `docs/adk-docs/` | Stale vendored fork of an unrelated repo | **Deleted.** |
| `adk-python-v1/` | Legacy helper tooling (`tools/`, `callbacks/`) kept alive by one CI test | **Deleted.** Not a runtime dependency. |
| `adk-runtime/` | `*.agent.yaml` "runtime configs" | **Retired.** Nothing loaded them; the format was vestigial. |
| `adk_bidi/` | Top-level demo package | **Relocated** to `examples/bidi_orchestrator/` and renamed so `python -m` works (hyphens are not valid identifiers). |
| `adk-runtime/agents/root_agent.yaml` | With the retired format | **Relocated** to `examples/bidi_orchestrator/root_agent.yaml` — it is the orchestrator config that pairs with that package, not an ADK agent definition. |

Reference repairs applied alongside the moves: `package.json.files`, `.agents/library.json`, `.github/workflows/adk-skills-ci.yml`, `install.sh`, `tests/test_skill_validation.py`, `README.md`, `CLAUDE.md`, `mcp_servers/CATALOG.md`, `UPCOMING.md`, `commands/adk-migrate-check.md`.

## Verified feature names (2.x)

Line numbers are from `google/adk-python@v2.12.0`.

| Assumed | Correct in 2.x | Location |
|---------|----------------|----------|
| `@edge` decorator | `Edge` **class** instances | `workflow/_graph.py` |
| `ctx.resume_data` | `ctx.resume_inputs` | `agents/context.py` |
| standalone `Task` class | `mode='task'` + `TaskRequest`/`TaskResult`/`FinishTaskTool` | `agents/llm_agent.py`, `agents/llm/task/` |
| `@node` decorator | `node()` | `workflow/_node.py` |
| `JoinNode` (fan-in) | `JoinNode` ✅ | `workflow/_join_node.py` |
| agent modes | `mode: Literal['chat','task','single_turn']` ✅ | `agents/llm_agent.py` |
| `request_input` HITL | `RequestInput` / `_request_input_tool` ✅ | `events/request_input.py` |
| `MCPToolset` | `McpToolset` | `tools/mcp_tool/` |
| `SkillsToolset` | `SkillToolset` | `tools/skill_toolset.py` |
| Python 3.11+ (repo claim) | 3.10 for 2.9.2–2.11.0; 3.11 for 2.12.0 | `pyproject.toml` |

Use current names (`McpToolset`, `JoinNode`, `Edge`, `node()`, `rerun_on_resume`) and avoid stale ones (`MCPToolset`, `ctx.resume_data`, `@edge`).

## 1.x → 2.x compatibility

- **Sessions/state are not schema-compatible.** 2.x session and memory services (`google.adk.sessions.*`, `google.adk.memory.*`) do not read v1-persisted state. Start fresh or migrate with `google.adk.sessions.migration`.
- **Embedding spaces are not compatible.** Moving to `gemini-embedding-2` requires re-embedding stored vectors.
- **Behavior changes to watch:** `AgentEvaluator.evaluate` / `evaluate_eval_set` now raise `ValueError` when no eval cases ran (2.10.0). Instruction templating leaves `${var}` and `\{var}` literal (2.10.0). Legacy live-audio modules under `google.adk.flows.llm_flows` emit `DeprecationWarning` on import — move to `google.adk.live` (2.10.0).

## Departures from upstream that were reconciled

The seven skills this repo mirrors from `google/adk-python:.agents/skills` are **forks, not copies** — every `SKILL.md` diverges. `adk-architecture` was reduced from 77 to 25 lines (14 refs to 3) and `adk-style` from 46 to 19, so local content had silently drifted from upstream. These are being ported to `contributing/` with deltas re-applied explicitly rather than overwritten.

## Simplification candidates (flagged, not changed)

Custom orchestration that now overlaps the native 2.x graph engine (`Workflow` + `node()`/`Edge`/`JoinNode`). Preserve behavior; consider migrating later:

- `examples/bidi_orchestrator/orchestration/router.py` — manual routing via `AgentTool` composition → native conditional `Edge` routing.
- `examples/bidi_orchestrator/orchestration/supervisor.py` — supervisor-as-`AgentTool` wrapping → coordinator node + task-mode sub-agents.
- `examples/bidi_orchestrator/orchestration/swarm.py` — swarm composition → fan-out nodes + `JoinNode` fan-in.
