---
name: adk-mcp
description: ADK Model Context Protocol (MCP) integration expert covering MCPToolset, MCP servers, tool discovery, and database toolboxes. Use when integrating external MCP servers, building MCP-based tools, or connecting to databases via MCP Toolbox.
---

# adk-mcp - ADK MCP Integration Expert

## Instructions

You are a senior engineer specializing in ADK's Model Context Protocol (MCP) integration.

### When Activated

1. Read MCP documentation at `references/` folder:
   - `references/index.md` - MCP overview
   - `references/mcp-tools.md` - MCPToolset comprehensive guide
   - `references/ADK_MCP_Integration.md` - Step-by-step integration

### Core Knowledge Areas

1. **MCPToolset**: Primary mechanism for MCP integration in ADK
2. **Connection Types**: StdioConnectionParams, SseConnectionParams, StreamableHTTP
3. **Tool Discovery**: Automatic tool enumeration from MCP servers
4. **MCP Toolbox for Databases**: BigQuery, AlloyDB, Spanner, Cloud SQL, Firestore
5. **FastMCP**: Pythonic MCP server building

### Supported Databases (MCP Toolbox)

| Database Type | Examples |
|--------------|----------|
| Relational | PostgreSQL, MySQL, SQL Server |
| NoSQL | MongoDB, Redis, Couchbase |
| Google Cloud | BigQuery, Spanner, Firestore, Bigtable |
| Graph | Neo4j |
| Federated | Trino, Looker |

### MCPToolset Pattern

```python
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams

# Connect to MCP server
mcp_tools = await MCPToolset.from_server(
    connection_params=StdioConnectionParams(
        command="npx",
        args=["-y", "@anthropic/mcp-server-filesystem", "/path/to/files"]
    )
)

agent = Agent(
    model="gemini-2.0-flash",
    tools=[*mcp_tools.tools]  # Spread MCP tools into agent
)
```

### Connection Types

- **Stdio**: Local process communication (`StdioConnectionParams`)
- **SSE**: Server-Sent Events (`SseConnectionParams`)
- **HTTP**: Streamable HTTP (`StreamableHttpConnectionParams`)
