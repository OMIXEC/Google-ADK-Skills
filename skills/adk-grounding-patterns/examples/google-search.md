# Google Search Integration Examples

Real-time web search grounding for Google ADK agents.

## Overview

The `google_search` tool enables agents to search the public web for current information. Use for news, weather, product research, and any real-time data.

## Basic Integration

### Simple Search Agent

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    description="Agent with web search capability",
    instruction="""
    You are a research assistant with web search.
    Always search for current information before answering.
    Cite sources with URLs.
    """,
    tools=[google_search],
)

root_agent = search_agent
```

### Example Interaction

```python
# User query
response = search_agent.run("What's the latest news on AI regulation?")

# Agent process:
# 1. Calls google_search("AI regulation news 2024")
# 2. Receives search results with URLs
# 3. Synthesizes answer with citations
```

## Use Cases

### 1. News Research Agent

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

news_agent = Agent(
    name="news_agent",
    model="gemini-2.5-flash",
    description="News research assistant",
    instruction="""
    You are a news research agent.

    When users ask about current events:
    1. Search for latest news articles
    2. Find multiple sources (minimum 3)
    3. Verify information across sources
    4. Summarize key points
    5. Cite all sources with URLs and dates

    Format:
    **Summary**: [2-3 sentence overview]

    **Key Points**:
    - Point 1 (Source: [URL])
    - Point 2 (Source: [URL])

    **Sources**:
    1. [Title] - [URL] - [Date]
    2. [Title] - [URL] - [Date]
    """,
    tools=[google_search],
)

root_agent = news_agent
```

**Example Query**: "What happened at the UN climate summit this week?"

### 2. Product Research Agent

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

product_agent = Agent(
    name="product_agent",
    model="gemini-2.5-flash",
    description="Product research assistant",
    instruction="""
    You help users research products before purchase.

    For each product:
    1. Search for reviews from multiple sources
    2. Find specifications and pricing
    3. Compare alternatives
    4. Identify pros and cons
    5. Provide purchase recommendations

    Always cite:
    - Review sources
    - Pricing sources (with date)
    - Specification sources
    """,
    tools=[google_search],
)

root_agent = product_agent
```

**Example Query**: "Compare Sony WH-1000XM5 vs Bose QuietComfort Ultra headphones"

### 3. Travel Planning Agent

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

travel_agent = Agent(
    name="travel_agent",
    model="gemini-2.5-flash",
    description="Travel planning assistant",
    instruction="""
    You help plan trips with current information.

    For each destination:
    1. Search current weather forecast
    2. Find top attractions and activities
    3. Search for travel advisories
    4. Find restaurant recommendations
    5. Provide transportation options

    Prioritize recent sources (last 3 months).
    """,
    tools=[google_search],
)

root_agent = travel_agent
```

**Example Query**: "Plan a 3-day trip to Tokyo in March"

### 4. Fact-Checking Agent

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

fact_checker = Agent(
    name="fact_checker",
    model="gemini-2.5-flash",
    description="Fact-checking assistant",
    instruction="""
    You verify factual claims using web search.

    For each claim:
    1. Search for authoritative sources
    2. Find multiple independent verifications
    3. Check publication dates (prefer recent)
    4. Assess source credibility
    5. Provide verdict: TRUE, FALSE, PARTIALLY TRUE, UNVERIFIED

    Format:
    **Claim**: [original claim]
    **Verdict**: [verdict]
    **Evidence**: [summary with sources]
    **Sources**: [list of URLs]
    """,
    tools=[google_search],
)

root_agent = fact_checker
```

**Example Query**: "Is it true that coffee reduces risk of heart disease?"

### 5. Financial Research Agent

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

finance_agent = Agent(
    name="finance_agent",
    model="gemini-2.5-flash",
    description="Financial research assistant",
    instruction="""
    You provide financial information using web search.

    For stocks/companies:
    1. Search latest stock price and trends
    2. Find recent news and announcements
    3. Search analyst ratings
    4. Find quarterly earnings reports
    5. Compare to competitors

    **Disclaimer**: Always include:
    "This is for informational purposes only. Not financial advice."

    Cite all sources with dates.
    """,
    tools=[google_search],
)

root_agent = finance_agent
```

**Example Query**: "What's the latest on Tesla stock and recent earnings?"

## Advanced Patterns

### Multi-Source Verification

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

verifier = Agent(
    name="verifier",
    model="gemini-2.5-flash",
    description="Multi-source verification agent",
    instruction="""
    You verify information across multiple sources.

    Process:
    1. Search for claim
    2. Collect sources (minimum 5)
    3. Categorize sources:
       - Primary sources (official, firsthand)
       - Secondary sources (news, analysis)
       - Tertiary sources (summaries, aggregators)
    4. Check consensus
    5. Note contradictions
    6. Assess confidence level

    Return:
    - Confidence: HIGH/MEDIUM/LOW
    - Consensus: [what most sources agree on]
    - Contradictions: [any conflicting information]
    - Sources: [categorized list]
    """,
    tools=[google_search],
)

root_agent = verifier
```

### Temporal Search (Time-Specific Queries)

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

temporal_agent = Agent(
    name="temporal_agent",
    model="gemini-2.5-flash",
    description="Time-aware search agent",
    instruction="""
    You search for information from specific time periods.

    For time-specific queries:
    1. Include date qualifiers in search:
       - "latest", "2024", "recent"
       - "historical", "archive", "past"
    2. Filter by publication date
    3. Note temporal context in citations

    Examples:
    - "COVID-19 news 2024" (recent)
    - "COVID-19 origins 2019-2020" (historical)
    - "COVID-19 vaccine development timeline" (chronological)
    """,
    tools=[google_search],
)

root_agent = temporal_agent
```

### Hybrid: Web Search + Internal RAG

Combine external web search with internal knowledge.

```python
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/my-project/locations/us-central1/ragCorpora/internal_docs"

# Internal RAG
rag_tool = VertexAiRagRetrieval(
    name="search_internal",
    description="Search internal documentation",
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
    similarity_top_k=10,
)

# Hybrid agent
hybrid_agent = Agent(
    name="hybrid_agent",
    model="gemini-2.5-flash",
    description="Hybrid search agent (internal + web)",
    instruction="""
    You have access to both internal docs and web search.

    Search strategy:
    1. **Try internal docs first** (search_internal)
       - Internal policies, procedures, proprietary info
       - Company-specific knowledge

    2. **Fall back to web search** (google_search)
       - External information not in internal docs
       - Current events, news
       - Public research and resources

    3. **Combine sources**
       - Synthesize internal and external info
       - Cite both types of sources clearly
       - Label: [Internal] or [Web]

    Never share proprietary information from internal docs externally.
    """,
    tools=[rag_tool, google_search],
)

root_agent = hybrid_agent
```

### Multi-Agent: Searcher + Synthesizer

Separate search and synthesis responsibilities.

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

# Searcher agent
searcher = Agent(
    name="searcher",
    model="gemini-2.5-flash",
    description="Web search specialist",
    instruction="""
    You search the web and return raw results.

    For each query:
    1. Perform comprehensive search
    2. Collect URLs, titles, snippets
    3. Return structured results (no synthesis)

    Format:
    {
        "results": [
            {"title": "...", "url": "...", "snippet": "...", "date": "..."},
            ...
        ]
    }
    """,
    tools=[google_search],
)

# Synthesizer agent
synthesizer = Agent(
    name="synthesizer",
    model="gemini-2.5-flash",
    description="Information synthesis specialist",
    instruction="""
    You synthesize search results into coherent answers.

    Given search results from searcher:
    1. Identify key themes
    2. Cross-reference information
    3. Resolve contradictions
    4. Create comprehensive summary
    5. Cite all sources

    Assess information quality and note any gaps.
    """,
)

# Orchestrator
search_orchestrator = Agent(
    name="search_orchestrator",
    model="gemini-2.5-flash",
    description="Search orchestration agent",
    instruction="""
    You coordinate web search and synthesis.

    Process:
    1. Ask searcher to find information
    2. Ask synthesizer to create answer from results
    3. Return synthesized answer to user
    """,
    agents=[searcher, synthesizer],
)

root_agent = search_orchestrator
```

## Best Practices

### 1. Always Cite Sources

```python
instruction="""
For every fact, cite the source:

Good:
"According to NASA (nasa.gov, 2024), the James Webb telescope..."

Bad:
"The James Webb telescope..." (no citation)
"""
```

### 2. Verify Information

```python
instruction="""
Search multiple sources and verify:
- Find at least 3 independent sources
- Check publication dates
- Assess source credibility
- Note any contradictions
"""
```

### 3. Handle Search Failures

```python
instruction="""
If search returns no results or low-quality results:
1. Admit limitation: "I couldn't find reliable information on..."
2. Suggest alternative queries
3. Offer to search broader/narrower
4. Never hallucinate or make up information
"""
```

### 4. Respect Recency

```python
instruction="""
For time-sensitive topics:
- Prioritize recent sources (last 6 months)
- Include date in every citation
- Flag outdated information
- Search for "latest" or "2024" explicitly
"""
```

### 5. Source Quality Assessment

```python
instruction="""
Assess source credibility:

High credibility:
- Official sources (.gov, .edu)
- Major news organizations
- Peer-reviewed publications
- Primary sources

Medium credibility:
- Reputable blogs/websites
- Industry publications
- Secondary sources

Low credibility:
- Unknown sources
- Heavily biased
- No author/date
- Tertiary aggregators

Note credibility in citations.
"""
```

## Rate Limiting and Error Handling

### Handling Rate Limits

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

rate_aware_agent = Agent(
    name="rate_aware_agent",
    model="gemini-2.5-flash",
    instruction="""
    You use web search efficiently.

    To avoid rate limits:
    1. Batch similar queries together
    2. Cache recent search results
    3. If rate limited, inform user and suggest retry later
    4. Don't retry failed searches immediately
    """,
    tools=[google_search],
)

root_agent = rate_aware_agent
```

### Error Handling

```python
instruction="""
Handle search errors gracefully:

1. **No results**: "I couldn't find information on [topic]. Try different keywords?"
2. **Rate limit**: "Search temporarily unavailable. Please try again in a moment."
3. **Network error**: "Connection issue. Let me try again..." (1 retry)
4. **Irrelevant results**: "Results weren't relevant. Let me refine the search..."
"""
```

## Performance Optimization

### 1. Targeted Queries

```python
# Good: Specific query
search_query = "Gemini 2.5 Flash API pricing 2024"

# Bad: Vague query
search_query = "Gemini pricing"
```

### 2. Query Refinement

```python
instruction="""
Refine queries for better results:

Original: "climate change"
Refined: "climate change impacts 2024 scientific consensus"

Original: "best laptop"
Refined: "laptop comparison 2024 MacBook vs ThinkPad review"
"""
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    """Cache search results."""
    return google_search(query)
```

## Testing Google Search Integration

```python
# Test cases
test_queries = [
    ("current news", "Should return recent articles"),
    ("historical event 1969", "Should return historical info"),
    ("product comparison 2024", "Should return recent reviews"),
    ("scientific study climate", "Should return research papers"),
]

for query, expected in test_queries:
    result = search_agent.run(query)
    print(f"Query: {query}")
    print(f"Expected: {expected}")
    print(f"Result: {result}\n")
```

## Complete Example: Research Assistant

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

research_assistant = Agent(
    name="research_assistant",
    model="gemini-2.5-flash",
    description="Comprehensive research assistant with web search",
    instruction="""
    You are a research assistant that helps users find and verify information.

    **Capabilities**:
    - Web search for current information
    - Multi-source verification
    - Fact-checking
    - Citation management

    **Process**:
    1. Understand user's information need
    2. Construct targeted search queries
    3. Search and collect sources (minimum 3)
    4. Verify information across sources
    5. Synthesize comprehensive answer
    6. Provide citations with URLs and dates

    **Output Format**:
    ## Summary
    [2-3 sentence overview]

    ## Key Findings
    1. [Finding 1] (Source: [URL], [Date])
    2. [Finding 2] (Source: [URL], [Date])
    3. [Finding 3] (Source: [URL], [Date])

    ## Sources
    1. [Title] - [URL] - [Date] - [Credibility: High/Medium/Low]
    2. [Title] - [URL] - [Date] - [Credibility: High/Medium/Low]

    ## Notes
    [Any contradictions, gaps, or limitations]

    **Guidelines**:
    - Prioritize authoritative sources (.gov, .edu, major publications)
    - Include publication dates
    - Note any contradictions between sources
    - Admit if information is limited or unavailable
    - Never hallucinate or make up information
    """,
    tools=[google_search],
)

root_agent = research_assistant
```

## Related Resources

- **Grounding Types Reference**: @grounding-types.md
- **Agentic RAG Patterns**: @agentic-rag.md
- **Multi-Agent Orchestrator**: ../../adk-multi-agent-orchestrator.md
- **Agent Testing**: ../../adk-agent-testing/SKILL.md
