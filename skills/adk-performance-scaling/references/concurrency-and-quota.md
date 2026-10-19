# Concurrency and Quota

## The rule

One runner, many sessions, one task per session.

`Runner.run_async` is an async generator scoped to a `session_id`. It is not
re-entrant for the same session: two concurrent tasks would interleave events
and race on `session.state`. Concurrent **invocations** are fine because each
has its own session.

```python
import asyncio

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

session_service = DatabaseSessionService(db_url="postgresql+asyncpg://...")
runner = Runner(app=app, session_service=session_service)


async def one_turn(user_id: str, text: str) -> str:
    session = await session_service.create_session(
        app_name=app.name, user_id=user_id
    )
    message = types.Content(role="user", parts=[types.Part(text=text)])
    chunks: list[str] = []
    async for event in runner.run_async(
        user_id=user_id, session_id=session.id, new_message=message
    ):
        if event.content and event.content.parts:
            chunks.extend(p.text for p in event.content.parts if p.text)
    return "".join(chunks)


async def main(requests: list[tuple[str, str]]) -> list[str]:
    return await asyncio.gather(*(one_turn(u, t) for u, t in requests))
```

Bound the gather with a semaphore sized to your model quota, not to your CPU:

```python
sem = asyncio.Semaphore(8)

async def bounded(user_id: str, text: str) -> str:
    async with sem:
        return await one_turn(user_id, text)
```

## Per-run caps

| Cap | Default | Set with | Applies to |
|---|---|---|---|
| LLM calls per invocation | 500 | `RunConfig(max_llm_calls=N)` or `ADK_MAX_LLM_CALLS` | One `run_async` |
| Sync tool worker threads | 4 | `RunConfig(tool_thread_pool_config=ToolThreadPoolConfig(max_workers=N))` | Sync function tools, outside live mode |
| Agent-loop iterations | model-driven | Instruction or state counter | Agents that loop |

```python
from google.adk.agents import RunConfig
from google.adk.agents.run_config import ToolThreadPoolConfig

run_config = RunConfig(
    max_llm_calls=40,
    tool_thread_pool_config=ToolThreadPoolConfig(max_workers=8),
)
```

A high `max_llm_calls` is a safety valve, not a performance setting. If a run
needs more than a few dozen calls, the graph is probably looping.

## Fan-out inside one turn

Two different mechanisms:

| Need | Use | Behaviour |
|---|---|---|
| Same step, N independent items | `Agent(parallel_worker=True)` | ADK runs a worker per item and joins the outputs |
| Different steps that can overlap | `ParallelAgent(sub_agents=[...])` | Fixed parallel branches, then join |

```python
from google.adk.agents import Agent, ParallelAgent

researcher = Agent(name="researcher", model="gemini-3.8-flash", instruction="...")
coder = Agent(name="coder", model="gemini-3.8-flash", instruction="...")

fan_out = ParallelAgent(name="fan_out", sub_agents=[researcher, coder])
```

Parallel branches multiply token spend. Cap each branch's output and give the
join step a clear contract.

## Quota and rate limits

Three failure shapes, three responses:

| Response | Meaning | Action |
|---|---|---|
| `429` | Per-minute token or request quota | Retry with exponential backoff and jitter |
| `503` | Model temporarily overloaded | Retry; consider a fallback model |
| `RESOURCE_EXHAUSTED` on a project limit | Hard quota | Stop retrying; raise the quota or reduce concurrency |

ADK passes `http_options` through to the GenAI client for each run:

```python
from google.adk.agents import RunConfig
from google.genai import types

run_config = RunConfig(
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=5,
            initial_delay=1.0,
            max_delay=60.0,
            exp_base=2,
            jitter=1,
            http_status_codes=(408, 429, 500, 502, 503, 504),
        )
    )
)
```

Defaults are `attempts=5`, `initial_delay=1.0`, `max_delay=60.0`,
`exp_base=2`, `jitter=1`, and the six status codes above. Retries are only
safe when the work is idempotent: a retried `create_order` creates two orders
unless the tool takes an idempotency key.

## Quota math

Do this arithmetic before load testing:

```
required_tokens_per_minute
    = requests_per_minute
    × average_tokens_in
    × average_turns_per_request
```

Compare with the project's per-minute token quota for the model, not with
requests-per-minute. A request that fans out to four agents consumes four
model calls against the same quota.

## Where concurrency actually blocks

| Blocking point | Symptom | Fix |
|---|---|---|
| Sync tool inside an async agent | One slow tool stalls other tasks | Make the tool `async def`, or raise the tool thread pool |
| `DatabaseSessionService` connection pool | Spikes of pool timeouts | Size `pool_size` to concurrency |
| Single Cloud Run instance | CPU throttling, long queue | Raise concurrency or instances; see `deployment-sizing.md` |
| Per-session lock by the application | Only one turn per user at a time | Expected; queue at the edge |
