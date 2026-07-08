# Models, Thinking & Embeddings — 1.x → 2.3

## Model IDs

Replace every deprecated Gemini model with a current 3.x ID.

| Deprecated | Replacement |
|------------|-------------|
| `gemini-2.0-flash`, `gemini-2.0-flash-001`, `gemini-2.5-flash` | `gemini-3.5-flash` |
| `gemini-2.0-flash-lite*`, `gemini-2.5-flash-lite` | `gemini-3.1-flash-lite` |
| `gemini-2.5-pro`, `gemini-3-pro-preview` | `gemini-3.1-pro-preview` |
| `gemini-2.0-flash-exp`, `gemini-2.0-flash-live-001`, `gemini-live-2.5-flash-native-audio` | `gemini-3.1-flash-live-preview` |
| `gemini-1.5-*`, `gemini-1.0-*`, `gemini-pro` | `gemini-3.5-flash` |

See the `adk-model-routing` skill for routing by complexity/cost.

## Thinking / effort

Gemini 3.x replaces the numeric `thinking_budget` with the `thinking_level`
effort enum: `minimal`, `low`, `medium` (default in 3.5, was `high`), `high`.

```python
# 1.x
generate_content_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=1024),
)
# 2.3
from google.adk.planners import BuiltInPlanner
agent = LlmAgent(
    model="gemini-3.5-flash", name="worker",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(thinking_level="medium"),
    ),
)
```

- Do **not** set both `thinking_level` and `thinking_budget` → `400`.
- **Remove** `temperature`, `top_p`, `top_k`, `candidate_count` on Gemini 3.x —
  no longer recommended / unsupported; the defaults are tuned for reasoning.
- Thought preservation is automatic across turns; keep thought signatures in
  history for stateless multi-turn function calling.

## Embeddings

| Deprecated | Replacement |
|------------|-------------|
| `text-embedding-004`, `embedding-001`, `gemini-embedding-001` (text-only) | `gemini-embedding-2` (multimodal) |

`gemini-embedding-2` drops the `task_type` parameter (use prompt task prefixes),
auto-normalizes truncated dimensions, and aggregates multi-input into one vector.
**Embedding spaces are incompatible** — re-embed all stored vectors when
migrating. See the `adk-embeddings` skill for generation + vector-DB storage.

## Dependencies & runtime

```txt
google-adk>=2.3.0,<3      # was: google-adk 1.x
google-genai>=2.0.0       # Interactions API (breaking changes from earlier)
```

- **Python 3.10+** (official ADK metadata advertises `requires-python = ">=3.10"`).
  Drop any 3.11-only assumption.
- Prefer `uv` in repos standardized on it.

## Sessions & state

- 1.x and 2.3 **session/state schemas are incompatible** — do not reuse persisted
  1.x sessions. Migration helpers live under `google.adk.sessions.migration`
  (local mirror path: `adk-python-v2.3/src/google/adk/sessions/migration/`).
- New database/serverless backends in 2.3: `DatabaseSessionService`
  (Postgres/Cloud SQL/MySQL), `FirestoreSessionService`/`FirestoreMemoryService`
  (`google.adk.integrations.firestore`). See the `adk-embeddings` skill.
