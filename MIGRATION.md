# Migration — ADK v1 → v2.3

Status: **complete.** The bundle targets ADK **2.3.0 GA**. Runtime dependency is `google-adk>=2.3.0,<3` (root `requirements.txt`), Python **3.10+**.

## What moved

The single vendored `adk-python/` folder was split:

| Folder | Contents | Status |
|--------|----------|--------|
| `adk-python-v2.3/` | ADK 2.3.0 GA full source (`src/google/adk`, `pyproject.toml`) | **Source of truth.** Reference all API signatures here. |
| `adk-python-v1/` | Repo helper tooling only (`tools/model_tools.py`, `tools/scaffold_tools.py`, `callbacks/`) + helper `requirements.txt` | **Reference-only.** Kept indefinitely for migration diffing and the legacy helper-import regression test. Not on any runtime import path for new code. Never copy patterns from it. |

Path references were re-pointed off the deleted bare `adk-python/`:

- `CLAUDE.md` — helper prose → `adk-python-v1/`; added "Vendored SDK — Source of Truth" + "v2.3 Core Concepts" sections pointing API references at `adk-python-v2.3/`.
- `install.sh` — helper `requirements.txt` install → `adk-python-v1/requirements.txt`.
- `.github/workflows/adk-skills-ci.yml` — helper install + `sys.path.insert` + `from tools.model_tools` regression test → `adk-python-v1/`.
- `package.json` — `files` array `"adk-python"` → `"adk-python-v1"` + `"adk-python-v2.3"`.
- `README.md` — added migration-status line; corrected runtime-helper Python requirement to 3.10+.

## Verified v2.3 feature names (corrections vs. common assumptions)

Confirmed against `adk-python-v2.3/src/google/adk/`:

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

The skills already used the correct names (`ctx.resume_inputs`, `JoinNode`, `Edge`, `node()`, `rerun_on_resume`); no skill code required correction. Only doc/version drift and dangling paths were fixed.

## Code migration status

- `adk_bidi/`, `agents/`, `adk-runtime/`, and `skills/**/references` already import exclusively from `google.adk.*` — no v1 API surface remained. Streaming symbols verified present in 2.3: `LiveRequestQueue` (`agents/live_request_queue.py`), `RunConfig`/`StreamingMode` (`agents/run_config.py`), `runner.run_live` (`runners.py`). Accessibility/streaming product behavior unchanged — only the vendored-path plumbing moved.
- **Session/state schema:** v2.3 session/memory services (`google.adk.sessions.*`, `google.adk.memory.*`) are not schema-compatible with v1-persisted state. Do not reuse old persisted sessions.

## Simplification candidates (flagged, not changed)

Custom orchestration that now overlaps the native 2.3 graph engine (`Workflow` + `node()`/`Edge`/`JoinNode`). Preserve behavior; consider migrating later:

- `adk_bidi/orchestration/router.py` — manual routing via `AgentTool` composition → native conditional `Edge` routing.
- `adk_bidi/orchestration/supervisor.py` — supervisor-as-`AgentTool` wrapping → coordinator node + task-mode sub-agents.
- `adk_bidi/orchestration/swarm.py` — swarm composition → fan-out nodes + `JoinNode` fan-in.

## v1 folder disposition

`adk-python-v1/` is **kept indefinitely** as a reference/diff and to back the legacy helper regression test. It is not a runtime dependency and must not be deleted without explicit instruction.
