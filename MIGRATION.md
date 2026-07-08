# Migration — ADK v1 → v2.3

Status: **complete.** The bundle targets ADK **2.3.0 GA**. Runtime dependency is `google-adk>=2.3.0,<3` (root `requirements.txt`), Python **3.10+**.

The full upstream `google/adk-python` repository is **not vendored** into this package. Keep a local `adk-python-v2.3/` checkout only as a gitignored source mirror when doing source-backed updates. The package should contain extracted skills, docs, commands, runtime configs, and the small legacy helper folder only.

## What moved

The old `adk-python/` helper folder was renamed:

| Folder | Contents | Status |
|--------|----------|--------|
| `adk-python-v1/` | Repo helper tooling only (`tools/model_tools.py`, `tools/scaffold_tools.py`, `callbacks/`) + helper `requirements.txt` | **Legacy helper compatibility only.** Kept for installer/runtime-helper compatibility and the legacy helper-import regression test. Not on any runtime import path for new ADK code. Never copy patterns from it. |
| `adk-python-v2.3/` | Optional local checkout of upstream ADK 2.3 source | **Ignored reference mirror.** Use for grep/source confirmation only when present. Do not commit or package it. |

Path references were re-pointed off the deleted bare `adk-python/`:

- `CLAUDE.md` — helper prose → `adk-python-v1/`; added Context7-first ADK 2.3 source policy and current core concepts.
- `install.sh` — helper `requirements.txt` install → `adk-python-v1/requirements.txt`.
- `.github/workflows/adk-skills-ci.yml` — helper install + `sys.path.insert` + `from tools.model_tools` regression test → `adk-python-v1/`.
- `package.json` — `files` array `"adk-python"` → `"adk-python-v1"` only; the full upstream SDK checkout stays out of package artifacts.
- `README.md` — added migration-status line; corrected runtime-helper Python requirement to 3.10+.

## Verified v2.3 feature names (corrections vs. common assumptions)

Confirmed through Context7 `/google/adk-docs` and the local `adk-python-v2.3/` mirror where present:

| Assumed | Correct in 2.3 | Location |
|---------|----------------|----------|
| `@edge` decorator | `Edge` **class** instances | `workflow/_graph.py:58` |
| `ctx.resume_data` | `ctx.resume_inputs` | `agents/context.py:328` |
| standalone `Task` class / "Task API" | `mode='task'` + `TaskRequest`/`TaskResult`/`FinishTaskTool` | `agents/llm_agent.py:344`, `agents/llm/task/` |
| `@node` decorator | `node()` ✅ | `workflow/_node.py:79` |
| `JoinNode` (fan-in) | `JoinNode` ✅ | `workflow/_join_node.py:41` |
| agent modes | `mode: Literal['chat','task','single_turn']` ✅ | `agents/llm_agent.py:344` |
| `request_input` HITL | `RequestInput` / `_request_input_tool` ✅ | `events/request_input.py`, `tools/_request_input_tool.py` |
| Python 3.11+ | Python **3.10+** | `pyproject.toml:15` |

The skills should use current names (`McpToolset`, `JoinNode`, `Edge`, `node()`, `rerun_on_resume`) and avoid stale names (`MCPToolset`, `ctx.resume_data`, `@edge`). Only relevant upstream ADK `.agents/skills` guidance should be copied into this repo; do not import the entire upstream SDK repository.

## Code migration status

- `adk_bidi/`, `agents/`, `adk-runtime/`, and `skills/**/references` already import exclusively from `google.adk.*` — no v1 API surface remained. Streaming symbols verified present in 2.3: `LiveRequestQueue` (`agents/live_request_queue.py`), `RunConfig`/`StreamingMode` (`agents/run_config.py`), `runner.run_live` (`runners.py`). Accessibility/streaming product behavior unchanged — only the vendored-path plumbing moved.
- **Session/state schema:** v2.3 session/memory services (`google.adk.sessions.*`, `google.adk.memory.*`) are not schema-compatible with v1-persisted state. Do not reuse old persisted sessions.

## Simplification candidates (flagged, not changed)

Custom orchestration that now overlaps the native 2.3 graph engine (`Workflow` + `node()`/`Edge`/`JoinNode`). Preserve behavior; consider migrating later:

- `adk_bidi/orchestration/router.py` — manual routing via `AgentTool` composition → native conditional `Edge` routing.
- `adk_bidi/orchestration/supervisor.py` — supervisor-as-`AgentTool` wrapping → coordinator node + task-mode sub-agents.
- `adk_bidi/orchestration/swarm.py` — swarm composition → fan-out nodes + `JoinNode` fan-in.

## v1 folder disposition

`adk-python-v1/` is kept as legacy helper compatibility and to back the helper regression test. It is not a runtime dependency and must not be used as a source for new ADK examples.
