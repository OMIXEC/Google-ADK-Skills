# Vector Stores — pgvector, Firestore vector, custom MemoryService

Store `gemini-embedding-2` vectors for retrieval. Match the vector column/field
dimension to your `output_dimensionality` (768 / 1536 / 3072).

## Option A — Cloud SQL / Postgres + pgvector

Enable the extension and create a table with a `vector` column.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE memories (
    id           bigserial PRIMARY KEY,
    user_id      text NOT NULL,
    content      text NOT NULL,
    embedding    vector(1536) NOT NULL,   -- == output_dimensionality
    created_at   timestamptz DEFAULT now()
);

-- ANN index (cosine). Use HNSW for recall/latency, IVFFlat for build speed.
CREATE INDEX ON memories USING hnsw (embedding vector_cosine_ops);
```

Query nearest neighbours (cosine distance `<=>`), scoped per user:

```sql
SELECT content, 1 - (embedding <=> :query_vec) AS score
FROM memories
WHERE user_id = :user_id
ORDER BY embedding <=> :query_vec
LIMIT 5;
```

Insert with the embedding from `references/embeddings.md`. Connect the same way
as `DatabaseSessionService` (see `references/session-backends.md`) — reuse the
Cloud SQL Connector / async engine.

## Option B — Firestore vector search (KNN)

Firestore supports native KNN with `find_nearest`. Store the embedding as a
`Vector` field; enforce per-user isolation with a subcollection.

```python
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

db = firestore.Client(project="ion-sight")
col = db.collection("users").document(user_id).collection("memories")

# Store
col.add({"content": text, "embedding": Vector(vector)})   # vector = 1536 floats

# Retrieve (KNN, cosine)
results = col.find_nearest(
    vector_field="embedding",
    query_vector=Vector(query_vec),
    distance_measure=DistanceMeasure.COSINE,
    limit=5,
).get()
```

Create the vector index before querying:

```bash
gcloud firestore indexes composite create \
  --collection-group=memories --query-scope=COLLECTION \
  --field-config=field-path=embedding,vector-config='{"dimension":1536,"flat":{}}'
```

## Option C — Custom ADK MemoryService over your vector store

Back ADK's memory recall (`PreloadMemoryTool` / `load_memory`) with any store by
subclassing `BaseMemoryService` (`google.adk.memory`). Implement the four
abstract methods; embed with `gemini-embedding-2`, then KNN-search.

```python
from google.adk.memory import BaseMemoryService
from google.adk.memory.memory_entry import MemoryEntry

class PgVectorMemoryService(BaseMemoryService):
    async def add_session_to_memory(self, session): ...      # embed + upsert events
    async def add_events_to_memory(self, *, app_name, user_id, events): ...
    async def add_memory(self, *, app_name, user_id, memory): ...
    async def search_memory(self, *, app_name, user_id, query):
        qvec = embed(query)                                  # gemini-embedding-2
        rows = knn_search(user_id, qvec, limit=5)            # pgvector / Firestore
        return SearchMemoryResponse(memories=[MemoryEntry(...) for r in rows])
```

Attach on the `Runner` via `memory_service=PgVectorMemoryService(...)`. Confirm
the exact `search_memory` return type and method signatures against
`adk-python-v2.3/src/google/adk/memory/base_memory_service.py` before shipping.

## Managed alternatives

- `FirestoreMemoryService` (`google.adk.integrations.firestore`) — keyword-based
  memory from session events, no custom vector code (see the main SKILL).
- `VertexAiMemoryBankService` / `VertexAiRagMemoryService` (`google.adk.memory`) —
  fully managed recall/RAG.
- **AlloyDB** and **BigQuery** — managed vector search at scale (Google Cloud).

## Best practices

- **Dimension match:** vector column/field size == `output_dimensionality`.
- **Per-user isolation:** always scope by `user_id` (row filter / subcollection).
- **Cosine** distance; `gemini-embedding-2` auto-normalizes truncated dims.
- **Re-embed on model change:** `-001` and `-2` spaces are incompatible.
- **Consistent task formatting:** embed documents and queries with matching task
  prefixes (`references/embeddings.md`).
