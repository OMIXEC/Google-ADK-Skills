# Agentic RAG Examples

Advanced retrieval-augmented generation where agents reason about how to search.

## Overview

Traditional RAG: User query → Embedding → Vector search → Return chunks

Agentic RAG: User query → Agent analyzes intent → Plans search strategy → Constructs filters → Multi-step retrieval → Synthesizes answer

## Pattern 1: Query Planning Agent

Agent that analyzes user intent and constructs optimal search parameters.

### Implementation

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag
import json

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/product_docs"

# Step 1: Query Planner Agent
query_planner = Agent(
    name="query_planner",
    model="gemini-2.5-flash",
    description="Analyzes queries and plans search strategy",
    instruction="""
    You are a query planning expert.

    Analyze the user's query and create a search plan:

    1. **Intent Classification**
       - What is the user trying to accomplish?
       - Is this a factual lookup, comparison, troubleshooting, or exploration?

    2. **Concept Extraction**
       - Key entities, topics, and technical terms
       - Synonyms and related concepts

    3. **Metadata Filters**
       - Date ranges (if time-sensitive)
       - Categories (product, API, guide, reference)
       - Version numbers
       - Author/team

    4. **Search Strategy**
       - Single query or multi-step?
       - Broad exploration or narrow precision?
       - How many results needed?

    Return a JSON search plan:
    {
        "intent": "troubleshooting|lookup|comparison|exploration",
        "concepts": ["concept1", "concept2"],
        "synonyms": ["alt1", "alt2"],
        "filters": {
            "category": "api_docs",
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "version": "2.0"
        },
        "strategy": "multi_step|single_query",
        "top_k": 10,
        "distance_threshold": 0.3
    }
    """,
)

# Step 2: RAG Retrieval Tool
rag_tool = VertexAiRagRetrieval(
    name="search_docs",
    description="Search documentation with filters",
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
    similarity_top_k=10,
    vector_distance_threshold=0.3,
)

# Step 3: Orchestrator Agent
agentic_rag = Agent(
    name="agentic_rag",
    model="gemini-2.5-flash",
    description="Intelligent search orchestrator",
    instruction="""
    You are an intelligent search agent that uses agentic RAG.

    For each user query:

    1. **Plan**: Ask query_planner to analyze the query and create a search plan
    2. **Execute**: Use search_docs with the planned parameters
    3. **Evaluate**: Check if results are sufficient
    4. **Refine**: If needed, adjust strategy and search again
    5. **Synthesize**: Combine results into comprehensive answer

    **Multi-Step Strategy**:
    - Break complex queries into sub-queries
    - Search each independently
    - Deduplicate and rank results
    - Synthesize coherent answer

    **Always**:
    - Cite specific documents and sections
    - Explain your search reasoning
    - Admit if information is insufficient
    """,
    tools=[rag_tool],
    agents=[query_planner],
)

root_agent = agentic_rag
```

### Example Interaction

```
User: How do I implement authentication in the API, and what changed in version 2.0?

Agent (internal reasoning):
1. Ask query_planner to analyze
   → Intent: comparison (v1.x vs v2.0 auth)
   → Concepts: ["authentication", "API", "version 2.0"]
   → Filters: category="api_docs", version="2.0"
   → Strategy: multi_step (search v1.x, then v2.0, then compare)

2. Execute multi-step search:
   Step 1: Search "authentication API version 1.x"
   Step 2: Search "authentication API version 2.0"
   Step 3: Search "authentication migration guide"

3. Synthesize answer with citations
```

## Pattern 2: Dynamic Metadata Filtering

Agent constructs metadata filters based on query intent.

### Implementation

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/research_papers"

filter_agent = Agent(
    name="filter_constructor",
    model="gemini-2.5-flash",
    description="Constructs optimal metadata filters",
    instruction="""
    You construct metadata filters for document search.

    Analyze the query and determine:

    1. **Temporal Filters**
       - Recent papers (last 1-2 years)
       - Historical context (specific year or range)
       - No temporal constraint

    2. **Category Filters**
       - Research area (ML, NLP, Vision, etc.)
       - Paper type (survey, empirical, theoretical)
       - Venue (conference, journal)

    3. **Author Filters**
       - Specific authors or institutions
       - Exclude certain sources

    4. **Quality Filters**
       - Citation count threshold
       - Peer review status

    Return JSON:
    {
        "temporal": {"start": "2023-01-01", "end": "2024-12-31"},
        "category": "machine_learning",
        "subcategory": "large_language_models",
        "venue": ["NeurIPS", "ICML", "ACL"],
        "min_citations": 50
    }
    """,
)

rag_tool = VertexAiRagRetrieval(
    name="search_papers",
    description="Search research papers with filters",
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
    similarity_top_k=20,
    vector_distance_threshold=0.25,
)

research_agent = Agent(
    name="research_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a research assistant with intelligent filtering.

    For each query:
    1. Ask filter_constructor to build optimal filters
    2. Search papers with those filters
    3. Rank by relevance and quality
    4. Summarize key findings with citations
    """,
    tools=[rag_tool],
    agents=[filter_agent],
)

root_agent = research_agent
```

## Pattern 3: Multi-Step Retrieval

Break complex queries into sequential search steps.

### Implementation

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/legal_docs"

decomposer = Agent(
    name="query_decomposer",
    model="gemini-2.5-flash",
    description="Decomposes complex queries into sub-queries",
    instruction="""
    You decompose complex queries into searchable sub-queries.

    For each query, create a sequence of searches:

    Example:
    Query: "What are the tax implications of forming an LLC in California vs Delaware?"

    Decomposition:
    {
        "sub_queries": [
            "LLC formation requirements California",
            "LLC tax obligations California",
            "LLC formation requirements Delaware",
            "LLC tax obligations Delaware",
            "California vs Delaware LLC comparison"
        ],
        "synthesis_strategy": "compare_and_contrast"
    }

    Return JSON with sub_queries array and synthesis_strategy.
    """,
)

rag_tool = VertexAiRagRetrieval(
    name="search_legal",
    description="Search legal documents",
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
    similarity_top_k=5,
)

legal_agent = Agent(
    name="legal_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a legal research assistant.

    For complex queries:
    1. Ask query_decomposer to break down into sub-queries
    2. Execute each sub-query sequentially
    3. Track results from each step
    4. Synthesize comprehensive answer
    5. Cite specific statutes and cases

    **Important**: Legal information requires precision. Always cite sources.
    """,
    tools=[rag_tool],
    agents=[decomposer],
)

root_agent = legal_agent
```

## Pattern 4: Hybrid Search with Reranking

Combine keyword and semantic search, then rerank.

### Implementation

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/code_docs"

# Semantic search
semantic_search = VertexAiRagRetrieval(
    name="semantic_search",
    description="Semantic similarity search",
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
    similarity_top_k=20,
    vector_distance_threshold=0.4,
)

reranker = Agent(
    name="reranker",
    model="gemini-2.5-flash",
    description="Reranks search results by relevance",
    instruction="""
    You rerank search results for optimal relevance.

    Given search results, rerank based on:
    1. Query-result semantic match
    2. Recency (prefer recent docs)
    3. Authority (official docs > community)
    4. Completeness (full examples > fragments)

    Return top 5 results with reasoning.
    """,
)

hybrid_agent = Agent(
    name="hybrid_search_agent",
    model="gemini-2.5-flash",
    instruction="""
    You perform hybrid search with reranking.

    Steps:
    1. Execute semantic_search (broad retrieval)
    2. Ask reranker to select top 5 most relevant
    3. Synthesize answer from reranked results
    4. Cite sources
    """,
    tools=[semantic_search],
    agents=[reranker],
)

root_agent = hybrid_agent
```

## Pattern 5: Iterative Refinement

Search, evaluate, refine, and search again if needed.

### Implementation

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/medical_literature"

rag_tool = VertexAiRagRetrieval(
    name="search_medical",
    description="Search medical literature",
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
    similarity_top_k=10,
)

evaluator = Agent(
    name="result_evaluator",
    model="gemini-2.5-flash",
    description="Evaluates search result quality",
    instruction="""
    You evaluate search results for quality and completeness.

    For each result set, assess:
    1. **Relevance**: Do results match query intent?
    2. **Completeness**: Is information sufficient?
    3. **Quality**: Are sources authoritative?
    4. **Gaps**: What's missing?

    Return JSON:
    {
        "quality_score": 0.85,
        "is_sufficient": true,
        "gaps": ["missing recent studies", "no meta-analysis"],
        "refinement_suggestions": [
            "broaden date range",
            "add synonym 'cardiovascular'",
            "search meta-analyses specifically"
        ]
    }
    """,
)

iterative_agent = Agent(
    name="iterative_search",
    model="gemini-2.5-flash",
    instruction="""
    You perform iterative search refinement.

    Process (max 3 iterations):
    1. Execute initial search
    2. Ask result_evaluator to assess quality
    3. If insufficient:
       - Apply refinement suggestions
       - Search again with adjusted parameters
    4. If sufficient or max iterations reached:
       - Synthesize answer from best results

    Track all iterations and explain refinement reasoning.
    """,
    tools=[rag_tool],
    agents=[evaluator],
)

root_agent = iterative_agent
```

## Best Practices

### 1. Balance Agent Calls with Performance

Agentic RAG uses multiple agent calls, increasing latency and cost.

**Good**: 2-3 agent hops for complex queries
```
User → Query Planner → RAG Search → Synthesizer
```

**Avoid**: Excessive nesting
```
User → Analyzer → Planner → Filter Builder → Searcher → Reranker → Evaluator → Refiner → Synthesizer
```

### 2. Cache Agent Decisions

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query_plan(query: str):
    """Cache query plans for similar queries."""
    return query_planner.run(query)
```

### 3. Implement Fallbacks

```python
instruction="""
If multi-step retrieval fails:
1. Fall back to simple vector search
2. Broaden search parameters
3. Admit information gap if still insufficient
"""
```

### 4. Monitor Costs

Track LLM calls per query:
- Simple RAG: 1 call (user query)
- Agentic RAG: 3-5 calls (planner + searcher + synthesizer)

### 5. Test Search Quality

```python
# Test cases
test_queries = [
    "How do I authenticate API requests?",
    "Compare v1 vs v2 authentication",
    "What changed in auth between versions?",
]

for query in test_queries:
    result = agentic_rag.run(query)
    # Evaluate precision, recall, answer quality
```

## Performance Comparison

| Pattern | Latency | Cost | Quality | Complexity |
|---------|---------|------|---------|------------|
| Simple RAG | Low | Low | Medium | Low |
| Query Planning | Medium | Medium | High | Medium |
| Multi-Step | High | Medium | High | Medium |
| Iterative Refinement | High | High | Very High | High |
| Hybrid + Reranking | Medium | Medium | High | Medium |

## When to Use Agentic RAG

**Use agentic RAG when:**
- Queries are complex and multi-faceted
- High accuracy is critical (legal, medical, financial)
- Large knowledge bases with rich metadata
- Users need comprehensive, well-sourced answers

**Use simple RAG when:**
- Queries are straightforward
- Latency is critical
- Cost optimization is priority
- Knowledge base is small/homogeneous

## Complete Example: Technical Documentation Assistant

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/tech_docs"

# Component agents
query_planner = Agent(
    name="query_planner",
    model="gemini-2.5-flash",
    description="Plans search strategy for technical queries",
    instruction="Analyze query, extract concepts, plan filters and search steps.",
)

filter_builder = Agent(
    name="filter_builder",
    model="gemini-2.5-flash",
    description="Constructs metadata filters",
    instruction="Build filters for: version, category, date range, API vs guide vs reference.",
)

rag_tool = VertexAiRagRetrieval(
    name="search_docs",
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
    similarity_top_k=15,
)

# Main agent
tech_docs_agent = Agent(
    name="tech_docs_assistant",
    model="gemini-2.5-flash",
    description="Technical documentation assistant with agentic RAG",
    instruction="""
    You are a technical documentation assistant.

    For each query:
    1. Ask query_planner to analyze intent
    2. Ask filter_builder to construct metadata filters
    3. Search docs with planned parameters
    4. Evaluate result quality
    5. Refine if needed (max 2 iterations)
    6. Synthesize answer with code examples and citations

    Always cite:
    - Document name
    - Section/page
    - Version number
    - Last updated date
    """,
    tools=[rag_tool],
    agents=[query_planner, filter_builder],
)

root_agent = tech_docs_agent
```

## Related Resources

- **Grounding Types Reference**: @grounding-types.md
- **Google Search Integration**: @google-search.md
- **ADK Multi-Agent Patterns**: ../../adk-multi-agent-orchestrator.md
