# Cost and Caching

Cost per turn = input tokens + output tokens + cache storage + summarizer calls.
The first two dominate. Reduce input tokens with caching and compaction; reduce
output tokens with a shorter contract.

## Context caching

ADK caches the **prefix** of a conversation across invocations. It is configured
on the `App`, which means it applies to every agent in that app.

```python
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps import App

app = App(
    name="support",
    root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        cache_intervals=10,   # invocations to reuse one cache
        ttl_seconds=1800,     # 30 minutes
        min_tokens=2048,      # gate on the previous prompt's token count
    ),
)
```

| Field | Default | Range | Meaning |
|---|---|---|---|
| `cache_intervals` | 10 | 1–100 | Invocations before the cache is refreshed |
| `ttl_seconds` | 1800 | > 0 | Cache lifetime |
| `min_tokens` | 0 | ≥ 0 | Minimum previous-prompt tokens before caching is attempted |

Hard facts:

- Caching begins on the **second turn at the earliest**. A single-turn request
  is never cached because there is no previous token count.
- The model minimum always applies: **2048 tokens for Gemini 2.5** and
  **4096 for Gemini 3**. A shorter prefix creates no cache.
- Storage is billed while the cache lives. A cache that is written but never
  reused costs more than no cache.

So: enable it for long, stable system prompts and tool schemas; leave it off
for short prompts and one-shot calls.

## Event compaction

Compaction summarizes old turns so the prompt stops growing. It is also set on
the `App`.

```python
from google.adk.apps.app import EventsCompactionConfig
from google.adk.apps import App

app = App(
    name="support",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=5,   # every 5 new user turns...
        overlap_size=1,          # ...keep 1 turn of overlap
    ),
)
```

Two triggers. Each is a **pair that must be set together**:

| Trigger | Pair | Use when |
|---|---|---|
| Sliding window | `compaction_interval` + `overlap_size` | Turn count is a good proxy for size |
| Token budget | `token_threshold` + `event_retention_size` | You want a hard ceiling |

At least one pair is required, or construction raises `ValueError`. If
`summarizer` is unset, ADK builds an `LlmEventSummarizer` from the root agent's
model — which means compaction is itself a model call. Compacting every turn
trades a cheap long prompt for an expensive summary chain. Compact when the
session is long, not on every turn.

## Token accounting

Every model event carries usage metadata. Sum it for the turn instead of
estimating:

```python
async def turn_usage(runner, session_id, user_id, message):
    prompt = output = 0
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message
    ):
        if event.usage_metadata:
            prompt += event.usage_metadata.prompt_token_count or 0
            output += event.usage_metadata.candidates_token_count or 0
    return {"input": prompt, "output": output}
```

| Number | Honest source |
|---|---|
| Input tokens per turn | Sum `prompt_token_count` over the turn's events |
| Output tokens per turn | Sum `candidates_token_count` |
| Cached tokens | `cached_content_token_count` when present |
| Price | The provider's current sheet; never hard-code it in a skill |

## Serving tier

`RunConfig.service_tier` selects the serving tier for models on the
interactions API. `ServiceTier.DEFERRED` queues calls for off-peak capacity and
is cheaper, but adds unbounded delay. It is appropriate for nightly batch
evaluation, not for interactive chat. `ServiceTier.PRIORITY` is the opposite
trade: latency over price. The generate_content path ignores the field.

## A repeatable measurement loop

1. Pin one representative conversation of 10+ turns.
2. Record input tokens, output tokens, and total latency per turn.
3. Change exactly one lever: cache, compaction, or prompt.
4. Re-record. Keep the change only if cost falls without p95 latency rising.
5. Re-run the eval set before shipping; a cheaper prompt that scores lower is
   not a win. Use the native eval path in `adk-deploy-production`.

## Common false economies

| Change | Hidden cost |
|---|---|
| Summarize every turn | One extra model call per turn; quality drift |
| Cache a 900-token prompt | Below the Gemini 3 minimum; cache never created |
| Trim tool descriptions aggressively | The model guesses arguments and retries |
| Drop history entirely | The agent re-asks questions the user already answered |
| Raise `max_llm_calls` | Turns a bug into a recurring bill |
