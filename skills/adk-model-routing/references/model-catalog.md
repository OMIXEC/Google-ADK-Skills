# Model Catalog

Verified against <https://ai.google.dev/gemini-api/docs/models> and
<https://ai.google.dev/gemini-api/docs/deprecations> on **2026-10-19**.
Machine-readable copy: `model-cache.json` in the `adk-agent-architecture`
skill, refreshed by `scripts/fetch_models.py`.

## Current models

| Role | Model ID | Status | Context / output |
|---|---|---|---|
| Frontier | `gemini-4-argon` | Stable, GA 2026-10-13 | 1,048,576 shared; 65,536 per synchronous request |
| Balanced (default) | `gemini-3.8-flash` | Stable 2026-09-02 | 1,048,576 / 65,536 |
| Previous Flash | `gemini-3.6-flash` | Stable 2026-07-21 | 1,048,576 / 65,536 |
| Cost-optimized | `gemini-3.5-flash-lite` | Stable 2026-07-21 | 1,048,576 / 65,536 |
| Low-cost, retiring | `gemini-3.1-flash-lite` | Stable, shutdown 2027-05-07 | 1,048,576 / 65,536 |
| Pro preview | `gemini-3.1-pro-preview` | Preview 2026-02-19 | 1M / 65k |
| Live voice | `gemini-3.8-live` | Stable 2026-09-15 | Live API |
| Live + reasoning | `gemini-3.8-live-extended-thinking` | Stable 2026-09-15 | Live API |
| Live translate | `gemini-3.5-live-translate-preview` | Preview 2026-06 | Live API |
| TTS flagship | `gemini-3.8-flash-tts` | Stable 2026-09-22 | 130 languages |
| TTS volume | `gemini-3.8-flash-lite-tts` | Stable 2026-09-22 | 101 languages |
| Transcribe | `gemini-3.5-transcribe`, `gemini-3.5-transcribe-live` | Stable 2026-08 | Speech-to-text |
| Embeddings | `gemini-embedding-2` | Stable 2026-04-22 | Multimodal |
| Image | `gemini-nano-banana-2.1` | Stable 2026-10-06 | Image gen/edit |
| Image | `gemini-3.1-flash-image`, `gemini-3.1-flash-lite-image`, `gemini-3-pro-image` | Stable | Nano Banana 2 / 2 Lite / Pro |
| Video | `gemini-omni-1.1-flash` | Stable 2026-08-27 | Video gen/edit, native audio |
| Agents | `deep-research-preview-04-2026`, `deep-research-max-preview-04-2026`, `antigravity-preview-09-2026` | Preview | Managed agents |

## Redirecting IDs

| ID | Routes to | Meaning |
|---|---|---|
| `gemini-3.5-flash` | `gemini-3.6-flash` | Endpoint alive, not selectable |
| `gemini-3.7-flash` | `gemini-3.8-flash` | Endpoint alive, not selectable |

## Retired — never use

| Retired | Replace with | Shutdown |
|---|---|---|
| `gemini-2.0-flash`, `-001`, `-lite`, `-lite-001` | `gemini-3.6-flash` / `gemini-3.1-flash-lite` | 2026-06-01 |
| `gemini-3-pro-preview` | `gemini-3.1-pro-preview` | 2026-03-09 |
| `gemini-3.1-flash-lite-preview` | `gemini-3.1-flash-lite` | 2026-05-25 |
| `gemini-3.1-flash-live-preview` | `gemini-3.8-live` | 2026-11-17 |
| `gemini-2.5-flash-native-audio-preview-12-2025` | `gemini-3.8-live` | 2026-11-17 |
| `gemini-3.1-flash-tts-preview` | `gemini-3.8-flash-tts` | 2026-11-17 |
| `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts` | `gemini-3.8-flash-tts` | 2026-11-17 |
| `gemini-2.5-flash-image` | `gemini-3.1-flash-lite-image` | 2027-03-15 |
| `imagen-4.0-*` | `gemini-nano-banana-2.1` | 2026-08-17 |
| `veo-3.1-*-preview` | `gemini-omni-1.1-flash` | 2026-10-22 |
| `gemini-3.1-flash-lite` | `gemini-3.5-flash-lite` | 2027-05-07 |
| `gemini-embedding-001` | `gemini-embedding-2` | 2028-05-14 |
| `text-embedding-004`, `embedding-001`, `gemini-embedding-exp*` | `gemini-embedding-2` | already shut down |
| `gemini-2.5-computer-use-preview-10-2025` | `gemini-3.8-flash` | 2026-07-28 |
| `gemini-robotics-er-1.6-preview` | `gemini-robotics-er-2-preview` | 2026-08-31 |

Still supported with no shutdown date: `gemini-2.5-pro`, `gemini-2.5-flash`,
`gemini-2.5-flash-lite`.

## Selecting a model

- Default to `gemini-3.8-flash`.
- Drop to `gemini-3.5-flash-lite` for high-volume, low-complexity work.
- Raise to `gemini-3.1-pro-preview` for hard reasoning that still fits 65k out.
- Use `gemini-4-argon` only for the frontier tail: long decodes, very large
  contexts, or quality that Flash cannot reach. Budget the shared token window.
- Live voice → `gemini-3.8-live`; add `-extended-thinking` only when background
  reasoning is required.
- Embeddings/RAG → `gemini-embedding-2` (see `adk-rag`).

## Refreshing this table

```bash
python skills/adk-agent-architecture/scripts/fetch_models.py
python skills/adk-agent-architecture/scripts/fetch_models.py --check-only
```

`--check-only` exits 1 when a model is added, removed, or changes status.
