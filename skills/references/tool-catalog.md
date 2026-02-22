# ADK Tool Catalog

Comprehensive catalog of FunctionTool and MCPToolset patterns for Google ADK agents.

## FunctionTool Patterns

### Basic FunctionTool

```python
from google.adk.tools import FunctionTool

def search_database(query: str, limit: int = 10) -> list:
    """Search database for matching records.

    Args:
        query: Search query string
        limit: Maximum results to return

    Returns:
        List of matching records
    """
    # Implementation
    results = db.search(query, limit=limit)
    return results

agent = Agent(
    name="agent",
    tools=[FunctionTool(search_database)],
)
```

**Key Points:**
- Docstring is used by model to understand tool purpose
- Type hints guide model on parameter types
- Return structured data (dicts, lists) for easy parsing

### Tool with Error Handling

```python
def safe_api_call(endpoint: str, params: dict = None) -> dict:
    """Make API call with error handling.

    Args:
        endpoint: API endpoint path
        params: Optional query parameters

    Returns:
        Dict with 'success' (bool), 'data' or 'error' fields
    """
    try:
        response = requests.get(f"https://api.example.com/{endpoint}", params=params)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
```

### Tool with Validation

```python
from pydantic import BaseModel, validator

class SearchParams(BaseModel):
    query: str
    limit: int = 10

    @validator('limit')
    def limit_range(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v

def validated_search(query: str, limit: int = 10) -> dict:
    """Search with input validation."""
    params = SearchParams(query=query, limit=limit)
    results = db.search(params.query, limit=params.limit)
    return {"results": results, "count": len(results)}
```

## Domain-Specific Tool Collections

### Customer Service Tools

```python
def search_faq(query: str) -> list:
    """Search FAQ knowledge base."""
    return kb.search(query, category="faq")

def create_ticket(
    title: str,
    description: str,
    priority: str = "medium"
) -> dict:
    """Create support ticket.

    Args:
        title: Ticket title
        description: Detailed description
        priority: low|medium|high|critical

    Returns:
        Ticket details with ticket_id
    """
    ticket = support_system.create_ticket(
        title=title,
        description=description,
        priority=priority,
    )
    return {"ticket_id": ticket.id, "status": "created"}

def get_order_status(order_id: str) -> dict:
    """Get order status by ID."""
    order = orders_db.get(order_id)
    return {
        "order_id": order.id,
        "status": order.status,
        "tracking": order.tracking_number,
    }

# Agent with customer service tools
agent = Agent(
    name="customer_service",
    tools=[
        FunctionTool(search_faq),
        FunctionTool(create_ticket),
        FunctionTool(get_order_status),
    ],
)
```

### Research Tools

```python
def web_search(query: str, num_results: int = 10) -> list:
    """Search web for information."""
    results = search_engine.search(query, num_results=num_results)
    return [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]

def academic_search(query: str, sources: list = None) -> list:
    """Search academic papers.

    Args:
        query: Search query
        sources: Optional list of sources (arxiv, pubmed, scholar)

    Returns:
        List of academic papers with citations
    """
    sources = sources or ["arxiv", "scholar"]
    papers = academic_db.search(query, sources=sources)
    return papers

def summarize_content(text: str, max_words: int = 200) -> str:
    """Summarize long text content."""
    summary = summarizer.summarize(text, max_words=max_words)
    return summary

def extract_key_points(text: str) -> list:
    """Extract key points from text."""
    points = nlp.extract_key_points(text)
    return points
```

### Vision/Image Tools

```python
def process_image(image_url: str) -> dict:
    """Process and analyze image.

    Args:
        image_url: URL or path to image

    Returns:
        Image analysis with detected objects, colors, text
    """
    image = load_image(image_url)
    analysis = {
        "objects": detect_objects(image),
        "colors": extract_colors(image),
        "text": ocr_extract(image),
        "dimensions": image.size,
    }
    return analysis

def detect_pose(image_url: str) -> dict:
    """Detect human pose/joints in image."""
    image = load_image(image_url)
    pose = pose_detector.detect(image)
    return {
        "keypoints": pose.keypoints,
        "confidence": pose.confidence,
        "detected_poses": len(pose.people),
    }

def analyze_form(exercise: str, image_url: str) -> dict:
    """Analyze exercise form from image.

    Args:
        exercise: Exercise type (squat, deadlift, etc.)
        image_url: Image showing exercise

    Returns:
        Form analysis with corrections
    """
    pose = detect_pose(image_url)
    analysis = form_analyzer.analyze(exercise, pose)
    return {
        "score": analysis.score,
        "corrections": analysis.corrections,
        "risks": analysis.injury_risks,
    }
```

### Data/Calculation Tools

```python
def calculate(expression: str) -> dict:
    """Safely evaluate mathematical expression.

    Args:
        expression: Math expression (e.g., "2 + 2", "sqrt(16)")

    Returns:
        Calculation result or error
    """
    try:
        result = safe_eval(expression)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": f"Invalid expression: {e}"}

def get_market_data(symbol: str, period: str = "1d") -> dict:
    """Get stock market data.

    Args:
        symbol: Stock ticker symbol
        period: Time period (1d, 1w, 1m, 1y)

    Returns:
        Market data with price, volume, change
    """
    data = market_api.get_stock(symbol, period=period)
    return {
        "symbol": symbol,
        "price": data.current_price,
        "change": data.price_change,
        "volume": data.volume,
    }
```

## MCPToolset Patterns

### SQLite Database MCP

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

database_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uvx',
            args=["mcp-server-sqlite", "--db-path", "data/app.db"],
        ),
    ),
)

agent = Agent(
    name="database_agent",
    tools=[database_toolset],
)
```

**Available Tools** (auto-discovered):
- `query`: Execute SQL SELECT queries
- `execute`: Execute SQL INSERT/UPDATE/DELETE
- `describe_table`: Get table schema
- `list_tables`: List all tables

### PostgreSQL Database MCP

```python
postgres_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uvx',
            args=["mcp-server-postgres"],
            env={
                "POSTGRES_CONNECTION": os.getenv("DATABASE_URL"),
            },
        ),
    ),
)
```

### Web Search MCP (Brave)

```python
search_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-brave-search"],
            env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")},
        ),
    ),
)
```

**Available Tools:**
- `brave_web_search`: Search the web
- `brave_local_search`: Search local businesses

### GitHub MCP

```python
github_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-github"],
            env={"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")},
        ),
    ),
)
```

**Available Tools:**
- `create_issue`: Create GitHub issue
- `create_pull_request`: Create PR
- `list_repositories`: List repos
- `search_code`: Search code across repos
- `get_issue`: Get issue details

### GitLab MCP

```python
gitlab_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-gitlab"],
            env={
                "GITLAB_TOKEN": os.getenv("GITLAB_TOKEN"),
                "GITLAB_URL": os.getenv("GITLAB_URL", "https://gitlab.com"),
            },
        ),
    ),
)
```

### Notion MCP

```python
notion_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-notion"],
            env={"NOTION_API_KEY": os.getenv("NOTION_API_KEY")},
        ),
    ),
)
```

**Available Tools:**
- `search_pages`: Search Notion pages
- `create_page`: Create new page
- `update_page`: Update existing page
- `query_database`: Query Notion database

### Slack MCP

```python
slack_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-slack"],
            env={
                "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN"),
                "SLACK_TEAM_ID": os.getenv("SLACK_TEAM_ID"),
            },
        ),
    ),
)
```

### Pinecone Multimodal MCP

```python
pinecone_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-pinecone"],
            env={
                "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
                "PINECONE_INDEX_NAME": "multimodal-kb",
            },
        ),
    ),
)
```

**Available Tools:**
- `query_vectors`: Semantic search
- `upsert_vectors`: Add/update vectors
- `delete_vectors`: Remove vectors
- `describe_index`: Index statistics

### Custom MCP Server

```python
custom_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python',
            args=["custom_mcp_server.py"],
            env={"API_KEY": os.getenv("CUSTOM_API_KEY")},
        ),
    ),
)
```

## Multi-MCP Agent

```python
# Agent with multiple MCP servers
agent = Agent(
    name="multi_tool_agent",
    model="gemini-2.5-flash",
    description="Agent with database, search, and GitHub access",
    tools=[
        database_toolset,  # SQLite database
        search_toolset,    # Brave web search
        github_toolset,    # GitHub integration
    ],
)
```

## Tool Best Practices

### 1. Naming

- Use descriptive verb_noun names: `search_faq`, `create_ticket`, `get_order`
- Avoid abbreviations: `analyze_image` not `analyze_img`

### 2. Docstrings

```python
def tool_name(param: str) -> dict:
    """Short one-line summary of what tool does.

    Longer description if needed, explaining behavior,
    constraints, or important details.

    Args:
        param: Description of parameter purpose

    Returns:
        Description of return value structure
    """
```

### 3. Return Values

Always return structured data:

```python
# Good - structured
return {
    "success": True,
    "data": result,
    "metadata": {"count": len(result)}
}

# Bad - unstructured
return "Found 5 results: " + str(result)
```

### 4. Error Handling

```python
def robust_tool(param: str) -> dict:
    """Tool with comprehensive error handling."""
    try:
        result = operation(param)
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}
```

### 5. Testing Tools

```python
# Test FunctionTool before adding to agent
tool_function = search_database

# Test directly
result = tool_function(query="test", limit=5)
assert result is not None

# Test with FunctionTool wrapper
from google.adk.tools import FunctionTool
tool = FunctionTool(tool_function)

# Test in agent
agent = Agent(name="test", tools=[tool])
```

## Related Files

- @agent-patterns.md - Agent architecture patterns
- @deployment-configs.md - Deployment configurations
- @streaming-patterns.md - Real-time patterns
