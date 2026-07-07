---
name: adk-embeddings
description: >-
  ADK memory + embeddings across databases. Generate multimodal embeddings with
  gemini-embedding-2, persist agent sessions/memory to Cloud SQL, Postgres,
  Firestore, or SQLite, and store/retrieve vectors for RAG (pgvector, Firestore
  vector). Use when choosing a session/memory backend, wiring a database
  SessionService or MemoryService, generating embeddings, or building a
  vector store for retrieval on an ADK agent.
---

# adk-embeddings — Memory & Embeddings Across Databases

Persist ADK agent memory to a real database and store embeddings for retrieval.
Grounded in ADK 2.3 (`adk-python-v2.3/`) and the current Gemini embeddings guide.
Verify signatures against `adk-python-v2.3/src/google/adk/`, never `adk-python-v1/`.

## When to use

- Choosing a **SessionService** backend: Cloud SQL / Postgres / SQLite / Firestore / Vertex.
- Wiring a **MemoryService** (managed or database-backed) onto the `Runner`.
- Generating embeddings with `gemini-embedding-2` (multimodal) or `gemini-embedding-001` (text).
- Building a **vector store** (pgvector on Cloud SQL/Postgres, Firestore vector) for RAG.

## Two layers: sessions vs long-term memory

- **SessionService** — the conversation/state store for a live run (short-lived operational state).
- **MemoryService** — durable, searchable long-term memory recalled via `PreloadMemoryTool`/`load_memory`.

Both attach to the `Runner`. Pick a backend per layer.

## Session backends (verified in `google.adk`)

| Backend | Class | Import |
|---------|-------|--------|
| In-memory (dev) | `InMemorySessionService` | `google.adk.sessions` |
| SQLite (local file) | `SqliteSessionService` | `google.adk.sessions` |
| **Postgres / Cloud SQL / MySQL** | `DatabaseSessionService(db_url=...)` | `google.adk.sessions` |
| **Firestore** | `FirestoreSessionService` | `google.adk.integrations.firestore` |
| Vertex managed | `VertexAiSessionService` | `google.adk.sessions` |

`DatabaseSessionService` is SQLAlchemy-based — one class serves Postgres, Cloud
SQL, MySQL, and SQLite via the connection URL (or an existing `db_engine`).
Full connection strings (incl. the Cloud SQL Python Connector) and Firestore
setup: `references/session-backends.md`.

## Memory backends (verified in `google.adk`)

| Backend | Class | Import |
|---------|-------|--------|
| In-memory (dev) | `InMemoryMemoryService` | `google.adk.memory` |
| **Firestore** | `FirestoreMemoryService` | `google.adk.integrations.firestore` |
| Vertex Memory Bank | `VertexAiMemoryBankService` | `google.adk.memory` |
| Vertex RAG corpus | `VertexAiRagMemoryService` | `google.adk.memory` |
| Custom (pgvector / Firestore vector) | subclass `BaseMemoryService` | `google.adk.memory` |

`BaseMemoryService` requires `add_session_to_memory`, `add_events_to_memory`,
`add_memory`, and `search_memory` — implement these to back memory with your own
vector store (see `references/vector-stores.md`).

## Wiring to the Runner

```python
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.integrations.firestore import FirestoreMemoryService

runner = Runner(
    agent=root_agent,
    app_name="ion-sight",
    session_service=DatabaseSessionService(db_url="postgresql+pg8000://..."),
    memory_service=FirestoreMemoryService(),  # or a custom pgvector-backed service
)
```

Agents recall via `PreloadMemoryTool` / `load_memory` (see the `adk-memory` skill).

## Embeddings — `gemini-embedding-2`

The current multimodal embedding model. Generate via `google.genai`:

```python
from google import genai
from google.genai import types

client = genai.Client()
result = client.models.embed_content(
    model="gemini-embedding-2",
    contents="task: search result | query: nearest pharmacy",
    config=types.EmbedContentConfig(output_dimensionality=1536),  # 768 | 1536 | 3072
)
vector = result.embeddings[0].values
```

Key facts (full detail in `references/embeddings.md`):

- **Multimodal:** text, image, audio, video, PDF → one unified space (8192-token limit).
- **No `task_type` on `gemini-embedding-2`** — put the task in the prompt (`task: ... | query: ...` for queries, `title: ... | text: ...` for documents). `gemini-embedding-001` (text-only) still uses the `task_type` enum.
- **`output_dimensionality`:** 768 / 1536 / 3072 recommended; `-2` auto-normalizes truncated dims (`-001` needs manual L2 normalization).
- **Incompatible spaces:** `-001` and `-2` embeddings are not comparable — re-embed everything when migrating.
- **Cosine similarity** for retrieval.

## Vector storage for RAG

| Store | Best for | Reference |
|-------|----------|-----------|
| Cloud SQL / Postgres + `pgvector` | Relational app already on Postgres/Cloud SQL | `references/vector-stores.md` |
| Firestore vector (`find_nearest`, KNN) | Serverless, per-user isolation | `references/vector-stores.md` |
| AlloyDB / BigQuery | Scale / analytics | (managed — see Google Cloud) |

Match the vector column dimension to your `output_dimensionality` (e.g. `vector(1536)`).

## Reference loading

| File | When |
|------|------|
| `references/embeddings.md` | `gemini-embedding-2` generation, task prefixes, dims, multimodal, `-001` migration |
| `references/session-backends.md` | Cloud SQL / Postgres / SQLite / Firestore / Vertex SessionService setup |
| `references/vector-stores.md` | pgvector + Firestore vector schema, KNN retrieval, custom `BaseMemoryService` |

Related skills: `adk-memory` (recall flow), `adk-rag` (retrieval pipelines), `adk-model-routing` (embedding model selection).
