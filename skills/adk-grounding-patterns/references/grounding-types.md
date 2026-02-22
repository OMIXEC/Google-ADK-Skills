# Grounding Types - Comprehensive Reference

Complete guide to grounding methods for Google ADK agents.

## Overview

Grounding connects agents to authoritative data sources to reduce hallucinations and improve factual accuracy. Choose the right grounding method based on your use case.

## Grounding Method Comparison

| Method | Data Source | Freshness | Setup Complexity | Cost | Best For |
|--------|-------------|-----------|------------------|------|----------|
| Google Search | Web | Real-time | Low | Low | Current events, public info |
| Vertex AI RAG | Documents | Static | Medium | Medium | Internal docs, knowledge bases |
| Vector Search 2.0 | Embeddings | Static | High | Medium | Semantic search, recommendations |
| Custom Source | Database/API | Real-time | High | Low | Business data, proprietary info |
| Agentic RAG | Documents | Static | Medium | High | Complex queries, multi-faceted search |

## 1. Google Search Grounding

### Overview

Real-time web search using Google's search index. Provides current information from the public web.

### Architecture

```
User Query → Agent → google_search tool → Google Search API → Web Results → Agent Response
```

### Configuration

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    tools=[google_search],
    instruction="Always search for current information.",
)
```

### Advantages

- Real-time data (news, weather, stocks)
- No setup required
- Global knowledge coverage
- Low cost

### Limitations

- Public web only (no private data)
- Rate limits apply
- Quality varies by source
- No control over content

### Use Cases

1. **News and Current Events**
   ```python
   instruction="""
   You are a news research agent.
   Search for latest news on requested topics.
   Cite sources with publication dates.
   """
   ```

2. **Product Research**
   ```python
   instruction="""
   You are a product research assistant.
   Search for product reviews, specifications, and pricing.
   Compare multiple sources.
   """
   ```

3. **Weather and Location**
   ```python
   instruction="""
   You are a travel assistant.
   Search for weather, attractions, and local information.
   """
   ```

## 2. Vertex AI RAG Engine

### Overview

Managed retrieval-augmented generation using Vertex AI. Ingest documents into corpora and retrieve relevant chunks.

### Architecture

```
User Query → Agent → VertexAiRagRetrieval → Embedding → Vector Search → Chunk Retrieval → Agent Response
```

### Configuration

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/PROJECT/locations/LOCATION/ragCorpora/CORPUS_ID"

agent = Agent(
    name="rag_agent",
    model="gemini-2.5-flash",
    tools=[
        VertexAiRagRetrieval(
            name="search_docs",
            description="Search knowledge base",
            rag_resources=[
                rag.RagResource(rag_corpus=RAG_CORPUS)
            ],
            similarity_top_k=10,
            vector_distance_threshold=0.3,
        ),
    ],
)
```

### Corpus Management

```python
from vertexai import rag

# Create corpus
corpus = rag.create_corpus(
    display_name="product_docs",
    description="Product documentation",
)

# Ingest documents
rag.import_files(
    corpus.name,
    paths=["gs://bucket/docs/"],
    chunk_size=512,
    chunk_overlap=50,
)

# List files
files = rag.list_files(corpus_name=corpus.name)
print(f"Files: {len(files)}")
```

### Advantages

- Managed service (no infrastructure)
- Automatic chunking and embedding
- Hybrid keyword + vector search
- Supports PDF, HTML, TXT, DOCX

### Limitations

- Static data (must re-ingest for updates)
- Corpus size limits
- Ingestion latency
- Medium cost

### Retrieval Optimization

```python
# Precise retrieval
VertexAiRagRetrieval(
    similarity_top_k=5,              # Fewer, better results
    vector_distance_threshold=0.2,   # High similarity required
)

# Broad retrieval
VertexAiRagRetrieval(
    similarity_top_k=20,             # More coverage
    vector_distance_threshold=0.5,   # Lower similarity threshold
)
```

### Use Cases

1. **Documentation Assistant**
   - Internal wikis
   - API documentation
   - Policy manuals

2. **Customer Support**
   - Product guides
   - FAQs
   - Troubleshooting docs

3. **Research Assistant**
   - Research papers
   - Academic articles
   - Technical reports

## 3. Vector Search 2.0

### Overview

Semantic similarity search using Vertex AI Vector Search. Build custom indexes over embeddings.

### Architecture

```
User Query → Embedding Model → Query Vector → Vector Index → Nearest Neighbors → Results
```

### Setup

```python
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

# Initialize
aiplatform.init(project="my-project", location="us-central1")

# Embedding model
embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")

# Create index
index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="document_index",
    contents_delta_uri="gs://bucket/embeddings/",
    dimensions=768,
    approximate_neighbors_count=10,
)

# Create endpoint
index_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name="document_endpoint",
)

# Deploy index
index_endpoint.deploy_index(
    index=index,
    deployed_index_id="deployed_index",
)
```

### Query

```python
def vector_search(query: str, top_k: int = 10):
    """Semantic similarity search."""
    # Generate embedding
    query_embedding = embedding_model.get_embeddings([query])[0].values

    # Search index
    response = index_endpoint.find_neighbors(
        deployed_index_id="deployed_index",
        queries=[query_embedding],
        num_neighbors=top_k,
    )

    return [{"id": n.id, "distance": n.distance} for n in response[0]]
```

### Advantages

- Full control over embeddings
- High performance (low latency)
- Scalable to billions of vectors
- Multimodal support (text, images)

### Limitations

- Complex setup
- Manual embedding generation
- Infrastructure management
- Higher upfront cost

### Use Cases

1. **Semantic Document Search**
2. **Product Recommendations**
3. **Code Similarity Detection**
4. **Image/Video Search**

## 4. Custom Data Sources

### Overview

Integrate agents with databases, APIs, and custom data sources.

### Database Integration

```python
import psycopg2
from google.adk.agents import Agent

def database_query(query: str) -> str:
    """Query PostgreSQL database."""
    conn = psycopg2.connect("postgresql://localhost/mydb")
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return str(results)

agent = Agent(
    name="db_agent",
    model="gemini-2.5-flash",
    tools=[database_query],
    instruction="""
    You can query the PostgreSQL database.
    Construct SQL queries based on user requests.
    Always sanitize inputs to prevent SQL injection.
    """,
)
```

### REST API Integration

```python
import requests
from google.adk.agents import Agent

def api_search(query: str) -> str:
    """Search via REST API."""
    response = requests.get(
        "https://api.example.com/search",
        params={"q": query},
        headers={"Authorization": "Bearer TOKEN"},
    )
    return response.json()

agent = Agent(
    name="api_agent",
    model="gemini-2.5-flash",
    tools=[api_search],
)
```

### File System Access

```python
import os
from google.adk.agents import Agent

def search_files(pattern: str) -> str:
    """Search local file system."""
    import glob
    files = glob.glob(f"**/{pattern}", recursive=True)
    return "\n".join(files)

agent = Agent(
    name="file_agent",
    model="gemini-2.5-flash",
    tools=[search_files],
)
```

### Advantages

- Real-time data
- Full control over logic
- Low cost
- Integration with existing systems

### Limitations

- Custom implementation required
- Maintenance overhead
- Security considerations
- Error handling complexity

## 5. Agentic RAG

### Overview

Advanced RAG pattern where agents reason about how to search. Agents plan queries, construct filters, and orchestrate multi-step retrieval.

### Architecture

```
User Query → Query Planner Agent → Search Plan → RAG Retrieval (with filters) → Synthesizer Agent → Response
```

### Implementation

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/PROJECT/locations/LOCATION/ragCorpora/CORPUS_ID"

# Query planning agent
query_planner = Agent(
    name="query_planner",
    model="gemini-2.5-flash",
    description="Plans optimal search strategy",
    instruction="""
    Analyze user query and plan search:
    1. Extract key concepts
    2. Identify metadata filters (date, category, author)
    3. Determine search breadth (narrow vs broad)
    4. Plan multi-step retrieval if needed

    Return JSON search plan:
    {
        "concepts": ["concept1", "concept2"],
        "filters": {"category": "technical", "year": "2024"},
        "top_k": 10,
        "multi_step": false
    }
    """,
)

# RAG retrieval
rag_tool = VertexAiRagRetrieval(
    name="search_with_filters",
    description="Search with dynamic filters",
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
    similarity_top_k=10,
)

# Orchestrator agent
agentic_rag_agent = Agent(
    name="agentic_rag_agent",
    model="gemini-2.5-flash",
    description="Intelligent search orchestrator",
    instruction="""
    For each user query:
    1. Ask query_planner to analyze and plan
    2. Execute search with planned parameters
    3. Evaluate result quality
    4. Refine and re-search if needed
    5. Synthesize comprehensive answer

    Cite sources and explain reasoning.
    """,
    tools=[rag_tool],
    agents=[query_planner],
)

root_agent = agentic_rag_agent
```

### Advanced Patterns

**1. Multi-Step Retrieval**

```python
instruction="""
For complex queries:
1. Break into sub-queries
2. Search each independently
3. Combine and deduplicate results
4. Synthesize coherent answer
"""
```

**2. Metadata Filtering**

```python
# Plan filters dynamically
{
    "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
    "category": "research",
    "author": "specific_team",
}
```

**3. Hybrid Search**

```python
instruction="""
Combine search strategies:
1. Keyword search for exact matches
2. Vector search for semantic similarity
3. Rerank combined results
4. Return top N
"""
```

### Advantages

- Intelligent query understanding
- Dynamic filter construction
- Multi-step reasoning
- Better result quality

### Limitations

- Higher latency (multi-agent)
- More complex to implement
- Higher LLM costs
- Requires careful prompt engineering

### Use Cases

1. **Complex Research Queries**
   - Multi-faceted information needs
   - Requires reasoning about search strategy

2. **Legal/Medical Document Search**
   - Precise filtering by jurisdiction, date, specialty
   - High accuracy requirements

3. **Enterprise Knowledge Bases**
   - Large corpora with rich metadata
   - Need for intelligent query refinement

## Grounding Best Practices

### 1. Combine Multiple Methods

```python
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.retrieval import VertexAiRagRetrieval

multi_grounded_agent = Agent(
    name="multi_grounded",
    model="gemini-2.5-flash",
    tools=[
        VertexAiRagRetrieval(...),  # Internal knowledge
        google_search,               # External knowledge
    ],
    instruction="""
    Search strategy:
    1. Check internal RAG first
    2. If insufficient, use Google Search
    3. Synthesize and cite all sources
    """,
)
```

### 2. Implement Source Attribution

```python
instruction="""
Always cite sources:
- RAG: Include document name and chunk
- Google Search: Include URL and snippet
- Database: Include table and timestamp
"""
```

### 3. Monitor Grounding Quality

```python
# Track metrics
metrics = {
    "retrieval_precision": 0.85,  # Relevant results / total results
    "answer_accuracy": 0.92,      # Validated correctness
    "source_coverage": 3.5,       # Avg unique sources per answer
}
```

### 4. Fallback Strategies

```python
instruction="""
If grounding fails:
1. Admit knowledge gap
2. Suggest alternative queries
3. Offer to search broader
4. Never hallucinate
"""
```

## Performance Optimization

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    """Cache frequent queries."""
    return rag_tool.search(query)
```

### Parallel Retrieval

```python
import asyncio

async def parallel_search(queries):
    """Search multiple sources in parallel."""
    tasks = [
        rag_search(q),
        google_search(q),
        db_search(q),
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### Batch Processing

```python
# Process multiple queries together
queries = ["query1", "query2", "query3"]
embeddings = embedding_model.get_embeddings(queries)
# Batch vector search
```

## Troubleshooting

### Low Retrieval Quality

1. Adjust `similarity_top_k` and `vector_distance_threshold`
2. Improve chunk size and overlap
3. Enhance query with context
4. Use hybrid search

### High Latency

1. Reduce `similarity_top_k`
2. Cache frequent queries
3. Use parallel retrieval
4. Optimize network

### High Costs

1. Use smaller `similarity_top_k`
2. Implement caching
3. Choose cost-effective models
4. Batch processing

## Related Resources

- **Vertex AI RAG Documentation**: https://cloud.google.com/vertex-ai/docs/rag
- **Vector Search 2.0 Guide**: https://cloud.google.com/vertex-ai/docs/vector-search
- **Agentic RAG Patterns**: @agentic-rag.md
- **Google Search Integration**: @google-search.md
