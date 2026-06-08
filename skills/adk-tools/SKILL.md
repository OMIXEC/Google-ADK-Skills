---
name: adk-tools
description: ADK tools expert covering custom function tools, Google built-in tools (Search, Code Execution), OpenAPI integrations, and tool composition. Use when creating custom tools, integrating external APIs, or configuring built-in Google tools.
---

# adk-tools - ADK Tools Expert

## Instructions

You are a senior engineer specializing in ADK tool creation and integration.

### When Activated

1. Read tools documentation at `references/` folder:
   - `references/index.md` - Tools overview
   - `references/function-tools.md` - Custom function tools
   - `references/built-in-tools.md` - Google built-in tools
   - `references/mcp-tools.md` - MCP tool integration
   - `references/openapi-tools.md` - OpenAPI integration
   - `references/google-cloud-tools.md` - GCP-specific tools

### Core Knowledge Areas

1. **Custom Function Tools**: Python functions decorated as tools, type hints, docstrings
2. **Built-in Google Tools**: google_search, code_execution, vertex_ai_search
3. **OpenAPI Tools**: External API specifications, automatic tool generation
4. **Tool Composition**: Multiple tools, parallel execution, chained operations
5. **Human-in-the-Loop**: Tools requiring human approval, confirmation flows

### Tool Types

| Type | Use Case | Example |
|------|----------|---------|
| Custom Function | Domain-specific logic | `@tool def search_inventory(...)` |
| Built-in Google | Search, code execution | `google_search`, `code_execution` |
| OpenAPI | External APIs | REST API integration |
| Agent Tool | Agent as tool | Sub-agent delegation |

### Custom Tool Pattern

```python
from google.adk.tools import tool

@tool
def get_weather(city: str, units: str = "celsius") -> dict:
    """Get current weather for a city.

    Args:
        city: City name to get weather for
        units: Temperature units (celsius or fahrenheit)

    Returns:
        Weather data including temperature and conditions
    """
    # Implementation
    return {"city": city, "temp": 22, "conditions": "sunny"}
```

### Built-in Tools

```python
from google.adk.tools import google_search, code_execution

agent = Agent(
    model="gemini-2.0-flash",
    tools=[google_search, code_execution, custom_tool]
)
```
