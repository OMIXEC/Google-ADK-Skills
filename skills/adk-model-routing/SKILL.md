---
name: adk-model-routing
description: >-
  Selects and routes models for ADK agents: the current Gemini catalog
  (gemini-4-argon, gemini-3.8-flash, gemini-3.8-live,
  gemini-3.8-live-extended-thinking, gemini-3.1-pro-preview,
  gemini-embedding-2), thinking_level effort tiers, retired sampling
  parameters, redirecting model IDs, and primary-to-fallback chains. Use when
  choosing a model, tuning effort, routing by complexity or cost, or rejecting a
  retired ID. Don't use for crossing to non-Google providers (use adk-litellm),
  for prompt wording (use adk-prompts), or for deployment-time quotas (use
  adk-deploy-production).
compatibility: google-adk>=2.9.2,<3
---

# Model Routing

Route each agent to the cheapest capable model, set the right thinking level,
and fall back safely. Catalog checked against the Gemini API models and
deprecations pages on **2026-10-19**.

## Current catalog

| Tier | Model ID | Status | Notes |
|---|---|---|---|
| Frontier | `gemini-4-argon` | Stable (GA 2026-10-13) | 1M tokens shared across input, thinking, and output; long decode; paid tier only |
| Balanced (default) | `gemini-3.8-flash` | Stable (2026-09-02) | 1M ctx, 65k out; long-horizon coding and agents |
| Previous Flash | `gemini-3.6-flash` | Stable | Use when 3.8 is unavailable or pinned |
| Cost-optimized | `gemini-3.5-flash-lite` | Stable | High-throughput, light agent work |
| Legacy low-cost | `gemini-3.1-flash-lite` | Stable · shutdown 2027-05-07 | Still valid; plan the move |
| Pro (preview) | `gemini-3.1-pro-preview` | Preview | Deep reasoning; no shutdown announced |
| Live voice | `gemini-3.8-live` | Stable (2026-09-15) | Default low-latency voice, no reasoning delay |
| Live + reasoning | `gemini-3.8-live-extended-thinking` | Stable (2026-09-15) | Background reasoning during live voice |
| TTS | `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts` | Stable (2026-09-22) | Studio fidelity vs high-volume |
| Embeddings | `gemini-embedding-2` | Stable (2026-04-22) | Multimodal; `gemini-embedding-2-preview` also resolves |

**Redirecting IDs — callable, but not the model you named:**

| ID | Routes to |
|---|---|
| `gemini-3.5-flash` | `gemini-3.6-flash` |
| `gemini-3.7-flash` | `gemini-3.8-flash` |

Pin the target ID explicitly. An alias that silently moves is a production
surprise.

**Retired or imminent — never use in new code:**

- `gemini-2.0-*` (shut down 2026-06-01), `gemini-1.5-*`, `gemini-1.0-*`.
- `gemini-3-pro-preview` (shut down 2026-03-09) → `gemini-3.1-pro-preview`.
- `gemini-3.1-flash-lite-preview` (shut down 2026-05-25) → `gemini-3.1-flash-lite`.
- `gemini-3.1-flash-live-preview` and `gemini-2.5-flash-native-audio-preview-12-2025` → `gemini-3.8-live` by **2026-11-17**.
- `gemini-3.1-flash-tts-preview`, `gemini-2.5-*-preview-tts` → `gemini-3.8-flash-tts` by **2026-11-17**.
- `text-embedding-004`, `embedding-001`, `gemini-embedding-001` → `gemini-embedding-2`.
- `imagen-4.0-*` (shut down 2026-08-17) → `gemini-nano-banana-2.1`.
- `veo-3.1-*-preview` (shut down **2026-10-22**) → `gemini-omni-1.1-flash`.

Full machine-readable catalog, including shutdown dates and replacements:
`references/model-catalog.md` and `model-cache.json` in the
`adk-agent-architecture` skill. `python scripts/fetch_models.py --check-only`
fails CI when this table drifts.

## Route by complexity

| Work | Model | thinking_level |
|---|---|---|
| Triage, formatting, classification, simple tools | `gemini-3.5-flash-lite` | `low` (or `minimal` on 3.5 Flash-Lite) |
| RAG, multi-step tools, content, most agents | `gemini-3.8-flash` | `medium` (default) |
| Hard reasoning, architecture, difficult code | `gemini-3.1-pro-preview` | `high` |
| Frontier tail, >65k output, hardest tasks | `gemini-4-argon` | `high` |
| Live voice | `gemini-3.8-live` | n/a (streaming) |
| Live voice that must reason | `gemini-3.8-live-extended-thinking` | n/a |

Start at `gemini-3.8-flash`. Move down only for measured cost or latency, up
only for measured quality. Argon is not a default: it is paid-only and its
shared 1M budget counts thinking and output.

## Thinking and effort

`thinking_level` is the control surface: `minimal`, `low`, `medium`, `high`.
`thinking_budget` is retired.

| Model family | Levels | Default | Rejected |
|---|---|---|---|
| Gemini 4 Argon | `low`, `medium`, `high` | `medium` | `minimal` → 400; `thinking_budget` → 400 |
| Gemini 3.8 / 3.6 Flash | `low`, `medium`, `high` | `medium` | `minimal` → 400 |
| Gemini 3.1 Pro (preview) | `low`, `medium`, `high` | `high` | `minimal` |
| Gemini 3.5 Flash-Lite | `minimal`, `low`, `medium`, `high` | `low` | — |
| Gemini 3.8 Live | n/a | — | thinking config on Live |

Sampling parameters (`temperature`, `top_p`, `top_k`) are ignored by Gemini 3.x
and 4. Do not send them expecting an effect. `candidate_count` is unsupported.

ADK wiring:

```python
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

agent = LlmAgent(
    model="gemini-3.8-flash",
    name="researcher",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(thinking_level="high"),
    ),
)
```

A planner config wins over `generate_content_config` when both set thinking.
Never set `thinking_level` and `thinking_budget` together.

## Argon-specific rules

- Budget the **shared** 1,048,576-token window: input + thinking + output.
- A single synchronous request emits up to 65,536 tokens (32,768 for
  non-streaming direct HTTP). Longer output needs long decode with
  `continuation_token`.
- Implicit caching only, 6,144-token minimum. Explicit `cachedContents` is not
  supported.
- No Live API, no audio or image generation. Keep those on the 3.8 family.
- Paid tier only. Free-tier code that defaults to Argon will fail.

## Fallback

1. **Validate at build time** — reject blocked IDs before the agent starts.
2. **Same-provider tier fallback** — on `429`/`503`, degrade one tier.
3. **Cross-provider fallback** — via LiteLLM (see `adk-litellm`).
4. **Resilience** — retry with backoff, circuit breaker, timeout, and an
   explicit `ok | degraded | error` signal.
5. **Safety never degrades silently.**

```python
FALLBACK_CHAINS = {
    "frontier":  ["gemini-4-argon", "gemini-3.1-pro-preview", "gemini-3.8-flash"],
    "reasoning": ["gemini-3.1-pro-preview", "gemini-3.8-flash"],
    "general":   ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"],
    "volume":    ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"],
    "live":      ["gemini-3.8-live", "gemini-3.8-live-extended-thinking"],
    "embedding": ["gemini-embedding-2"],
}
```

## References

| File | Load when |
|---|---|
| `references/model-catalog.md` | IDs, replacements, shutdown dates, embeddings |
| `references/thinking-effort.md` | Per-model level support and migration |
| `references/fallback.md` | Build-time validation, chains, resilience contract |
