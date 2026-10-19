# ADK 2.x Baseline

Version and API facts this skill depends on. Checked against
`google/adk-python@v2.12.0` (SHA `38381f65f2bee0f70a89f938ee64e51b34916fa7`).

## Version baseline

- Target: `google-adk>=2.9.2,<3`; validated through **2.12.0** (2026-10-13).
- Python: **3.10** for 2.9.2–2.11.0; **3.11** for 2.12.0. Supported through 3.15.
- The **1.x line still ships in parallel** (1.39.1). 2.x is not a drop-in
  replacement for every 1.x project.
- The SDK is never vendored. Import from the installed `google.adk.*`.

## Core imports

```python
from google.adk import Agent
from google.adk.agents import RunConfig
from google.adk.agents.run_config import StreamingMode, ToolThreadPoolConfig
from google.adk.apps import App, ResumabilityConfig
from google.adk.apps.app import EventsCompactionConfig
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.genai import types
```

`StreamingMode` and `RunConfig` live in `google.adk.agents.run_config`; importing
them from `google.adk.runners` fails.

## Performance-relevant limits

| Limit | Default | Where |
|---|---|---|
| LLM calls per invocation | 500 | `RunConfig.max_llm_calls`, env `ADK_MAX_LLM_CALLS` |
| Sync tool worker threads | 4 | `RunConfig.tool_thread_pool_config` |
| Context cache intervals | 10 | `ContextCacheConfig.cache_intervals` (1–100) |
| Context cache TTL | 1800 s | `ContextCacheConfig.ttl_seconds` |
| Cache minimum prefix | 2048 (Gemini 2.5), 4096 (Gemini 3) | Model-side, always applied |
| Event compaction | no default | `EventsCompactionConfig` requires one trigger pair |

## Runner facts

- `Runner.run_async` is an async generator bound to one `session_id`.
- `InMemoryRunner.run` is the sync convenience wrapper; it still needs
  `user_id`, `session_id`, and a `types.Content` message.
- `InMemoryRunner(agent=...)` auto-creates an in-memory session service; create
  the session explicitly before the first turn.
- `Runner(agent=...)`, `Runner(node=...)`, and `Runner(app=...)` are mutually
  exclusive; `app` is the recommended form.

## Model IDs

Prefer current IDs: `gemini-3.8-flash` (default), `gemini-3.5-flash-lite`,
`gemini-3.1-pro-preview`, `gemini-4-argon` (frontier), and `gemini-3.8-live`
(live audio). `gemini-3.5-flash` redirects to 3.6 and `gemini-3.7-flash` to 3.8;
`gemini-3.8-flash` is the model itself.
