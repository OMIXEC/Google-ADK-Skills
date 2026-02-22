---
name: ADK Integration Tools & MCP
description: This skill should be used when the user asks to "integrate MCP servers", "connect external tools", "add MCP server", "external service integration", or "model context protocol". Provides comprehensive guidance for integrating external systems and services using MCP (Model Context Protocol).
version: 1.0.0
---

# ADK Integration Tools & MCP

MCP (Model Context Protocol) enables seamless integration with external services and data sources. This skill covers setting up MCP servers and integrating them with agents.

## MCP Overview

MCP is a standard protocol for integrating external tools and services with AI agents:

```
Agent → MCP Client → MCP Server → External Service
                        ↓
                   Tools & Data
```

## Supported Integrations

### Pinecone (Vector Search)

```python
from adk_bidi.integrations import PineconeIntegration

pinecone = PineconeIntegration(
    api_key=os.getenv("PINECONE_API_KEY"),
    index_name="my-index"
)

agent.add_tool(pinecone.embed_tool())
agent.add_tool(pinecone.search_tool())
agent.add_tool(pinecone.upsert_tool())
```

Use for: Vector search, semantic similarity, embeddings

### SQLite/PostgreSQL (Databases)

```python
from adk_bidi.integrations import DatabaseIntegration

db = DatabaseIntegration(
    connection_string="postgresql://user:pass@host/db"
)

agent.add_tool(db.query_tool())
agent.add_tool(db.insert_tool())
agent.add_tool(db.update_tool())
```

Use for: Data queries, CRUD operations, business logic

### Brave Search (Web Search)

```python
from adk_bidi.integrations import BraveSearchIntegration

search = BraveSearchIntegration(
    api_key=os.getenv("BRAVE_API_KEY")
)

agent.add_tool(search.web_search_tool())
```

Use for: Web search, current information, research

### GitHub (Code Repository)

```python
from adk_bidi.integrations import GitHubIntegration

github = GitHubIntegration(
    token=os.getenv("GITHUB_TOKEN"),
    owner="username",
    repo="repo-name"
)

agent.add_tool(github.list_issues_tool())
agent.add_tool(github.create_issue_tool())
agent.add_tool(github.read_file_tool())
```

Use for: Repository management, issue tracking, code access

### Notion (Document Management)

```python
from adk_bidi.integrations import NotionIntegration

notion = NotionIntegration(
    token=os.getenv("NOTION_TOKEN"),
    database_id="database-id"
)

agent.add_tool(notion.query_database_tool())
agent.add_tool(notion.create_page_tool())
```

Use for: Document management, knowledge bases, wikis

### Slack (Team Communication)

```python
from adk_bidi.integrations import SlackIntegration

slack = SlackIntegration(
    token=os.getenv("SLACK_BOT_TOKEN"),
    channel="alerts"
)

agent.add_tool(slack.send_message_tool())
agent.add_tool(slack.read_messages_tool())
```

Use for: Team notifications, message integration, communication

### Custom MCP Servers

Build custom MCP servers for proprietary systems:

```python
from adk_bidi.mcp import MCPServer

class CustomMCPServer(MCPServer):
    def __init__(self, port=8001):
        super().__init__(port)
        self.register_tool(self.my_tool)

    def my_tool(self, param1: str) -> str:
        # Your implementation
        return result

    def start(self):
        self.run_server()
```

## Setting Up MCP Servers

### Configuration

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "pinecone": {
      "command": "python",
      "args": ["-m", "adk_bidi.integrations.pinecone_mcp"],
      "env": {
        "PINECONE_API_KEY": "${PINECONE_API_KEY}",
        "PINECONE_INDEX_HOST": "${PINECONE_INDEX_HOST}"
      }
    },
    "database": {
      "command": "python",
      "args": ["-m", "adk_bidi.integrations.database_mcp"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "github": {
      "command": "python",
      "args": ["-m", "adk_bidi.integrations.github_mcp"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Environment Variables

Store credentials in `.env`:

```bash
PINECONE_API_KEY=your_key
PINECONE_INDEX_HOST=your_host
DATABASE_URL=postgresql://user:pass@host/db
GITHUB_TOKEN=ghp_xxx
NOTION_TOKEN=secret_xxx
SLACK_BOT_TOKEN=xoxb_xxx
BRAVE_API_KEY=your_key
```

## Integrating with Agents

### Add Single Integration

```python
from adk_bidi.integrations import GitHubIntegration

github = GitHubIntegration(token=os.getenv("GITHUB_TOKEN"))
agent.add_tool(github.create_issue_tool())
```

### Add Multiple Integrations

```python
from adk_bidi.integrations import (
    GitHubIntegration,
    NotionIntegration,
    SlackIntegration
)

# Create integrations
github = GitHubIntegration(token=os.getenv("GITHUB_TOKEN"))
notion = NotionIntegration(token=os.getenv("NOTION_TOKEN"))
slack = SlackIntegration(token=os.getenv("SLACK_BOT_TOKEN"))

# Add to agent
agent.add_tool(github.list_issues_tool())
agent.add_tool(notion.query_database_tool())
agent.add_tool(slack.send_message_tool())
```

### Create Integration-Specific Agent

```python
class IntegrationAgent(Agent):
    def __init__(self):
        super().__init__()

        # Setup integrations
        self.github = GitHubIntegration(...)
        self.database = DatabaseIntegration(...)

        # Add tools
        self.add_tools_from_integration(self.github)
        self.add_tools_from_integration(self.database)

    def add_tools_from_integration(self, integration):
        for tool in integration.get_all_tools():
            self.add_tool(tool)
```

## Building Custom Integrations

Create MCP servers for proprietary systems:

```python
class PropertyManagementMCP(MCPServer):
    """MCP server for property management system."""

    def __init__(self, api_url: str, api_key: str):
        super().__init__(port=8002)
        self.api_url = api_url
        self.api_key = api_key

    @MCPTool(
        name="get_properties",
        description="Get all properties",
        params={
            "status": "Optional status filter (active, sold, pending)"
        }
    )
    async def get_properties(self, status: str = None) -> list:
        """Retrieve properties from API."""
        params = {"status": status} if status else {}
        return await self._call_api("GET", "/properties", params)

    @MCPTool(
        name="create_listing",
        description="Create new property listing",
        params={
            "address": "Property address",
            "price": "Listing price",
            "beds": "Number of bedrooms"
        }
    )
    async def create_listing(self, address: str, price: float, beds: int) -> dict:
        """Create a property listing."""
        return await self._call_api("POST", "/listings", {
            "address": address,
            "price": price,
            "bedrooms": beds
        })

    async def _call_api(self, method: str, endpoint: str, params: dict) -> dict:
        """Call the property management API."""
        # Implementation
        pass
```

## Error Handling for Integrations

```python
try:
    result = github.create_issue_tool()(
        title="Bug found",
        body="Description"
    )
except IntegrationError as e:
    logger.error(f"GitHub integration failed: {e}")
    # Fallback behavior

except AuthenticationError as e:
    logger.error("Invalid GitHub token")
    # Request re-authentication

except RateLimitError as e:
    logger.warning("GitHub rate limit reached, retrying later")
    # Implement backoff and retry
```

## Security Best Practices

**Do:**
- Store credentials in environment variables
- Use API tokens, not passwords
- Validate all API responses
- Log integration usage (without credentials)
- Implement timeout for API calls
- Use HTTPS for connections

**Don't:**
- Hardcode credentials in code
- Log full API responses
- Trust user input for API calls
- Skip API validation
- Leave integration errors silent
- Store credentials in version control

## Supporting Resources

### References
- **`references/mcp-servers.md`** - Supported MCP server catalog
- **`references/custom-mcp.md`** - Building custom MCP servers
- **`references/integration-patterns.md`** - Integration patterns and examples

### Examples
- **`examples/github-integration.py`** - GitHub integration example
- **`examples/database-integration.py`** - Database integration
- **`examples/custom-mcp-server.py`** - Custom MCP server

## Next Steps

1. **Choose integrations** - Which external services do you need?
2. **Set up credentials** - Configure `.env` and MCP servers
3. **Add to agent** - Integrate tools into agent
4. **Test connections** - Verify integrations work
5. **Deploy** - Use adk-production-deployment with MCP support

See **adk-custom-agent-builder** skill for implementing agents with tools.
