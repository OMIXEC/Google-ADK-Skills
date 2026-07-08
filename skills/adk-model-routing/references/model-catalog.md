# Model Catalog — Current Gemini 3.x (ADK 2.3)

Authoritative model IDs for new ADK agents. Reference signatures against
Context7 `/google/adk-docs` and the local `adk-python-v2.3/` mirror when present.
Cross-check live availability at
<https://ai.google.dev/gemini-api/docs/models> and
<https://ai.google.dev/gemini-api/docs/deprecations>.

## Preferred models

| Role | Model ID | Context | Notes |
|------|----------|---------|-------|
| Balanced / agentic / coding (default) | `gemini-3.5-flash` | 1M in / 65k out | GA, stable. Thinking, Computer Use (Preview), full tool set. Knowledge cutoff Jan 2025. |
| Low-cost / high-volume | `gemini-3.1-flash-lite` | 1M | Stable, long-term, efficiency-optimized. Default `thinking_level` `minimal`. |
| Complex reasoning / research | `gemini-3.1-pro-preview` | 1M | Replaces `gemini-3-pro-preview`. Deepest reasoning. |
| Live / bidi audio+video | `gemini-3.1-flash-live-preview` | — | Gemini Live API; must support `bidiGenerateContent`. |
| Embeddings (multimodal) | `gemini-embedding-2` | — | Text, images, video, audio, PDF → unified embeddings. |

## Deprecated / blocked — never use in new code

| Blocked | Replace with |
|---------|-------------|
| `gemini-2.0-flash`, `gemini-2.0-flash-001` | `gemini-3.5-flash` |
| `gemini-2.0-flash-lite`, `gemini-2.0-flash-lite-001` | `gemini-3.1-flash-lite` |
| `gemini-2.0-flash-exp`, `gemini-2.0-flash-live-001` | `gemini-3.1-flash-live-preview` |
| `gemini-3-pro-preview` | `gemini-3.1-pro-preview` |
| `gemini-1.5-*`, `gemini-1.0-*`, `gemini-pro` | `gemini-3.5-flash` |
| `text-embedding-004`, `embedding-001`, `gemini-embedding-001` | `gemini-embedding-2` |

`gemini-3-flash-preview` remains available for preview testing, but migrate to
`gemini-3.5-flash` for GA stability. `gemini-2.5-*` are legacy — use only if
explicitly required.

## Selecting a model

- Start at `gemini-3.5-flash`. Drop to `gemini-3.1-flash-lite` for cost/latency
  on simple, high-volume work; raise to `gemini-3.1-pro-preview` for the hardest
  reasoning.
- Live voice/video → `gemini-3.1-flash-live-preview` (see the `adk-bidi-live` skill).
- Embeddings/RAG → `gemini-embedding-2` (see the `adk-rag` skill).

## SDK note

Use the `google-genai` SDK v2.0.0+ for the Interactions API (breaking changes
from earlier versions). ADK 2.3 depends on `google-adk>=2.3.0,<3`.
