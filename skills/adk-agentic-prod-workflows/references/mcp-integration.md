# MCP Integration for ADK Workflows

MCP (Model Context Protocol) is the standard tool protocol for ADK agents. It enables agents to discover and invoke tools from external servers via JSON-RPC 2.0 over stdio, SSE, or HTTP transport.

## Architecture

```
┌──────────────┐     JSON-RPC 2.0      ┌──────────────┐
│  ADK Agent   │ ◄──────────────────► │  MCP Server   │
│  (MCPToolset)│    tools/list          │  (tools)      │
│              │    tools/call          │               │
└──────────────┘                       └──────────────┘
```

Client (ADK agent through `MCPToolset`) discovers tools from the server, then calls them. The server can expose tools, resources, and prompts.

## MCPToolset vs FunctionTool

| | FunctionTool | MCPToolset |
|---|---|---|
| **Location** | In-process function | External server process |
| **Language** | Same as agent | Any language |
| **Lifecycle** | Same as agent | Independent server lifecycle |
| **Discovery** | Manual registration | Auto-discovery from server |
| **Use when** | Simple utility functions, internal logic, no external deps | External APIs, DB access, separate security boundary, multi-language, shared infrastructure |

Rule: side-effect tools (DB writes, API calls) → prefer MCP. Pure computation, internal state → FunctionTool OK.

## MCP Server Building

### Python — using `mcp` package

```python
# mcp_server.py — MCP server exposing database tools
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio

server = Server("my-db-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_users",
            description="Query users table by filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="insert_order",
            description="Create a new order",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "item": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
                "required": ["user_id", "item", "quantity"],
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_users":
        # Parameterized query — never string interpolation
        rows = await db_query(
            "SELECT * FROM users WHERE user_id = %s LIMIT %s",
            (arguments["user_id"], arguments.get("limit", 50)),
        )
        return [TextContent(type="text", text=str(rows))]
    elif name == "insert_order":
        order_id = await db_execute(
            "INSERT INTO orders (user_id, item, quantity) VALUES (%s, %s, %s) RETURNING id",
            (arguments["user_id"], arguments["item"], arguments["quantity"]),
        )
        return [TextContent(type="text", text=f"Order created: {order_id}")]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

### Python — using FastMCP (simpler)

```python
# fastmcp_server.py
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def query_users(user_id: str, limit: int = 50) -> str:
    """Query users table. Returns JSON list of matching users."""
    rows = db_query("SELECT * FROM users WHERE user_id = %s LIMIT %s", (user_id, limit))
    return str(rows)

@mcp.tool()
def insert_order(user_id: str, item: str, quantity: int) -> str:
    """Create a new order. Returns order ID."""
    return db_execute(
        "INSERT INTO orders (user_id, item, quantity) VALUES (%s, %s, %s) RETURNING id",
        (user_id, item, quantity),
    )

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Go — using `mcp-go`

```go
// mcp_server.go
package main

import (
    "context"
    "encoding/json"
    "fmt"

    "github.com/mark3labs/mcp-go/mcp"
    "github.com/mark3labs/mcp-go/server"
)

func main() {
    s := server.NewMCPServer(
        "my-db-server", "1.0.0",
        server.WithToolCapabilities(true),
    )

    s.AddTool(mcp.NewTool("query_users",
        mcp.WithDescription("Query users table by filters"),
        mcp.WithString("user_id", mcp.Required()),
        mcp.WithNumber("limit", mcp.DefaultValue(50)),
    ), queryUsersHandler)

    s.AddTool(mcp.NewTool("insert_order",
        mcp.WithDescription("Create a new order"),
        mcp.WithString("user_id", mcp.Required()),
        mcp.WithString("item", mcp.Required()),
        mcp.WithNumber("quantity", mcp.Required()),
    ), insertOrderHandler)

    server.ServeStdio(s)
}

func queryUsersHandler(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
    userID := req.Params.Arguments["user_id"].(string)
    limit := int(req.Params.Arguments["limit"].(float64))
    rows, _ := dbQuery("SELECT * FROM users WHERE user_id = $1 LIMIT $2", userID, limit)
    result, _ := json.Marshal(rows)
    return mcp.NewToolResultText(string(result)), nil
}

func insertOrderHandler(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
    args := req.Params.Arguments
    orderID, _ := dbExecute(
        "INSERT INTO orders (user_id, item, quantity) VALUES ($1, $2, $3) RETURNING id",
        args["user_id"], args["item"], int(args["quantity"].(float64)),
    )
    return mcp.NewToolResultText(fmt.Sprintf("Order created: %v", orderID)), nil
}
```

### TypeScript — using `@modelcontextprotocol/sdk`

```typescript
// mcp_server.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "my-db-server",
  version: "1.0.0",
});

server.tool(
  "query_users",
  "Query users table by filters",
  {
    user_id: z.string().describe("User ID to query"),
    limit: z.number().default(50).describe("Max results"),
  },
  async ({ user_id, limit }) => {
    const rows = await dbQuery(
      "SELECT * FROM users WHERE user_id = $1 LIMIT $2",
      [user_id, limit],
    );
    return { content: [{ type: "text", text: JSON.stringify(rows) }] };
  },
);

server.tool(
  "insert_order",
  "Create a new order",
  {
    user_id: z.string(),
    item: z.string(),
    quantity: z.number().int().positive(),
  },
  async ({ user_id, item, quantity }) => {
    const orderId = await dbExecute(
      "INSERT INTO orders (user_id, item, quantity) VALUES ($1, $2, $3) RETURNING id",
      [user_id, item, quantity],
    );
    return { content: [{ type: "text", text: `Order created: ${orderId}` }] };
  },
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

## MCP Client Integration in ADK Agents

### Python — `MCPToolset` in `LlmAgent`

```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Stdio transport (local MCP server)
agent = LlmAgent(
    model="gemini-2.5-flash",
    name="db_assistant",
    instruction="Use database tools to help users query and insert data.",
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="python3",
                args=["/path/to/mcp_server.py"],
            ),
            tool_filter=["query_users", "insert_order"],  # Optional: allowlist
        ),
    ],
)
```

### Python — SSE transport (remote MCP server)

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

agent = LlmAgent(
    model="gemini-2.5-flash",
    name="remote_assistant",
    instruction="Use remote tools to help users.",
    tools=[
        MCPToolset(
            connection_params=SseServerParams(
                url="https://mcp-server.example.com/sse",
                headers={"Authorization": f"Bearer {os.getenv('MCP_TOKEN')}"},
            ),
        ),
    ],
)
```

### Python — `from_server` helper (simpler)

```python
tools, exit_stack = await MCPToolset.from_server(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem"],
    ),
)
agent = LlmAgent(tools=tools)
# ... use agent ...
await exit_stack.aclose()
```

## Transport Selection

| Transport | When | Pros | Cons |
|-----------|------|------|------|
| **stdio** | Local development, same machine | Zero network overhead, simple | Same process tree, no remote access |
| **SSE** | Remote server, cross-machine | Standard HTTP, CDN-friendly | Polling overhead, unidirectional events |
| **HTTP** | Production remote, streaming | Bidirectional, low latency | More complex setup |

Default: stdio for dev, SSE for remote, HTTP for high-throughput production.

## MCP Resource Exposure

MCP servers can also expose resources (files, DB views, API endpoints) that agents can read without invoking tools:

```python
# Python — expose a resource
@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="db://users/schema",
            name="Users Schema",
            description="Current users table schema",
            mimeType="text/plain",
        ),
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "db://users/schema":
        return "CREATE TABLE users (id TEXT, email TEXT, ...)"
    raise ValueError(f"Unknown resource: {uri}")
```

## Tool Discovery & Filtering

```python
# Allowlist — only these tools are available to the agent
MCPToolset(
    connection_params=StdioServerParameters(...),
    tool_filter=["query_users", "insert_order"],
)

# Blocklist — all tools except these
# (Filter on server side or wrap MCPToolset)

# No filter — all server tools exposed to agent (use with caution)
MCPToolset(connection_params=StdioServerParameters(...))
```

## MCP Security

1. **Auth at transport level**: SSE/HTTP servers should require `Authorization` header. stdio inherits OS process permissions.
2. **Tool access control**: Use `tool_filter` to limit which tools each agent can access.
3. **Parameterized queries**: MCP tools wrapping DB access must use parameterized queries — never string interpolation.
4. **Network isolation**: Remote MCP servers should be in same VPC or use mTLS.
5. **Secrets**: MCP server credentials from env/secret manager, never hardcoded.
6. **Audit logging**: Log every `tools/call` with tool name, caller agent, latency, status.

## When to Use MCP vs FunctionTool

```
┌─────────────────────────────────────────────────┐
│ Need external API call, DB access, or file I/O?  │
│          YES → Use MCPToolset (separate process) │
│          NO  ↓                                   │
│ Need cross-language tool sharing?                │
│          YES → Use MCPToolset                    │
│          NO  ↓                                   │
│ Pure computation, internal state?                │
│          YES → Use FunctionTool (in-process)     │
│          NO  ↓                                   │
│ Reconsider your tool design                      │
└─────────────────────────────────────────────────┘
```

Rule of thumb: MCP for side effects and multi-language. FunctionTool for pure functions and internal logic.

## MCP in Workflow Scaffolding

When scaffolding a workflow with `--with-mcp`:

1. Generate `mcp_server.py` (or `.go`, `.ts`) alongside agent code
2. Wire `MCPToolset` into agent `tools` list
3. Generate `mcp_config.yaml` with server connection params
4. Add MCP server to `docker-compose.yml` if local deployment
5. Add MCP health check to monitoring
