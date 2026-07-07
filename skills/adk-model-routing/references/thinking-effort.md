# Thinking / Effort Levels (Gemini 3.x)

Gemini 3.x models are reasoning models. Control reasoning depth with the
`thinking_level` effort enum instead of the raw numeric `thinking_budget`.

## Effort tiers

| Level | When to use |
|-------|-------------|
| `minimal` | Response speed. Chat, quick factual answers, simple tool calls. |
| `low` | Code/agentic tasks needing lower latency and fewer steps; light analysis/writing. |
| `medium` **(default in 3.5)** | Best quality for most tasks. Recommended for complex code and agentic use cases. |
| `high` | Maximizes reasoning + tool use. Hard math, difficult code/agent tasks, extended thoughts. |

Default effort changed from `high` (Gemini 3 Flash Preview) to **`medium`** in
Gemini 3.5 Flash. Start at `medium`; use `low`/`minimal` for speed and cost,
`high` for the hardest problems.

## Per-model support

| Level | 3.5 Flash | 3.1 Pro | 3.1 Flash-Lite | 3 Flash |
|-------|-----------|---------|----------------|---------|
| `minimal` | ✓ | — | ✓ (default) | ✓ |
| `low` | ✓ | ✓ | ✓ | ✓ |
| `medium` | ✓ (default) | ✓ | ✓ | ✓ |
| `high` | ✓ (dynamic) | ✓ (default, dynamic) | ✓ (dynamic) | ✓ (default, dynamic) |

## Setting it in ADK 2.3

`types.ThinkingConfig` (from `google.genai`) carries `thinking_level`,
`thinking_budget`, and `include_thoughts`. Attach via a planner or the model config:

```python
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

agent = LlmAgent(
    model="gemini-3.5-flash",
    name="coder",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(thinking_level="medium"),
    ),
)
```

If both the planner and `generate_content_config` set thinking, the **planner's
config wins** (`adk-python-v2.3/src/google/adk/agents/llm_agent.py`). A
`ThinkingConfig` on a model that doesn't support thinking raises an error.

## Migration & best practices (all Gemini 3.x)

- **Replace `thinking_budget` → `thinking_level`.** Do not set both in one
  request → `400`. (`thinking_budget` still works for backward-compat but is not
  recommended.)
- **Remove `temperature`, `top_p`, `top_k`** — no longer recommended; defaults
  are tuned for 3.x reasoning. For determinism, use a system instruction with
  explicit rules instead.
- **Remove `candidate_count`** — not supported on Gemini 3.x.
- **Thought preservation** is automatic across turns. For stateless multi-turn
  function calling, keep thought signatures in `contents` (official SDKs handle this).
- **Reduce excess tool calls:** lower the thinking level first; if it persists,
  add a system instruction capping the tool-call budget.
- **Function-calling strict matching:** every `FunctionResponse` must include the
  call `id`, match the `name`, and return exactly one response per `FunctionCall`.

## Backend effort mapping (future plan)

Map operating mode + complexity → effort:

| Mode / complexity | thinking_level |
|-------------------|----------------|
| Ambient / passive monitor | `minimal` |
| On-demand assist, tool-calling, RAG | `low`–`medium` |
| Complex reasoning, planning | `high` |
| Safety-critical decisions | `high` (never below `medium`) |
