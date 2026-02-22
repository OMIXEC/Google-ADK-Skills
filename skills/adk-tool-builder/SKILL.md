---
name: ADK Tool Builder
description: This skill should be used when the user asks to "create a custom tool", "build a FunctionTool", "wrap a function as a tool", "create an AgentTool", "integrate MCP tools", "add a search tool", "create RAG retrieval tool", "build long-running tools", or "create ADK tools". Provides comprehensive patterns for creating all types of ADK tools with proper schema generation and integration.
version: 1.0.0
---

# ADK Tool Builder

Custom tools are the primary way agents interact with external systems, APIs, and services. The ADK provides multiple tool types for different use cases, from simple function wrappers to complex agent composition.

## Tool Type Overview

The ADK supports six main tool types:

| Tool Type | Use Case | Execution | Schema |
|-----------|----------|-----------|--------|
| **FunctionTool** | Wrap Python/TS/Java functions | Synchronous | Auto-generated from type hints |
| **LongRunningFunctionTool** | Background/async tasks | Asynchronous | Auto-generated from type hints |
| **AgentTool** | Agent composition/delegation | Agent execution | Defined by agent interface |
| **MCPToolset** | External MCP server integration | MCP protocol | Provided by MCP server |
| **GoogleSearchTool** | Web search (built-in) | Google Search API | Pre-defined |
| **VertexAiRagRetrieval** | RAG retrieval | Vertex AI RAG | Pre-defined |

## FunctionTool: Basic Tool Creation

The most common tool type - wraps a function to make it available to agents.

### Python FunctionTool

```python
from google.adk.tools import FunctionTool

def get_weather(city: str, units: str = "celsius") -> dict:
    """Get current weather for a city.

    Args:
        city: The city name to get weather for.
        units: Temperature units ('celsius' or 'fahrenheit').

    Returns:
        Weather information including temperature and conditions.
    """
    # Implementation (call weather API, etc.)
    return {
        "city": city,
        "temperature": 22,
        "units": units,
        "condition": "sunny",
        "humidity": 65
    }

# Create tool - schema auto-generated from type hints and docstring
weather_tool = FunctionTool(get_weather)

# Use with agent
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="weather_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool],
)
```

**Key Requirements:**
- Type hints on all parameters (required for schema generation)
- Comprehensive docstring (used in tool description)
- Return type must be `dict` (or serializable to JSON)
- Args section in docstring describes parameters for the LLM

### TypeScript FunctionTool

```typescript
import { FunctionTool } from '@google-labs/adk';
import { z } from 'zod';

// Define schema with Zod
const weatherSchema = z.object({
  city: z.string().describe('The city name to get weather for'),
  units: z.enum(['celsius', 'fahrenheit']).default('celsius').describe('Temperature units'),
});

// Function implementation
async function getWeather(params: z.infer<typeof weatherSchema>) {
  const { city, units } = params;

  // Implementation
  return {
    city,
    temperature: 22,
    units,
    condition: 'sunny',
    humidity: 65,
  };
}

// Create tool
const weatherTool = new FunctionTool({
  name: 'get_weather',
  description: 'Get current weather for a city',
  schema: weatherSchema,
  handler: getWeather,
});

// Use with agent
import { LlmAgent } from '@google-labs/adk';

const agent = new LlmAgent({
  name: 'weather_agent',
  model: 'gemini-2.0-flash-exp',
  tools: [weatherTool],
});
```

**TypeScript Specifics:**
- Use Zod for schema validation
- `.describe()` provides LLM-visible descriptions
- Handler receives validated parameters
- Async functions supported

### Java FunctionTool

```java
import com.google.adk.tools.FunctionTool;
import com.google.adk.tools.Schema;
import java.util.Map;

public class WeatherTool {

    @Schema(description = "Get current weather for a city")
    public Map<String, Object> getWeather(
        @Schema(description = "The city name to get weather for")
        String city,

        @Schema(description = "Temperature units", defaultValue = "celsius")
        String units
    ) {
        // Implementation
        return Map.of(
            "city", city,
            "temperature", 22,
            "units", units,
            "condition", "sunny",
            "humidity", 65
        );
    }

    // Create tool
    public FunctionTool createTool() {
        return new FunctionTool(this::getWeather);
    }
}
```

**Java Specifics:**
- Use `@Schema` annotations for descriptions
- Return type must be `Map<String, Object>` or POJO
- Method reference syntax for tool creation

## Advanced FunctionTool Patterns

### Error Handling

```python
from google.adk.tools import FunctionTool

def fetch_user_data(user_id: str) -> dict:
    """Fetch user data from database.

    Args:
        user_id: The unique user identifier.

    Returns:
        User data or error information.
    """
    try:
        # Database call
        user = database.get_user(user_id)
        return {
            "success": True,
            "user": user.to_dict(),
        }
    except UserNotFoundError:
        return {
            "success": False,
            "error": "User not found",
            "error_code": "USER_NOT_FOUND",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "error_code": "DB_ERROR",
        }

# Always return dict - never raise exceptions from tools
user_tool = FunctionTool(fetch_user_data)
```

**Best Practice:** Return structured errors as dict instead of raising exceptions. The agent can handle error responses gracefully.

### Multiple Parameters with Validation

```python
from typing import List, Optional

def search_products(
    query: str,
    category: str,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    limit: int = 10,
    tags: Optional[List[str]] = None,
) -> dict:
    """Search product catalog.

    Args:
        query: Search query string.
        category: Product category to filter by.
        price_min: Minimum price filter (optional).
        price_max: Maximum price filter (optional).
        limit: Maximum number of results to return (default: 10).
        tags: Optional list of tags to filter by.

    Returns:
        Search results with matching products.
    """
    # Validation
    if limit > 100:
        return {"error": "Limit cannot exceed 100"}

    if price_min and price_max and price_min > price_max:
        return {"error": "price_min cannot be greater than price_max"}

    # Search implementation
    results = catalog.search(
        query=query,
        category=category,
        price_range=(price_min, price_max),
        limit=limit,
        tags=tags or [],
    )

    return {
        "query": query,
        "count": len(results),
        "results": [r.to_dict() for r in results],
    }

search_tool = FunctionTool(search_products)
```

### Stateful Tools with Classes

```python
class DatabaseTool:
    """Tool with internal state."""

    def __init__(self, connection_string: str):
        self.db = Database(connection_string)
        self.query_count = 0

    def query_database(self, sql: str) -> dict:
        """Execute SQL query.

        Args:
            sql: The SQL query to execute.

        Returns:
            Query results.
        """
        self.query_count += 1

        try:
            results = self.db.execute(sql)
            return {
                "success": True,
                "rows": results,
                "query_number": self.query_count,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

# Create instance and tool
db_instance = DatabaseTool("postgresql://localhost/mydb")
db_tool = FunctionTool(db_instance.query_database)
```

## LongRunningFunctionTool: Async Operations

For operations that take significant time (API calls, file processing, etc.).

```python
import asyncio
from google.adk.tools import LongRunningFunctionTool

async def process_video(
    video_url: str,
    operations: List[str],
) -> dict:
    """Process video with specified operations.

    Args:
        video_url: URL of the video to process.
        operations: List of operations (e.g., ['transcribe', 'summarize']).

    Returns:
        Processing results for each operation.
    """
    results = {}

    # Download video (async)
    video_data = await download_video(video_url)

    # Process operations in parallel
    tasks = []
    for op in operations:
        if op == "transcribe":
            tasks.append(transcribe_video(video_data))
        elif op == "summarize":
            tasks.append(summarize_video(video_data))
        elif op == "extract_frames":
            tasks.append(extract_frames(video_data))

    # Wait for all operations
    completed = await asyncio.gather(*tasks)

    # Build results
    for op, result in zip(operations, completed):
        results[op] = result

    return {
        "video_url": video_url,
        "operations_completed": operations,
        "results": results,
        "duration_seconds": 45.2,
    }

# Create long-running tool
video_tool = LongRunningFunctionTool(process_video)

# Use with agent
agent = LlmAgent(
    name="video_processor",
    model="gemini-2.0-flash-exp",
    tools=[video_tool],
)
```

**When to use:**
- Network I/O operations
- File processing
- External API calls
- Database queries
- Any operation > 1 second

## AgentTool: Agent Composition

Enable one agent to delegate tasks to another agent.

```python
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, AgentTool

# Create specialized sub-agents
researcher_agent = LlmAgent(
    name="researcher",
    model="gemini-2.0-flash-exp",
    system_instruction="You are a research specialist. Find accurate information on requested topics.",
    tools=[web_search_tool, database_tool],
)

analyst_agent = LlmAgent(
    name="analyst",
    model="gemini-2.0-flash-exp",
    system_instruction="You are a data analyst. Analyze provided data and extract insights.",
    tools=[calculate_tool, visualize_tool],
)

# Wrap agents as tools
researcher_tool = AgentTool(researcher_agent)
analyst_tool = AgentTool(analyst_agent)

# Create orchestrator agent that uses sub-agents
orchestrator = LlmAgent(
    name="orchestrator",
    model="gemini-2.0-flash-exp",
    system_instruction="You coordinate research and analysis tasks. Delegate to specialists.",
    tools=[researcher_tool, analyst_tool],
)

# The orchestrator can now delegate:
# User: "Research Python trends and analyze the data"
# Orchestrator: Uses researcher_tool -> then analyst_tool -> synthesizes results
```

**Use Cases:**
- Task decomposition (split complex work)
- Specialization (domain experts)
- Separation of concerns
- Hierarchical agent systems

## MCPToolset: External Tool Integration

Integrate tools from MCP (Model Context Protocol) servers.

```python
from google.adk.tools import MCPToolset
from google.adk.agents import LlmAgent

# Connect to MCP server
mcp_toolset = MCPToolset(
    server_url="stdio://path/to/mcp-server",
    name="filesystem_tools",
)

# MCPToolset automatically discovers and wraps all tools from the server
agent = LlmAgent(
    name="file_agent",
    model="gemini-2.0-flash-exp",
    tools=[mcp_toolset],  # All MCP tools available
)

# Agent can now use any tool exposed by the MCP server
# Examples: read_file, write_file, list_directory, search_files
```

**MCP Server Examples:**

```python
# Filesystem MCP server
fs_tools = MCPToolset(
    server_url="stdio://mcp-server-filesystem",
    name="filesystem",
)

# Database MCP server
db_tools = MCPToolset(
    server_url="stdio://mcp-server-postgres",
    name="database",
    config={
        "connection_string": "postgresql://localhost/mydb",
    },
)

# Browser automation MCP server
browser_tools = MCPToolset(
    server_url="stdio://mcp-server-puppeteer",
    name="browser",
)

# Use all together
agent = LlmAgent(
    name="automation_agent",
    model="gemini-2.0-flash-exp",
    tools=[fs_tools, db_tools, browser_tools],
)
```

For more on MCP integration, see **adk-mcp-integration** skill.

## Built-in Tools

### GoogleSearchTool

```python
from google.adk.tools import GoogleSearchTool
from google.adk.agents import LlmAgent

# Create search tool (requires API key)
search_tool = GoogleSearchTool(
    api_key="YOUR_GOOGLE_SEARCH_API_KEY",
    search_engine_id="YOUR_SEARCH_ENGINE_ID",
    num_results=5,  # Results per query
)

agent = LlmAgent(
    name="search_agent",
    model="gemini-2.0-flash-exp",
    tools=[search_tool],
)

# Agent can now search the web
# User: "What are the latest AI developments?"
# Agent: Uses GoogleSearchTool -> summarizes findings
```

**Configuration:**
- `api_key`: Google Custom Search API key
- `search_engine_id`: Programmable Search Engine ID
- `num_results`: Number of results to return (default: 5)

### VertexAiRagRetrieval

```python
from google.adk.tools import VertexAiRagRetrieval
from google.adk.agents import LlmAgent

# Create RAG retrieval tool
rag_tool = VertexAiRagRetrieval(
    project_id="your-gcp-project",
    location="us-central1",
    rag_corpus_id="your-corpus-id",
    top_k=5,  # Number of chunks to retrieve
)

agent = LlmAgent(
    name="rag_agent",
    model="gemini-2.0-flash-exp",
    tools=[rag_tool],
    system_instruction="Answer questions using the knowledge base. Always cite sources.",
)

# Agent retrieves relevant context from RAG corpus before answering
```

For comprehensive RAG patterns, see **adk-pinecone-rag** skill.

## Schema Generation Best Practices

### Python: Type Hints and Docstrings

```python
from typing import List, Dict, Optional, Literal

def analyze_sentiment(
    text: str,
    language: Literal["en", "es", "fr", "de"] = "en",
    include_entities: bool = False,
) -> dict:
    """Analyze sentiment of text.

    Performs sentiment analysis and optionally extracts named entities.

    Args:
        text: The text to analyze (max 5000 characters).
        language: Language code (ISO 639-1). Supported: en, es, fr, de.
        include_entities: Whether to extract named entities (default: False).

    Returns:
        Sentiment analysis results with score, magnitude, and optional entities.
    """
    # Implementation
    return {
        "sentiment": "positive",
        "score": 0.8,
        "magnitude": 3.2,
        "entities": [...] if include_entities else [],
    }
```

**The LLM sees:**
- Function name: `analyze_sentiment`
- Description: First paragraph of docstring
- Parameters: From Args section with type constraints
- It understands: `language` must be one of 4 values, `text` is required, `include_entities` is optional

### TypeScript: Zod Schema

```typescript
import { z } from 'zod';
import { FunctionTool } from '@google-labs/adk';

const analyzeSentimentSchema = z.object({
  text: z.string()
    .max(5000)
    .describe('The text to analyze (max 5000 characters)'),
  language: z.enum(['en', 'es', 'fr', 'de'])
    .default('en')
    .describe('Language code (ISO 639-1)'),
  include_entities: z.boolean()
    .default(false)
    .describe('Whether to extract named entities'),
});

async function analyzeSentiment(params: z.infer<typeof analyzeSentimentSchema>) {
  // Implementation
  return {
    sentiment: 'positive',
    score: 0.8,
    magnitude: 3.2,
    entities: params.include_entities ? [...] : [],
  };
}

const tool = new FunctionTool({
  name: 'analyze_sentiment',
  description: 'Analyze sentiment of text with optional entity extraction',
  schema: analyzeSentimentSchema,
  handler: analyzeSentiment,
});
```

### Java: Annotations

```java
import com.google.adk.tools.Schema;

@Schema(description = "Analyze sentiment of text")
public Map<String, Object> analyzeSentiment(
    @Schema(description = "The text to analyze (max 5000 characters)")
    String text,

    @Schema(
        description = "Language code (ISO 639-1). Supported: en, es, fr, de",
        defaultValue = "en",
        allowedValues = {"en", "es", "fr", "de"}
    )
    String language,

    @Schema(description = "Whether to extract named entities", defaultValue = "false")
    boolean includeEntities
) {
    // Implementation
    return Map.of(
        "sentiment", "positive",
        "score", 0.8,
        "magnitude", 3.2,
        "entities", includeEntities ? Arrays.asList(...) : Collections.emptyList()
    );
}
```

## Tool Testing

Always test tools in isolation before integrating with agents:

```python
import pytest
from my_tools import get_weather, search_products

def test_get_weather_returns_dict():
    """Tool returns properly formatted dict."""
    result = get_weather("London", "celsius")

    assert isinstance(result, dict)
    assert "city" in result
    assert "temperature" in result
    assert result["city"] == "London"

def test_get_weather_handles_invalid_city():
    """Tool gracefully handles invalid input."""
    result = get_weather("InvalidCity123", "celsius")

    # Should return error dict, not raise exception
    assert isinstance(result, dict)
    assert "error" in result or "city" in result

def test_search_products_respects_limit():
    """Tool respects limit parameter."""
    result = search_products("laptop", "electronics", limit=5)

    assert len(result["results"]) <= 5

@pytest.mark.asyncio
async def test_long_running_tool():
    """Long-running tool completes successfully."""
    from my_tools import process_video

    result = await process_video(
        "https://example.com/video.mp4",
        operations=["transcribe"],
    )

    assert result["success"] == True
    assert "transcribe" in result["results"]
```

For comprehensive testing patterns, see **adk-agent-testing** skill.

## Quick Start

```bash
# Create a new tool
/adk:create-tool --name weather_lookup --type function

# Test tool standalone
python -c "from my_tools import weather_tool; print(weather_tool.invoke({'city': 'London'}))"

# Add tool to existing agent
# Edit agent.py to include tool in tools list

# Test with agent
adk run --input "What's the weather in Paris?"
```

## Common Patterns

### API Wrapper Tool

```python
import requests

def call_external_api(
    endpoint: str,
    method: str = "GET",
    params: Optional[dict] = None,
) -> dict:
    """Call external REST API.

    Args:
        endpoint: API endpoint path.
        method: HTTP method (GET, POST, PUT, DELETE).
        params: Optional query parameters or request body.

    Returns:
        API response data.
    """
    base_url = "https://api.example.com"

    try:
        response = requests.request(
            method=method,
            url=f"{base_url}/{endpoint}",
            json=params if method in ["POST", "PUT"] else None,
            params=params if method == "GET" else None,
            timeout=30,
        )
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "status_code": response.status_code,
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None),
        }

api_tool = FunctionTool(call_external_api)
```

### Database Query Tool

```python
from typing import List

def query_customers(
    filters: dict,
    limit: int = 10,
) -> dict:
    """Query customer database.

    Args:
        filters: Filter criteria (e.g., {"country": "US", "active": true}).
        limit: Maximum results to return.

    Returns:
        List of matching customers.
    """
    # Build safe query
    query = "SELECT * FROM customers WHERE "
    conditions = []
    params = []

    for key, value in filters.items():
        conditions.append(f"{key} = ?")
        params.append(value)

    query += " AND ".join(conditions)
    query += f" LIMIT {limit}"

    # Execute with parameterized query (safe from SQL injection)
    results = db.execute(query, params)

    return {
        "count": len(results),
        "customers": [dict(r) for r in results],
    }

customer_tool = FunctionTool(query_customers)
```

### File Processing Tool

```python
import os
from pathlib import Path

def process_file(
    file_path: str,
    operation: Literal["read", "summarize", "extract_metadata"],
) -> dict:
    """Process file with specified operation.

    Args:
        file_path: Path to the file to process.
        operation: Operation to perform.

    Returns:
        Processing results.
    """
    path = Path(file_path)

    # Security: Validate path
    if not path.exists():
        return {"error": "File not found"}

    if not path.is_file():
        return {"error": "Path is not a file"}

    # Check file size (limit to 10MB)
    if path.stat().st_size > 10 * 1024 * 1024:
        return {"error": "File too large (max 10MB)"}

    # Perform operation
    if operation == "read":
        content = path.read_text()
        return {"content": content, "size": len(content)}

    elif operation == "extract_metadata":
        return {
            "name": path.name,
            "extension": path.suffix,
            "size": path.stat().st_size,
            "modified": path.stat().st_mtime,
        }

    elif operation == "summarize":
        content = path.read_text()
        # Use LLM to summarize
        summary = summarize_text(content)
        return {"summary": summary, "original_size": len(content)}

file_tool = FunctionTool(process_file)
```

## Related Skills

- **adk-callback-patterns** - Intercept and modify tool execution
- **adk-mcp-integration** - Integrate external MCP tool servers
- **adk-agent-testing** - Test tools before agent integration
- **adk-multi-agent-orchestrator** - Use AgentTool for orchestration

## Next Steps

1. **Choose tool type** based on your use case
2. **Implement function** with proper type hints and error handling
3. **Create FunctionTool** wrapper
4. **Test tool standalone** before agent integration
5. **Add to agent** via `tools` parameter
6. **Test with agent** using `adk run` or `adk web`
