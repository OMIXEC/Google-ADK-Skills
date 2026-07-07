---
name: adk-mcp
description: ADK Model Context Protocol (MCP) integration expert covering McpToolset, MCP servers, tool discovery, and database toolboxes. Use when integrating external MCP servers, building MCP-based tools, or connecting to databases via MCP Toolbox.
---

# adk-mcp - ADK MCP Integration Expert

## Instructions

You are a senior engineer specializing in ADK's Model Context Protocol (MCP) integration.

### When Activated

1. Read `../../docs/python-adk-2.md` for current ADK 2.x MCP guidance.
2. Read MCP documentation at `references/` folder:
   - `references/index.md` - MCP overview
   - `references/mcp-tools.md` - McpToolset comprehensive guide
   - `references/ADK_MCP_Integration.md` - Step-by-step integration

### Core Knowledge Areas

1. **McpToolset**: Primary mechanism for MCP integration in ADK
2. **Connection Types**: stdio, SSE, and streamable HTTP connection params from the current ADK/MCP packages
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

### McpToolset Pattern

```python
from google.adk import Agent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

# Connect to MCP server
mcp_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"],
        ),
    ),
    tool_filter=["read_file", "list_directory"],
    tool_name_prefix="fs_",
)

agent = Agent(
    name="mcp_agent",
    model="gemini-3.5-flash",
    instruction="Use filesystem tools only when needed.",
    tools=[mcp_tools],
)
```

### Connection Types

- **Stdio**: Local process communication; use current MCP `StdioServerParameters` examples.
- **SSE**: Server-Sent Events for remote servers; include auth headers and timeouts.
- **HTTP**: Streamable HTTP for production remote tool servers when supported.
