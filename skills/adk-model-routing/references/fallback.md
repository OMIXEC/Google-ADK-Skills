# Fallback Methodology (Production)

Every production route needs a primary model and a safe fallback path. Design for
model outages, quota exhaustion, and deprecation — not just the happy path.

## 1. Validate at build time

Reject deprecated/blocked model IDs before an agent starts, so a bad config fails
fast instead of at first request.

```python
HARD_BLOCKED = {
    "gemini-2.0-flash", "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite", "gemini-2.0-flash-lite-001",
    "gemini-3-pro-preview", "text-embedding-004", "embedding-001",
}
REPLACEMENTS = {
    "gemini-2.0-flash": "gemini-3.5-flash",
    "gemini-2.0-flash-lite": "gemini-3.1-flash-lite",
    "gemini-3-pro-preview": "gemini-3.1-pro-preview",
}

def validate_model(model_id: str) -> str:
    if model_id in HARD_BLOCKED:
        raise ValueError(
            f"{model_id} is blocked. Use {REPLACEMENTS.get(model_id, 'gemini-3.5-flash')}."
        )
    return model_id
```

## 2. Same-provider tier fallback

On `429` / quota / model-unavailable, degrade to the next capable Gemini tier.
Keep an explicit ordered chain per capability, cheapest-capable first, with a
higher tier as backup only where quality demands it.

```python
FALLBACK_CHAINS = {
    "reasoning":   ["gemini-3.1-pro-preview", "gemini-3.5-flash"],
    "general":     ["gemini-3.5-flash", "gemini-3.1-flash-lite"],
    "high_volume": ["gemini-3.1-flash-lite", "gemini-3.5-flash"],
    "live":        ["gemini-3.1-flash-live-preview"],
    "embedding":   ["gemini-embedding-2"],
}
```

## 3. Cross-provider fallback

When Gemini is fully unavailable, route to another provider via LiteLLM. See the
`adk-litellm` skill for wrapping OpenAI/Anthropic/Bedrock/OpenRouter models as
ADK models and building provider fallback.

## 4. Resilience contract

Wrap model calls with:

- **Retry with backoff** on transient errors (`429`, `503`, timeouts).
- **Circuit breaker** per model — after N consecutive failures, skip to the next
  chain entry for a cooldown window.
- **Timeout** on every call.
- **Structured result:** return `ok | degraded | error` with `confidence`,
  `correlation_id`, and `latency_ms`. Emit `degraded` (not silent success) when a
  fallback fired, so callers and telemetry can see it.

## 5. Safety never degrades silently

Safety-critical routes must surface degradation explicitly and must not drop or
silently downgrade a response. Never fall back below a safe reasoning tier for
safety decisions (see `references/thinking-effort.md` — keep safety at `high`,
never below `medium`).

## Anti-patterns

- Hardcoding a single model with no fallback.
- Falling back to a deprecated/blocked model (validate the whole chain).
- Swallowing a fallback as if it were the primary result (no `degraded` signal).
- Retrying a hard `400` (e.g. `thinking_level` + `thinking_budget` conflict) —
  fix the request, don't retry.
