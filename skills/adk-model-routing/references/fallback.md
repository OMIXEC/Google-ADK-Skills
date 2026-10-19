# Fallback Methodology

Every production route needs a primary and a fallback. Design for quota,
outage, and deprecation, not only the happy path.

## 1. Validate at build time

```python
HARD_BLOCKED = {
    "gemini-2.0-flash", "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite", "gemini-2.0-flash-lite-001",
    "gemini-3-pro-preview", "gemini-3.1-flash-lite-preview",
    "gemini-3.1-flash-live-preview", "gemini-3.1-flash-tts-preview",
    "text-embedding-004", "embedding-001", "gemini-embedding-001",
    "imagen-4.0-generate", "veo-3.1-generate-preview",
}

REPLACEMENTS = {
    "gemini-2.0-flash": "gemini-3.6-flash",
    "gemini-2.0-flash-lite": "gemini-3.1-flash-lite",
    "gemini-3-pro-preview": "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite-preview": "gemini-3.1-flash-lite",
    "gemini-3.1-flash-live-preview": "gemini-3.8-live",
    "gemini-3.1-flash-tts-preview": "gemini-3.8-flash-tts",
    "text-embedding-004": "gemini-embedding-2",
}

def validate_model(model_id: str) -> str:
    if model_id in HARD_BLOCKED:
        raise ValueError(
            f"{model_id} is blocked. Use "
            f"{REPLACEMENTS.get(model_id, 'gemini-3.8-flash')}."
        )
    return model_id
```

Reject redirecting IDs too when the exact model matters:
`gemini-3.5-flash` → 3.6, `gemini-3.7-flash` → 3.8.

## 2. Same-provider tier fallback

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

Two constraints that break naive chains:

- **Thinking levels differ.** A chain cannot send `minimal` to Argon or 3.8
  Flash; it returns 400. Store `(model, thinking_level)` pairs, not model IDs
  alone.
- **Argon is paid-only and shares one token budget** across input, thinking,
  and output. A fallback into Argon can fail on budget rather than quota.

## 3. Cross-provider fallback

Route to another provider through LiteLLM when Gemini is unavailable. See
`adk-litellm`.

## 4. Resilience contract

- Retry with backoff on `429`, `503`, and timeouts.
- Circuit breaker per model; after N consecutive failures skip to the next
  chain entry for a cooldown.
- Timeout on every call.
- Return `ok | degraded | error` with `confidence`, `correlation_id`, and
  `latency_ms`. Emit `degraded` when a fallback fired.
- A `400` is not transient. Fix the request; retrying repeats the error.

## 5. Safety never degrades silently

Safety-critical routes keep `high` thinking and must surface degradation. Never
drop or silently downgrade a safety response. Never fall below `medium` for a
safety decision.

## Anti-patterns

- One hardcoded model with no fallback.
- Falling back to a blocked or redirecting ID.
- Sending the same `thinking_level` to every model in a chain.
- Swallowing a fallback as if it were the primary result.
- Retrying a `400` caused by `thinking_level` plus `thinking_budget`.
