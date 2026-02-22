---
name: adk-grounding-patterns
description: Ground ADK agents with real-time data using Google Search, Vertex AI RAG, Vector Search 2.0, and agentic RAG patterns. Actions include google-search (web grounding), rag-engine (document retrieval), vector-search (semantic similarity), custom-source (API/database integration), and agentic-rag (dynamic query construction). Use for fact-checking, current events, knowledge-based systems, and hybrid search applications.
version: 1.0.0
---

# adk-grounding-patterns

**Grounding Strategies for Accurate ADK Agents**

Ground ADK agents with authoritative data sources to ensure factual accuracy and reduce hallucinations. Supports Google Search, Vertex AI RAG, Vector Search, custom data sources, and agentic RAG patterns.

## When to Use

Use this skill when:
- Agent needs real-time information (news, weather, stocks)
- Fact-checking is critical (legal, medical, financial)
- Connecting to knowledge bases (documentation, research)
- Building retrieval-augmented generation (RAG) systems
- Implementing semantic search across embeddings
- Dynamic query construction based on user intent

## Quick Start

```bash
# Google Search grounding
/adk-grounding-patterns --action "google-search" --agent "research_agent"

# RAG Engine grounding
/adk-grounding-patterns --action "rag-engine" --corpus_id "corpus_123" --agent "support_agent"

# Agentic RAG with dynamic queries
/adk-grounding-patterns --action "agentic-rag" --corpus_id "corpus_123" --agent "smart_search"
```

## Parameters

```bash
--action "google-search|rag-engine|vector-search|custom-source|agentic-rag"  # Grounding method
--agent "agent_name"                  # Target agent
--corpus_id "corpus_id"               # RAG corpus (for rag-engine, agentic-rag)
--similarity_top_k 10                 # Number of results (default: 10)
--distance_threshold 0.3              # Similarity threshold (default: 0.3)
--data_source "url_or_path"           # Custom data source
--enable_dynamic_filters true         # Enable metadata filtering (agentic-rag)
```

## Grounding Methods

### 1. Google Search Grounding

Real-time web search for current information.

**Use cases:**
- Current events and news
- Product information
- Weather and location data
- Recent research findings

**Example:**
```bash
/adk-grounding-patterns --action "google-search" --agent "news_agent"
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools import google_search

news_agent = Agent(
    name="news_agent",
    model="gemini-2.5-flash",
    description="Agent with real-time web search",
    instruction="""
    You are a news research agent.
    Always search for current information using google_search.
    Cite sources with URLs.
    Verify information across multiple sources.
    """,
    tools=[google_search],
)

root_agent = news_agent
```

### 2. Vertex AI RAG Engine

Document retrieval from managed RAG corpora.

**Use cases:**
- Internal documentation
- Product knowledge bases
- Research paper collections
- Policy and compliance documents

**Example:**
```bash
/adk-grounding-patterns --action "rag-engine" \
  --corpus_id "projects/my-project/locations/us-central1/ragCorpora/123" \
  --agent "docs_agent" \
  --similarity_top_k 10
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/123"

docs_agent = Agent(
    name="docs_agent",
    model="gemini-2.5-flash",
    description="Documentation assistant with RAG",
    instruction="""
    You are a documentation assistant.
    Search the knowledge base for accurate information.
    Always cite document sections and page numbers.
    If unsure, admit knowledge limitations.
    """,
    tools=[
        VertexAiRagRetrieval(
            name="search_docs",
            description="Search documentation corpus",
            rag_resources=[
                rag.RagResource(rag_corpus=RAG_CORPUS)
            ],
            similarity_top_k=10,
            vector_distance_threshold=0.3,
        ),
    ],
)

root_agent = docs_agent
```

### 3. Vector Search 2.0

Semantic similarity search across embeddings.

**Use cases:**
- Semantic document search
- Similar product recommendations
- Code similarity detection
- Image/multimodal search

**Example:**
```bash
/adk-grounding-patterns --action "vector-search" \
  --data_source "vector_index_endpoint" \
  --agent "similarity_agent"
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.cloud import aiplatform
from typing import List, Dict

# Vector Search setup
aiplatform.init(project="my-project", location="us-central1")
index_endpoint = aiplatform.MatchingEngineIndexEndpoint("endpoint_id")

def vector_search_tool(query: str, top_k: int = 10) -> List[Dict]:
    """Semantic similarity search using Vector Search 2.0."""
    # Generate query embedding
    from vertexai.language_models import TextEmbeddingModel
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
    query_embedding = embedding_model.get_embeddings([query])[0].values

    # Search index
    response = index_endpoint.find_neighbors(
        deployed_index_id="deployed_index_id",
        queries=[query_embedding],
        num_neighbors=top_k,
    )

    return [{"id": n.id, "distance": n.distance} for n in response[0]]

similarity_agent = Agent(
    name="similarity_agent",
    model="gemini-2.5-flash",
    tools=[vector_search_tool],
)

root_agent = similarity_agent
```

### 4. Custom Data Sources

Integration with databases, APIs, and file systems.

**Use cases:**
- Database queries
- REST API integration
- File system access
- Custom business logic

**Example:**
```bash
/adk-grounding-patterns --action "custom-source" \
  --data_source "postgresql://localhost/mydb" \
  --agent "data_agent"
```

**Generated Code:**
```python
from google.adk.agents import Agent
import psycopg2

def database_search(query: str) -> str:
    """Search PostgreSQL database."""
    conn = psycopg2.connect("postgresql://localhost/mydb")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE content ILIKE %s LIMIT 10", (f"%{query}%",))
    results = cursor.fetchall()
    conn.close()
    return str(results)

data_agent = Agent(
    name="data_agent",
    model="gemini-2.5-flash",
    tools=[database_search],
)

root_agent = data_agent
```

### 5. Agentic RAG (Advanced)

Agents that reason about how to search - dynamic query construction, metadata filtering, and hybrid search.

**Use cases:**
- Complex information retrieval
- Multi-faceted document search
- Intent-based query refinement
- Hybrid keyword + semantic search

**Example:**
```bash
/adk-grounding-patterns --action "agentic-rag" \
  --corpus_id "projects/my-project/locations/us-central1/ragCorpora/123" \
  --agent "smart_search" \
  --enable_dynamic_filters true
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag
from typing import Dict, List

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/123"

# Agentic RAG: Agent decides HOW to search
query_planner = Agent(
    name="query_planner",
    model="gemini-2.5-flash",
    description="Plans optimal search strategy",
    instruction="""
    You are a query planning agent.

    Analyze user intent and construct optimal search parameters:
    1. Identify key concepts and entities
    2. Determine required metadata filters (date, category, author)
    3. Decide between broad vs narrow search
    4. Plan multi-step retrieval if needed

    Return structured search plan as JSON.
    """,
)

# RAG retrieval with dynamic filtering
rag_tool = VertexAiRagRetrieval(
    name="search_with_filters",
    description="Search with dynamic metadata filters",
    rag_resources=[
        rag.RagResource(rag_corpus=RAG_CORPUS)
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.3,
)

# Main agent coordinates search
smart_search = Agent(
    name="smart_search",
    model="gemini-2.5-flash",
    description="Intelligent search orchestrator",
    instruction="""
    You are an intelligent search agent.

    For each query:
    1. Ask query_planner to analyze intent
    2. Use search_with_filters with planned parameters
    3. Rank and synthesize results
    4. Identify gaps and refine search if needed

    Provide comprehensive, well-sourced answers.
    """,
    tools=[rag_tool],
    agents=[query_planner],
)

root_agent = smart_search
```

## Grounding Configuration

### RAG Retrieval Tuning

```python
VertexAiRagRetrieval(
    name="search_docs",
    rag_resources=[rag.RagResource(rag_corpus=CORPUS)],

    # Number of chunks to retrieve
    similarity_top_k=10,

    # Minimum similarity (0.0 - 1.0, lower = more similar)
    vector_distance_threshold=0.3,
)
```

### Hybrid Search (Keyword + Semantic)

```python
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

# Enable hybrid search
rag_tool = VertexAiRagRetrieval(
    name="hybrid_search",
    description="Hybrid keyword and semantic search",
    rag_resources=[
        rag.RagResource(
            rag_corpus=CORPUS,
            # Hybrid search weights keyword + vector
        )
    ],
    similarity_top_k=20,  # More results for reranking
)
```

## Integration with MCP Servers

Combine with Model Context Protocol for enhanced grounding:

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from google.adk.tools import mcp_tool

# Vertex AI RAG
rag_tool = VertexAiRagRetrieval(
    name="search_vertex_rag",
    rag_resources=[rag.RagResource(rag_corpus=CORPUS)],
    similarity_top_k=10,
)

# Pinecone MCP server
pinecone_tool = mcp_tool(
    server="uvx",
    args=["mcp-server-pinecone"],
    tool_name="query_pinecone",
)

# Chroma MCP server
chroma_tool = mcp_tool(
    server="uvx",
    args=["mcp-server-chroma"],
    tool_name="search_chroma",
)

multi_source_agent = Agent(
    name="multi_source_agent",
    model="gemini-2.5-flash",
    tools=[rag_tool, pinecone_tool, chroma_tool],
    instruction="""
    Search multiple knowledge bases:
    1. Vertex AI RAG for primary docs
    2. Pinecone for vector embeddings
    3. Chroma for local knowledge

    Synthesize results from all sources.
    """,
)

root_agent = multi_source_agent
```

## Best Practices

### 1. Choose the Right Grounding Method

| Method | Best For | Latency | Cost |
|--------|----------|---------|------|
| Google Search | Current events | Medium | Low |
| RAG Engine | Internal docs | Low | Medium |
| Vector Search | Semantic similarity | Low | Medium |
| Custom Source | Business data | Varies | Low |
| Agentic RAG | Complex queries | Medium | High |

### 2. Optimize Retrieval Parameters

```python
# Precise retrieval (fewer, higher quality)
similarity_top_k=5
vector_distance_threshold=0.2

# Broad retrieval (more coverage)
similarity_top_k=20
vector_distance_threshold=0.5
```

### 3. Implement Fallback Strategies

```python
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.retrieval import VertexAiRagRetrieval

fallback_agent = Agent(
    name="fallback_agent",
    model="gemini-2.5-flash",
    tools=[
        VertexAiRagRetrieval(...),  # Primary: Internal RAG
        google_search,               # Fallback: Web search
    ],
    instruction="""
    Search strategy:
    1. Try internal RAG first
    2. If no good results, use Google Search
    3. Combine and cite all sources
    """,
)
```

### 4. Monitor Grounding Quality

Track metrics:
- Retrieval precision (relevant results / total results)
- Answer accuracy (validated against ground truth)
- Source coverage (unique sources cited)
- User feedback (helpful/not helpful)

## Generated Project Structure

```
grounded-agent/
+-- src/
|   +-- agent.py              # Agent with grounding
|   +-- grounding_config.py   # Grounding setup
|   +-- config.py
+-- scripts/
|   +-- test_grounding.py     # Test retrieval
|   +-- evaluate_quality.py   # Quality metrics
+-- deployment/
+-- README.md
```

## Examples

### Example 1: Research Assistant

```bash
$ /adk-grounding-patterns --action "agentic-rag" \
    --corpus_id "research_papers" \
    --agent "research_assistant" \
    --enable_dynamic_filters true

Agentic RAG Agent Created
Agent: research_assistant
Corpus: research_papers
Features: Dynamic query planning, metadata filtering
```

### Example 2: Multi-Source News Agent

```bash
$ /adk-grounding-patterns --action "google-search" --agent "news_agent"

Google Search Grounding Enabled
Agent: news_agent
Tools: google_search
Real-time web search active
```

## Related Skills

- **adk-rag-builder** - Create and manage RAG corpora
- **adk-mcp-integration** - Add MCP tools (Pinecone, Chroma, Qdrant)
- **adk-agent-testing** - Test grounding accuracy
- **adk-deployment-manager** - Deploy grounded agents

## Reference Files

For comprehensive implementation details:
- @grounding-types.md - Detailed grounding method comparison
- @agentic-rag.md - Advanced agentic RAG patterns
- @google-search.md - Google Search integration examples
