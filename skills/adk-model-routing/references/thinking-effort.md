# Thinking / Effort Levels

Gemini 3.x and 4 use `thinking_level`, an effort enum. `thinking_budget` is
retired.

## Tiers

| Level | Use |
|---|---|
| `minimal` | Speed only. Chat, extraction, simple calls. Accepted by 3.5 Flash-Lite; rejected by Argon and the 3.8 family. |
| `low` | Latency-sensitive agents, light analysis. |
| `medium` | Default for most work. |
| `high` | Hard math, difficult code, long-horizon agents, safety-critical decisions. |

## Per-model support

| Model | `minimal` | `low` | `medium` | `high` | Default |
|---|---|---|---|---|---|
| `gemini-4-argon` | — (400) | ✓ | ✓ | ✓ | `medium` |
| `gemini-3.8-flash` | — (400) | ✓ | ✓ | ✓ | `medium` |
| `gemini-3.6-flash` | — | ✓ | ✓ | ✓ | `medium` |
| `gemini-3.5-flash-lite` | ✓ | ✓ | ✓ | ✓ | `low` |
| `gemini-3.1-flash-lite` | ✓ | ✓ | ✓ | ✓ | `minimal` |
| `gemini-3.1-pro-preview` | — | ✓ | ✓ | ✓ | `high` |
| `gemini-3.8-live` | n/a | n/a | n/a | n/a | streaming |

Argon rejects `thinking_budget` outright with a 400. The 3.x family accepts it
for compatibility but the value is not the supported control surface.

## Setting it in ADK

```python
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

agent = LlmAgent(
    model="gemini-3.8-flash",
    name="coder",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(thinking_level="medium"),
    ),
)
```

If both the planner and `generate_content_config` set thinking, the planner
wins. Never set `thinking_level` and `thinking_budget` in one request; the API
returns 400 and a retry will fail the same way.

## Sampling parameters

`temperature`, `top_p`, and `top_k` are ignored by Gemini 3.x and 4. Send them
and nothing changes; rely on them and behavior drifts for reasons you cannot
see. For determinism, put explicit rules in the system instruction.
`candidate_count` is unsupported.

## Function calling

- Echo `id` and `name` on every `FunctionResponse`; one response per
  `FunctionCall`.
- Keep thought signatures in `contents` for stateless multi-turn calls. SDKs
  handle this when history is passed through unchanged.
- The last message must not have `role="model"`.

## Effort mapping

| Mode / complexity | thinking_level |
|---|---|
| Ambient monitor, extraction | `minimal` (where supported) |
| On-demand assist, RAG, tools | `low`–`medium` |
| Complex planning and code | `high` |
| Safety-critical | `high`, never below `medium` |
