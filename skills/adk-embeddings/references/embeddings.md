# Embeddings — gemini-embedding-2 (and -001)

Generate embeddings with the Gemini API `embedContent` method via `google.genai`.

## Models

| Model | Input | Output dims | Task typing | Notes |
|-------|-------|-------------|-------------|-------|
| `gemini-embedding-2` | Text, image, audio, video, PDF (8192 tok) | 128–3072 (rec. 768/1536/3072) | **Prompt prefix** (no `task_type`) | Multimodal, auto-normalizes truncated dims, aggregates multi-input |
| `gemini-embedding-001` | Text only (2048 tok) | 128–3072 | `task_type` enum | Manual normalization for non-3072 |

`gemini-embedding-2` is the current default. Use `-001` only for text-only work
that still relies on the `task_type` parameter.

## Generate (Python)

```python
from google import genai
from google.genai import types

client = genai.Client()

result = client.models.embed_content(
    model="gemini-embedding-2",
    contents="task: search result | query: nearest pharmacy",
    config=types.EmbedContentConfig(output_dimensionality=1536),
)
vector = result.embeddings[0].values   # length 1536
```

## Task formatting for gemini-embedding-2

`gemini-embedding-2` has **no `task_type` parameter** — encode the task in the
text. Be consistent: embed queries and documents with matching task formats.

**Asymmetric (retrieval)** — prefix the query, structure the document:

| Use case | Query | Document |
|----------|-------|----------|
| Search | `task: search result \| query: {q}` | `title: {title} \| text: {content}` |
| Q&A | `task: question answering \| query: {q}` | `title: {title} \| text: {content}` |
| Fact check | `task: fact checking \| query: {q}` | `title: {title} \| text: {content}` |
| Code | `task: code retrieval \| query: {q}` | `title: {title} \| text: {content}` |

Use `title: none` when a document has no title.

**Symmetric (single-input)** — same format for both sides:
`task: classification | query: {content}`, `task: clustering | query: {content}`,
`task: sentence similarity | query: {content}`.

## Task types for gemini-embedding-001

`-001` takes an explicit `task_type` in `EmbedContentConfig`:

```python
result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=["What is the meaning of life?", "What is the purpose of existence?"],
    config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
)
```

Supported: `SEMANTIC_SIMILARITY`, `CLASSIFICATION`, `CLUSTERING`,
`RETRIEVAL_DOCUMENT`, `RETRIEVAL_QUERY`, `CODE_RETRIEVAL_QUERY`,
`QUESTION_ANSWERING`, `FACT_VERIFICATION`. Pair queries with documents
(`RETRIEVAL_QUERY` ↔ `RETRIEVAL_DOCUMENT`).

## Dimensions & normalization

- Set `output_dimensionality` to 768, 1536, or 3072 (default 3072). Smaller =
  cheaper storage, minimal quality loss (MRL).
- `gemini-embedding-2` **auto-normalizes** truncated dimensions.
- `gemini-embedding-001` needs **manual L2 normalization** for non-3072 dims:

```python
import numpy as np
v = np.array(result.embeddings[0].values)
normed = v / np.linalg.norm(v)   # only for gemini-embedding-001
```

- Use **cosine similarity** for comparison (direction, not magnitude).

## Multimodal & aggregation (gemini-embedding-2)

```python
result = client.models.embed_content(
    model="gemini-embedding-2",
    contents=[
        "An image of a dog",
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
    ],
)  # multiple parts in one `contents` → ONE aggregated embedding
```

Wrap each input in its own `types.Content` to get **separate** embeddings.
Limits: ≤6 images, audio ≤180s, video ≤120s (≤32 frames), PDF ≤1 file/6 pages;
8192 tokens total (inputs over the limit are silently truncated).

## Migration -001 → -2

The two embedding spaces are **incompatible** — vectors are not comparable
across models. When switching to `gemini-embedding-2` you must **re-embed all
stored data**. Also: `-2` drops `task_type` (use prompt prefixes), aggregates
multi-input into one vector, and auto-normalizes truncated dims.

## Throughput

For non-latency-sensitive bulk work, use the Batch API (≈50% cost) instead of
per-item `embed_content` calls.
