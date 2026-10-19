---
name: adk-performance-scaling
description: >-
  Makes an ADK agent faster and cheaper under load: latency decomposition, concurrent
  invocations, tool-thread and LLM-call limits, 429 and 5xx retry policy, context
  caching, event compaction, token budget, and provider capacity. Use when an agent is
  slow, times out, hits quota or rate limits under concurrency, or costs more per turn
  than expected. Don't use for cloud target selection or manifests (use adk-deployment),
  for the pre-deploy gate, CI/CD, or resilience patterns (use adk-deploy-production),
  for choosing between model tiers (use adk-model-routing), or for memory policy
  (use adk-memory).
compatibility: google-adk>=2.9.2,<3
---

# Performance and Scaling

Four levers, in the order they usually pay:

| Lever | Symptom it fixes | Where |
|---|---|---|
| Fewer tokens per turn | Slow first token, high cost, context-limit errors | `ContextCacheConfig`, `EventsCompactionConfig`, prompt diet |
| Right concurrency | Throughput plateaus, queueing, timeouts under load | async `run_async`, per-invocation sessions, thread pools |
| Correct retry policy | 429/5xx spikes, duplicated work, long tails | `HttpRetryOptions`, idempotent tools |
| Provider capacity | Saturation at the instance, not the agent | Cloud Run / GKE / Agent Engine sizing |

Measure before changing any of them. The three numbers that matter are
**time to first token**, **tokens per turn**, and **p95 end-to-end latency**.
ADK publishes the first two as OpenTelemetry metrics
(`gen_ai.client.token.usage`, `gen_ai.invoke_agent.duration`); see
`references/latency-budget.md`.

## Start here: which lever

| Observation | Read |
|---|---|
| One turn is slow but the agent is idle | `references/latency-budget.md` |
| Slow only when many users arrive at once | `references/concurrency-and-quota.md` |
| Cost per turn grows with conversation length | `references/cost-and-caching.md` |
| Fast locally, slow or 429-heavy in production | `references/deployment-sizing.md` |

## The three hard limits

These are the only per-run caps ADK enforces. Everything else is provider-side.

| Limit | Default | Where | Notes |
|---|---|---|---|
| LLM calls per invocation | **500** | `RunConfig.max_llm_calls` | Override with `ADK_MAX_LLM_CALLS` |
| Sync tool threads | **4** | `RunConfig.tool_thread_pool_config` | `ToolThreadPoolConfig(max_workers=N)`; outside live mode only |
| Active skills (BOUNDED mode) | **5** | `SkillLifecycleConfig.max_active_skills` | Separate subsystem; see `adk-skills-authoring` |

Raising `max_llm_calls` without a stop condition turns a runaway loop into a
bigger bill. Pair it with an explicit exit in the instruction or a loop
counter in state.

## Concurrency in one paragraph

`Runner.run_async` is an async generator over a **single session**. Concurrency
comes from running many invocations, each on its own session, against one
runner and one async `SessionService`. Do not share a session across concurrent
tasks: events interleave and state writes race. For fan-out inside one turn,
use `ParallelAgent` or `Agent(parallel_worker=True)` and let ADK join the
results. `references/concurrency-and-quota.md` has the working pattern and the
quota math.

## Token diet

In order of effect:

1. **Enable context caching** when the prompt has a stable prefix of at least
   2048 tokens (Gemini 2.5) or 4096 tokens (Gemini 3). Caching starts on the
   second turn, not the first.
2. **Compact events** once a session exceeds a few dozen turns. Compaction
   replaces old turns with a summary; the raw turns stay addressable.
3. **Drop what the model never reads.** Retrieved documents, tool schemas, and
   history that no node references are pure cost.
4. **Move stable instructions into the cached prefix**, not into per-turn
   user content.

`references/cost-and-caching.md` has the config, the pairing rules, and the
measurement loop.

## Anti-patterns

| Pattern | Why it hurts |
|---|---|
| `asyncio.gather` over one session | Interleaved events, lost state writes |
| Retrying a non-idempotent tool on 429 | Duplicate side effects |
| Raising `max_llm_calls` to "fix" truncation | Hides the loop; multiplies cost |
| Caching a prompt under the model minimum | No cache is created; you pay the overhead |
| Compacting every turn | Summaries of summaries; quality collapses |
| Sizing the instance before measuring tokens per turn | You scale the expensive part |

## References

| File | Load when |
|---|---|
| `references/latency-budget.md` | Decomposing one slow turn and setting targets |
| `references/concurrency-and-quota.md` | Running many invocations, thread pools, 429 handling |
| `references/cost-and-caching.md` | Context cache, compaction, token accounting |
| `references/deployment-sizing.md` | Choosing and tuning the runtime that hosts the runner |
| `references/adk-2x-baseline.md` | Version floor, imports, model IDs |
