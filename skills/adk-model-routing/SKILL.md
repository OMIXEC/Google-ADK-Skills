---
name: adk-model-routing
description: >-
  ADK model routing, thinking/effort levels, and fallback methodology for
  production backends. Covers the current Gemini 3.x model catalog
  (gemini-3.5-flash, gemini-3.1-flash-lite, gemini-3.1-pro-preview,
  gemini-3.1-flash-live-preview, gemini-embedding-2), thinking_level effort
  tiers (minimal/low/medium/high), deprecation of thinking_budget and sampling
  params, and primary→fallback chains. Use when selecting a model, tuning
  thinking/effort, routing by task complexity/cost, or designing model fallback
  for an ADK agent.
---

# adk-model-routing — Model Selection, Thinking/Effort & Fallback

Route each agent to the cheapest capable model, set the right thinking/effort
level, and fall back safely when a model is unavailable. Grounded in the current
Gemini 3.x guidance and ADK 2.3. Verify signatures with Context7
`/google/adk-docs` first, then the local `adk-python-v2.3/` mirror when present;
never use `adk-python-v1/` for new ADK APIs.

## When to use

- Choosing a model ID for an agent (avoid deprecated/blocked models).
- Setting thinking/effort (`thinking_level`) by task complexity and cost.
- Designing primary→fallback chains and cross-provider fallback.
- Migrating off `thinking_budget` and legacy sampling params.

## Current model catalog (authoritative)

| Role | Model ID | Notes |
|------|----------|-------|
| Balanced / agentic / coding (default) | `gemini-3.5-flash` | GA, 1M ctx, 65k out, thinking. Most intelligent Flash. |
| Low-cost / high-volume | `gemini-3.1-flash-lite` | Stable, latency/cost-optimized. |
| Complex reasoning / research | `gemini-3.1-pro-preview` | Replaces `gemini-3-pro-preview`. |
| Live / bidi audio+video | `gemini-3.1-flash-live-preview` | Gemini Live API (`bidiGenerateContent`). |
| Embeddings (multimodal) | `gemini-embedding-2` | Text, image, video, audio → unified embeddings. |

**Deprecated / blocked — NEVER use:** `gemini-2.0-*`, `gemini-1.5-*`,
`gemini-1.0-*`, `gemini-pro`, `gemini-3-pro-preview`, `text-embedding-004`,
`embedding-001`. Reject these at agent-build time (see `references/fallback.md`).

Full catalog, replacements, and shutdown dates: `references/model-catalog.md`.

## Routing by task complexity

| Complexity | Model | thinking_level |
|-----------|-------|----------------|
| Low (triage, formatting, classification, chat) | `gemini-3.1-flash-lite` | `minimal` / `low` |
| Medium (RAG, tool-calling, multi-step, content) | `gemini-3.5-flash` | `medium` (default) |
| High (architecture, hard reasoning, difficult code/agent) | `gemini-3.1-pro-preview` | `high` |
| Live voice/video | `gemini-3.1-flash-live-preview` | n/a (streaming) |

## Thinking / effort levels

Gemini 3.x replaces raw `thinking_budget` with the `thinking_level` effort enum:
`minimal`, `low`, `medium` (**default in 3.5**, changed from `high`), `high`.
Full table, per-model support, and migration: `references/thinking-effort.md`.

ADK 2.3 wiring (verified against Context7 and the local source mirror when present):

```python
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

# Preferred: a planner (planner config wins if both planner and
# generate_content_config set thinking — llm_agent.py).
agent = LlmAgent(
    model="gemini-3.5-flash",
    name="researcher",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(thinking_level="high"),  # minimal|low|medium|high
    ),
)

# Alternative: inline on the model config.
agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="triage",
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="minimal"),
    ),
)
```

- Do **not** set both `thinking_level` and `thinking_budget` in one request → 400 error.
- Remove `temperature`, `top_p`, `top_k`, `candidate_count` on Gemini 3.x — no longer recommended; the defaults are tuned for its reasoning.
- Thought preservation is automatic across turns; for stateless multi-turn function calling, keep thought signatures in history (SDKs handle this).

## Fallback methodology

Every production route needs a primary and a fallback path. See
`references/fallback.md` for the full pattern:

1. **Validate at build time** — reject blocked/deprecated model IDs before the agent starts.
2. **Same-provider tier fallback** — on quota/`429`/unavailable, degrade to the next Gemini tier.
3. **Cross-provider fallback** — route to another provider via LiteLLM (see the `adk-litellm` skill).
4. **Resilience** — retry with backoff, circuit breaker, timeout; emit `ok | degraded | error` with `confidence`, `correlation_id`, `latency_ms`.
5. **Safety never degrades silently** — surface degradation; never drop a safety-critical response without signalling.

## Backend integration (future plan)

For platform backends adopting this (e.g. a `select_model` router):

- Map task complexity + operating mode → `(model_id, thinking_level)`. Ambient/passive monitors bias to `minimal`/`low`; on-demand assist to `medium`; safety/complex reasoning to `high`.
- Replace any `thinking_budget` usage with `thinking_level`; strip legacy sampling params.
- Encode the primary→fallback chain per capability tier, with a circuit breaker per model, so a single model outage degrades gracefully instead of failing the request.
- Keep model IDs in one config source; validate against the blocklist on load.

## Reference loading

| File | When |
|------|------|
| `references/model-catalog.md` | Model IDs, replacements, shutdown dates, embeddings |
| `references/thinking-effort.md` | `thinking_level` tiers, per-model support, `thinking_budget`/sampling migration |
| `references/fallback.md` | Build-time validation, tier + provider fallback, resilience contract |
