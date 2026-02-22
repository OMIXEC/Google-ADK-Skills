# ADK Tool Types Reference

This reference provides detailed specifications for all ADK tool types.

## Tool Type Comparison

| Feature | FunctionTool | LongRunningFunctionTool | AgentTool | MCPToolset |
|---------|--------------|------------------------|-----------|------------|
| **Execution** | Synchronous | Asynchronous | Agent delegation | MCP protocol |
| **Use Case** | Simple operations | I/O, API calls | Task delegation | External integration |
| **Timeout** | Default: 30s | Configurable | Agent timeout | MCP timeout |
| **Schema** | Auto-generated | Auto-generated | Agent-defined | MCP-provided |
| **State** | Stateless or stateful | Stateless or stateful | Agent state | MCP server state |
| **Error Handling** | Return dict | Return dict | Agent handles | MCP protocol |
| **Best For** | Calculations, simple queries | Network ops, file processing | Multi-agent systems | Third-party tools |

## FunctionTool Specification

### Python

```python
from google.adk.tools import FunctionTool
from typing import Dict, List, Optional, Any

# Signature
FunctionTool(
    func: Callable[..., Dict[str, Any]],
    name: Optional[str] = None,  # Defaults to function name
    description: Optional[str] = None,  # Defaults to docstring
)
```

**Requirements:**
- Function must have type hints on all parameters
- Function must return `dict`
- Docstring must include Args section
- Parameters with defaults are optional for LLM

**Schema Generation:**
- Type hints → JSON schema types
- Docstring first paragraph → tool description
- Args section → parameter descriptions
- Default values → optional parameters

### TypeScript

```typescript
import { FunctionTool } from '@google-labs/adk';
import { z } from 'zod';

new FunctionTool({
  name: string,
  description: string,
  schema: z.ZodObject,  // Zod schema
  handler: (params: T) => Promise<any> | any,
});
```

**Requirements:**
- Zod schema for parameter validation
- Handler receives validated params
- Handler can be sync or async

### Java

```java
import com.google.adk.tools.FunctionTool;

new FunctionTool(methodReference)
new FunctionTool(lambdaExpression)
```

**Requirements:**
- `@Schema` annotations on method and parameters
- Return type `Map<String, Object>` or serializable POJO
- Method must be public

## LongRunningFunctionTool Specification

### Python

```python
from google.adk.tools import LongRunningFunctionTool
import asyncio

# Signature
LongRunningFunctionTool(
    func: Callable[..., Awaitable[Dict[str, Any]]],
    name: Optional[str] = None,
    description: Optional[str] = None,
    timeout: int = 300,  # 5 minutes default
)
```

**Requirements:**
- Function must be `async def`
- Same schema requirements as FunctionTool
- Function should be cancellable (respect asyncio cancellation)

**Example:**

```python
import asyncio

async def fetch_large_dataset(
    query: str,
    max_results: int = 1000,
) -> dict:
    """Fetch large dataset from API.

    Args:
        query: Search query.
        max_results: Maximum results to fetch.

    Returns:
        Dataset with results.
    """
    results = []

    # Paginated fetching
    page = 1
    while len(results) < max_results:
        batch = await fetch_page(query, page)
        if not batch:
            break
        results.extend(batch)
        page += 1

        # Allow cancellation
        await asyncio.sleep(0)

    return {
        "query": query,
        "count": len(results),
        "results": results,
    }

dataset_tool = LongRunningFunctionTool(
    fetch_large_dataset,
    timeout=600,  # 10 minutes
)
```

### TypeScript

```typescript
import { LongRunningFunctionTool } from '@google-labs/adk';

new LongRunningFunctionTool({
  name: string,
  description: string,
  schema: z.ZodObject,
  handler: async (params: T) => any,
  timeout?: number,  // milliseconds
});
```

## AgentTool Specification

### Python

```python
from google.adk.tools import AgentTool
from google.adk.agents import LlmAgent

# Create specialized agent
specialist = LlmAgent(
    name="specialist",
    model="gemini-2.0-flash-exp",
    system_instruction="You are a specialist in X.",
    tools=[...],
)

# Wrap as tool
specialist_tool = AgentTool(
    agent=specialist,
    name="specialist_agent",  # Optional custom name
    description="Delegate tasks requiring expertise in X.",  # Optional
)

# Use in parent agent
parent = LlmAgent(
    name="parent",
    model="gemini-2.0-flash-exp",
    tools=[specialist_tool],
)
```

**Behavior:**
- Parent agent passes task description to specialist
- Specialist agent processes with its own tools
- Result returned to parent agent
- Specialist maintains its own conversation state

**Schema:**
- Parameters: `{"task": str}`
- Return: Agent's response as dict

### Multi-Level Delegation

```python
# Level 3: Executor agents
file_reader = LlmAgent(name="file_reader", tools=[read_tool])
web_scraper = LlmAgent(name="web_scraper", tools=[scrape_tool])

# Level 2: Coordinator agents
researcher = LlmAgent(
    name="researcher",
    tools=[AgentTool(file_reader), AgentTool(web_scraper)],
)

analyst = LlmAgent(
    name="analyst",
    tools=[calculate_tool, visualize_tool],
)

# Level 1: Orchestrator
orchestrator = LlmAgent(
    name="orchestrator",
    tools=[AgentTool(researcher), AgentTool(analyst)],
)
```

## MCPToolset Specification

### Python

```python
from google.adk.tools import MCPToolset

toolset = MCPToolset(
    server_url: str,  # "stdio://path" or "http://host:port"
    name: str,  # Toolset identifier
    config: Optional[dict] = None,  # Server-specific config
    timeout: int = 30,  # Request timeout
)
```

**Server URL Formats:**
- `stdio://path/to/server` - Stdio transport (local process)
- `http://host:port` - HTTP transport (remote server)
- `https://host:port` - HTTPS transport

**Example:**

```python
# Filesystem MCP server
fs_tools = MCPToolset(
    server_url="stdio:///usr/local/bin/mcp-server-filesystem",
    name="filesystem",
)

# Database MCP server with config
db_tools = MCPToolset(
    server_url="stdio:///usr/local/bin/mcp-server-postgres",
    name="database",
    config={
        "connection_string": "postgresql://localhost/mydb",
        "max_connections": 10,
    },
)

# Remote MCP server
remote_tools = MCPToolset(
    server_url="https://api.example.com/mcp",
    name="external_tools",
    timeout=60,
)

agent = LlmAgent(
    name="agent",
    model="gemini-2.0-flash-exp",
    tools=[fs_tools, db_tools, remote_tools],
)
```

**Tool Discovery:**
- MCPToolset automatically calls `tools/list` on server
- All discovered tools become available to agent
- Tool schemas provided by MCP server

### TypeScript

```typescript
import { MCPToolset } from '@google-labs/adk';

const toolset = new MCPToolset({
  serverUrl: string,
  name: string,
  config?: object,
  timeout?: number,
});
```

## Built-in Tools

### GoogleSearchTool

```python
from google.adk.tools import GoogleSearchTool

GoogleSearchTool(
    api_key: str,  # Google Custom Search API key
    search_engine_id: str,  # Programmable Search Engine ID
    num_results: int = 5,  # Results per query
    safe_search: bool = True,  # Enable safe search
    country: Optional[str] = None,  # Country code (e.g., "us")
    language: Optional[str] = None,  # Language code (e.g., "en")
)
```

**Setup:**
1. Get API key from Google Cloud Console
2. Create Programmable Search Engine at https://programmablesearchengine.google.com
3. Get Search Engine ID from control panel

**Usage:**

```python
search_tool = GoogleSearchTool(
    api_key=os.environ["GOOGLE_SEARCH_API_KEY"],
    search_engine_id=os.environ["SEARCH_ENGINE_ID"],
    num_results=10,
    safe_search=True,
)

agent = LlmAgent(
    name="search_agent",
    model="gemini-2.0-flash-exp",
    tools=[search_tool],
)
```

**Response Format:**

```python
{
    "query": "Python tutorials",
    "results": [
        {
            "title": "Learn Python - Tutorial",
            "link": "https://example.com/python",
            "snippet": "Comprehensive Python tutorial...",
        },
        # ... more results
    ],
    "search_metadata": {
        "total_results": "1,230,000",
        "search_time": 0.45,
    }
}
```

### VertexAiRagRetrieval

```python
from google.adk.tools import VertexAiRagRetrieval

VertexAiRagRetrieval(
    project_id: str,  # GCP project ID
    location: str,  # GCP region (e.g., "us-central1")
    rag_corpus_id: str,  # RAG corpus identifier
    top_k: int = 5,  # Number of chunks to retrieve
    similarity_threshold: float = 0.7,  # Minimum similarity score
)
```

**Setup:**
1. Create RAG corpus in Vertex AI
2. Upload documents to corpus
3. Get corpus ID from console

**Usage:**

```python
rag_tool = VertexAiRagRetrieval(
    project_id="my-gcp-project",
    location="us-central1",
    rag_corpus_id="projects/123/locations/us-central1/ragCorpora/456",
    top_k=5,
    similarity_threshold=0.7,
)

agent = LlmAgent(
    name="rag_agent",
    model="gemini-2.0-flash-exp",
    tools=[rag_tool],
    system_instruction="Answer using retrieved context. Always cite sources.",
)
```

**Response Format:**

```python
{
    "query": "What is ADK?",
    "chunks": [
        {
            "content": "The Agent Development Kit (ADK)...",
            "source": "docs/intro.md",
            "score": 0.92,
        },
        # ... more chunks
    ],
    "sources": ["docs/intro.md", "docs/getting-started.md"],
}
```

## Tool Return Value Requirements

All tools must return a dictionary (or object serializable to JSON).

### Good Return Values

```python
# Success with data
return {
    "success": True,
    "data": {...},
    "metadata": {...},
}

# Error with details
return {
    "success": False,
    "error": "User not found",
    "error_code": "USER_NOT_FOUND",
}

# Simple data
return {
    "temperature": 72,
    "condition": "sunny",
}

# List results
return {
    "count": 3,
    "results": [...],
}
```

### Bad Return Values

```python
# ❌ Returning None
return None

# ❌ Returning primitive
return "some string"
return 42
return True

# ❌ Raising exception (should return error dict instead)
raise ValueError("Invalid input")

# ❌ Returning complex objects
return MyCustomObject()  # Not JSON serializable
```

### Structured Error Returns

```python
def tool_function(param: str) -> dict:
    """Tool with proper error handling."""

    # Validation errors
    if not param:
        return {
            "success": False,
            "error": "Parameter 'param' is required",
            "error_type": "validation_error",
        }

    # Business logic errors
    try:
        result = do_something(param)
        if result is None:
            return {
                "success": False,
                "error": "Resource not found",
                "error_type": "not_found",
            }

        return {
            "success": True,
            "data": result,
        }

    # System errors
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "system_error",
        }
```

The agent can interpret these error structures and respond appropriately.

## Schema Best Practices

### Use Descriptive Parameter Names

```python
# Good
def search_products(category: str, price_max: float):
    ...

# Bad
def search_products(cat: str, max: float):
    ...
```

### Provide Detailed Descriptions

```python
def process_order(
    order_id: str,
    action: Literal["confirm", "cancel", "refund"],
) -> dict:
    """Process order action.

    Performs the specified action on an existing order.

    Args:
        order_id: The unique order identifier (format: ORD-XXXXXX).
        action: The action to perform:
            - confirm: Mark order as confirmed
            - cancel: Cancel the order (only if not shipped)
            - refund: Issue refund (requires manager approval)

    Returns:
        Order status after action, including updated state and timestamp.
    """
    ...
```

### Use Type Constraints

```python
from typing import Literal, List

# Enum-like constraints
def set_priority(
    priority: Literal["low", "medium", "high", "urgent"],
) -> dict:
    ...

# List types
def tag_items(
    item_ids: List[str],
    tags: List[str],
) -> dict:
    ...
```

### Provide Defaults When Appropriate

```python
def search(
    query: str,
    limit: int = 10,  # Sensible default
    include_metadata: bool = False,  # Optional feature
) -> dict:
    ...
```

## Tool Configuration Patterns

### Environment-based Configuration

```python
import os

class ConfiguredTool:
    """Tool with environment-based config."""

    def __init__(self):
        self.api_key = os.environ.get("API_KEY")
        self.base_url = os.environ.get("API_URL", "https://api.example.com")
        self.timeout = int(os.environ.get("TIMEOUT", "30"))

    def call_api(self, endpoint: str, params: dict) -> dict:
        """Call API endpoint.

        Args:
            endpoint: API endpoint path.
            params: Request parameters.

        Returns:
            API response.
        """
        # Use configured values
        url = f"{self.base_url}/{endpoint}"
        # ... implementation
        return result

# Create tool instance
tool_instance = ConfiguredTool()
api_tool = FunctionTool(tool_instance.call_api)
```

### Runtime Configuration

```python
def create_database_tool(connection_string: str):
    """Factory function for configured tool."""

    def query_database(sql: str) -> dict:
        """Execute SQL query.

        Args:
            sql: SQL query to execute.

        Returns:
            Query results.
        """
        db = connect(connection_string)  # Uses closure
        results = db.execute(sql)
        return {"rows": results}

    return FunctionTool(query_database)

# Create configured tool
db_tool = create_database_tool("postgresql://localhost/mydb")
```

## Related Documentation

- MCP Protocol: https://modelcontextprotocol.io
- Google Custom Search API: https://developers.google.com/custom-search
- Vertex AI RAG: https://cloud.google.com/vertex-ai/docs/rag
