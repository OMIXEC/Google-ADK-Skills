# Latency Budget

Decompose a slow turn before changing anything. One ADK turn has four
measurable segments.

| Segment | What it contains | Typical lever |
|---|---|---|
| Queue | Time waiting for a worker, model quota, or a tool slot | Concurrency, capacity |
| Prefill | Prompt tokens processed before the first output token | Shorter prompt, caching |
| Decode | Output tokens generated | Output cap, shorter instruction |
| Tool time | Function calls, MCP round trips, retrieval | Parallel fan-out, timeouts |

## Measure with ADK's own telemetry

ADK instruments itself. The two metrics that separate prefill from decode are:

- `gen_ai.invoke_agent.duration` — wall clock per agent invocation, in seconds
- `gen_ai.client.token.usage` — input and output tokens per model call,
  labelled `gen_ai.token.type` = `input` | `output`

```python
from google.adk.telemetry.setup import maybe_set_otel_providers

maybe_set_otel_providers()  # reads OTEL_EXPORTER_OTLP_ENDPOINT
```

Derive the numbers you actually need:

| Number | How |
|---|---|
| Tokens per turn | Sum `gen_ai.client.token.usage` for one invocation |
| Output tokens per second | `output tokens / (invoke_agent.duration - prefill proxy)` |
| Cost per turn | tokens × the current price sheet; never hard-code a price in the skill |
| p95 latency | histogram quantile over `gen_ai.invoke_agent.duration` |

Set `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` only in a
non-production environment. It copies prompts and responses into spans.

## Local timing harness

When you do not have a tracing backend, time the segments directly:

```python
import time

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types


@pytest.mark.asyncio
async def test_turn_latency(agent):
    runner = InMemoryRunner(agent=agent, app_name="perf")
    session = await runner.session_service.create_session(
        app_name="perf", user_id="perf"
    )
    message = types.Content(role="user", parts=[types.Part(text="Standard request")])

    start = time.monotonic()
    first_text = None
    output = ""
    async for event in runner.run_async(
        user_id="perf", session_id=session.id, new_message=message
    ):
        if event.content and event.content.parts:
            text = "".join(p.text for p in event.content.parts if p.text)
            if text and first_text is None:
                first_text = time.monotonic() - start
            output += text

    total = time.monotonic() - start
    print(f"first text {first_text:.2f}s  total {total:.2f}s  chars {len(output)}")
```

`first text` approximates time to first token plus queue. `total - first_text`
approximates decode. If `first text` dominates, shrink the prompt or cache it.
If the gap dominates, cap output length or move work into parallel tools.

## Targets

Set targets from the product, not from the model:

| Interaction | Target | If missed |
|---|---|---|
| Interactive chat, first token | < 2 s | Cache the prefix, shorten instructions |
| Interactive chat, full turn | < 10 s | Cap output, split into nodes |
| Background job | minutes are acceptable | Prefer `ServiceTier.DEFERRED` |
| Voice / live | < 1 s to first audio | See `adk-bidi-live`; latency is a different pipeline |

## Output caps

Two independent caps, both cheap:

- `generate_content_config=types.GenerateContentConfig(max_output_tokens=N)` on
  the agent bounds decode time.
- A stop condition in the instruction ("answer in at most N bullets") does the
  same thing without a hard truncation.

Truncation is not a latency fix: a cut-off answer usually triggers a retry,
which costs more than the tokens you saved.
